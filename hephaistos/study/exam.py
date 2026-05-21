from __future__ import annotations

import random
import re
from collections.abc import Iterator, Sequence
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
    source: str
    index: int
    text: str


@dataclass(frozen=True, slots=True)
class ExamQuestion:
    question: str
    source_ref: str
    marks: int | None = None

    @property
    def time_limit_minutes(self) -> int:
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
    questions = _focused_exam_questions(_iter_exam_questions(chunks), topic)
    if not questions:
        return None
    chooser = rng or random.SystemRandom()
    return chooser.choice(questions)


def _focused_exam_questions(
    questions: Sequence[ExamQuestion],
    topic: str,
) -> list[ExamQuestion]:
    all_questions = list(questions)
    if not topic:
        return all_questions
    topic_lower = topic.lower()
    focused = [question for question in all_questions if topic_lower in question.question.lower()]
    return focused or all_questions


def supporting_source_refs(
    chunks: Sequence[ExamChunk],
    question: str,
    *,
    limit: int = 3,
) -> list[str]:
    question_terms = _content_terms(question)
    if not question_terms:
        return []

    scored = [
        scored_ref
        for chunk in chunks
        if (scored_ref := _supporting_ref_score(chunk, question_terms)) is not None
    ]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [source_ref for _score, source_ref in scored[:limit]]


def _supporting_ref_score(chunk: ExamChunk, question_terms: set[str]) -> tuple[int, str] | None:
    role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
    if role == "past_exam":
        return None
    overlap = len(question_terms & _content_terms(chunk.text))
    if overlap <= 0:
        return None
    return overlap, f"{chunk.source}#chunk={chunk.index}"


def _iter_exam_questions(chunks: Sequence[ExamChunk]) -> list[ExamQuestion]:
    chunk_list = list(chunks)
    questions = [
        question
        for position, chunk in enumerate(chunk_list)
        if _is_past_exam_chunk(chunk)
        for question in _chunk_exam_questions(chunk_list, position)
    ]
    return _dedupe_exam_questions(questions)


def _is_past_exam_chunk(chunk: ExamChunk) -> bool:
    role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
    return role == "past_exam"


def _chunk_exam_questions(chunks: Sequence[ExamChunk], position: int) -> Iterator[ExamQuestion]:
    chunk = chunks[position]
    text = _contextual_exam_text(chunks, position)
    for section in _problem_sections(text):
        for question in _questions_from_section(section):
            yield _exam_question(question, chunk)


def _exam_question(question: str, chunk: ExamChunk) -> ExamQuestion:
    marks_match = _MARK_RE.search(question)
    return ExamQuestion(
        question=question,
        source_ref=f"{chunk.source}#chunk={chunk.index}",
        marks=int(marks_match.group("marks")) if marks_match else None,
    )


def _dedupe_exam_questions(questions: Sequence[ExamQuestion]) -> list[ExamQuestion]:
    seen_questions: set[str] = set()
    unique_questions: list[ExamQuestion] = []
    for question in questions:
        normalized_question = _normalized_question_key(question.question)
        if normalized_question in seen_questions:
            continue
        seen_questions.add(normalized_question)
        unique_questions.append(question)
    return unique_questions


def _normalized_question_key(question: str) -> str:
    return _WHITESPACE_RE.sub(" ", question.casefold()).strip()


def _contextual_exam_text(chunks: Sequence[ExamChunk], position: int) -> str:
    chunk = chunks[position]
    parts: list[str] = []
    if _same_source_before(chunks, position):
        parts.append(chunks[position - 1].text)
    parts.append(chunk.text)
    if continuation := _next_chunk_continuation(chunks, position):
        parts.append(continuation)
    return "\n".join(parts)


def _same_source_before(chunks: Sequence[ExamChunk], position: int) -> bool:
    return position > 0 and chunks[position - 1].source == chunks[position].source


def _same_source_after(chunks: Sequence[ExamChunk], position: int) -> bool:
    return position + 1 < len(chunks) and chunks[position + 1].source == chunks[position].source


def _looks_truncated(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return bool(lines) and lines[-1].endswith((",", ";", ":", "=", "->", "→", "↦", "{", "[", "("))


def _next_chunk_continuation(chunks: Sequence[ExamChunk], position: int) -> str:
    if not (_same_source_after(chunks, position) and _looks_truncated(chunks[position].text)):
        return ""
    continuation_lines: list[str] = []
    for line in chunks[position + 1].text.splitlines():
        if _PROBLEM_START_RE.match(line):
            break
        continuation_lines.append(line)
    return "\n".join(continuation_lines).strip()


def _problem_sections(text: str) -> list[str]:
    sections = _raw_problem_sections(text.splitlines())
    if not sections and text.strip():
        return [_clean_question_text(text)]
    return [
        cleaned for section in sections if (cleaned := _clean_question_text("\n".join(section)))
    ]


def _raw_problem_sections(lines: Sequence[str]) -> list[list[str]]:
    sections: list[list[str]] = []
    current: list[str] = []
    collecting = False

    for line in lines:
        if _PROBLEM_START_RE.match(line):
            current = _start_problem_section(sections, current, line)
            collecting = True
        elif collecting:
            current.append(line)

    if current:
        sections.append(current)
    return sections


def _start_problem_section(
    sections: list[list[str]],
    current: list[str],
    line: str,
) -> list[str]:
    if current:
        sections.append(current)
    return [line]


def _questions_from_section(section: str) -> list[str]:
    lines = [line.rstrip() for line in section.splitlines()]
    subpart_starts = _subpart_start_indices(lines)
    if not subpart_starts:
        return _single_section_question(section)

    stem = _clean_question_text("\n".join(lines[: subpart_starts[0]]))
    stem_is_prompt = _is_question_like(stem)
    return [
        question
        for subpart in _iter_subparts(lines, subpart_starts)
        if (question := _question_from_subpart(stem, stem_is_prompt, subpart)) is not None
    ]


def _subpart_start_indices(lines: Sequence[str]) -> list[int]:
    return [index for index, line in enumerate(lines) if _SUBQUESTION_START_RE.match(line)]


def _single_section_question(section: str) -> list[str]:
    question = _question_from_line(section)
    return [question] if question is not None else []


def _iter_subparts(lines: Sequence[str], starts: Sequence[int]) -> Iterator[str]:
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        yield _clean_question_text("\n".join(lines[start:end]))


def _question_from_subpart(stem: str, stem_is_prompt: bool, subpart: str) -> str | None:
    if not (_is_question_like(subpart) or stem_is_prompt):
        return None
    question = subpart if not stem else f"{stem}\n{subpart}"
    return question if _is_valid_exam_question(question) else None


def _is_valid_exam_question(question: str) -> bool:
    return _is_answerable_exam_prompt(question) and _EXAM_PROMPT_NOISE_RE.search(question) is None


def _question_from_line(line: str) -> str | None:
    prefix = _QUESTION_PREFIX_RE.match(line)
    question = _strip_question_prefix(line, prefix)
    if not _is_question_like(question):
        return None
    return _clean_prompt_question(_question_with_prefix_marks(question, prefix))


def _strip_question_prefix(line: str, prefix: re.Match[str] | None) -> str:
    return line[prefix.end() :].strip() if prefix is not None else line.strip()


def _question_with_prefix_marks(question: str, prefix: re.Match[str] | None) -> str:
    if prefix is None or not prefix.group("marks") or _MARK_RE.search(question):
        return question
    return f"{question} {prefix.group('marks')}"


def _clean_prompt_question(question: str) -> str | None:
    cleaned = _clean_question_text(question)
    return None if _EXAM_PROMPT_NOISE_RE.search(cleaned) is not None else cleaned


def _is_question_like(text: str) -> bool:
    normalized = text.strip()
    if len(normalized) < 12:
        return False
    return bool("?" in normalized or _PROMPT_CUE_RE.search(normalized))


def _is_answerable_exam_prompt(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    return bool(lines) and _is_standalone_exam_prompt(lines)


def _is_standalone_exam_prompt(lines: Sequence[str]) -> bool:
    first_line = lines[0]
    if not _starts_with_subpart(first_line):
        return True
    return len(lines) == 1 and not _is_context_dependent_subpart(first_line)


def _starts_with_subpart(line: str) -> bool:
    return _SUBQUESTION_START_RE.match(line) is not None


def _is_context_dependent_subpart(line: str) -> bool:
    lowered = line.casefold()
    return bool(
        re.search(r"\b(?:f|g|h|it|this|the|above|given|diese[rs]?|obige[rs]?|dazu)\b", lowered)
        or re.search(r"\b(?:auf|on|in)\s+[A-Z]\b", line)
    )


def _clean_question_text(text: str) -> str:
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    compacted: list[str] = []
    for line in lines:
        _append_clean_question_line(compacted, line)
    return "\n".join(_strip_blank_edges(compacted))


def _append_clean_question_line(compacted: list[str], line: str) -> None:
    if _PAGE_TURN_RE.match(line):
        return
    if not line:
        if compacted and compacted[-1]:
            compacted.append("")
        return
    compacted.append(line)


def _strip_blank_edges(lines: list[str]) -> list[str]:
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return lines


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
