"""Intent classifier contract for material chat turns."""

from __future__ import annotations

import re
from collections.abc import Mapping

from hephaion.chat.turn_contract import TurnIntentResolution, intent_resolution_from_payload

MODEL_NORMALIZED_INTENTS = (
    "material_overview",
    "source_qa",
    "source_only_policy",
    "topic_presentation",
    "topic_drill",
    "ready_for_recall",
    "recall_clarification",
    "recall_answer_attempt",
    "reveal_request",
    "hint_request",
    "skip_request",
    "scaffold_request",
    "material_review",
    "priority_request",
    "driven_learning_calibration",
    "wait",
    "heph_action",
    "heph_help",
    "chat",
)
MODEL_NORMALIZED_CONFIDENCE_THRESHOLD = 0.75
LEARNING_INTENT_NORMALIZATION_SCHEMA = "\n".join(
    (
        "{",
        f'  "intent": "{" | ".join(MODEL_NORMALIZED_INTENTS)}",',
        '  "canonical_english_request": "concise English request preserving the user\'s intent",',
        '  "is_followup": true,',
        (
            '  "followup_target": "what prior answer, cited claim, bullet, source, '
            'or topic this refers to",'
        ),
        (
            '  "answer_mode": "answer_from_evidence | transform_prior_answer | '
            'reason_from_prior_evidence",'
        ),
        '  "answer_format": "plain | table | list",',
        (
            '  "retrieval_strategy": "retrieve | reuse_prior_evidence | '
            'expand_prior_evidence | overview | none",'
        ),
        (
            '  "retrieval_query": "semantic retrieval query derived from the '
            'conversation, not filler words",'
        ),
        '  "direct_evidence_required": true,',
        '  "prior_answer_reference": true,',
        '  "prior_answer_positions": [1, 3],',
        '  "prior_answer_position_basis": "cited_claims | list_items | none",',
        '  "confidence": 0.0',
        "}",
    )
)
LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT = """
Resolve routing hints for the current Heph turn; do not answer the user.

Materials are the default subject. Keep the current user request primary; use prior context only
to resolve references. New source content uses answer_from_evidence. Broad corpus views use
overview. Specific facts, definitions, quotes, named concepts, or named sources use retrieve.
Product/self explanation turns use heph_help with retrieval_strategy=none, not material_overview.
Product operations that create, validate, or import armories/material files use heph_action with
retrieval_strategy=none.
Corpus-level synthesis, comparison, evaluation, ranking, prioritization, or judgment over the
materials uses material_overview with retrieval_strategy=overview, even when the answer should
name one resulting topic or source. Do not turn a corpus-level operation into a literal keyword
lookup unless the user asks about a specific named concept, source, citation, or quoted claim.
If the user asks for a direct source-stated answer, use source_qa with
direct_evidence_required=true even when the answer may be that the retrieved evidence does not
state it. Do not convert direct answerability into a broad corpus overview.
Set is_followup=false unless the current request explicitly depends on a prior answer, citation,
source, listed item, table row, or continuing instruction. A fresh question about the materials is
not a follow-up merely because previous turns exist.
Use topic_drill only when the current user request asks Heph to quiz, drill, practice, or ask a
recall question; never carry drill mode from the previous assistant question by inertia.
Pure rewrites of a displayed prior answer use transform_prior_answer and reuse prior evidence.
Requests that change the prior answer's length, language, format, or presentation without asking
for a new source fact are transform_prior_answer turns, not source lookups.
Questions about why a cited prior answer matters use reason_from_prior_evidence.
Interpretation, relevance, implication, application, or cited synthesis follow-ups over a cited
prior answer use reason_from_prior_evidence with direct_evidence_required=false. Set
direct_evidence_required=true only when the requested answer is an exact quoted span, source or
citation location, or whether a source states a specific claim.
When the user points to cited/list/table positions in a prior answer, fill prior_answer_positions
and prior_answer_position_basis.

Return compact JSON only:
""".strip()


def classifier_intent_from_payload(
    payload: Mapping[str, object] | None,
) -> tuple[str, float]:
    if payload is None:
        return ("", 0.0)
    raw_intent = payload.get("intent")
    if not isinstance(raw_intent, str):
        return ("", 0.0)
    intent = re.sub(r"[^a-z0-9]+", "_", raw_intent.strip().casefold()).strip("_")
    if intent not in MODEL_NORMALIZED_INTENTS:
        return ("", 0.0)
    return (intent, normalized_confidence(payload.get("confidence")))


def normalized_learning_intent_from_payload(
    payload: Mapping[str, object] | None,
) -> TurnIntentResolution | None:
    intent, confidence = classifier_intent_from_payload(payload)
    if not intent:
        return None
    return intent_resolution_from_payload(payload, intent=intent, confidence=confidence)


def normalized_confidence(value: object) -> float:
    if isinstance(value, int | float):
        confidence = float(value)
    elif isinstance(value, str):
        try:
            confidence = float(value.strip().rstrip("%"))
        except ValueError:
            return 0.0
    else:
        return 0.0
    if confidence > 1.0:
        confidence /= 100.0
    return min(1.0, max(0.0, confidence))


_MODEL_NORMALIZED_INTENTS = MODEL_NORMALIZED_INTENTS
_MODEL_NORMALIZED_CONFIDENCE_THRESHOLD = MODEL_NORMALIZED_CONFIDENCE_THRESHOLD
_LEARNING_INTENT_NORMALIZATION_SCHEMA = LEARNING_INTENT_NORMALIZATION_SCHEMA
_LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT = LEARNING_INTENT_NORMALIZATION_SYSTEM_PROMPT
_classifier_intent_from_payload = classifier_intent_from_payload
_normalized_learning_intent_from_payload = normalized_learning_intent_from_payload
_normalized_confidence = normalized_confidence
