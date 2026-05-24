from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from hephaistos.armory import storage
from hephaistos.chat.events import AssistantDeltaEvent, TurnCompleteEvent
from hephaistos.chat.session import ChatSession
from hephaistos.chat.turn_contract import TurnContract
from hephaistos.rag import Chunk, EvidenceChunk, TurnEvidence
from hephaistos.runtime import ChatConfig, Conversation, EngineError
from scripts import create_chat_reliability_fixture as fixture
from scripts import run_chat_reliability_gauntlet as gauntlet


def _session(tmp_path: Path) -> ChatSession:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="gauntlet-test",
        armory_path=tmp_path,
    )
    object.__setattr__(session, "trace", MagicMock())
    return session


def _evidence() -> TurnEvidence:
    chunk = Chunk(
        text="The material says the method uses cited evidence.",
        source="materials/source.md",
        index=0,
        char_start=0,
        char_end=48,
    )
    return TurnEvidence(
        (
            EvidenceChunk(
                evidence_id="E1",
                chunk=chunk,
                score=0.9,
                content=chunk.text,
            ),
        )
    )


def _fake_events(
    session: ChatSession,
    prompt: str,
) -> list[AssistantDeltaEvent | TurnCompleteEvent]:
    session.last_turn_evidence = _evidence()
    session.last_turn_contract = TurnContract(
        original_user_input=prompt,
        resolved_intent="source_qa",
        canonical_request=f"semantic request for {prompt}",
        is_followup=True,
        followup_target="previous answer",
        retrieval_strategy="expand_prior_evidence",
        retrieval_query=f"semantic query for {prompt}",
        evidence_refs=("materials/source.md#chunk=0",),
        citation_required=True,
        validation_result="ok",
    )
    return [
        AssistantDeltaEvent("Grounded answer [E1]."),
        TurnCompleteEvent("Grounded answer [E1].", 0, 1.0, "stop", 100),
    ]


def test_built_in_full_script_meets_required_turn_mix() -> None:
    turns = gauntlet.built_in_turns(turns=100)
    counts = gauntlet._category_counts(turns)
    requirements = gauntlet.full_requirements()

    failures = gauntlet._requirement_failures(
        counts,
        requirements,
        resume_count=requirements.resumes,
        compact_count=requirements.compactions,
    )

    assert len(turns) == 100
    assert failures == []


def test_smoke_script_meets_smoke_required_turn_mix() -> None:
    turns = gauntlet.smoke_turns()
    counts = gauntlet._category_counts(turns)
    requirements = gauntlet.smoke_requirements(turns=len(turns))

    failures = gauntlet._requirement_failures(
        counts,
        requirements,
        resume_count=requirements.resumes,
        compact_count=requirements.compactions,
    )

    assert len(turns) == 15
    assert failures == []


def test_seeded_full_scripts_paraphrase_followup_wording() -> None:
    first_seed_prompts = {turn.prompt for turn in gauntlet.built_in_turns(turns=100, seed=0)}
    second_seed_prompts = {turn.prompt for turn in gauntlet.built_in_turns(turns=100, seed=1)}
    third_seed_prompts = {turn.prompt for turn in gauntlet.built_in_turns(turns=100, seed=2)}

    assert "Go on." in first_seed_prompts
    assert "Please continue." in second_seed_prompts
    assert "Continue." in third_seed_prompts
    assert len(first_seed_prompts | second_seed_prompts | third_seed_prompts) > len(
        first_seed_prompts
    )


def test_trace_audit_pairs_user_messages_with_reply_contracts(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        "\n".join(
            json.dumps(payload)
            for payload in (
                {"type": "user_message", "content": "What else?"},
                {
                    "type": "session",
                    "event": "reply",
                    "reply_excerpt": "Grounded answer [E1].",
                    "retrieval_query": "semantic query",
                    "turn_contract": {
                        "original_user_input": "What else?",
                        "resolved_intent": "source_qa",
                        "canonical_request": "continue the previous answer",
                        "retrieval_strategy": "expand_prior_evidence",
                        "retrieval_query": "semantic query",
                        "validation_result": "ok",
                    },
                    "evidence_refs": ["materials/source.md#chunk=0"],
                    "evidence_coverage": {"evidence_blocks": 1},
                    "evidence_items": [],
                    "verification_notice": "",
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    audit = gauntlet._trace_audit(trace_path)
    failures = gauntlet._trace_failures(trace_path, audit, expected_turns=1)

    assert audit["user_turns"] == 1
    assert audit["reply_contracts"] == 1
    assert audit["replayable_turns"] == 1
    assert failures == []


def test_trace_audit_rejects_reply_contract_for_wrong_user_message(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        "\n".join(
            json.dumps(payload)
            for payload in (
                {"type": "user_message", "content": "What else?"},
                {
                    "type": "session",
                    "event": "reply",
                    "reply_excerpt": "Grounded answer [E1].",
                    "retrieval_query": "semantic query",
                    "turn_contract": {
                        "original_user_input": "Tell me more.",
                        "resolved_intent": "source_qa",
                        "canonical_request": "continue the previous answer",
                        "retrieval_strategy": "expand_prior_evidence",
                        "retrieval_query": "semantic query",
                        "validation_result": "ok",
                    },
                    "evidence_refs": ["materials/source.md#chunk=0"],
                    "evidence_coverage": {"evidence_blocks": 1},
                    "evidence_items": [],
                    "verification_notice": "",
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    audit = gauntlet._trace_audit(trace_path)

    assert audit["replayable_turns"] == 0
    assert audit["failures"] == ["trace line 2: reply contract does not match user message"]


def test_trace_audit_skips_orphaned_user_messages_from_retried_turns(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        "\n".join(
            json.dumps(payload)
            for payload in (
                {"type": "user_message", "content": "Timed out"},
                {"type": "user_message", "content": "Recovered"},
                {
                    "type": "session",
                    "event": "reply",
                    "reply_excerpt": "Grounded answer [E1].",
                    "retrieval_query": "semantic query",
                    "turn_contract": {
                        "original_user_input": "Recovered",
                        "resolved_intent": "source_qa",
                        "canonical_request": "answer recovered request",
                        "retrieval_strategy": "retrieve",
                        "retrieval_query": "semantic query",
                        "validation_result": "ok",
                    },
                    "evidence_refs": ["materials/source.md#chunk=0"],
                    "evidence_coverage": {"evidence_blocks": 1},
                    "evidence_items": [],
                    "verification_notice": "",
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    audit = gauntlet._trace_audit(trace_path)

    assert audit["replayable_turns"] == 1
    assert audit["failures"] == []


def test_config_from_args_can_select_openai_codex_subscription() -> None:
    parser = gauntlet._build_parser()
    args = parser.parse_args(
        [
            "armory",
            "--provider",
            "openai-codex",
            "--model",
            "gpt-5.1-codex-mini",
            "--reasoning-level",
            "low",
        ]
    )

    config = gauntlet._config_from_args(args)

    assert config.provider_slug == "openai-codex"
    assert config.base_url == gauntlet.DEFAULT_BASE_URL
    assert config.model == "gpt-5.1-codex-mini"
    assert config.reasoning_level == "low"
    assert config.is_feature_enabled("disable_memory_extraction")
    assert config.resolved_api_key == ""


def test_prepare_fixture_armories_creates_seeded_gauntlet_armories(tmp_path: Path) -> None:
    primary, seeded = gauntlet._prepare_fixture_armories(
        tmp_path / "generated",
        level="seeded",
        seeded_armories=(),
        min_seeded_runs=3,
        seed_prefix="acceptance-seed",
        force=False,
    )

    assert primary == seeded[0]
    assert len(seeded) == 3
    assert all((path / storage.MARKER_FILE).is_file() for path in seeded)
    assert all(
        (
            path / storage.MATERIALS_DIR / fixture.FIXTURE_MATERIALS_DIR / "fixture-manifest.md"
        ).is_file()
        for path in seeded
    )


def test_reliability_conversation_records_resumes_and_contracts(tmp_path: Path) -> None:
    session = _session(tmp_path)
    turns = [
        gauntlet.ReliabilityTurnSpec(
            "What is the material about?",
            (gauntlet.CATEGORY_TOPIC_SWITCH,),
            require_citations_when_evidence=True,
        ),
        gauntlet.ReliabilityTurnSpec(
            "What else?",
            (gauntlet.CATEGORY_VAGUE_FOLLOWUP,),
            require_citations_when_evidence=True,
        ),
    ]
    requirements = gauntlet.RunRequirements(turns=2, vague_followups=1, resumes=1)

    with (
        patch("scripts.run_chat_reliability_gauntlet.create_session", return_value=session),
        patch("scripts.run_chat_reliability_gauntlet.resume_session", return_value=session),
        patch("scripts.run_chat_reliability_gauntlet.save_session", return_value=tmp_path),
        patch("scripts.run_chat_reliability_gauntlet.iter_chat_events", side_effect=_fake_events),
    ):
        report = gauntlet.run_reliability_conversation(
            tmp_path,
            ChatConfig(),
            level="test",
            turns=turns,
            requirements=requirements,
            resume_every=2,
            require_trace=False,
        )

    assert report["status"] == 0
    assert report["resume_count"] == 1
    assert report["metrics"]["turn_pass_rate"] == 1.0
    assert report["metrics"]["claim_audit_checked_turns"] == 0
    assert report["results"][1]["prompt"] == "What else?"
    assert report["results"][1]["retrieval_query"] == "semantic query for What else?"


def test_reliability_conversation_fails_literal_followup_retrieval(tmp_path: Path) -> None:
    session = _session(tmp_path)

    def fake_literal_events(
        session: ChatSession,
        prompt: str,
    ) -> list[AssistantDeltaEvent | TurnCompleteEvent]:
        events = _fake_events(session, prompt)
        assert session.last_turn_contract is not None
        session.last_turn_contract = TurnContract(
            original_user_input=prompt,
            resolved_intent=session.last_turn_contract.resolved_intent,
            canonical_request=session.last_turn_contract.canonical_request,
            is_followup=True,
            followup_target=session.last_turn_contract.followup_target,
            retrieval_strategy=session.last_turn_contract.retrieval_strategy,
            retrieval_query=prompt,
            evidence_refs=session.last_turn_contract.evidence_refs,
            citation_required=True,
            validation_result="ok",
        )
        return events

    with (
        patch("scripts.run_chat_reliability_gauntlet.create_session", return_value=session),
        patch(
            "scripts.run_chat_reliability_gauntlet.iter_chat_events",
            side_effect=fake_literal_events,
        ),
    ):
        report = gauntlet.run_reliability_conversation(
            tmp_path,
            ChatConfig(),
            level="test",
            turns=[
                gauntlet.ReliabilityTurnSpec(
                    "What else?",
                    (gauntlet.CATEGORY_VAGUE_FOLLOWUP,),
                    require_citations_when_evidence=True,
                )
            ],
            requirements=gauntlet.RunRequirements(turns=1, vague_followups=1),
            resume_every=0,
            require_trace=False,
        )

    assert report["status"] == 1
    assert report["metrics"]["literal_followup_retrieval_failures"] == 1
    assert "literal user text" in report["failures"][0]


def test_reliability_conversation_fails_unsupported_claim_audit(tmp_path: Path) -> None:
    session = _session(tmp_path)

    with (
        patch("scripts.run_chat_reliability_gauntlet.create_session", return_value=session),
        patch("scripts.run_chat_reliability_gauntlet.iter_chat_events", side_effect=_fake_events),
        patch(
            "scripts.run_chat_reliability_gauntlet.stream_reply",
            return_value=iter(
                [
                    (
                        '{"passed":false,"unsupported_claims":["invented fact"],'
                        '"reason":"invented fact is not in evidence"}'
                    )
                ]
            ),
        ),
    ):
        report = gauntlet.run_reliability_conversation(
            tmp_path,
            ChatConfig(),
            level="test",
            turns=[
                gauntlet.ReliabilityTurnSpec(
                    "What is the material about?",
                    (gauntlet.CATEGORY_TOPIC_SWITCH,),
                    require_citations_when_evidence=True,
                )
            ],
            requirements=gauntlet.RunRequirements(turns=1, topic_switches=1),
            resume_every=0,
            require_trace=False,
            audit_claims=True,
        )

    assert report["status"] == 1
    assert report["unsupported_claims_checked"] is True
    assert report["metrics"]["unsupported_claim_failures"] == 1
    assert report["metrics"]["claim_audit_checked_turns"] == 1
    assert report["results"][0]["unsupported_claims"] == ["invented fact"]
    assert "unsupported claim audit failed" in report["failures"][0]


def test_claim_audit_rebuilds_evidence_from_contract_refs(tmp_path: Path) -> None:
    session = _session(tmp_path)
    evidence = _evidence()

    def fake_events(
        session: ChatSession,
        prompt: str,
    ) -> list[AssistantDeltaEvent | TurnCompleteEvent]:
        session.last_turn_evidence = None
        session.last_turn_contract = TurnContract(
            original_user_input=prompt,
            resolved_intent="source_qa",
            retrieval_strategy="reuse_prior_evidence",
            evidence_refs=("materials/source.md#chunk=0",),
            citation_required=True,
            validation_result="ok",
        )
        return [
            AssistantDeltaEvent("Source-backed recall prompt."),
            TurnCompleteEvent("Source-backed recall prompt.", 0, 1.0, "stop", 100),
        ]

    with (
        patch("scripts.run_chat_reliability_gauntlet.create_session", return_value=session),
        patch("scripts.run_chat_reliability_gauntlet.iter_chat_events", side_effect=fake_events),
        patch(
            "scripts.run_chat_reliability_gauntlet.build_turn_evidence_from_refs",
            return_value=evidence,
        ) as rebuild,
        patch(
            "scripts.run_chat_reliability_gauntlet.stream_reply",
            return_value=iter(['{"passed":true,"unsupported_claims":[],"reason":"supported"}']),
        ),
    ):
        report = gauntlet.run_reliability_conversation(
            tmp_path,
            ChatConfig(),
            level="test",
            turns=[
                gauntlet.ReliabilityTurnSpec(
                    "Ask one source-backed recall prompt.",
                    (gauntlet.CATEGORY_VAGUE_FOLLOWUP,),
                )
            ],
            requirements=gauntlet.RunRequirements(turns=1, vague_followups=1),
            resume_every=0,
            require_trace=False,
            audit_claims=True,
        )

    rebuild.assert_called_once_with(session, ["materials/source.md#chunk=0"], max_tokens=6000)
    assert report["status"] == 0
    assert report["metrics"]["claim_audit_checked_turns"] == 1


def test_claim_audit_rebuild_preserves_live_evidence_ids() -> None:
    live_chunk = Chunk(
        text="Short visible evidence.",
        source="materials/study.md",
        index=0,
        char_start=0,
        char_end=23,
    )
    rebuilt_chunk = Chunk(
        text="Longer rebuilt evidence with the same source and chunk.",
        source="materials/study.md",
        index=0,
        char_start=0,
        char_end=55,
    )
    live_evidence = TurnEvidence(
        (
            EvidenceChunk(
                evidence_id="E7",
                chunk=live_chunk,
                score=0.3,
                content=live_chunk.text,
            ),
        )
    )
    rebuilt_evidence = TurnEvidence(
        (
            EvidenceChunk(
                evidence_id="E1",
                chunk=rebuilt_chunk,
                score=1.0,
                content=rebuilt_chunk.text,
            ),
        )
    )

    aligned = gauntlet._rebuilt_audit_evidence_with_live_ids(
        live_evidence,
        rebuilt_evidence,
    )

    assert [item.evidence_id for item in aligned.items] == ["E7"]
    assert aligned.items[0].content == rebuilt_chunk.text


def test_claim_audit_retries_transient_provider_timeout() -> None:
    calls = 0

    def fake_stream(
        _config: ChatConfig,
        _conversation: Conversation,
    ) -> list[str]:
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise EngineError("ChatGPT Codex request failed: The read operation timed out")
        return ['{"passed":true,"unsupported_claims":[],"reason":"supported"}']

    with patch("scripts.run_chat_reliability_gauntlet.stream_reply", side_effect=fake_stream):
        result = gauntlet._audit_answer_claims(
            "Supported answer [E1].",
            _evidence(),
            ChatConfig(),
        )

    assert calls == 3
    assert result["passed"] is True


def test_claim_audit_parser_treats_support_affirming_reason_as_passed() -> None:
    parsed = gauntlet._parse_claim_audit_reply(
        json.dumps(
            {
                "passed": False,
                "unsupported_claims": ["The source does not provide that detail."],
                "reason": "E1 does state that detail directly.",
            }
        )
    )

    assert parsed["passed"] is True
    assert parsed["unsupported_claims"] == []


def test_claim_audit_parser_treats_relabelled_support_reason_as_passed() -> None:
    parsed = gauntlet._parse_claim_audit_reply(
        json.dumps(
            {
                "passed": False,
                "unsupported_claims": ["The cited label differs."],
                "reason": (
                    "E10 directly contains the relevant study-methods guidance; "
                    "the phrase appears in E10, not E3."
                ),
            }
        )
    )

    assert parsed["passed"] is True
    assert parsed["unsupported_claims"] == []


def test_claim_audit_parser_treats_definitional_support_reason_as_passed() -> None:
    parsed = gauntlet._parse_claim_audit_reply(
        json.dumps(
            {
                "passed": False,
                "unsupported_claims": ["The source does not define an order."],
                "reason": "E1 states a two-step checklist, which does define an order.",
            }
        )
    )

    assert parsed["passed"] is True
    assert parsed["unsupported_claims"] == []


def test_claim_audit_skips_non_citation_required_practice_turns() -> None:
    contract = TurnContract(
        original_user_input="Can you turn the previous point into a practice question?",
        resolved_intent="topic_drill",
        citation_required=False,
    )

    assert gauntlet._should_audit_answer_claims(contract, _evidence()) is False


def test_reliability_conversation_records_turn_exception_as_report_failure(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path)

    with (
        patch("scripts.run_chat_reliability_gauntlet.create_session", return_value=session),
        patch(
            "scripts.run_chat_reliability_gauntlet.iter_chat_events",
            side_effect=RuntimeError("provider unavailable"),
        ),
    ):
        report = gauntlet.run_reliability_conversation(
            tmp_path,
            ChatConfig(),
            level="test",
            turns=[
                gauntlet.ReliabilityTurnSpec(
                    "What is the material about?",
                    (gauntlet.CATEGORY_TOPIC_SWITCH,),
                    require_citations_when_evidence=True,
                ),
                gauntlet.ReliabilityTurnSpec(
                    "What else?",
                    (gauntlet.CATEGORY_VAGUE_FOLLOWUP,),
                    require_citations_when_evidence=True,
                ),
            ],
            requirements=gauntlet.RunRequirements(turns=2, topic_switches=1),
            resume_every=0,
            require_trace=False,
        )

    assert report["status"] == 1
    assert report["turns"] == 1
    assert report["metrics"]["failed_turns"] == 1
    assert "turn raised RuntimeError: provider unavailable" in report["failures"][0]


def test_reliability_conversation_retries_transient_provider_timeout(tmp_path: Path) -> None:
    session = _session(tmp_path)
    calls = 0

    def fake_events(
        session: ChatSession,
        prompt: str,
    ) -> list[AssistantDeltaEvent | TurnCompleteEvent]:
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise EngineError("ChatGPT Codex request failed: The read operation timed out")
        return _fake_events(session, prompt)

    with (
        patch("scripts.run_chat_reliability_gauntlet.create_session", return_value=session),
        patch("scripts.run_chat_reliability_gauntlet.iter_chat_events", side_effect=fake_events),
    ):
        report = gauntlet.run_reliability_conversation(
            tmp_path,
            ChatConfig(),
            level="test",
            turns=[
                gauntlet.ReliabilityTurnSpec(
                    "What is the material about?",
                    (gauntlet.CATEGORY_TOPIC_SWITCH,),
                )
            ],
            requirements=gauntlet.RunRequirements(turns=1, topic_switches=1),
            resume_every=0,
            require_trace=False,
        )

    assert calls == 3
    assert report["status"] == 0


def test_full_suite_requires_claim_audit_for_acceptance() -> None:
    reports = [
        gauntlet.ReliabilityConversationReport(
            armory="/tmp/armory",
            level="full",
            model="model",
            base_url="base",
            turns=100,
            status=0,
            category_counts={},
            requirements={},
            resume_count=5,
            compact_count=3,
            trace_user_turns=100,
            trace_reply_contracts=100,
            trace_replayable_turns=100,
            unsupported_claims_checked=False,
            metrics=gauntlet.ReliabilityConversationMetrics(
                turn_pass_rate=1.0,
                passed_turns=100,
                failed_turns=0,
                citation_verification_failures=0,
                missing_citation_failures=0,
                literal_followup_retrieval_failures=0,
                claim_audit_checked_turns=0,
                unsupported_claim_failures=0,
            ),
            failures=[],
            results=[],
        )
    ]

    failures = gauntlet._suite_failures(
        "full",
        reports,
        (),
        min_seeded_runs=10,
        require_claim_audit=True,
    )

    assert failures == ["unsupported claim audit skipped for conversation(s): 1"]


def test_seeded_suite_requires_distinct_armories(tmp_path: Path) -> None:
    session = _session(tmp_path)
    armory_a = tmp_path / "a"
    armory_b = tmp_path / "b"

    with (
        patch("scripts.run_chat_reliability_gauntlet.create_session", return_value=session),
        patch("scripts.run_chat_reliability_gauntlet.resume_session", return_value=session),
        patch("scripts.run_chat_reliability_gauntlet.save_session", return_value=tmp_path),
        patch("scripts.run_chat_reliability_gauntlet.compact_session"),
        patch("scripts.run_chat_reliability_gauntlet.iter_chat_events", side_effect=_fake_events),
    ):
        report = gauntlet.run_suite(
            armory_a,
            ChatConfig(),
            level="seeded",
            seeded_armories=(armory_a, armory_b),
            min_seeded_runs=2,
            require_trace=False,
        )

    assert report["status"] == 0
    assert report["conversations"] == 2
    assert report["metrics"]["turn_pass_rate"] == 1.0
