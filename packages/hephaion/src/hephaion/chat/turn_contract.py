"""Durable per-turn contracts for material chat."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from hephaion._types import is_string_mapping

RETRIEVAL_STRATEGY_RETRIEVE = "retrieve"
RETRIEVAL_STRATEGY_REUSE_PRIOR = "reuse_prior_evidence"
RETRIEVAL_STRATEGY_EXPAND_PRIOR = "expand_prior_evidence"
RETRIEVAL_STRATEGY_OVERVIEW = "overview"
RETRIEVAL_STRATEGY_NONE = "none"
ANSWER_MODE_FROM_EVIDENCE = "answer_from_evidence"
ANSWER_MODE_TRANSFORM_PRIOR = "transform_prior_answer"
ANSWER_MODE_REASON_FROM_PRIOR = "reason_from_prior_evidence"
ANSWER_FORMAT_PLAIN = "plain"
ANSWER_FORMAT_TABLE = "table"
ANSWER_FORMAT_LIST = "list"

_RETRIEVAL_STRATEGIES = frozenset(
    {
        RETRIEVAL_STRATEGY_RETRIEVE,
        RETRIEVAL_STRATEGY_REUSE_PRIOR,
        RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        RETRIEVAL_STRATEGY_OVERVIEW,
        RETRIEVAL_STRATEGY_NONE,
    }
)
_ANSWER_MODES = frozenset(
    {ANSWER_MODE_FROM_EVIDENCE, ANSWER_MODE_TRANSFORM_PRIOR, ANSWER_MODE_REASON_FROM_PRIOR}
)
_ANSWER_FORMATS = frozenset({ANSWER_FORMAT_PLAIN, ANSWER_FORMAT_TABLE, ANSWER_FORMAT_LIST})


@dataclass(frozen=True, slots=True)
class TurnIntentResolution:
    """Model-resolved user meaning before deterministic planning."""

    intent: str = ""
    canonical_request: str = ""
    confidence: float = 0.0
    is_followup: bool = False
    followup_target: str = ""
    answer_mode: str = ANSWER_MODE_FROM_EVIDENCE
    answer_format: str = ANSWER_FORMAT_PLAIN
    retrieval_strategy: str = RETRIEVAL_STRATEGY_RETRIEVE
    retrieval_query: str = ""
    direct_evidence_required: bool = False
    prior_answer_reference: bool = False
    prior_answer_positions: tuple[int, ...] = ()
    prior_answer_position_basis: str = ""


@dataclass(frozen=True, slots=True)
class TurnContract:
    """Serializable contract for a material-chat turn."""

    original_user_input: str
    resolved_intent: str = ""
    canonical_request: str = ""
    is_followup: bool = False
    followup_target: str = ""
    answer_mode: str = ANSWER_MODE_FROM_EVIDENCE
    answer_format: str = ANSWER_FORMAT_PLAIN
    retrieval_strategy: str = RETRIEVAL_STRATEGY_RETRIEVE
    retrieval_query: str = ""
    evidence_refs: tuple[str, ...] = ()
    citation_required: bool = False
    direct_evidence_required: bool = False
    prior_answer_reference: bool = False
    prior_answer_positions: tuple[int, ...] = ()
    prior_answer_position_basis: str = ""
    prior_turn_original_user_input: str = ""
    prior_turn_resolved_intent: str = ""
    prior_turn_canonical_request: str = ""
    prior_turn_evidence_refs: tuple[str, ...] = ()
    prior_turn_validation_result: str = ""
    prior_answer_excerpt: str = ""
    validation_result: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "original_user_input": self.original_user_input,
            "resolved_intent": self.resolved_intent,
            "canonical_request": self.canonical_request,
            "is_followup": self.is_followup,
            "followup_target": self.followup_target,
            "answer_mode": self.answer_mode,
            "answer_format": self.answer_format,
            "retrieval_strategy": self.retrieval_strategy,
            "retrieval_query": self.retrieval_query,
            "evidence_refs": list(self.evidence_refs),
            "citation_required": self.citation_required,
            "direct_evidence_required": self.direct_evidence_required,
            "prior_answer_reference": self.prior_answer_reference,
            "prior_answer_positions": list(self.prior_answer_positions),
            "prior_answer_position_basis": self.prior_answer_position_basis,
            "prior_turn_original_user_input": self.prior_turn_original_user_input,
            "prior_turn_resolved_intent": self.prior_turn_resolved_intent,
            "prior_turn_canonical_request": self.prior_turn_canonical_request,
            "prior_turn_evidence_refs": list(self.prior_turn_evidence_refs),
            "prior_turn_validation_result": self.prior_turn_validation_result,
            "prior_answer_excerpt": self.prior_answer_excerpt,
            "validation_result": self.validation_result,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, payload: object) -> TurnContract | None:
        if not is_string_mapping(payload):
            return None
        original_user_input = _payload_string(payload, "original_user_input")
        if not original_user_input:
            return None
        return cls(
            original_user_input=original_user_input,
            resolved_intent=_payload_string(payload, "resolved_intent"),
            canonical_request=_payload_string(payload, "canonical_request"),
            is_followup=_payload_bool(payload, "is_followup"),
            followup_target=_payload_string(payload, "followup_target"),
            answer_mode=_normalized_answer_mode(_payload_string(payload, "answer_mode")),
            answer_format=_normalized_answer_format(_payload_string(payload, "answer_format")),
            retrieval_strategy=_normalized_retrieval_strategy(
                _payload_string(payload, "retrieval_strategy")
            ),
            retrieval_query=_payload_string(payload, "retrieval_query"),
            evidence_refs=tuple(_payload_string_sequence(payload, "evidence_refs")),
            citation_required=_payload_bool(payload, "citation_required"),
            direct_evidence_required=_payload_bool(payload, "direct_evidence_required"),
            prior_answer_reference=_payload_bool(payload, "prior_answer_reference"),
            prior_answer_positions=tuple(_payload_int_sequence(payload, "prior_answer_positions")),
            prior_answer_position_basis=_payload_string(
                payload,
                "prior_answer_position_basis",
            ),
            prior_turn_original_user_input=_payload_string(
                payload,
                "prior_turn_original_user_input",
            ),
            prior_turn_resolved_intent=_payload_string(payload, "prior_turn_resolved_intent"),
            prior_turn_canonical_request=_payload_string(
                payload,
                "prior_turn_canonical_request",
            ),
            prior_turn_evidence_refs=tuple(
                _payload_string_sequence(payload, "prior_turn_evidence_refs")
            ),
            prior_turn_validation_result=_payload_string(
                payload,
                "prior_turn_validation_result",
            ),
            prior_answer_excerpt=_payload_string(payload, "prior_answer_excerpt"),
            validation_result=_payload_string(payload, "validation_result"),
            confidence=_payload_float(payload, "confidence"),
        )


def turn_contract_from_resolution(
    original_user_input: str,
    resolution: TurnIntentResolution,
) -> TurnContract:
    return TurnContract(
        original_user_input=original_user_input,
        resolved_intent=resolution.intent,
        canonical_request=resolution.canonical_request,
        is_followup=resolution.is_followup,
        followup_target=resolution.followup_target,
        answer_mode=resolution.answer_mode,
        answer_format=resolution.answer_format,
        retrieval_strategy=resolution.retrieval_strategy,
        retrieval_query=resolution.retrieval_query,
        direct_evidence_required=resolution.direct_evidence_required,
        prior_answer_reference=resolution.prior_answer_reference,
        prior_answer_positions=resolution.prior_answer_positions,
        prior_answer_position_basis=resolution.prior_answer_position_basis,
        confidence=resolution.confidence,
    )


def intent_resolution_from_payload(
    payload: Mapping[str, object] | None,
    *,
    intent: str,
    confidence: float,
) -> TurnIntentResolution:
    if payload is None:
        return TurnIntentResolution(intent=intent, confidence=confidence)
    canonical_request = _payload_string(payload, "canonical_english_request")
    retrieval_query = _payload_string(payload, "retrieval_query") or _payload_string(
        payload, "query"
    )
    return TurnIntentResolution(
        intent=intent,
        canonical_request=canonical_request,
        confidence=confidence,
        is_followup=_payload_bool(payload, "is_followup"),
        followup_target=_payload_string(payload, "followup_target"),
        answer_mode=_normalized_answer_mode(_payload_string(payload, "answer_mode")),
        answer_format=_normalized_answer_format(_payload_string(payload, "answer_format")),
        retrieval_strategy=_normalized_retrieval_strategy(
            _payload_string(payload, "evidence_strategy")
            or _payload_string(payload, "retrieval_strategy")
        ),
        retrieval_query=retrieval_query,
        direct_evidence_required=_payload_bool(payload, "direct_evidence_required"),
        prior_answer_reference=_payload_bool(payload, "prior_answer_reference"),
        prior_answer_positions=tuple(_payload_int_sequence(payload, "prior_answer_positions")),
        prior_answer_position_basis=_payload_string(payload, "prior_answer_position_basis"),
    )


def _payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def _payload_bool(payload: Mapping[str, object], key: str) -> bool:
    return payload.get(key) is True


def _payload_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, int | float):
        return max(0.0, min(1.0, float(value)))
    return 0.0


def _payload_string_sequence(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def _payload_int_sequence(payload: Mapping[str, object], key: str) -> tuple[int, ...]:
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return ()
    numbers: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool):
            continue
        if item > 0 and item not in numbers:
            numbers.append(item)
    return tuple(numbers)


def _normalized_retrieval_strategy(value: str) -> str:
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    return normalized if normalized in _RETRIEVAL_STRATEGIES else RETRIEVAL_STRATEGY_RETRIEVE


def _normalized_answer_mode(value: str) -> str:
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    return normalized if normalized in _ANSWER_MODES else ANSWER_MODE_FROM_EVIDENCE


def _normalized_answer_format(value: str) -> str:
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    return normalized if normalized in _ANSWER_FORMATS else ANSWER_FORMAT_PLAIN


__all__ = [
    "ANSWER_FORMAT_LIST",
    "ANSWER_FORMAT_PLAIN",
    "ANSWER_FORMAT_TABLE",
    "ANSWER_MODE_FROM_EVIDENCE",
    "ANSWER_MODE_REASON_FROM_PRIOR",
    "ANSWER_MODE_TRANSFORM_PRIOR",
    "RETRIEVAL_STRATEGY_EXPAND_PRIOR",
    "RETRIEVAL_STRATEGY_NONE",
    "RETRIEVAL_STRATEGY_OVERVIEW",
    "RETRIEVAL_STRATEGY_RETRIEVE",
    "RETRIEVAL_STRATEGY_REUSE_PRIOR",
    "TurnContract",
    "TurnIntentResolution",
    "intent_resolution_from_payload",
    "turn_contract_from_resolution",
]
