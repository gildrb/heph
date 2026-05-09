"""Local extraction of active-recall exam questions."""

from __future__ import annotations

import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from hephaistos.materials import infer_material_role

_MARK_RE = re.compile(
    r"(?:\[\s*)?(?P<marks>\d{1,2})\s*(?:marks?|pts?|points?)(?:\s*\])?",
    re.IGNORECASE,
)
_QUESTION_PREFIX_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:Question\s*\d*\s*)?(?P<marks>\[[^\]]*marks?[^\]]*\])?\s*[:.)-]?\s*",
    re.IGNORECASE,
)


class ExamChunk(Protocol):
    """Minimal chunk shape needed to extract exam prompts."""

    source: str
    index: int
    text: str


@dataclass(frozen=True, slots=True)
class ExamQuestion:
    """A question found in a past-exam source."""

    question: str
    source_ref: str
    marks: int | None = None

    @property
    def time_limit_minutes(self) -> int:
        """Derive light exam pressure from mark value."""
        if self.marks is None:
            return 5
        if self.marks <= 4:
            return 3
        if self.marks <= 10:
            return 8
        return 12


def select_exam_question(
    chunks: Sequence[ExamChunk],
    *,
    topic: str = "",
    rng: random.Random | None = None,
) -> ExamQuestion | None:
    """Select a random question from indexed past-exam chunks."""
    questions = list(_iter_exam_questions(chunks))
    if topic:
        topic_lower = topic.lower()
        focused = [question for question in questions if topic_lower in question.question.lower()]
        if focused:
            questions = focused
    if not questions:
        return None
    chooser = rng or random.SystemRandom()
    return chooser.choice(questions)


def supporting_source_refs(
    chunks: Sequence[ExamChunk],
    question: str,
    *,
    limit: int = 3,
) -> list[str]:
    """Find supporting non-exam chunks for assessing a selected question."""
    question_terms = _content_terms(question)
    if not question_terms:
        return []

    scored: list[tuple[int, str]] = []
    for chunk in chunks:
        role, _confidence, _reason = infer_material_role(chunk.source)
        if role == "past_exam":
            continue
        overlap = len(question_terms & _content_terms(chunk.text))
        if overlap <= 0:
            continue
        scored.append((overlap, f"{chunk.source}#chunk={chunk.index}"))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [source_ref for _score, source_ref in scored[:limit]]


def _iter_exam_questions(chunks: Sequence[ExamChunk]) -> list[ExamQuestion]:
    questions: list[ExamQuestion] = []
    for chunk in chunks:
        role, _confidence, _reason = infer_material_role(chunk.source)
        if role != "past_exam":
            continue
        for line in chunk.text.splitlines():
            question = _question_from_line(line)
            if question is None:
                continue
            questions.append(
                ExamQuestion(
                    question=question,
                    source_ref=f"{chunk.source}#chunk={chunk.index}",
                    marks=_marks_from_text(question),
                )
            )
    return questions


def _question_from_line(line: str) -> str | None:
    prefix = _QUESTION_PREFIX_RE.match(line)
    question = line[prefix.end() :].strip() if prefix is not None else line.strip()
    if len(question) < 12:
        return None
    if not (
        "?" in question or _MARK_RE.search(question) or question.lower().startswith("explain ")
    ):
        return None
    if prefix is not None and prefix.group("marks") and not _MARK_RE.search(question):
        question = f"{question} {prefix.group('marks')}"
    return question


def _marks_from_text(text: str) -> int | None:
    match = _MARK_RE.search(text)
    if match is None:
        return None
    return int(match.group("marks"))


def _content_terms(text: str) -> set[str]:
    stopwords = {
        "and",
        "answer",
        "define",
        "explain",
        "for",
        "from",
        "identify",
        "marks",
        "question",
        "state",
        "the",
        "through",
        "using",
        "with",
    }
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_+-]{2,}", text)
        if token.lower() not in stopwords
    }
