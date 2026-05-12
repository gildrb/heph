"""Local extraction of active-recall exam questions."""

from __future__ import annotations

import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from hephaistos.materials import infer_material_role_from_text

_LETTER = r"A-Za-zÀ-ÖØ-öø-ÿ"
_MARK_RE = re.compile(
    r"(?:\[\s*)?(?P<marks>\d{1,2})\s*(?:marks?|pts?|points?|punkte?)(?:\s*\])?",
    re.IGNORECASE,
)
_QUESTION_PREFIX_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:Question\s*\d*\s*)?(?P<marks>\[[^\]]*marks?[^\]]*\])?\s*[:.)-]?\s*",
    re.IGNORECASE,
)
_PROBLEM_START_RE = re.compile(
    rf"^\s*(?:"
    rf"(?:question|problem|exercise|aufgabe)\s*\d+[{_LETTER}]?"
    rf"|\d+\s*[.)]"
    rf")\b",
    re.IGNORECASE,
)
_SUBQUESTION_START_RE = re.compile(
    rf"^\s*(?P<label>\(?\s*[{_LETTER}]\s*\)|[{_LETTER}]\s*[.)])\s+",
    re.IGNORECASE,
)
_PROMPT_CUE_RE = re.compile(
    r"\b(?:"
    r"analyze|answer|begründen|berechnen|bestimmen|calculate|compute|decide|define|"
    r"derive|describe|discuss|entscheiden|evaluate|explain|find|prove|show|sketch|"
    r"state|untersuchen|why"
    r")\b",
    re.IGNORECASE,
)
_WHITESPACE_RE = re.compile(r"[ \t]+")


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
        role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
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
        role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
        if role != "past_exam":
            continue
        questions.extend(
            ExamQuestion(
                question=question,
                source_ref=f"{chunk.source}#chunk={chunk.index}",
                marks=_marks_from_text(question),
            )
            for question in _questions_from_text(chunk.text)
        )
    return questions


def _questions_from_text(text: str) -> list[str]:
    questions: list[str] = []
    for section in _problem_sections(text):
        questions.extend(_questions_from_section(section))
    return questions


def _problem_sections(text: str) -> list[str]:
    lines = text.splitlines()
    sections: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if _PROBLEM_START_RE.match(line) and current:
            sections.append(current)
            current = [line]
            continue
        current.append(line)

    if current:
        sections.append(current)

    return [
        _clean_question_text("\n".join(section))
        for section in sections
        if "\n".join(section).strip()
    ]


def _questions_from_section(section: str) -> list[str]:
    lines = [line.rstrip() for line in section.splitlines()]
    subpart_starts = [
        index for index, line in enumerate(lines) if _SUBQUESTION_START_RE.match(line)
    ]
    if not subpart_starts:
        return [question for line in lines if (question := _question_from_line(line)) is not None]

    stem = _clean_question_text("\n".join(lines[: subpart_starts[0]]))
    questions: list[str] = []
    for position, start in enumerate(subpart_starts):
        end = subpart_starts[position + 1] if position + 1 < len(subpart_starts) else len(lines)
        subpart = _clean_question_text("\n".join(lines[start:end]))
        if not _is_question_like(subpart):
            continue
        question = _join_stem_and_subpart(stem, subpart)
        if _is_answerable_exam_prompt(question):
            questions.append(question)
    return questions


def _join_stem_and_subpart(stem: str, subpart: str) -> str:
    if not stem:
        return subpart
    return f"{stem}\n{subpart}"


def _question_from_line(line: str) -> str | None:
    prefix = _QUESTION_PREFIX_RE.match(line)
    question = line[prefix.end() :].strip() if prefix is not None else line.strip()
    if len(question) < 12:
        return None
    if not _is_question_like(question):
        return None
    if prefix is not None and prefix.group("marks") and not _MARK_RE.search(question):
        question = f"{question} {prefix.group('marks')}"
    return _clean_question_text(question)


def _is_question_like(text: str) -> bool:
    normalized = text.strip()
    if len(normalized) < 12:
        return False
    return bool(
        "?" in normalized or _MARK_RE.search(normalized) or _PROMPT_CUE_RE.search(normalized)
    )


def _is_answerable_exam_prompt(text: str) -> bool:
    """Reject orphaned subparts that need a missing stem to be answerable."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    starts_with_subpart = _SUBQUESTION_START_RE.match(lines[0]) is not None
    if starts_with_subpart and len(lines) == 1:
        return not _references_external_context(lines[0])
    return not starts_with_subpart


def _references_external_context(text: str) -> bool:
    lowered = text.casefold()
    return bool(
        re.search(r"\b(?:f|g|h|it|this|the|above|given|diese[rs]?|obige[rs]?|dazu)\b", lowered)
        or re.search(r"\b(?:auf|on|in)\s+[A-Z]\b", text)
    )


def _clean_question_text(text: str) -> str:
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    compacted: list[str] = []
    for line in lines:
        if not line:
            if compacted and compacted[-1]:
                compacted.append("")
            continue
        compacted.append(line)
    while compacted and not compacted[-1]:
        compacted.pop()
    while compacted and not compacted[0]:
        compacted.pop(0)
    return "\n".join(compacted)


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
