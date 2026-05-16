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
    rf"(?:question|problem|exercise|aufgabe)\s*\d+[{_LETTER}]?\b"
    rf"|\d+\s*[.)]"
    rf")",
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
_PAGE_TURN_RE = re.compile(
    r"^\s*(?:please\s+turn\s+over|continued\s+on\s+next\s+page|bitte\s+wenden)\s*!?\s*$",
    re.IGNORECASE,
)
_EXAM_PROMPT_NOISE_RE = re.compile(r"[�©@]|(?:\?[^.!?\n]{0,24}[=+\-*/^])")


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
    questions = select_exam_questions(chunks, topic=topic)
    if not questions:
        return None
    chooser = rng or random.SystemRandom()
    return chooser.choice(questions)


def select_exam_questions(
    chunks: Sequence[ExamChunk],
    *,
    topic: str = "",
) -> list[ExamQuestion]:
    """Return all extracted past-exam questions, optionally focused by topic."""
    questions = list(_iter_exam_questions(chunks))
    if not topic:
        return questions
    topic_lower = topic.lower()
    focused = [question for question in questions if topic_lower in question.question.lower()]
    return focused or questions


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
    seen_questions: set[str] = set()
    chunk_list = list(chunks)
    for position, chunk in enumerate(chunk_list):
        role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
        if role != "past_exam":
            continue
        text = _contextual_exam_text(chunk_list, position)
        for question in _questions_from_text(text):
            normalized_question = _dedupe_key(question)
            if normalized_question in seen_questions:
                continue
            seen_questions.add(normalized_question)
            questions.append(
                ExamQuestion(
                    question=question,
                    source_ref=f"{chunk.source}#chunk={chunk.index}",
                    marks=_marks_from_text(question),
                )
            )
    return questions


def _contextual_exam_text(chunks: Sequence[ExamChunk], position: int) -> str:
    """Include neighboring same-source text so split PDF chunks keep problem stems."""
    chunk = chunks[position]
    parts: list[str] = []
    if position > 0 and chunks[position - 1].source == chunk.source:
        parts.append(chunks[position - 1].text)
    parts.append(chunk.text)
    if (
        position + 1 < len(chunks)
        and chunks[position + 1].source == chunk.source
        and _looks_truncated(chunk.text)
    ):
        continuation = _leading_continuation(chunks[position + 1].text)
        if continuation:
            parts.append(continuation)
    return "\n".join(parts)


def _looks_truncated(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    tail = lines[-1]
    return tail.endswith((",", ";", ":", "=", "->", "→", "↦", "{", "[", "("))


def _leading_continuation(text: str) -> str:
    """Return text before the next full problem starts."""
    lines = text.splitlines()
    continuation: list[str] = []
    for line in lines:
        if _PROBLEM_START_RE.match(line):
            break
        continuation.append(line)
    return "\n".join(continuation).strip()


def _questions_from_text(text: str) -> list[str]:
    questions: list[str] = []
    for section in _problem_sections(text):
        questions.extend(_questions_from_section(section))
    return questions


def _problem_sections(text: str) -> list[str]:
    lines = text.splitlines()
    sections: list[list[str]] = []
    current: list[str] = []
    saw_problem_start = False

    for line in lines:
        if _PROBLEM_START_RE.match(line):
            if current:
                sections.append(current)
            current = [line]
            saw_problem_start = True
            continue
        if not saw_problem_start:
            continue
        current.append(line)

    if current:
        sections.append(current)

    if not sections and text.strip():
        return [_clean_question_text(text)]
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
        question = _question_from_line(section)
        return [question] if question is not None else []

    stem = _clean_question_text("\n".join(lines[: subpart_starts[0]]))
    stem_is_prompt = _is_question_like(stem)
    questions: list[str] = []
    for position, start in enumerate(subpart_starts):
        end = subpart_starts[position + 1] if position + 1 < len(subpart_starts) else len(lines)
        subpart = _clean_question_text("\n".join(lines[start:end]))
        if not (_is_question_like(subpart) or stem_is_prompt):
            continue
        question = _join_stem_and_subpart(stem, subpart)
        if _is_answerable_exam_prompt(question) and not _has_extraction_noise(question):
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
    cleaned = _clean_question_text(question)
    if _has_extraction_noise(cleaned):
        return None
    return cleaned


def _is_question_like(text: str) -> bool:
    normalized = text.strip()
    if len(normalized) < 12:
        return False
    return bool("?" in normalized or _PROMPT_CUE_RE.search(normalized))


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


def _has_extraction_noise(text: str) -> bool:
    return _EXAM_PROMPT_NOISE_RE.search(text) is not None


def _clean_question_text(text: str) -> str:
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    compacted: list[str] = []
    for line in lines:
        if _PAGE_TURN_RE.match(line):
            continue
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


def _dedupe_key(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.casefold()).strip()


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
