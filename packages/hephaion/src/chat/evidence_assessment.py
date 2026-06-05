from __future__ import annotations

import difflib
from dataclasses import dataclass, replace

from rag.context import EvidenceChunk, TurnEvidence
from rag.scoring import tokenize
from study.policy import EvidenceAssessment, assess_evidence
from study.prompt_plans import LearningTurnPlan
from study.state import LearningAction

from chat.evidence_format import evidence_refs
from chat.evidence_format import excerpt as _excerpt
from chat.turn_contract import (
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
)

_QUOTE_CHARS = "'\"\u201c\u201d\u2018\u2019"
_DIRECT_SUPPORT_MIN_TOKEN_LEN = 4
_DIRECT_SUPPORT_MIN_COVERAGE = 0.5
_EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE = 0.3
_DIRECT_SUPPORT_MIN_MATCHES = 2
_DIRECT_SUPPORT_DISTINCTIVE_TOKEN_FLOOR = 0.5
_DIRECT_SUPPORT_DISTINCTIVE_MIN_MISSING = 2
_DIRECT_SUPPORT_QUERY_OVERLAP_FLOOR = 0.6
_DIRECT_SUPPORT_DOMINANT_SCORE_FLOOR = 0.75
_DIRECT_SUPPORT_DOMINANT_SCORE_RATIO = 2.0
_DIRECT_SUPPORT_DOMINANT_MIN_MATCHES = 2


@dataclass(frozen=True, slots=True)
class _DirectSupportSignals:
    query: str
    strict_source_match: bool
    expanded_prior: bool
    support_floor: float
    expanded_prior_direct_query_missing: bool
    strict_terms_missing: bool
    quoted_phrase_missing: bool


def assess_turn_evidence(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
) -> EvidenceAssessment:
    source_only = _plan_needs_source_only_answer(plan)
    assessment = assess_evidence(
        tuple(evidence_refs(turn_evidence)),
        source_only=source_only,
        missing_hint=_missing_evidence_hint(plan, source_only=source_only),
    )
    assessment = _adjust_evidence_assessment(plan, assessment)
    return _direct_support_adjusted_assessment(plan, turn_evidence, assessment)


def _plan_needs_source_only_answer(plan: LearningTurnPlan) -> bool:
    return plan.action is LearningAction.SOURCE_QA


def _missing_evidence_hint(plan: LearningTurnPlan, *, source_only: bool) -> str:
    if plan.action is LearningAction.PRIORITY:
        return "recurring topics, exam weighting, or prerequisite evidence"
    if source_only:
        return "source span that directly answers the source-only question"
    if plan.action is LearningAction.ASSESS:
        return "rubric, mark scheme, or source span for grounded assessment"
    return "source span that supports the requested response"


def _adjust_evidence_assessment(
    plan: LearningTurnPlan,
    assessment: EvidenceAssessment,
) -> EvidenceAssessment:
    if assessment.sufficient or assessment.recommended_action != "retrieve_more":
        return assessment
    if _should_ask_clarifying_query(plan, assessment):
        return replace(assessment, recommended_action="ask_clarifying_question")
    return assessment


def _direct_support_adjusted_assessment(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
    assessment: EvidenceAssessment,
) -> EvidenceAssessment:
    if plan.action is not LearningAction.SOURCE_QA:
        return assessment
    if _source_answer_reuses_prior_evidence(plan, turn_evidence):
        return _direct_support_sufficient_assessment(
            assessment,
            support=_DIRECT_SUPPORT_MIN_COVERAGE,
        )
    query = _source_answer_query(plan)
    if not query:
        return assessment
    signals = _direct_support_signals(plan, turn_evidence, query)
    support = _direct_support_value(signals, turn_evidence)
    if support >= signals.support_floor:
        if assessment.sufficient:
            return assessment
        return _direct_support_sufficient_assessment(assessment, support=support)
    if _can_keep_existing_assessment(signals):
        return assessment
    return _direct_support_abstention_assessment(assessment, signals.query, support=support)


def _direct_support_signals(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
    query: str,
) -> _DirectSupportSignals:
    strict_source_match = plan.requires_direct_evidence or plan.retrieval_query is None
    expanded_prior = _source_answer_expands_prior_evidence(plan)
    expanded_prior_source_anchor = _expanded_prior_source_anchor(
        expanded_prior,
        query,
        turn_evidence,
    )
    query_terms_missing = _query_terms_missing(query, turn_evidence)
    return _DirectSupportSignals(
        query=query,
        strict_source_match=strict_source_match,
        expanded_prior=expanded_prior,
        support_floor=_support_floor(
            expanded_prior_source_anchor=expanded_prior_source_anchor,
            strict_source_match=strict_source_match,
            expanded_prior=expanded_prior,
        ),
        expanded_prior_direct_query_missing=_expanded_prior_direct_query_missing(
            plan,
            expanded_prior=expanded_prior,
            query_terms_missing=query_terms_missing,
            expanded_prior_source_anchor=expanded_prior_source_anchor,
        ),
        strict_terms_missing=bool(
            strict_source_match and not expanded_prior and query_terms_missing
        ),
        quoted_phrase_missing=_quoted_phrase_missing(plan, turn_evidence),
    )


def _expanded_prior_source_anchor(
    expanded_prior: bool,
    query: str,
    turn_evidence: TurnEvidence | None,
) -> bool:
    return bool(
        expanded_prior
        and turn_evidence is not None
        and _query_matches_evidence_source(query, turn_evidence)
    )


def _support_floor(
    *,
    expanded_prior_source_anchor: bool,
    strict_source_match: bool,
    expanded_prior: bool,
) -> float:
    if expanded_prior_source_anchor:
        return _EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE
    if strict_source_match:
        return _DIRECT_SUPPORT_MIN_COVERAGE
    if expanded_prior:
        return _EXPANDED_DIRECT_SUPPORT_MIN_COVERAGE
    return _DIRECT_SUPPORT_MIN_COVERAGE


def _query_terms_missing(query: str, turn_evidence: TurnEvidence | None) -> bool:
    return bool(
        query
        and turn_evidence is not None
        and _distinctive_query_terms_missing(
            _direct_support_terms(query),
            turn_evidence,
        )
    )


def _expanded_prior_direct_query_missing(
    plan: LearningTurnPlan,
    *,
    expanded_prior: bool,
    query_terms_missing: bool,
    expanded_prior_source_anchor: bool,
) -> bool:
    return bool(
        expanded_prior
        and plan.requires_direct_evidence
        and plan.retrieval_query
        and query_terms_missing
        and not expanded_prior_source_anchor
        and _query_preserves_user_terms(
            plan.retrieval_query,
            _source_answer_original_request(plan),
        )
    )


def _quoted_phrase_missing(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
) -> bool:
    return bool(
        plan.retrieval_query
        and turn_evidence is not None
        and _quoted_phrase_terms_missing(plan.retrieval_query, turn_evidence)
    )


def _direct_support_value(
    signals: _DirectSupportSignals,
    turn_evidence: TurnEvidence | None,
) -> float:
    if (
        signals.strict_terms_missing
        or signals.expanded_prior_direct_query_missing
        or signals.quoted_phrase_missing
    ):
        return 0.0
    if signals.expanded_prior:
        return _direct_support_coverage_score(signals.query, turn_evidence)
    support = _direct_support_score(signals.query, turn_evidence)
    return max(support, _dominant_retrieval_support_score(signals.query, turn_evidence))


def _can_keep_existing_assessment(signals: _DirectSupportSignals) -> bool:
    return (
        not signals.strict_source_match
        and not signals.expanded_prior_direct_query_missing
        and not signals.quoted_phrase_missing
    )


def _direct_support_sufficient_assessment(
    assessment: EvidenceAssessment,
    *,
    support: float,
) -> EvidenceAssessment:
    return replace(
        assessment,
        sufficient=True,
        confidence=max(assessment.confidence, support),
        missing_information=(),
        recommended_action="answer",
    )


def _direct_support_abstention_assessment(
    assessment: EvidenceAssessment,
    query: str,
    *,
    support: float,
) -> EvidenceAssessment:
    return replace(
        assessment,
        sufficient=False,
        confidence=min(assessment.confidence, support),
        missing_information=(f"direct source span for {_excerpt(query, limit=140)}",),
        recommended_action="abstain",
    )


def _source_answer_reuses_prior_evidence(
    plan: LearningTurnPlan,
    turn_evidence: TurnEvidence | None,
) -> bool:
    return bool(
        plan.retrieval_strategy == RETRIEVAL_STRATEGY_REUSE_PRIOR
        and not plan.requires_direct_evidence
        and plan.evidence_refs
        and turn_evidence is not None
        and turn_evidence.items
    )


def _source_answer_expands_prior_evidence(plan: LearningTurnPlan) -> bool:
    return bool(plan.retrieval_strategy == RETRIEVAL_STRATEGY_EXPAND_PRIOR and plan.evidence_refs)


def _source_answer_query(plan: LearningTurnPlan) -> str:
    original_request = _source_answer_original_request(plan)
    if plan.requires_direct_evidence and original_request:
        return original_request
    if plan.retrieval_query:
        return plan.retrieval_query
    return original_request


def _source_answer_original_request(plan: LearningTurnPlan) -> str:
    return plan.original_user_input.strip()


def _direct_support_score(query: str, turn_evidence: TurnEvidence | None) -> float:
    if turn_evidence is None:
        return 0.0
    query_terms = _direct_support_terms(query)
    if not query_terms:
        return 1.0
    if _distinctive_query_terms_missing(query_terms, turn_evidence):
        return 0.0
    min_matches = (
        1 if len(query_terms) <= _DIRECT_SUPPORT_MIN_MATCHES else _DIRECT_SUPPORT_MIN_MATCHES
    )
    return max(
        (
            _direct_support_item_score(query_terms, item, min_matches=min_matches)
            for item in turn_evidence.items
        ),
        default=0.0,
    )


def _direct_support_coverage_score(query: str, turn_evidence: TurnEvidence | None) -> float:
    if turn_evidence is None:
        return 0.0
    query_terms = _direct_support_terms(query)
    if not query_terms:
        return 0.0
    min_matches = (
        1 if len(query_terms) <= _DIRECT_SUPPORT_MIN_MATCHES else _DIRECT_SUPPORT_MIN_MATCHES
    )
    return max(
        (
            _direct_support_item_score(query_terms, item, min_matches=min_matches)
            for item in turn_evidence.items
        ),
        default=0.0,
    )


def _dominant_retrieval_support_score(query: str, turn_evidence: TurnEvidence | None) -> float:
    if turn_evidence is None or not turn_evidence.items:
        return 0.0
    query_terms = _direct_support_terms(query)
    if not query_terms:
        return 0.0
    top_item = turn_evidence.items[0]
    if top_item.score < _DIRECT_SUPPORT_DOMINANT_SCORE_FLOOR:
        return 0.0
    if not _dominant_score_ratio_allows(top_item.score, turn_evidence):
        return 0.0
    return _dominant_top_term_score(query_terms, top_item)


def _dominant_score_ratio_allows(top_score: float, turn_evidence: TurnEvidence) -> bool:
    next_score = max((item.score for item in turn_evidence.items[1:]), default=0.0)
    return next_score <= 0 or top_score / next_score >= _DIRECT_SUPPORT_DOMINANT_SCORE_RATIO


def _dominant_top_term_score(
    query_terms: tuple[str, ...],
    top_item: EvidenceChunk,
) -> float:
    top_terms = set(_direct_support_terms(f"{top_item.chunk.heading}\n{top_item.content}"))
    matches = sum(1 for term in query_terms if _direct_term_in_terms(term, top_terms))
    if matches < _DIRECT_SUPPORT_DOMINANT_MIN_MATCHES:
        return 0.0
    return max(_DIRECT_SUPPORT_MIN_COVERAGE, matches / len(query_terms))


def _direct_support_item_score(
    query_terms: tuple[str, ...],
    item: EvidenceChunk,
    *,
    min_matches: int,
) -> float:
    item_terms = set(_direct_support_terms(f"{item.chunk.heading}\n{item.content}"))
    matches = sum(1 for term in query_terms if _direct_term_in_terms(term, item_terms))
    if matches < min_matches:
        return 0.0
    return matches / len(query_terms)


def _query_preserves_user_terms(query: str, user_request: str) -> bool:
    query_terms = set(_direct_support_terms(query))
    request_terms = set(_direct_support_terms(user_request))
    if not query_terms or not request_terms:
        return False
    return (
        sum(1 for term in query_terms if _direct_term_in_terms(term, request_terms))
        / len(query_terms)
        >= _DIRECT_SUPPORT_QUERY_OVERLAP_FLOOR
    )


def _direct_support_terms(text: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            term
            for term in tokenize(text)
            if len(term) >= _DIRECT_SUPPORT_MIN_TOKEN_LEN and not term.isdigit()
        )
    )


def _query_matches_evidence_source(query: str, turn_evidence: TurnEvidence) -> bool:
    query_terms = set(_direct_support_terms(query))
    if not query_terms:
        return False
    for item in turn_evidence.items:
        source_terms = set(_direct_support_terms(item.source))
        if source_terms and any(_direct_term_in_terms(term, source_terms) for term in query_terms):
            return True
    return False


def _distinctive_query_terms_missing(
    query_terms: tuple[str, ...],
    turn_evidence: TurnEvidence,
) -> bool:
    if len(query_terms) < _DIRECT_SUPPORT_MIN_MATCHES:
        return False
    evidence_terms = _turn_evidence_terms(turn_evidence)
    missing_terms = [
        term for term in query_terms if not _direct_term_in_terms(term, evidence_terms)
    ]
    if len(missing_terms) < _DIRECT_SUPPORT_DISTINCTIVE_MIN_MISSING:
        return False
    return len(missing_terms) / len(query_terms) >= _DIRECT_SUPPORT_DISTINCTIVE_TOKEN_FLOOR


def _turn_evidence_terms(turn_evidence: TurnEvidence) -> set[str]:
    terms: set[str] = set()
    for item in turn_evidence.items:
        terms.update(_direct_support_terms(f"{item.chunk.heading}\n{item.content}"))
    return terms


def _quoted_phrase_terms_missing(query: str, turn_evidence: TurnEvidence) -> bool:
    evidence_terms = _turn_evidence_terms(turn_evidence)
    for phrase in _quoted_phrases(query):
        phrase_terms = _direct_support_terms(phrase)
        if len(phrase_terms) < _DIRECT_SUPPORT_MIN_MATCHES:
            continue
        if not all(_direct_term_in_terms(term, evidence_terms) for term in phrase_terms):
            return True
    return False


def _direct_term_in_terms(term: str, terms: set[str]) -> bool:
    return any(_direct_terms_match(term, candidate) for candidate in terms)


def _direct_terms_match(left: str, right: str) -> bool:
    if left == right:
        return True
    if min(len(left), len(right)) < _DIRECT_SUPPORT_MIN_TOKEN_LEN + 1:
        return False
    return difflib.SequenceMatcher(a=left, b=right).ratio() >= 0.84


def _quoted_phrases(text: str) -> tuple[str, ...]:
    phrases: list[str] = []
    opening_index: int | None = None
    for index, character in enumerate(text):
        if not _is_quote_delimiter(text, index, character):
            continue
        if opening_index is None:
            opening_index = index
            continue
        phrase = text[opening_index + 1 : index].strip()
        if len(phrase) >= 3:
            phrases.append(phrase)
        opening_index = None
    return tuple(phrases)


def _is_quote_delimiter(text: str, index: int, character: str) -> bool:
    if character not in _QUOTE_CHARS:
        return False
    if character not in {"'", "\u2019"}:
        return True
    previous_is_word = index > 0 and text[index - 1].isalnum()
    next_is_word = index + 1 < len(text) and text[index + 1].isalnum()
    return not (previous_is_word and next_is_word)


def _should_ask_clarifying_query(
    plan: LearningTurnPlan,
    assessment: EvidenceAssessment,
) -> bool:
    if plan.action not in {LearningAction.PRESENT, LearningAction.PRIORITY}:
        return False
    if not _needs_clarifying_query(plan.retrieval_query or ""):
        return False
    return plan.action is not LearningAction.PRESENT or bool(assessment.supporting_refs)


def _needs_clarifying_query(query: str) -> bool:
    normalized = " ".join(query.split())
    return bool(normalized) and len(normalized) <= 18


def evidence_assessment_trace(
    assessment: EvidenceAssessment | None,
) -> dict[str, object]:
    if assessment is None:
        return {}
    return {
        "sufficient": assessment.sufficient,
        "confidence": round(assessment.confidence, 3),
        "supporting_refs": list(assessment.supporting_refs),
        "missing_information": list(assessment.missing_information),
        "conflicts": list(assessment.conflicts),
        "source_diversity_score": round(assessment.source_diversity_score, 3),
        "recommended_action": assessment.recommended_action,
    }
