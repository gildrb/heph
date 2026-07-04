"""Assessment parsing and recall-rating helpers for practice sessions."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from ai.logging import get_logger

from harness.documents.state import RecallFeedbackType, RecallRating

_log = get_logger("harness.documents.assessment")

ASSESS_PREFIX_RE = re.compile(r"^\s*(CORRECT|PARTIAL|WRONG)\s*[:\-]?\s*", re.IGNORECASE)
ASSESS_SECTION_RE = re.compile(
    r"^(?:Score|Got|Missing|Misconception|Correction|Confidence):",
    re.IGNORECASE,
)
CONFIDENCE_RE = re.compile(
    r"\b(?:confidence|confident|sure)(?:\s+is)?\s*[:=]?\s*"
    r"(?P<value>\d+(?:[.]\d+)?)\s*"
    r"(?P<unit>%|/10|/5)?(?=\s|[.,;:!?]|$)",
    re.IGNORECASE,
)


def _fallback_assessment_message(feedback: RecallFeedbackType) -> str:
    if feedback is RecallFeedbackType.CORRECT:
        return "I could not parse the assessment output as CORRECT."
    if feedback is RecallFeedbackType.WRONG:
        return "I could not parse the assessment output as WRONG."
    return "I could not parse the assessment output as PARTIAL."


def parse_assessment_reply(reply: str) -> tuple[RecallFeedbackType, str]:
    match = ASSESS_PREFIX_RE.match(reply)
    if not match:
        _log.warning("assessment reply missing prefix; defaulting to PARTIAL")
        cleaned = reply.strip() or _fallback_assessment_message(RecallFeedbackType.PARTIAL)
        return RecallFeedbackType.PARTIAL, _assessment_visible_reply("PARTIAL", cleaned)

    label = match.group(1).upper()
    cleaned = ASSESS_PREFIX_RE.sub("", reply, count=1).strip()
    feedback = {
        "CORRECT": RecallFeedbackType.CORRECT,
        "PARTIAL": RecallFeedbackType.PARTIAL,
        "WRONG": RecallFeedbackType.WRONG,
    }[label]
    body = cleaned or _fallback_assessment_message(feedback)
    return feedback, _assessment_visible_reply(label, body)


def _assessment_visible_reply(label: str, body: str) -> str:
    cleaned = body.strip()
    if ASSESS_SECTION_RE.match(cleaned):
        return f"{label}:\n{cleaned}"
    return f"{label}: {cleaned}"


def derive_recall_rating(
    feedback: RecallFeedbackType,
    elapsed_seconds: int | None,
) -> RecallRating:
    if feedback is RecallFeedbackType.WRONG:
        return RecallRating.HARD
    if feedback is RecallFeedbackType.PARTIAL:
        return _partial_recall_rating(elapsed_seconds)
    if feedback is RecallFeedbackType.CORRECT:
        return _correct_recall_rating(elapsed_seconds)
    return RecallRating.NONE


def _partial_recall_rating(elapsed_seconds: int | None) -> RecallRating:
    return (
        RecallRating.GOOD
        if elapsed_seconds is not None and elapsed_seconds <= 30
        else RecallRating.HARD
    )


def _correct_recall_rating(elapsed_seconds: int | None) -> RecallRating:
    if elapsed_seconds is None:
        return RecallRating.GOOD
    if elapsed_seconds <= 30:
        return RecallRating.EASY
    if elapsed_seconds <= 120:
        return RecallRating.GOOD
    return RecallRating.HARD


def elapsed_recall_seconds(
    recall_started_at: datetime | None,
    current_time: datetime,
) -> int | None:
    if recall_started_at is None:
        return None
    if recall_started_at.tzinfo is None:
        recall_started_at = recall_started_at.replace(tzinfo=UTC)
    return max(0, int((current_time - recall_started_at).total_seconds()))


def strip_assistant_confidence_values(reply: str) -> str:
    cleaned = CONFIDENCE_RE.sub("", reply)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([.!?]){2,}", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return "\n".join(line.strip() for line in cleaned.splitlines()).strip()
