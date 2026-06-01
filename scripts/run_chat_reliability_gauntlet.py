"""Run long multi-turn material-chat reliability gauntlets.

This runner is intentionally separate from one-turn replay benchmarks. It keeps
one chat session alive across many turns, saves/resumes at checkpoints, and
audits the durable turn contract, retrieval-query separation, citation validity,
and trace replay surface for every turn.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaion._types import is_string_mapping, parse_json_object_fragment
from hephaion.agent.citation import verify_citations, verify_response
from hephaion.chat.automation import iter_chat_events
from hephaion.chat.compaction import compact_session
from hephaion.chat.events import AssistantDeltaEvent, TurnCompleteEvent
from hephaion.chat.evidence import build_turn_evidence_from_refs
from hephaion.chat.session import ChatSession, create_session, resume_session, save_session
from hephaion.chat.turn_contract import (
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from hephaion.rag import EvidenceChunk, TurnEvidence
from hephaion.runtime import (
    ChatConfig,
    Conversation,
    EngineError,
    Message,
    reset_provider_circuit_breaker,
    stream_reply,
)
from hephaion.study import LearningState
from scripts.create_chat_reliability_fixture import (
    DEFAULT_SEED_PREFIX,
    create_fixture_armories,
    create_fixture_armory,
)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_CODEX_MODEL = "gpt-5.4-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_GAUNTLET_CODEX_TIMEOUT_SECONDS = 30.0
PROVIDER_OPENAI_CODEX = "openai-codex"
TRANSIENT_PROVIDER_RETRIES = 2
TRANSIENT_PROVIDER_RETRY_DELAYS_SECONDS = (1.0, 2.0)
EVIDENCE_CITATION_RE = re.compile(r"\[(?:e|E)\d+\]")
WORD_RE = re.compile(r"[^\W\d_][\w'-]*")

CATEGORY_VAGUE_FOLLOWUP = "vague_followup"
CATEGORY_CONTINUATION = "continuation"
CATEGORY_PRIOR_REFERENCE = "prior_reference"
CATEGORY_TOPIC_SWITCH = "topic_switch"
CATEGORY_SOURCE_SPECIFIC = "source_specific"
CATEGORY_CITATION_CHECK = "citation_check"
CATEGORY_LOW_EVIDENCE = "low_evidence"

LOW_EVIDENCE_PROMPTS = tuple(
    f"Using only the sources, what exact phrase supports absent-test-marker-{index}?"
    for index in range(1, 6)
)

VAGUE_FOLLOWUP_PROMPT_BANKS = (
    (
        "What else stands out?",
        "Go on.",
        "Tell me more.",
        "Why does that matter?",
        "Explain that more slowly.",
        "Give an example from the material.",
        "Compare the last two points.",
        "Is that important?",
        "What does the second point mean?",
        "Can you expand on that?",
        "Und was noch?",
        "Continue from the cited evidence.",
        "What should I notice there?",
        "How does that connect?",
        "Make that concrete.",
        "What follows from it?",
        "Show another angle.",
        "Why would a learner care?",
        "Can you clarify the claim you just cited?",
        "Give me the next useful detail.",
    ),
    (
        "What else should I take from that?",
        "Please continue.",
        "Say more about the same point.",
        "Why is that useful?",
        "Slow that explanation down.",
        "Use the material to give one example.",
        "Compare those two cited ideas.",
        "Does that point matter for learning?",
        "What is the meaning of the second idea?",
        "Can you develop that answer further?",
        "Was kommt noch dazu?",
        "Keep going from the evidence you cited.",
        "What detail deserves attention there?",
        "How is that connected to the prior answer?",
        "Make the point practical.",
        "What does that imply next?",
        "Show a different source-backed angle.",
        "Why should a learner remember it?",
        "Can you unpack the claim from the citation?",
        "Give another useful detail from there.",
    ),
    (
        "What more is worth noting?",
        "Continue.",
        "Add more context.",
        "Why should I care about that?",
        "Break that down further.",
        "Ground an example in the source.",
        "Compare the two ideas you just gave.",
        "Is that a key point?",
        "Explain the second item in plain language.",
        "Can you elaborate from the same evidence?",
        "Y que mas?",
        "Carry on from the cited material.",
        "What should stand out to me?",
        "How does that fit with the answer so far?",
        "Make it specific.",
        "What comes after that idea?",
        "Give me another perspective from the source.",
        "Why would this help someone learn?",
        "Clarify the cited claim.",
        "What is the next detail I should know?",
    ),
)

MIXED_FOLLOWUP_PROMPT_BANKS = (
    (
        "Give a concrete example tied to a citation.",
        "Explain how a beginner might misunderstand that.",
        "Compare this with the previous topic.",
        "What is the shortest accurate version?",
        "Can you make a two-step learning checklist from the evidence?",
        "Now ask me one source-grounded recall question.",
        "Clarify the most technical term you just used.",
        "What should I review before this?",
        "Give another cited detail, but keep it concise.",
        "How would this show up in an exam-style question?",
    ),
    (
        "Give a source-linked example.",
        "What mistake would a beginner make here?",
        "Relate this back to the previous topic.",
        "Compress that into the briefest accurate version.",
        "Turn the evidence into a two-step checklist.",
        "Ask one recall question grounded in the source.",
        "Define the most technical term from that answer.",
        "What background point should I review first?",
        "Add one concise cited detail.",
        "Make an exam-style question from this.",
    ),
    (
        "Show a concrete example from the cited material.",
        "Name a likely beginner misunderstanding.",
        "Compare that with the topic before it.",
        "Give the shortest version that stays accurate.",
        "Make a two-step checklist from the source evidence.",
        "Quiz me with one source-backed recall prompt.",
        "Explain the hardest term you used.",
        "What should I revisit before continuing?",
        "Add one more cited detail in one sentence.",
        "How might this appear on a short-answer exam?",
    ),
)


class ReliabilityTurnResult(TypedDict):
    turn: int
    prompt: str
    categories: list[str]
    answer_len: int
    retrieval_query: str
    retrieval_strategy: str
    evidence_refs: list[str]
    validation_result: str
    claim_audit_checked: bool
    claim_audit_reason: str
    unsupported_claims: list[str]
    failures: list[str]


class ReliabilityConversationMetrics(TypedDict):
    turn_pass_rate: float
    passed_turns: int
    failed_turns: int
    citation_verification_failures: int
    missing_citation_failures: int
    literal_followup_retrieval_failures: int
    claim_audit_checked_turns: int
    unsupported_claim_failures: int


class ReliabilityConversationReport(TypedDict):
    armory: str
    level: str
    model: str
    base_url: str
    turns: int
    status: int
    category_counts: dict[str, int]
    requirements: dict[str, int]
    resume_count: int
    compact_count: int
    trace_path: NotRequired[str]
    trace_user_turns: int
    trace_reply_contracts: int
    trace_replayable_turns: int
    unsupported_claims_checked: bool
    metrics: ReliabilityConversationMetrics
    failures: list[str]
    results: list[ReliabilityTurnResult]


class ReliabilitySuiteMetrics(TypedDict):
    turn_pass_rate: float
    total_turns: int
    total_failed_turns: int
    conversations_with_failures: int
    claim_audit_checked_conversations: int


class ReliabilitySuiteReport(TypedDict):
    level: str
    status: int
    conversations: int
    metrics: ReliabilitySuiteMetrics
    failures: list[str]
    reports: list[ReliabilityConversationReport]


class ClaimAuditResult(TypedDict):
    checked: bool
    passed: bool
    reason: str
    unsupported_claims: list[str]


class TraceAudit(TypedDict):
    user_turns: int
    reply_contracts: int
    replayable_turns: int
    failures: list[str]


@dataclass(frozen=True, slots=True)
class _PromptRetrySnapshot:
    messages: tuple[Message, ...]
    learning_state: LearningState
    last_turn_evidence: TurnEvidence | None
    last_plan_intent: str
    last_turn_contract: TurnContract | None
    trace_path: Path | None
    trace_size: int


@dataclass(frozen=True, slots=True)
class ReliabilityTurnSpec:
    prompt: str
    categories: tuple[str, ...] = ()
    require_citations_when_evidence: bool = False


@dataclass(frozen=True, slots=True)
class RunRequirements:
    turns: int
    vague_followups: int = 0
    continuations: int = 0
    prior_references: int = 0
    topic_switches: int = 0
    source_specific: int = 0
    citation_checks: int = 0
    low_evidence: int = 0
    resumes: int = 0
    compactions: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "turns": self.turns,
            "vague_followups": self.vague_followups,
            "continuations": self.continuations,
            "prior_references": self.prior_references,
            "topic_switches": self.topic_switches,
            "source_specific": self.source_specific,
            "citation_checks": self.citation_checks,
            "low_evidence": self.low_evidence,
            "resumes": self.resumes,
            "compactions": self.compactions,
        }


def stress_requirements(turns: int = 15) -> RunRequirements:
    return RunRequirements(
        turns=turns,
        vague_followups=3,
        continuations=2,
        prior_references=1,
        topic_switches=1,
        source_specific=1,
        citation_checks=1,
        low_evidence=1,
        resumes=1,
    )


def full_requirements(turns: int = 100) -> RunRequirements:
    return RunRequirements(
        turns=turns,
        vague_followups=20,
        continuations=10,
        prior_references=10,
        topic_switches=10,
        source_specific=10,
        citation_checks=10,
        low_evidence=5,
        resumes=5,
        compactions=3,
    )


def focus_requirements(turns: int = 22) -> RunRequirements:
    return RunRequirements(
        turns=turns,
        vague_followups=6,
        continuations=2,
        prior_references=5,
        topic_switches=3,
        source_specific=2,
        citation_checks=2,
        low_evidence=1,
        resumes=1,
    )


def built_in_turns(*, turns: int, seed: int = 0) -> list[ReliabilityTurnSpec]:
    """Build a generic long-conversation script without corpus-private terms."""
    specs = [_turn("What is the material about?", (CATEGORY_TOPIC_SWITCH,), citations=True)]
    specs.extend(_vague_followup_turns(seed=seed))
    specs.extend(_prior_reference_turns())
    specs.extend(_topic_switch_turns())
    specs.extend(_source_specific_turns())
    specs.extend(_citation_check_turns())
    specs.extend(_low_evidence_turns())
    specs.extend(_mixed_followup_turns(seed=seed))
    while len(specs) < turns:
        specs.extend(_mixed_followup_turns(seed=len(specs) + seed))
    return specs[:turns]


def focused_turns() -> list[ReliabilityTurnSpec]:
    """Exercise recent weak structural transitions without replaying the full suite."""
    return [
        _turn("What do you think about the material?", (CATEGORY_TOPIC_SWITCH,), citations=True),
        _turn(
            "Switch to a different source-backed point in the material and summarize it.",
            (CATEGORY_TOPIC_SWITCH,),
            citations=True,
        ),
        _turn("Where did that come from?", (CATEGORY_CITATION_CHECK,), citations=True),
        _turn(
            "Explain the term used in the last citation.",
            (CATEGORY_PRIOR_REFERENCE,),
            citations=True,
        ),
        _turn(
            "Compare the first and third cited ideas.",
            (CATEGORY_PRIOR_REFERENCE,),
            citations=True,
        ),
        _turn(
            "What assumption is behind the second cited claim?",
            (CATEGORY_PRIOR_REFERENCE,),
            citations=True,
        ),
        _turn(
            "Restate the previous answer using only source-backed claims.",
            (CATEGORY_PRIOR_REFERENCE,),
            citations=True,
        ),
        _turn(
            "Give a counterexample or limitation for the previous point if the material has one.",
            (CATEGORY_PRIOR_REFERENCE,),
            citations=True,
        ),
        _turn(
            "Switch to another source-backed point in the material and summarize the key idea.",
            (CATEGORY_TOPIC_SWITCH,),
            citations=True,
        ),
        _turn(
            "In that source, what is the stated definition, rule, or procedure?",
            (CATEGORY_SOURCE_SPECIFIC,),
            citations=True,
        ),
        _turn("Give a source-linked example.", (CATEGORY_VAGUE_FOLLOWUP,), citations=True),
        _turn(
            "Name a likely beginner misunderstanding.",
            (CATEGORY_VAGUE_FOLLOWUP,),
            citations=True,
        ),
        _turn(
            "Add one more cited detail in one sentence.",
            (CATEGORY_VAGUE_FOLLOWUP,),
            citations=True,
        ),
        _turn(
            "Turn the evidence into a two-step checklist.",
            (CATEGORY_VAGUE_FOLLOWUP,),
            citations=True,
        ),
        _turn(
            "Ask one recall question grounded in the source.",
            (CATEGORY_VAGUE_FOLLOWUP,),
            citations=True,
        ),
        _turn(
            "Now switch to another source-backed topic and explain its central rule or method.",
            (CATEGORY_TOPIC_SWITCH,),
            citations=True,
        ),
        _turn(
            "In that source, what does the rule or method follow from?",
            (CATEGORY_SOURCE_SPECIFIC,),
            citations=True,
        ),
        _turn(
            "Compare that with the topic before it.",
            (CATEGORY_VAGUE_FOLLOWUP,),
            citations=True,
        ),
        _turn(
            "What is the shortest accurate version?",
            (CATEGORY_VAGUE_FOLLOWUP,),
            citations=True,
        ),
        _turn(
            "Which citation supports the last answer?",
            (CATEGORY_CITATION_CHECK,),
            citations=True,
        ),
        _turn(
            "Use the source with the strongest procedural wording and explain the procedure.",
            (CATEGORY_SOURCE_SPECIFIC,),
            citations=True,
        ),
        _turn(
            "What background point should I review first?",
            (CATEGORY_VAGUE_FOLLOWUP,),
            citations=True,
        ),
        _turn(
            "What else should I take from that?",
            (CATEGORY_VAGUE_FOLLOWUP, CATEGORY_CONTINUATION),
            citations=True,
        ),
        _turn(
            "Continue from the cited evidence.",
            (CATEGORY_VAGUE_FOLLOWUP, CATEGORY_CONTINUATION),
            citations=True,
        ),
        _turn(
            "What is the most important cited phrase from that answer?",
            (CATEGORY_PRIOR_REFERENCE,),
            citations=True,
        ),
        _turn(
            LOW_EVIDENCE_PROMPTS[0],
            (CATEGORY_LOW_EVIDENCE,),
        ),
    ]


def stress_turns(*, seed: int = 0) -> list[ReliabilityTurnSpec]:
    """Build a short stress script that still exercises every required category."""
    mixed_followups = _mixed_followup_turns(seed=seed)
    return [
        _turn("What is the material about?", (CATEGORY_TOPIC_SWITCH,), citations=True),
        *_vague_followup_turns(seed=seed)[:3],
        *_prior_reference_turns()[:1],
        *_source_specific_turns()[:1],
        *_citation_check_turns()[:1],
        *mixed_followups[:5],
        *mixed_followups[6:8],
        *_low_evidence_turns()[:1],
    ][:15]


def _turn(
    prompt: str,
    categories: Iterable[str],
    *,
    citations: bool = False,
) -> ReliabilityTurnSpec:
    return ReliabilityTurnSpec(
        prompt=prompt,
        categories=tuple(categories),
        require_citations_when_evidence=citations,
    )


def _vague_followup_turns(*, seed: int) -> list[ReliabilityTurnSpec]:
    rotated = _seeded_prompt_bank(VAGUE_FOLLOWUP_PROMPT_BANKS, seed)
    return [
        _turn(
            prompt,
            (
                CATEGORY_VAGUE_FOLLOWUP,
                CATEGORY_CONTINUATION if index < 10 else CATEGORY_PRIOR_REFERENCE,
            ),
            citations=True,
        )
        for index, prompt in enumerate(rotated)
    ]


def _prior_reference_turns() -> list[ReliabilityTurnSpec]:
    prompts = [
        "What does bullet 1 depend on?",
        "Where does the cited claim about the method come from?",
        "Explain the term used in the last citation.",
        "Give a counterexample or limitation for the previous point if the material has one.",
        "Compare the first and third cited ideas.",
        "Restate the previous answer using only source-backed claims.",
        "Which prior citation is strongest?",
        "What assumption is behind the second cited claim?",
        "Can you turn the previous point into a practice question?",
        "What is the most important cited phrase from that answer?",
    ]
    return [_turn(prompt, (CATEGORY_PRIOR_REFERENCE,), citations=True) for prompt in prompts]


def _topic_switch_turns() -> list[ReliabilityTurnSpec]:
    prompts = [
        "Switch to algorithms and summarize the key idea from the source.",
        "Now switch to calculus and explain the central rule.",
        "Move to physics and identify the main concept.",
        "Switch to study methods and explain the learning advice.",
        "Now use the history material and summarize one source-backed point.",
        "Change topic to exercises and explain what kind of work they ask for.",
        "Switch to exams and identify what the material expects.",
        "Move to any formula-heavy material and explain one formula's role.",
        "Switch to a non-math source and summarize it with citations.",
        "Now compare two different source areas.",
    ]
    return [_turn(prompt, (CATEGORY_TOPIC_SWITCH,), citations=True) for prompt in prompts]


def _source_specific_turns() -> list[ReliabilityTurnSpec]:
    prompts = [
        "In the algorithms source, how is the next item selected?",
        "In the calculus source, what does the rule follow from?",
        "In the physics source, what is decomposed?",
        "In the study-methods source, what does practice require?",
        "In the history source, what claim is actually supported?",
        "Which source discusses exercises, and what does it ask the learner to do?",
        "Which source has exam-style material, and what is one expected task?",
        "Use one source only: explain a definition from it.",
        "Use the source with the clearest example and summarize the example.",
        "Use the source with the strongest procedural wording and explain the procedure.",
    ]
    return [_turn(prompt, (CATEGORY_SOURCE_SPECIFIC,), citations=True) for prompt in prompts]


def _citation_check_turns() -> list[ReliabilityTurnSpec]:
    prompts = [
        "Where did that come from?",
        "Which citation supports the last answer?",
        "Show the evidence for the previous claim.",
        "Can you verify the source for that?",
        "Point me to the cited material behind the last point.",
        "Which evidence block backs up the comparison?",
        "Does the source really say that?",
        "Quote the smallest source-backed phrase that supports it.",
        "What citation should I check first?",
        "Separate what is directly cited from what is inferred.",
    ]
    return [_turn(prompt, (CATEGORY_CITATION_CHECK,), citations=True) for prompt in prompts]


def _low_evidence_turns() -> list[ReliabilityTurnSpec]:
    return [_turn(prompt, (CATEGORY_LOW_EVIDENCE,)) for prompt in LOW_EVIDENCE_PROMPTS]


def _mixed_followup_turns(*, seed: int) -> list[ReliabilityTurnSpec]:
    return [
        _turn(prompt, (CATEGORY_VAGUE_FOLLOWUP,), citations=True)
        for prompt in _seeded_prompt_bank(MIXED_FOLLOWUP_PROMPT_BANKS, seed)
    ]


def _seeded_prompt_bank(prompt_banks: Sequence[Sequence[str]], seed: int) -> list[str]:
    if not prompt_banks:
        return []
    bank_index = seed % len(prompt_banks)
    rotation = seed // len(prompt_banks)
    return _rotated(tuple(prompt_banks[bank_index]), rotation)


def _rotated(items: Sequence[str], seed: int) -> list[str]:
    if not items:
        return []
    offset = seed % len(items)
    return [*items[offset:], *items[:offset]]


def run_reliability_conversation(
    armory_path: Path,
    config: ChatConfig,
    *,
    level: str,
    turns: Sequence[ReliabilityTurnSpec],
    requirements: RunRequirements,
    resume_every: int,
    compact_every: int = 0,
    require_trace: bool = True,
    audit_claims: bool = False,
    progress: bool = False,
) -> ReliabilityConversationReport:
    session = create_session(config, armory_path)
    results: list[ReliabilityTurnResult] = []
    failures: list[str] = []
    resume_count = 0
    compact_count = 0

    for index, spec in enumerate(turns, start=1):
        try:
            answer = _run_prompt(session, spec.prompt)
            result = _turn_result(
                index,
                spec,
                session,
                answer,
                config,
                audit_claims=audit_claims,
            )
        except Exception as exc:
            result = _exception_turn_result(index, spec, session, exc)
            results.append(result)
            if progress:
                _print_turn_progress(level, result, len(turns))
            failures.extend(f"turn {index}: {failure}" for failure in result["failures"])
            break
        results.append(result)
        if progress:
            _print_turn_progress(level, result, len(turns))
        failures.extend(f"turn {index}: {failure}" for failure in result["failures"])
        if compact_every > 0 and index % compact_every == 0:
            compact_session(session)
            compact_count += 1
        if resume_every > 0 and index % resume_every == 0:
            save_session(session)
            session.trace.close()
            session = resume_session(config, armory_path, session.session_id)
            resume_count += 1

    executed_turns = turns[: len(results)]
    category_counts = _category_counts(executed_turns)
    halted_by_exception = _conversation_halted_by_turn_exception(results)
    if not halted_by_exception:
        if len(results) < requirements.turns:
            failures.append(f"turn count {len(results)} below required {requirements.turns}")
        failures.extend(
            _requirement_failures(category_counts, requirements, resume_count, compact_count)
        )
    trace_path = session.trace.path
    trace_audit = _trace_audit(trace_path)
    if require_trace:
        failures.extend(
            _trace_failures(trace_path, trace_audit, _expected_trace_reply_turns(results))
        )
    report: ReliabilityConversationReport = {
        "armory": str(armory_path),
        "level": level,
        "model": config.model,
        "base_url": config.base_url,
        "turns": len(results),
        "status": 1 if failures else 0,
        "category_counts": dict(category_counts),
        "requirements": requirements.to_dict(),
        "resume_count": resume_count,
        "compact_count": compact_count,
        "trace_user_turns": trace_audit["user_turns"],
        "trace_reply_contracts": trace_audit["reply_contracts"],
        "trace_replayable_turns": trace_audit["replayable_turns"],
        "unsupported_claims_checked": audit_claims,
        "metrics": _conversation_metrics(results),
        "failures": failures,
        "results": results,
    }
    if trace_path is not None:
        report["trace_path"] = str(trace_path)
    return report


def _print_turn_progress(level: str, result: ReliabilityTurnResult, total: int) -> None:
    status = "fail" if result["failures"] else "ok"
    failure_note = f" failures={len(result['failures'])}" if result["failures"] else ""
    print(
        f"{level} turn {result['turn']}/{total} {status}"
        f" answer={result['answer_len']} chars{failure_note}",
        flush=True,
    )


def _conversation_halted_by_turn_exception(results: Sequence[ReliabilityTurnResult]) -> bool:
    return bool(results and _turn_result_raised(results[-1]))


def _expected_trace_reply_turns(results: Sequence[ReliabilityTurnResult]) -> int:
    return sum(1 for result in results if not _turn_result_raised(result))


def _turn_result_raised(result: ReliabilityTurnResult) -> bool:
    return any(failure.startswith("turn raised ") for failure in result["failures"])


def _run_prompt(session: ChatSession, prompt: str) -> str:
    for attempt in range(TRANSIENT_PROVIDER_RETRIES + 1):
        snapshot = _prompt_retry_snapshot(session)
        try:
            return _run_prompt_once(session, prompt)
        except EngineError as exc:
            if attempt >= TRANSIENT_PROVIDER_RETRIES or not _transient_provider_error(exc):
                _restore_prompt_retry_snapshot(session, snapshot, restore_trace=False)
                raise
            reset_provider_circuit_breaker()
            _restore_prompt_retry_snapshot(session, snapshot, restore_trace=True)
            _sleep_before_transient_retry(attempt)
    return ""


def _prompt_retry_snapshot(session: ChatSession) -> _PromptRetrySnapshot:
    trace_path = session.trace.path
    return _PromptRetrySnapshot(
        messages=tuple(
            Message(message.role, message.content) for message in session.conversation.messages
        ),
        learning_state=session.learning_state.clone(),
        last_turn_evidence=session.last_turn_evidence,
        last_plan_intent=session.last_plan_intent,
        last_turn_contract=session.last_turn_contract,
        trace_path=trace_path,
        trace_size=(
            trace_path.stat().st_size
            if isinstance(trace_path, Path) and trace_path.exists()
            else 0
        ),
    )


def _restore_prompt_retry_snapshot(
    session: ChatSession,
    snapshot: _PromptRetrySnapshot,
    *,
    restore_trace: bool,
) -> None:
    session.conversation = Conversation(
        [Message(message.role, message.content) for message in snapshot.messages]
    )
    session.learning_state = snapshot.learning_state.clone()
    session.last_turn_evidence = snapshot.last_turn_evidence
    session.last_plan_intent = snapshot.last_plan_intent
    session.last_turn_contract = snapshot.last_turn_contract
    if restore_trace:
        _restore_trace_checkpoint(session, snapshot)


def _restore_trace_checkpoint(session: ChatSession, snapshot: _PromptRetrySnapshot) -> None:
    if snapshot.trace_path is None:
        return
    session.trace.close()
    if not snapshot.trace_path.exists():
        return
    with snapshot.trace_path.open("r+b") as file_handle:
        file_handle.truncate(snapshot.trace_size)


def _run_prompt_once(session: ChatSession, prompt: str) -> str:
    parts: list[str] = []
    completed = ""
    for event in iter_chat_events(session, prompt):
        if isinstance(event, AssistantDeltaEvent):
            parts.append(event.delta)
        elif isinstance(event, TurnCompleteEvent):
            completed = event.full_text
    answer = "".join(parts).strip()
    return completed.strip() or answer


def _transient_provider_error(exc: EngineError) -> bool:
    message = str(exc).casefold()
    if "429" in message or "too many requests" in message or "rate limit" in message:
        return False
    return any(
        fragment in message
        for fragment in (
            "timed out",
            "timeout",
            "upstream connect error",
            "remote connection failure",
            "connection reset",
            "connection refused",
            "retry your request",
            "transport failure",
            "disconnect/reset before headers",
            "backend request failed",
        )
    )


def _turn_result(
    turn: int,
    spec: ReliabilityTurnSpec,
    session: ChatSession,
    answer: str,
    config: ChatConfig,
    *,
    audit_claims: bool,
) -> ReliabilityTurnResult:
    contract = session.last_turn_contract
    evidence = session.last_turn_evidence
    claim_audit_evidence = _claim_audit_evidence(session, config)
    failures: list[str] = []
    if not answer:
        failures.append("empty answer")
    if not _answer_has_substantive_text(answer):
        failures.append("answer did not contain substantive text")
    if contract is None:
        failures.append("missing turn contract")
    else:
        if contract.original_user_input != spec.prompt:
            failures.append("turn contract did not preserve original user input")
        if (
            _is_semantic_followup(spec)
            and contract.retrieval_query
            and _normalized_text(contract.retrieval_query) == _normalized_text(spec.prompt)
            and not _content_rich_query(spec.prompt)
        ):
            failures.append("semantic follow-up used literal user text as retrieval query")
        if CATEGORY_LOW_EVIDENCE in spec.categories and not _query_preserves_current_terms(
            spec.prompt,
            contract.retrieval_query,
        ):
            failures.append("low-evidence turn did not preserve current query terms")
    verification_notice = verify_response(answer, evidence)
    if verification_notice and contract is not None and contract.citation_required:
        failures.append("citation verification failed")
    citation_result = verify_citations(answer, evidence)
    if (
        spec.require_citations_when_evidence
        and evidence
        and contract is not None
        and contract.citation_required
        and not citation_result.has_citations
    ):
        failures.append("source-grounded turn did not cite retrieved evidence")
    if _is_semantic_followup(spec) and CATEGORY_LOW_EVIDENCE not in spec.categories:
        if contract is not None and contract.retrieval_strategy == RETRIEVAL_STRATEGY_NONE:
            failures.append("semantic follow-up dropped retrieval/evidence state")
        if evidence and not citation_result.has_citations:
            failures.append("semantic follow-up did not ground answer in evidence")
    if (
        CATEGORY_LOW_EVIDENCE in spec.categories
        and contract is not None
        and contract.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
    ):
        failures.append("low-evidence request reused prior evidence")
    claim_audit = (
        _audit_answer_claims(
            answer,
            claim_audit_evidence,
            config,
            contract=contract,
            conversation_context=_prior_assistant_context(session.conversation, contract),
        )
        if audit_claims and _should_audit_answer_claims(contract, claim_audit_evidence)
        else _no_claim_audit()
    )
    if claim_audit["checked"] and not claim_audit["passed"]:
        failures.append("unsupported claim audit failed: " + claim_audit["reason"])
    return {
        "turn": turn,
        "prompt": spec.prompt,
        "categories": list(spec.categories),
        "answer_len": len(answer),
        "retrieval_query": contract.retrieval_query if contract is not None else "",
        "retrieval_strategy": contract.retrieval_strategy if contract is not None else "",
        "evidence_refs": list(contract.evidence_refs) if contract is not None else [],
        "validation_result": contract.validation_result if contract is not None else "",
        "claim_audit_checked": claim_audit["checked"],
        "claim_audit_reason": claim_audit["reason"],
        "unsupported_claims": claim_audit["unsupported_claims"],
        "failures": failures,
    }


def _claim_audit_evidence(session: ChatSession, config: ChatConfig) -> TurnEvidence | None:
    if session.last_turn_evidence:
        contract = session.last_turn_contract
        if contract is None or not contract.evidence_refs:
            return session.last_turn_evidence
        rebuilt = build_turn_evidence_from_refs(
            session,
            list(contract.evidence_refs),
            max_tokens=_claim_audit_context_budget(config),
        )
        if rebuilt is None:
            return session.last_turn_evidence
        return _rebuilt_audit_evidence_with_live_ids(session.last_turn_evidence, rebuilt)
    contract = session.last_turn_contract
    if contract is None or not contract.evidence_refs:
        return None
    return build_turn_evidence_from_refs(
        session,
        list(contract.evidence_refs),
        max_tokens=_claim_audit_context_budget(config),
    )


def _claim_audit_context_budget(config: ChatConfig) -> int:
    return max(config.rag_context_budget, 6000)


def _rebuilt_audit_evidence_with_live_ids(
    live_evidence: TurnEvidence,
    rebuilt_evidence: TurnEvidence,
) -> TurnEvidence:
    live_by_ref = {_evidence_item_ref(item): item for item in live_evidence.items}
    used_ids = {item.evidence_id for item in live_evidence.items}
    next_id = _next_evidence_id_number(used_ids)
    aligned_items: list[EvidenceChunk] = []
    for rebuilt_item in rebuilt_evidence.items:
        live_item = live_by_ref.get(_evidence_item_ref(rebuilt_item))
        if live_item is None:
            evidence_id = f"E{next_id}"
            next_id += 1
        else:
            evidence_id = live_item.evidence_id
        while evidence_id in used_ids and live_item is None:
            evidence_id = f"E{next_id}"
            next_id += 1
        used_ids.add(evidence_id)
        aligned_items.append(
            EvidenceChunk(
                evidence_id=evidence_id,
                chunk=rebuilt_item.chunk,
                score=rebuilt_item.score,
                content=rebuilt_item.content,
            )
        )
    return TurnEvidence(
        tuple(aligned_items),
        sampled_source_count=rebuilt_evidence.sampled_source_count,
        total_source_count=rebuilt_evidence.total_source_count,
    )


def _evidence_item_ref(item: EvidenceChunk) -> tuple[str, int]:
    return (item.source, item.chunk_index)


def _next_evidence_id_number(evidence_ids: set[str]) -> int:
    numeric_ids = [
        int(evidence_id[1:])
        for evidence_id in evidence_ids
        if evidence_id.startswith("E") and evidence_id[1:].isdigit()
    ]
    return max(numeric_ids, default=0) + 1


def _should_audit_answer_claims(
    contract: object,
    evidence: TurnEvidence | None,
) -> bool:
    if contract is None:
        return True
    if getattr(contract, "resolved_intent", "") == "topic_drill":
        return False
    citation_required = getattr(contract, "citation_required", None)
    if citation_required is False:
        return False
    if evidence:
        return True
    return citation_required is True


def _exception_turn_result(
    turn: int,
    spec: ReliabilityTurnSpec,
    session: ChatSession,
    exc: Exception,
) -> ReliabilityTurnResult:
    contract = _current_turn_contract(session, spec.prompt)
    failure = f"turn raised {type(exc).__name__}: {_exception_excerpt(exc)}"
    return {
        "turn": turn,
        "prompt": spec.prompt,
        "categories": list(spec.categories),
        "answer_len": 0,
        "retrieval_query": contract.retrieval_query if contract is not None else "",
        "retrieval_strategy": contract.retrieval_strategy if contract is not None else "",
        "evidence_refs": list(contract.evidence_refs) if contract is not None else [],
        "validation_result": contract.validation_result if contract is not None else "",
        "claim_audit_checked": False,
        "claim_audit_reason": "turn failed before claim audit",
        "unsupported_claims": [],
        "failures": [failure],
    }


def _current_turn_contract(session: ChatSession, prompt: str) -> TurnContract | None:
    contract = session.last_turn_contract
    if contract is None or contract.original_user_input != prompt:
        return None
    return contract


def _exception_excerpt(exc: Exception, *, limit: int = 300) -> str:
    message = " ".join(str(exc).split())
    if len(message) <= limit:
        return message
    return message[: limit - 1].rstrip() + "..."


def _no_claim_audit() -> ClaimAuditResult:
    return {
        "checked": False,
        "passed": True,
        "reason": "claim audit not requested",
        "unsupported_claims": [],
    }


def _audit_answer_claims(
    answer: str,
    evidence: TurnEvidence | None,
    config: ChatConfig,
    *,
    contract: object | None = None,
    conversation_context: str = "",
) -> ClaimAuditResult:
    conversation = Conversation()
    conversation.add(
        "system",
        (
            "You audit source-grounded answers. Return only compact JSON with keys "
            "passed, unsupported_claims, and reason. Mark passed=false if the answer "
            "contains a factual claim that is not supported by the provided evidence, "
            "if it contradicts the evidence, or if a low-evidence answer guesses instead "
            "of saying the sources do not contain the answer. Do not require citations in "
            "this audit. The passed boolean is authoritative; keep unsupported_claims "
            "empty for a passing verdict and nonempty for a failing verdict; citation syntax "
            "and citation-target labels are checked elsewhere. "
            "Audit source-material and external-world claims only. Do not fail product "
            "scaffolding such as asking the learner to answer from memory, include a "
            "confidence score, use a time limit, "
            "retry a narrowed request, or references that merely anchor the answer to a "
            "previous turn, bullet, or citation. Do not fail a practice question merely "
            "because it asks the learner to apply a source-supported rule. Do not fail "
            "discourse framing that marks the answer as a response to the requested "
            "comparison with prior conversation; audit the factual comparison content "
            "instead. Do not fail "
            "a clearly labeled hypothetical example merely because its invented numbers, "
            "list values, or placeholder facts are not in the source, as long as the answer "
            "does not claim those specifics appear in the evidence and cites only the rule "
            "being illustrated. Do not fail "
            "descriptors repeated from the user's request when the answer says the sources "
            "do not contain that requested thing. Do not fail a clearly labeled pedagogical "
            "inference requested by the user, such as a likely learner mistake, when it is "
            "grounded in a supported evidence contrast and is not presented as source-stated. "
            "Do not fail a user-requested source or citation choice merely because words like "
            "strongest, clearest, or first are answer-side judgement from visible directness; "
            "fail only if the answer claims the source itself ranks the evidence. "
            "Do not fail generic phrases such as provided evidence, source evidence, or armory "
            "evidence when they merely describe the evidence bundle being audited. Do not fail "
            "a retrieval-state statement that the current evidence lacks a direct cited answer "
            "for the resolved request, as long as it does not claim every enabled source or the "
            "whole armory was exhaustively checked. The requested missing fact, entity, "
            "ranking, or definition does not need to appear in evidence for the answer to say "
            "the current evidence did not retrieve direct support for that request. Do not "
            "fail imperative checklist or "
            "action-item wording when the user requested a checklist and the action preserves "
            "a cited source premise. A recall "
            "prompt may ask the learner to answer from memory even when the source-backed "
            "correct answer would be to say not found; that instruction is not a source claim "
            "and is not a contradiction. Do not fail operational fallback text about an "
            "overview draft being unreliable or refusing to infer from filenames or metadata; "
            "those are product state/scaffolding statements, not claims from the evidence. "
            "If conversation "
            "context is provided, use it only to judge references to prior-answer structure "
            "such as bullets, ordinals, comparisons, or the user's requested lens; still "
            "require source evidence for factual claims about the materials."
        ),
    )
    contract_text = _claim_audit_contract_text(contract)
    conversation_text = _claim_audit_conversation_context_text(conversation_context)
    conversation.add(
        "user",
        (
            f"{contract_text}"
            f"{conversation_text}"
            "Evidence blocks:\n"
            f"{_claim_audit_evidence_text(evidence)}\n\n"
            "Answer to audit:\n"
            f"{answer}\n\n"
            "Return JSON like "
            '{"passed":true,"unsupported_claims":[],"reason":"all claims supported"}.'
        ),
    )
    audit_config = replace(config, max_tokens=min(config.max_tokens, 700))
    result = _no_claim_audit()
    for attempt in range(2):
        raw_reply = _run_claim_audit_request(audit_config, conversation)
        result = _parse_claim_audit_reply(raw_reply)
        if result["reason"] != "claim audit returned invalid JSON":
            return result
        if attempt == 0:
            conversation.add("assistant", raw_reply)
            conversation.add(
                "user",
                (
                    "The previous audit reply was not valid JSON. Return only a single JSON "
                    "object with keys passed, unsupported_claims, and reason."
                ),
            )
    return result


def _prior_assistant_context(conversation: Conversation, contract: object | None = None) -> str:
    assistant_messages = [
        message.content.strip()
        for message in conversation.messages
        if message.role == "assistant" and message.content.strip()
    ]
    if len(assistant_messages) < 2:
        return ""
    prior_messages = assistant_messages[:-1]
    limit = 1 if getattr(contract, "prior_answer_reference", False) is True else 3
    return "\n\n".join(prior_messages[-limit:])


def _claim_audit_contract_text(contract: object | None) -> str:
    if contract is None:
        return ""
    fields = (
        ("User request", "original_user_input"),
        ("Resolved intent", "resolved_intent"),
        ("Canonical request", "canonical_request"),
        ("Answer mode", "answer_mode"),
        ("Answer format", "answer_format"),
        ("Followup target", "followup_target"),
    )
    lines = ["Turn contract:"]
    for label, attr in fields:
        value = getattr(contract, attr, "")
        if isinstance(value, str) and value.strip():
            lines.append(f"- {label}: {' '.join(value.split())}")
    return "\n".join(lines) + "\n\n" if len(lines) > 1 else ""


def _claim_audit_conversation_context_text(context: str) -> str:
    normalized = " ".join(context.split())
    if not normalized:
        return ""
    if len(normalized) > 1200:
        normalized = normalized[:1199].rstrip() + "…"
    return f"Prior assistant answer for conversation-state references only:\n{normalized}\n\n"


def _run_claim_audit_request(config: ChatConfig, conversation: Conversation) -> str:
    for attempt in range(TRANSIENT_PROVIDER_RETRIES + 1):
        try:
            return "".join(stream_reply(config, conversation)).strip()
        except EngineError as exc:
            if attempt >= TRANSIENT_PROVIDER_RETRIES or not _transient_provider_error(exc):
                raise
            reset_provider_circuit_breaker()
            _sleep_before_transient_retry(attempt)
    return ""


def _sleep_before_transient_retry(attempt: int) -> None:
    delay = TRANSIENT_PROVIDER_RETRY_DELAYS_SECONDS[
        min(attempt, len(TRANSIENT_PROVIDER_RETRY_DELAYS_SECONDS) - 1)
    ]
    time.sleep(delay)


def _claim_audit_evidence_text(evidence: TurnEvidence | None) -> str:
    if not evidence:
        return "(no evidence retrieved)"
    blocks = [
        f"[{item.evidence_id}] {item.chunk.source}#chunk={item.chunk.index}\n{item.content}"
        for item in evidence.items
    ]
    return "\n\n".join(blocks)


def _parse_claim_audit_reply(raw_reply: str) -> ClaimAuditResult:
    payload = parse_json_object_fragment(raw_reply)
    if payload is None:
        return {
            "checked": True,
            "passed": False,
            "reason": "claim audit returned invalid JSON",
            "unsupported_claims": [raw_reply[:200]],
        }
    passed = payload.get("passed")
    unsupported_claims = _string_list(payload.get("unsupported_claims"))
    reason = payload.get("reason")
    if not isinstance(passed, bool):
        return {
            "checked": True,
            "passed": False,
            "reason": "claim audit JSON missing boolean passed",
            "unsupported_claims": unsupported_claims,
        }
    if not isinstance(reason, str) or not reason.strip():
        reason = "claim audit did not provide a reason"
    return {
        "checked": True,
        "passed": passed,
        "reason": reason.strip(),
        "unsupported_claims": unsupported_claims,
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _conversation_metrics(
    results: Sequence[ReliabilityTurnResult],
) -> ReliabilityConversationMetrics:
    total_turns = len(results)
    failed_turns = sum(1 for result in results if result["failures"])
    passed_turns = total_turns - failed_turns
    return {
        "turn_pass_rate": _rate(total_turns, passed_turns),
        "passed_turns": passed_turns,
        "failed_turns": failed_turns,
        "citation_verification_failures": _failure_count(results, "citation verification failed"),
        "missing_citation_failures": _failure_count(results, "did not cite retrieved evidence"),
        "literal_followup_retrieval_failures": _failure_count(results, "literal user text"),
        "claim_audit_checked_turns": sum(1 for result in results if result["claim_audit_checked"]),
        "unsupported_claim_failures": _unsupported_claim_failure_count(results),
    }


def _failure_count(results: Sequence[ReliabilityTurnResult], needle: str) -> int:
    return sum(1 for result in results if any(needle in failure for failure in result["failures"]))


def _unsupported_claim_failure_count(results: Sequence[ReliabilityTurnResult]) -> int:
    return sum(
        1
        for result in results
        if result["unsupported_claims"]
        or any("unsupported claim audit failed" in failure for failure in result["failures"])
    )


def _rate(total: int, passed: int) -> float:
    if total <= 0:
        return 0.0
    return passed / total


def _is_semantic_followup(spec: ReliabilityTurnSpec) -> bool:
    return bool(
        {CATEGORY_VAGUE_FOLLOWUP, CATEGORY_CONTINUATION, CATEGORY_PRIOR_REFERENCE}
        & set(spec.categories)
    )


def _answer_has_substantive_text(answer: str) -> bool:
    citationless = EVIDENCE_CITATION_RE.sub(" ", answer)
    words = WORD_RE.findall(citationless)
    return len(words) >= 2


def _query_preserves_current_terms(prompt: str, query: str) -> bool:
    prompt_terms = _specific_terms(prompt)
    if len(prompt_terms) < 2:
        return True
    query_terms = _specific_terms(query)
    return len(prompt_terms & query_terms) >= min(2, len(prompt_terms))


def _content_rich_query(text: str) -> bool:
    return len(_specific_terms(text)) >= 3


def _specific_terms(text: str) -> frozenset[str]:
    return frozenset(term.casefold() for term in WORD_RE.findall(text) if len(term) >= 5)


def _normalized_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _category_counts(turns: Sequence[ReliabilityTurnSpec]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for spec in turns:
        counts.update(spec.categories)
    return counts


def _requirement_failures(
    category_counts: Counter[str],
    requirements: RunRequirements,
    resume_count: int,
    compact_count: int,
) -> list[str]:
    failures: list[str] = []
    checks = {
        "vague/anaphoric follow-ups": (
            category_counts[CATEGORY_VAGUE_FOLLOWUP],
            requirements.vague_followups,
        ),
        "continuation follow-ups": (
            category_counts[CATEGORY_CONTINUATION],
            requirements.continuations,
        ),
        "prior-reference turns": (
            category_counts[CATEGORY_PRIOR_REFERENCE],
            requirements.prior_references,
        ),
        "topic switches": (category_counts[CATEGORY_TOPIC_SWITCH], requirements.topic_switches),
        "source-specific turns": (
            category_counts[CATEGORY_SOURCE_SPECIFIC],
            requirements.source_specific,
        ),
        "citation-checking turns": (
            category_counts[CATEGORY_CITATION_CHECK],
            requirements.citation_checks,
        ),
        "empty/low-evidence turns": (
            category_counts[CATEGORY_LOW_EVIDENCE],
            requirements.low_evidence,
        ),
        "session resumes": (resume_count, requirements.resumes),
        "compaction checkpoints": (compact_count, requirements.compactions),
    }
    for label, (actual, expected) in checks.items():
        if actual < expected:
            failures.append(f"{label} {actual} below required {expected}")
    return failures


def _trace_failures(
    trace_path: Path | None,
    trace_audit: TraceAudit,
    expected_turns: int,
) -> list[str]:
    if not isinstance(trace_path, Path) or not trace_path.is_file():
        return ["trace file missing"]
    failures: list[str] = []
    if trace_audit["user_turns"] < expected_turns:
        failures.append(
            f"trace user messages {trace_audit['user_turns']} below expected {expected_turns}"
        )
    if trace_audit["reply_contracts"] < expected_turns:
        failures.append(
            "trace reply turn contracts "
            f"{trace_audit['reply_contracts']} below expected {expected_turns}"
        )
    if trace_audit["replayable_turns"] < expected_turns:
        failures.append(
            "trace replayable turns "
            f"{trace_audit['replayable_turns']} below expected {expected_turns}"
        )
    failures.extend(trace_audit["failures"])
    return failures


def _trace_audit(trace_path: Path | None) -> TraceAudit:
    if not isinstance(trace_path, Path) or not trace_path.is_file():
        return {
            "user_turns": 0,
            "reply_contracts": 0,
            "replayable_turns": 0,
            "failures": [],
        }
    pending_users: list[str] = []
    user_turns = 0
    reply_contracts = 0
    replayable_turns = 0
    failures: list[str] = []
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        payload = _trace_json_object(line)
        if payload is None:
            continue
        if payload.get("type") == "user_message":
            content = payload.get("content")
            if isinstance(content, str):
                pending_users.append(content)
                user_turns += 1
            else:
                failures.append(f"trace line {line_number}: user message missing content")
            continue
        if _trace_line_is_turn_error_payload(payload):
            original_user_input = payload.get("original_user_input")
            if not isinstance(original_user_input, str) or not original_user_input:
                failures.append(
                    f"trace line {line_number}: turn error missing original user input"
                )
                continue
            if not _pop_matching_pending_user(pending_users, original_user_input):
                failures.append(
                    f"trace line {line_number}: turn error has no preceding user message"
                )
            continue
        if not _trace_line_has_turn_contract_payload(payload):
            continue
        reply_contracts += 1
        contract = payload.get("turn_contract")
        if not is_string_mapping(contract):
            failures.append(f"trace line {line_number}: reply missing turn contract object")
            continue
        original_user_input = contract.get("original_user_input")
        if not isinstance(original_user_input, str) or not original_user_input:
            failures.append(f"trace line {line_number}: turn contract missing original user input")
            continue
        expected_user_input = _pop_matching_pending_user(pending_users, original_user_input)
        if not expected_user_input:
            failures.append(f"trace line {line_number}: reply has no preceding user message")
            continue
        if original_user_input != expected_user_input:
            failures.append(
                f"trace line {line_number}: reply contract does not match user message"
            )
            continue
        if not _trace_reply_has_replay_surface(payload, contract):
            failures.append(f"trace line {line_number}: reply lacks replay surface fields")
            continue
        replayable_turns += 1
    if pending_users:
        failures.append(f"trace has {len(pending_users)} user message(s) without replies")
    return {
        "user_turns": user_turns,
        "reply_contracts": reply_contracts,
        "replayable_turns": replayable_turns,
        "failures": failures,
    }


def _pop_matching_pending_user(pending_users: list[str], original_user_input: str) -> str:
    if not pending_users:
        return ""
    expected_user_input = pending_users.pop(0)
    if expected_user_input == original_user_input:
        return expected_user_input
    for index, candidate in enumerate(pending_users):
        if candidate != original_user_input:
            continue
        del pending_users[: index + 1]
        return candidate
    return expected_user_input


def _trace_json_object(line: str) -> dict[str, object] | None:
    try:
        payload: object = json.loads(line)
    except json.JSONDecodeError:
        return None
    return payload if is_string_mapping(payload) else None


def _trace_line_is_turn_error_payload(payload: Mapping[str, object]) -> bool:
    return payload.get("type") == "session" and payload.get("event") == "turn_error"


def _trace_reply_has_replay_surface(
    payload: Mapping[str, object],
    contract: Mapping[str, object],
) -> bool:
    return (
        _trace_reply_payload_has_replay_surface(payload)
        and _trace_contract_has_replay_surface(contract)
        and _trace_contract_matches_payload(payload, contract)
    )


def _trace_reply_payload_has_replay_surface(payload: Mapping[str, object]) -> bool:
    return (
        isinstance(payload.get("reply_excerpt"), str)
        and isinstance(payload.get("retrieval_query"), str)
        and _string_sequence(payload.get("evidence_refs")) is not None
        and is_string_mapping(payload.get("evidence_coverage"))
        and isinstance(payload.get("evidence_items"), list)
        and isinstance(payload.get("verification_notice"), str)
    )


def _trace_contract_has_replay_surface(contract: Mapping[str, object]) -> bool:
    required_strings = (
        "original_user_input",
        "resolved_intent",
        "canonical_request",
        "followup_target",
        "answer_mode",
        "answer_format",
        "retrieval_strategy",
        "retrieval_query",
        "prior_answer_position_basis",
        "prior_turn_original_user_input",
        "prior_turn_resolved_intent",
        "prior_turn_canonical_request",
        "prior_answer_excerpt",
        "validation_result",
    )
    required_bools = (
        "is_followup",
        "citation_required",
        "direct_evidence_required",
        "prior_answer_reference",
    )
    return (
        all(isinstance(contract.get(key), str) for key in required_strings)
        and all(isinstance(contract.get(key), bool) for key in required_bools)
        and _string_sequence(contract.get("evidence_refs")) is not None
        and _string_sequence(contract.get("prior_turn_evidence_refs")) is not None
        and _int_sequence(contract.get("prior_answer_positions")) is not None
        and isinstance(contract.get("confidence"), int | float)
        and bool(str(contract.get("original_user_input", "")).strip())
        and bool(str(contract.get("resolved_intent", "")).strip())
        and bool(str(contract.get("validation_result", "")).strip())
        and _trace_contract_has_required_prior_state(contract)
    )


def _trace_contract_has_required_prior_state(contract: Mapping[str, object]) -> bool:
    if not (
        contract.get("is_followup") is True
        or contract.get("prior_answer_reference") is True
        or contract.get("retrieval_strategy") in {"reuse_prior_evidence", "expand_prior_evidence"}
        or contract.get("answer_mode") in {"transform_prior_answer", "reason_from_prior_evidence"}
    ):
        return True
    return (
        bool(str(contract.get("prior_turn_original_user_input", "")).strip())
        and bool(str(contract.get("prior_answer_excerpt", "")).strip())
        and (
            bool(str(contract.get("prior_turn_resolved_intent", "")).strip())
            or bool(str(contract.get("prior_turn_canonical_request", "")).strip())
        )
    )


def _trace_contract_matches_payload(
    payload: Mapping[str, object],
    contract: Mapping[str, object],
) -> bool:
    payload_evidence_refs = _string_sequence(payload.get("evidence_refs"))
    contract_evidence_refs = _string_sequence(contract.get("evidence_refs"))
    return (
        payload.get("retrieval_query") == contract.get("retrieval_query")
        and payload_evidence_refs is not None
        and contract_evidence_refs is not None
        and payload_evidence_refs == contract_evidence_refs
    )


def _string_sequence(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return None
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return None
        items.append(item)
    return tuple(items)


def _int_sequence(value: object) -> tuple[int, ...] | None:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return None
    items: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool):
            return None
        items.append(item)
    return tuple(items)


def _trace_reply_contract_count(trace_path: Path | None) -> int:
    if not isinstance(trace_path, Path) or not trace_path.is_file():
        return 0
    count = 0
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if _trace_line_has_turn_contract(line):
            count += 1
    return count


def _trace_line_has_turn_contract(line: str) -> bool:
    payload = _trace_json_object(line)
    if payload is None:
        return False
    return _trace_line_has_turn_contract_payload(payload)


def _trace_line_has_turn_contract_payload(payload: Mapping[str, object]) -> bool:
    contract = payload.get("turn_contract")
    return payload.get("event") == "reply" and is_string_mapping(contract) and bool(contract)


def run_suite(
    armory_path: Path,
    config: ChatConfig,
    *,
    level: str,
    output_path: Path | None = None,
    seeded_armories: Sequence[Path] = (),
    min_seeded_runs: int = 10,
    require_trace: bool = True,
    audit_claims: bool = False,
    require_claim_audit: bool = False,
    progress: bool = False,
) -> ReliabilitySuiteReport:
    if level == "stress":
        stress_script = stress_turns()
        reports = [
            run_reliability_conversation(
                armory_path,
                config,
                level=level,
                turns=stress_script,
                requirements=stress_requirements(turns=len(stress_script)),
                resume_every=5,
                require_trace=require_trace,
                audit_claims=audit_claims,
                progress=progress,
            )
        ]
    elif level == "focus":
        focus_script = focused_turns()
        reports = [
            run_reliability_conversation(
                armory_path,
                config,
                level=level,
                turns=focus_script,
                requirements=focus_requirements(turns=len(focus_script)),
                resume_every=20,
                require_trace=require_trace,
                audit_claims=audit_claims,
                progress=progress,
            )
        ]
    elif level == "full":
        reports = [
            run_reliability_conversation(
                armory_path,
                config,
                level=level,
                turns=built_in_turns(turns=100),
                requirements=full_requirements(),
                resume_every=20,
                compact_every=33,
                require_trace=require_trace,
                audit_claims=audit_claims,
                progress=progress,
            )
        ]
    else:
        reports = _seeded_reports(
            armory_path,
            config,
            seeded_armories=seeded_armories,
            min_seeded_runs=min_seeded_runs,
            require_trace=require_trace,
            audit_claims=audit_claims,
            progress=progress,
        )
    failures = _suite_failures(
        level,
        reports,
        seeded_armories,
        min_seeded_runs,
        require_claim_audit=require_claim_audit,
    )
    report: ReliabilitySuiteReport = {
        "level": level,
        "status": 1 if failures else 0,
        "conversations": len(reports),
        "metrics": _suite_metrics(reports),
        "failures": failures,
        "reports": reports,
    }
    if output_path is not None:
        _write_json(output_path, report)
    return report


def _seeded_reports(
    armory_path: Path,
    config: ChatConfig,
    *,
    seeded_armories: Sequence[Path],
    min_seeded_runs: int,
    require_trace: bool,
    audit_claims: bool,
    progress: bool,
) -> list[ReliabilityConversationReport]:
    armories = list(seeded_armories) or [armory_path]
    reports: list[ReliabilityConversationReport] = []
    for index, seeded_armory in enumerate(armories[:min_seeded_runs]):
        reports.append(
            run_reliability_conversation(
                seeded_armory,
                config,
                level="seeded",
                turns=built_in_turns(turns=100, seed=index),
                requirements=full_requirements(),
                resume_every=20,
                compact_every=33,
                require_trace=require_trace,
                audit_claims=audit_claims,
                progress=progress,
            )
        )
    return reports


def _suite_failures(
    level: str,
    reports: Sequence[ReliabilityConversationReport],
    seeded_armories: Sequence[Path],
    min_seeded_runs: int,
    *,
    require_claim_audit: bool,
) -> list[str]:
    failures = [
        f"conversation {index}: {failure}"
        for index, report in enumerate(reports, start=1)
        for failure in report["failures"]
    ]
    if level == "seeded":
        unique_armories = {path.resolve() for path in seeded_armories}
        if len(reports) < min_seeded_runs:
            failures.append(
                f"seeded suite ran {len(reports)} conversations below required {min_seeded_runs}"
            )
        if len(unique_armories) < min_seeded_runs:
            failures.append(
                f"seeded suite has {len(unique_armories)} unique armories below "
                f"required {min_seeded_runs}"
            )
    if require_claim_audit:
        unchecked = [
            str(index)
            for index, report in enumerate(reports, start=1)
            if not report["unsupported_claims_checked"]
        ]
        if unchecked:
            failures.append(
                "unsupported claim audit skipped for conversation(s): " + ", ".join(unchecked)
            )
    return failures


def _suite_metrics(reports: Sequence[ReliabilityConversationReport]) -> ReliabilitySuiteMetrics:
    total_turns = sum(report["turns"] for report in reports)
    failed_turns = sum(report["metrics"]["failed_turns"] for report in reports)
    return {
        "turn_pass_rate": _rate(total_turns, total_turns - failed_turns),
        "total_turns": total_turns,
        "total_failed_turns": failed_turns,
        "conversations_with_failures": sum(1 for report in reports if report["failures"]),
        "claim_audit_checked_conversations": sum(
            1 for report in reports if report["unsupported_claims_checked"]
        ),
    }


def _write_json(path: Path, payload: ReliabilitySuiteReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _config_from_args(args: argparse.Namespace) -> ChatConfig:
    provider = cast("str", args.provider).strip()
    config = ChatConfig(
        api_key=cast("str", args.api_key),
        base_url=cast("str", args.base_url),
        model=_model_from_args(cast("str", args.model), provider=provider),
        max_tokens=cast("int", args.max_tokens),
        rag_context_budget=cast("int", args.rag_context_budget),
        reasoning_level=cast("str", args.reasoning_level),
        feature_flags=frozenset({"disable_memory_extraction"}),
    )
    if provider:
        env_var = "" if provider == PROVIDER_OPENAI_CODEX else _provider_api_key_env(provider)
        config.apply_provider_reference(provider, env_var)
    return config


def _configure_codex_timeout(args: argparse.Namespace, config: ChatConfig) -> None:
    if config.provider_slug != PROVIDER_OPENAI_CODEX:
        return
    timeout_seconds = cast("float", args.codex_timeout_seconds)
    if timeout_seconds > 0:
        os.environ["HEPHAION_CODEX_TIMEOUT_SECONDS"] = str(timeout_seconds)


def _model_from_args(model: str, *, provider: str) -> str:
    if model.strip():
        return model.strip()
    if provider == PROVIDER_OPENAI_CODEX:
        return DEFAULT_CODEX_MODEL
    return DEFAULT_MODEL


def _provider_api_key_env(provider: str) -> str:
    return {
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai": "ZAI_API_KEY",
        "custom": "CUSTOM_API_KEY",
        "pollinations": "",
    }.get(provider, "")


def _prepare_fixture_armories(
    armory_path: Path,
    *,
    level: str,
    seeded_armories: Sequence[Path],
    min_seeded_runs: int,
    seed_prefix: str,
    force: bool,
) -> tuple[Path, tuple[Path, ...]]:
    if level == "seeded":
        if seeded_armories:
            for index, seeded_armory in enumerate(seeded_armories, start=1):
                create_fixture_armory(
                    seeded_armory,
                    variant=f"{seed_prefix}-{index:02d}",
                    force=force,
                )
            return armory_path, tuple(seeded_armories)
        report = create_fixture_armories(
            armory_path,
            count=min_seeded_runs,
            seed_prefix=seed_prefix,
            force=force,
        )
        generated_armories = tuple(Path(item["armory"]) for item in report["armories"])
        primary_armory = generated_armories[0] if generated_armories else armory_path
        return primary_armory, generated_armories

    create_fixture_armory(armory_path, variant=level, force=force)
    return armory_path, tuple(seeded_armories)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "armory",
        type=Path,
        help=(
            "Armory path containing materials/. With --create-fixtures and --level seeded, "
            "this is the parent directory for generated seeded armories."
        ),
    )
    parser.add_argument(
        "--level",
        choices=("stress", "focus", "full", "seeded"),
        default="stress",
    )
    parser.add_argument(
        "--model",
        default="",
        help=(
            "Model name for ChatConfig. Defaults to "
            f"{DEFAULT_CODEX_MODEL} for --provider {PROVIDER_OPENAI_CODEX}, "
            f"otherwise {DEFAULT_MODEL}."
        ),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI-compatible base URL")
    parser.add_argument(
        "--provider",
        choices=("openai", PROVIDER_OPENAI_CODEX, "openrouter", "zai", "custom", "pollinations"),
        default=PROVIDER_OPENAI_CODEX,
        help=(
            "Heph provider slug. Defaults to openai-codex, which tests with the logged-in "
            "Codex subscription instead of an OpenAI API key."
        ),
    )
    parser.add_argument("--api-key", default="", help="Optional API key")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--rag-context-budget", type=int, default=2000)
    parser.add_argument(
        "--codex-timeout-seconds",
        type=float,
        default=DEFAULT_GAUNTLET_CODEX_TIMEOUT_SECONDS,
        help=(
            "Per-request ChatGPT Codex backend socket timeout for gauntlet runs. "
            "Only applied when --provider openai-codex."
        ),
    )
    parser.add_argument(
        "--reasoning-level",
        choices=("low", "medium", "high", "xhigh"),
        default="low",
        help="Reasoning effort for reasoning-capable models",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path")
    parser.add_argument(
        "--seeded-armory",
        type=Path,
        action="append",
        default=[],
        help="Armory path for seeded stress; repeat at least 10 times for acceptance",
    )
    parser.add_argument("--min-seeded-runs", type=int, default=10)
    parser.add_argument(
        "--no-require-trace",
        action="store_true",
        help="Developer-only: skip trace completeness failure checks",
    )
    parser.add_argument(
        "--claim-audit",
        action="store_true",
        help="Run model-backed support auditing in stress runs; full/seeded enable it by default",
    )
    parser.add_argument(
        "--skip-claim-audit",
        action="store_true",
        help="Developer-only: skip support auditing; full/seeded reports will fail acceptance",
    )
    parser.add_argument(
        "--create-fixtures",
        action="store_true",
        help=(
            "Create generic fixture materials before running. For seeded runs without "
            "--seeded-armory, creates --min-seeded-runs armories under the armory path."
        ),
    )
    parser.add_argument(
        "--force-fixtures",
        action="store_true",
        help="Overwrite generated fixture materials when used with --create-fixtures",
    )
    parser.add_argument(
        "--fixture-seed-prefix",
        default=DEFAULT_SEED_PREFIX,
        help="Directory/variant prefix for generated seeded fixture armories",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    output = cast("Path | None", args.output)
    seeded_armories = tuple(
        path.expanduser().resolve() for path in cast("list[Path]", args.seeded_armory)
    )
    min_seeded_runs = cast("int", args.min_seeded_runs)
    level = cast("str", args.level)
    if min_seeded_runs <= 0:
        parser.error("--min-seeded-runs must be positive")
    audit_claims = cast("bool", args.claim_audit) or level in {"focus", "full", "seeded"}
    if cast("bool", args.skip_claim_audit):
        audit_claims = False
    config = _config_from_args(args)
    _configure_codex_timeout(args, config)
    try:
        if cast("bool", args.create_fixtures):
            armory, seeded_armories = _prepare_fixture_armories(
                armory,
                level=level,
                seeded_armories=seeded_armories,
                min_seeded_runs=min_seeded_runs,
                seed_prefix=cast("str", args.fixture_seed_prefix),
                force=cast("bool", args.force_fixtures),
            )
        report = run_suite(
            armory,
            config,
            level=level,
            output_path=output.expanduser().resolve() if output is not None else None,
            seeded_armories=seeded_armories,
            min_seeded_runs=min_seeded_runs,
            require_trace=not cast("bool", args.no_require_trace),
            audit_claims=audit_claims,
            require_claim_audit=level in {"full", "seeded"},
            progress=True,
        )
    except Exception as exc:
        print(f"reliability gauntlet error: {exc}", file=sys.stderr)
        return 2
    _print_report(report)
    return int(report["status"])


def _print_report(report: ReliabilitySuiteReport) -> None:
    print(f"level={report['level']}")
    print(f"status={report['status']}")
    print(f"conversations={report['conversations']}")
    print(
        "metrics "
        f"turn_pass_rate={report['metrics']['turn_pass_rate']:.3f} "
        f"failed_turns={report['metrics']['total_failed_turns']}"
    )
    for child in report["reports"]:
        print(
            "conversation "
            f"level={child['level']} turns={child['turns']} "
            f"resumes={child['resume_count']} compactions={child['compact_count']} "
            f"turn_pass_rate={child['metrics']['turn_pass_rate']:.3f} "
            f"failures={len(child['failures'])}"
        )
    if report["failures"]:
        print("failures:")
        for failure in report["failures"][:50]:
            print(f"- {failure}")


if __name__ == "__main__":
    raise SystemExit(main())
