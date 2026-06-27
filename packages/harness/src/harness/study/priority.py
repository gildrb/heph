"""Deterministic priority analysis over indexed materials."""

from __future__ import annotations

import re
import time
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field

from harness.materials import material_display_name
from harness.study.priority_analysis import PriorityAnalysis, priority_tier
from harness.study.priority_progress import _emit_progress, _format_elapsed_since
from harness.study.priority_rendering import (
    _truncate,
    build_priority_cheat_sheet,
    render_priority_latex,
    verify_priority_output,
)
from harness.study.priority_report import (
    ExternalLatexCompiler,
    duckduckgo_search,
    generate_priority_report,
    subprocess,
)
from harness.study.priority_topics import valid_priority_topic
from harness.study.priority_types import (
    PriorityChunk,
    PriorityExamQuestion,
    PriorityPdfCompiler,
    PriorityPdfError,
    PriorityProgressReporter,
    PriorityReport,
    PriorityTopic,
    PriorityTopicEvidence,
    PriorityWebSearcher,
    PriorityWebSearchResult,
)
from harness.study.priority_web import with_web_prerequisites as _with_web_prerequisites

__all__ = [
    "ExternalLatexCompiler",
    "PriorityAnalysis",
    "PriorityPdfCompiler",
    "PriorityPdfError",
    "PriorityReport",
    "PriorityWebSearchResult",
    "analyze_priority",
    "build_priority_cheat_sheet",
    "duckduckgo_search",
    "generate_priority_report",
    "priority_tier",
    "render_priority_latex",
    "subprocess",
    "verify_priority_output",
]

_LETTER_RE = r"[^\W\d_]"
_WORD_BODY_RE = r"[\w+-]"
_TOKEN_RE = re.compile(rf"{_LETTER_RE}{_WORD_BODY_RE}{{2,}}")
_SENTENCE_RE = re.compile(r"[^.!?\n]+")
_TOPIC_SPAN_RE = re.compile(
    rf"\b{_LETTER_RE}{_WORD_BODY_RE}*(?:\s+{_LETTER_RE}{_WORD_BODY_RE}*){{1,5}}\b"
)
_QUESTION_START_RE = re.compile(
    rf"(?:^|\n|(?<=[.!?])\s+)\s*"
    rf"(?:\d+{_LETTER_RE}?\s*[.)]|[^\s:][^:\n]{{0,48}}(?:\[[^\]\n]{{1,48}}\])?\s*:)\s+"
)
_STRUCTURED_PROMPT_PREFIX_RE = re.compile(
    rf"^\s*(?:\d+{_LETTER_RE}?\s*[.)]|[^\s:][^:\n]{{0,48}}"
    rf"(?:\[[^\]\n]{{1,48}}\])?\s*:)\s*"
)
_SUBQUESTION_START_RE = re.compile(
    rf"(?:(?<=\n)\s*(?:\({_LETTER_RE}\)|{_LETTER_RE}\))|"
    rf"(?<!{_LETTER_RE})(?:\({_LETTER_RE}\))\s+)",
    re.IGNORECASE,
)
_TOPIC_SPLIT_RE = re.compile(r"[,;]|\band\b", re.IGNORECASE)
_HEADING_PREFIX_RE = re.compile(r"^(?:#+\s*|\d+(?:\.\d+)*[.)]?\s*|[-*]\s*)")
_WHITESPACE_RE = re.compile(r"\s+")
_WORD_SPLIT_RE = re.compile(rf"{_LETTER_RE}{_WORD_BODY_RE}*")
_CONTACT_OR_URL_RE = re.compile(r"(?:https?://|www\.|\S+@\S+)", re.IGNORECASE)
_BRACKETED_WEIGHT_RE = re.compile(r"[\[(]\s*(\d{1,3})(?:[^\]\)]{0,48})[\])]")

_SYMBOLIC_TOPIC_TOKEN_RE = re.compile(
    rf"^(?:{_LETTER_RE}{{1,2}}\d*|\d+|{_LETTER_RE}-{_LETTER_RE})$"
)


@dataclass(slots=True)
class _PriorityScanState:
    exam_counts: Counter[str] = field(default_factory=Counter)
    exam_marks: Counter[str] = field(default_factory=Counter)
    material_counts: Counter[str] = field(default_factory=Counter)
    prerequisite_hints: dict[str, Counter[str]] = field(default_factory=dict)
    sources_by_topic: dict[str, set[str]] = field(default_factory=dict)
    exam_sources_by_topic: dict[str, set[str]] = field(default_factory=dict)
    material_sources_by_topic: dict[str, set[str]] = field(default_factory=dict)
    evidence_by_topic: dict[str, list[PriorityTopicEvidence]] = field(default_factory=dict)
    seen_evidence_by_topic: dict[str, set[tuple[str, str]]] = field(default_factory=dict)
    past_exam_sources: set[str] = field(default_factory=set)
    material_sources: set[str] = field(default_factory=set)
    exam_questions: list[PriorityExamQuestion] = field(default_factory=list)

    def add_evidence(self, term: str, evidence: PriorityTopicEvidence) -> None:
        topic_evidence = self.evidence_by_topic.setdefault(term, [])
        seen = self.seen_evidence_by_topic.setdefault(term, set())
        evidence_key = (evidence.source, evidence.excerpt)
        if len(topic_evidence) < 4 and evidence_key not in seen:
            topic_evidence.append(evidence)
            seen.add(evidence_key)

    def record_exam_question(self, question: PriorityExamQuestion) -> None:
        self.exam_questions.append(question)
        for term in set(question.topics):
            self.exam_counts[term] += 1
            self.exam_marks[term] += question.marks
            self.sources_by_topic.setdefault(term, set()).add(question.source)
            self.exam_sources_by_topic.setdefault(term, set()).add(question.source)
            self.add_evidence(
                term,
                PriorityTopicEvidence(
                    source=question.source,
                    heading="Past exam question",
                    excerpt=question.prompt,
                    marks=question.marks,
                ),
            )

    def record_material_terms(self, chunk: PriorityChunk, terms: set[str]) -> None:
        self.material_sources.add(chunk.source)
        for term in terms:
            self.material_counts[term] += 1
            self.sources_by_topic.setdefault(term, set()).add(chunk.source)
            self.material_sources_by_topic.setdefault(term, set()).add(chunk.source)
            self.add_evidence(term, _topic_evidence(chunk, term, marks=0))

    def add_prerequisites(
        self,
        terms: set[str],
        explicit_prerequisites: list[str],
        dependency_prerequisites: dict[str, Counter[str]],
    ) -> None:
        for term in terms:
            if explicit_prerequisites:
                self.prerequisite_hints.setdefault(term, Counter()).update(explicit_prerequisites)
            if term in dependency_prerequisites:
                self.prerequisite_hints.setdefault(term, Counter()).update(
                    dependency_prerequisites[term]
                )


@dataclass(frozen=True, slots=True)
class _PriorityScanContext:
    chunk_list: tuple[PriorityChunk, ...]
    source_order: tuple[str, ...]
    source_positions: dict[str, int]
    source_chunk_counts: Counter[str]
    source_chunk_positions: Counter[str]
    seen_sources: set[str]
    total_chunks: int

    @property
    def total_sources(self) -> int:
        return len(self.source_order)


def analyze_priority(
    chunks: Iterable[PriorityChunk],
    *,
    limit: int = 8,
    web_searcher: PriorityWebSearcher | None = None,
    progress: PriorityProgressReporter | None = None,
) -> PriorityAnalysis:
    scan_started_at = time.perf_counter()
    scan = _priority_scan_context(chunks)
    if scan.total_sources:
        _emit_progress(
            progress,
            f"Ran priority.scan --sources {scan.total_sources} --chunks {scan.total_chunks}.",
        )
    state = _PriorityScanState()
    for global_index, chunk in enumerate(scan.chunk_list, start=1):
        _scan_priority_chunk(state, scan, chunk, global_index=global_index, progress=progress)

    _emit_progress(progress, "Scoring topic recurrence from exams and support files...")
    topics = _ranked_priority_topics(state)
    topics = _with_web_prerequisites(topics[:limit], web_searcher)
    _emit_progress(
        progress,
        f"Ranked {len(topics)} priority topic(s) in {_format_elapsed_since(scan_started_at)}.",
    )
    return PriorityAnalysis(
        topics=tuple(topics),
        past_exam_sources=tuple(sorted(state.past_exam_sources)),
        material_sources=tuple(sorted(state.material_sources)),
        chunks=scan.chunk_list,
        exam_questions=tuple(state.exam_questions),
    )


def _priority_scan_context(chunks: Iterable[PriorityChunk]) -> _PriorityScanContext:
    chunk_list = tuple(chunks)
    source_order = tuple(dict.fromkeys(chunk.source for chunk in chunk_list))
    return _PriorityScanContext(
        chunk_list=chunk_list,
        source_order=source_order,
        source_positions={source: index for index, source in enumerate(source_order, start=1)},
        source_chunk_counts=Counter(chunk.source for chunk in chunk_list),
        source_chunk_positions=Counter(),
        seen_sources=set(),
        total_chunks=len(chunk_list),
    )


def _scan_priority_chunk(
    state: _PriorityScanState,
    scan: _PriorityScanContext,
    chunk: PriorityChunk,
    *,
    global_index: int,
    progress: PriorityProgressReporter | None,
) -> None:
    chunk_started_at = time.perf_counter()
    scan.source_chunk_positions[chunk.source] += 1
    _emit_source_progress(scan, chunk, progress)
    chunk_label = _chunk_progress_label(
        chunk,
        global_index=global_index,
        total_chunks=scan.total_chunks,
        source_index=scan.source_positions.get(chunk.source, 0),
        total_sources=scan.total_sources,
        source_chunk_index=scan.source_chunk_positions[chunk.source],
        source_chunk_count=scan.source_chunk_counts[chunk.source],
    )
    if _chunk_is_exam_material(chunk):
        _record_exam_chunk(
            state,
            chunk,
            chunk_label,
            chunk_started_at,
            progress,
            require_structure=_chunk_has_exam_structure(chunk.text),
        )
        return
    _record_material_chunk(state, chunk, chunk_label, chunk_started_at, progress)


def _emit_source_progress(
    scan: _PriorityScanContext,
    chunk: PriorityChunk,
    progress: PriorityProgressReporter | None,
) -> None:
    if chunk.source in scan.seen_sources:
        return
    scan.seen_sources.add(chunk.source)
    _emit_progress(
        progress,
        f"Read source {len(scan.seen_sources)}/{scan.total_sources}: "
        f"@{material_display_name(chunk.source)} "
        f"({scan.source_chunk_counts[chunk.source]} chunk(s)).",
    )


def _record_exam_chunk(
    state: _PriorityScanState,
    chunk: PriorityChunk,
    chunk_label: str,
    chunk_started_at: float,
    progress: PriorityProgressReporter | None,
    *,
    require_structure: bool,
) -> None:
    state.past_exam_sources.add(chunk.source)
    structured_sections = tuple(_exam_sections(chunk.text))
    sections = structured_sections if require_structure and structured_sections else (chunk.text,)
    questions = tuple(_exam_questions(chunk.source, sections))
    for question in questions:
        state.record_exam_question(question)
    topic_signal_count = len({term for question in questions for term in question.topics})
    _emit_progress(
        progress,
        f"Read {chunk_label}: structured question material, {len(questions)} question(s), "
        f"{topic_signal_count} topic signal(s) in {_format_elapsed_since(chunk_started_at)}.",
    )


def _chunk_has_exam_structure(text: str) -> bool:
    return _mark_weight(text) > 0 or any(
        _section_looks_like_exam_question(section) for section in _exam_sections(text)
    )


def _section_looks_like_exam_question(section: str) -> bool:
    prefix_match = _STRUCTURED_PROMPT_PREFIX_RE.match(section)
    if _mark_weight(section) > 0:
        return True
    if prefix_match is None:
        return False
    prefix = prefix_match.group(0)
    return any(char.isdecimal() for char in prefix) or _section_body_starts_like_prompt(
        section[prefix_match.end() :]
    )


def _section_body_starts_like_prompt(text: str) -> bool:
    first_token_match = _WORD_SPLIT_RE.search(text)
    return first_token_match is not None and first_token_match.group(0)[:1].isupper()


def _chunk_is_exam_material(chunk: PriorityChunk) -> bool:
    return _chunk_has_exam_structure(chunk.text)


def _record_material_chunk(
    state: _PriorityScanState,
    chunk: PriorityChunk,
    chunk_label: str,
    chunk_started_at: float,
    progress: PriorityProgressReporter | None,
) -> None:
    terms = set(_topic_terms(chunk.heading, chunk.text))
    state.material_sources.add(chunk.source)
    if terms:
        state.record_material_terms(chunk, terms)
        state.add_prerequisites(
            terms,
            _explicit_prerequisites(chunk.text),
            _dependency_prerequisites(chunk.text, terms),
        )
    _emit_progress(
        progress,
        f"Read {chunk_label}: indexed material, {len(terms)} topic signal(s) in "
        f"{_format_elapsed_since(chunk_started_at)}.",
    )


def _ranked_priority_topics(state: _PriorityScanState) -> list[PriorityTopic]:
    topics = [
        topic
        for term in sorted(set(state.exam_counts) | set(state.material_counts))
        if (topic := _priority_topic(term, state)) is not None
    ]
    topics.sort(key=lambda topic: (-topic.score, -topic.exam_marks, -topic.exam_hits, topic.topic))
    return [topic for topic in topics if not _covered_by_preferred_topic(topic, topics)]


def _priority_topic(term: str, state: _PriorityScanState) -> PriorityTopic | None:
    exam_hits = state.exam_counts[term]
    marks = state.exam_marks[term]
    material_hits = state.material_counts[term]
    exam_source_frequency = len(state.exam_sources_by_topic.get(term, set()))
    supporting_material_coverage = len(state.material_sources_by_topic.get(term, set()))
    score = _priority_score(
        exam_hits=exam_hits,
        marks=marks,
        material_hits=material_hits,
        exam_source_frequency=exam_source_frequency,
        has_exam_corpus=bool(state.past_exam_sources),
    )
    if score <= 0:
        return None
    return PriorityTopic(
        topic=term,
        score=score,
        exam_hits=exam_hits,
        exam_marks=marks,
        material_hits=material_hits,
        sources=tuple(sorted(state.sources_by_topic.get(term, set()))),
        exam_source_frequency=exam_source_frequency,
        supporting_material_coverage=supporting_material_coverage,
        confidence=_topic_confidence(
            exam_hits=exam_hits,
            marks=marks,
            material_hits=material_hits,
            source_count=len(state.sources_by_topic.get(term, set())),
        ),
        prerequisites=_prerequisites_for(
            term,
            state.prerequisite_hints,
            state.exam_counts,
        ),
        evidence=tuple(state.evidence_by_topic.get(term, ())),
    )


def _priority_score(
    *,
    exam_hits: int,
    marks: int,
    material_hits: int,
    exam_source_frequency: int,
    has_exam_corpus: bool,
) -> float:
    if exam_hits:
        material_signal = min(material_hits, 6) * 0.6
    elif has_exam_corpus:
        material_signal = min(material_hits, 4) * 0.25
    else:
        material_signal = float(material_hits)
    return exam_hits * 10.0 + marks + exam_source_frequency * 3.0 + material_signal


def _chunk_progress_label(
    chunk: PriorityChunk,
    *,
    global_index: int,
    total_chunks: int,
    source_index: int,
    total_sources: int,
    source_chunk_index: int,
    source_chunk_count: int,
) -> str:
    label = (
        f"@{material_display_name(chunk.source)} chunk {source_chunk_index}/{source_chunk_count} "
        f"(global {global_index}/{total_chunks}, source {source_index}/{total_sources}, "
        f"index {chunk.index}, chars {chunk.char_start}-{chunk.char_end})"
    )
    if chunk.heading:
        label += f' heading "{_truncate(chunk.heading, 56)}"'
    return label


def _topic_terms(heading: str, text: str, *, keep_sparse_labels: bool = False) -> list[str]:
    raw = f"{heading}\n{text}"
    seen: set[str] = set()
    terms: list[str] = []
    candidates = [
        *_heading_candidates(heading),
        *_candidate_topic_phrases(raw, keep_sparse_labels=keep_sparse_labels),
    ]
    for candidate in candidates:
        canonical = " ".join(candidate.casefold().split())
        if valid_priority_topic(canonical, _SYMBOLIC_TOPIC_TOKEN_RE) and canonical not in seen:
            terms.append(canonical)
            seen.add(canonical)
    return terms


def _topic_confidence(
    *,
    exam_hits: int,
    marks: int,
    material_hits: int,
    source_count: int,
) -> float:
    signal = exam_hits * 0.32 + min(marks, 20) * 0.02 + material_hits * 0.08 + source_count * 0.08
    return min(1.0, max(0.2, signal))


def _candidate_topic_phrases(raw: str, *, keep_sparse_labels: bool = False) -> Iterator[str]:
    topic_text = _topic_candidate_text(raw, keep_sparse_labels=keep_sparse_labels)
    yield from _heading_candidates(topic_text)
    for phrase_match in _TOPIC_SPAN_RE.finditer(topic_text):
        phrase = phrase_match.group(0)
        parts = _split_topic_parts(phrase)
        if parts:
            for part in parts:
                yield from _topic_part_candidates(part)
            continue
        yield from _topic_part_candidates(phrase)


def _topic_part_candidates(phrase: str) -> Iterator[str]:
    useful = _useful_topic_words(phrase)
    if len(useful) == 1 and len(useful[0]) >= 5:
        yield useful[0]
        return
    yield from _content_phrase_candidates(phrase, useful)


def _heading_candidates(raw: str) -> Iterator[str]:
    for cleaned in _clean_heading_lines(raw):
        parts = _split_topic_parts(cleaned)
        if parts:
            for part in parts:
                yield from _topic_part_candidates(part)
            continue
        yield from _heading_word_candidates(cleaned)


def _clean_heading_lines(raw: str) -> Iterator[str]:
    for line in raw.splitlines():
        cleaned = _HEADING_PREFIX_RE.sub("", line.strip())
        if cleaned and len(cleaned) <= 90 and not _is_boilerplate_line(cleaned):
            yield cleaned


def _split_topic_parts(text: str) -> list[str]:
    return [
        part.strip()
        for part in _TOPIC_SPLIT_RE.split(text)
        if part.strip() and part.strip() != text
    ]


def _heading_word_candidates(cleaned: str) -> Iterator[str]:
    useful = _useful_topic_words(cleaned)
    if 2 <= len(useful) <= 6:
        yield " ".join(useful)
    elif len(useful) == 1 and len(useful[0]) >= 5:
        yield useful[0]


def _content_phrase_candidates(phrase: str, words: list[str]) -> Iterator[str]:
    if len(words) < 2:
        return
    if _should_emit_leading_content_word(phrase, words):
        yield words[0]
    for size in (2, 3):
        for start in range(len(words) - size + 1):
            yield " ".join(words[start : start + size])


def _should_emit_leading_content_word(phrase: str, words: list[str]) -> bool:
    first_token_match = _WORD_SPLIT_RE.search(phrase)
    return (
        first_token_match is not None
        and first_token_match.group(0)[:1].isupper()
        and first_token_match.group(0).lower() == words[0]
        and len(words[0]) >= 5
        and not _SYMBOLIC_TOPIC_TOKEN_RE.fullmatch(words[1])
    )


def _useful_topic_words(text: str) -> list[str]:
    return [
        word.lower()
        for word in _WORD_SPLIT_RE.findall(text)
        if len(word) >= 4 and not word.isdigit()
    ]


def _topic_candidate_text(raw: str, *, keep_sparse_labels: bool = False) -> str:
    return "\n".join(
        unit
        for line in raw.splitlines()
        for unit in _topic_candidate_line_units(line, keep_sparse_labels=keep_sparse_labels)
    )


def _topic_candidate_line_units(line: str, *, keep_sparse_labels: bool = False) -> Iterator[str]:
    if not line.strip():
        return
    for unit in re.split(r"(?<=[.!?])\s+", line):
        cleaned = unit.strip()
        if cleaned and (keep_sparse_labels or not _is_boilerplate_line(cleaned)):
            yield cleaned


def _is_boilerplate_line(line: str) -> bool:
    cleaned = _HEADING_PREFIX_RE.sub("", line.strip())
    if not cleaned:
        return True
    return bool(_CONTACT_OR_URL_RE.search(cleaned) or _looks_like_sparse_label_line(cleaned))


def _looks_like_sparse_label_line(text: str) -> bool:
    if _TOKEN_RE.search(text) is None:
        return True
    if not text.endswith("."):
        return False
    tokens = re.findall(rf"{_LETTER_RE}(?:{_WORD_BODY_RE}|')*", text[:-1])
    if not 1 <= len(tokens) <= 5:
        return False
    return all(token[:1].isupper() for token in tokens) or (
        len(tokens) <= 3 and tokens[0][:1].isupper()
    )


def _covered_by_preferred_topic(topic: PriorityTopic, topics: list[PriorityTopic]) -> bool:
    return any(
        _candidate_covers_topic(candidate, topic)
        for candidate in topics
        if candidate.topic != topic.topic
    )


def _candidate_covers_topic(candidate: PriorityTopic, topic: PriorityTopic) -> bool:
    return _topic_signals_match(candidate, topic) and _topic_is_preferred(
        candidate.topic,
        topic.topic,
    )


def _topic_signals_match(candidate: PriorityTopic, topic: PriorityTopic) -> bool:
    return (
        topic.exam_hits,
        topic.exam_marks,
        topic.material_hits,
        topic.sources,
    ) == (
        candidate.exam_hits,
        candidate.exam_marks,
        candidate.material_hits,
        candidate.sources,
    )


def _topic_is_preferred(candidate: str, current: str) -> bool:
    candidate_words = set(candidate.split())
    current_words = set(current.split())
    if candidate_words.isdisjoint(current_words):
        return False
    if _multiword_subset(candidate_words, current_words):
        return True
    if _multiword_subset(current_words, candidate_words):
        return False
    return _single_word_subset(current_words, candidate_words)


def _multiword_subset(left: set[str], right: set[str]) -> bool:
    return len(left) >= 2 and left < right


def _single_word_subset(left: set[str], right: set[str]) -> bool:
    return len(left) == 1 and left < right


def _explicit_prerequisites(text: str) -> list[str]:
    prerequisites: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"\bprerequisites?\s*:\s*([^.\n]+)", text, flags=re.IGNORECASE):
        for prerequisite in _prerequisite_tokens(match.group(1)):
            if prerequisite in seen:
                continue
            seen.add(prerequisite)
            prerequisites.append(prerequisite)
    return prerequisites


def _dependency_prerequisites(text: str, terms: set[str]) -> dict[str, Counter[str]]:
    prerequisites: dict[str, Counter[str]] = {}
    for term, hints in _iter_dependency_prerequisite_hints(text, terms):
        if hints:
            prerequisites.setdefault(term, Counter()).update(hints)
    return prerequisites


def _iter_dependency_prerequisite_hints(
    text: str,
    terms: set[str],
) -> Iterator[tuple[str, list[str]]]:
    for sentence_match in _SENTENCE_RE.finditer(text):
        yield from _dependency_prerequisite_hints_for_sentence(sentence_match.group(0), terms)


def _dependency_prerequisite_hints_for_sentence(
    sentence: str,
    terms: set[str],
) -> Iterator[tuple[str, list[str]]]:
    dependency = _dependency_sentence_parts(sentence)
    if dependency is None:
        return
    before, after = dependency
    normalized_before = before.casefold()
    for term in (term for term in terms if term in normalized_before):
        yield term, _prerequisite_tokens(after)


def _dependency_sentence_parts(sentence: str) -> tuple[str, str] | None:
    lower = sentence.casefold()
    for connector in (" depends on ", " requires "):
        if connector in lower:
            index = lower.index(connector)
            return sentence[:index], sentence[index + len(connector) :]
    return None


def _prerequisite_tokens(text: str) -> list[str]:
    return [
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if len(token) >= 4 and not token.isdigit()
    ]


def _mark_weight(text: str) -> int:
    return max((int(match.group(1)) for match in _BRACKETED_WEIGHT_RE.finditer(text)), default=0)


def _exam_sections(text: str) -> Iterator[str]:
    matches = list(_QUESTION_START_RE.finditer(text))
    if not matches:
        return
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.start() : end].strip()
        if section:
            yield from _split_exam_subquestions(section)


def _split_exam_subquestions(section: str) -> Iterator[str]:
    matches = list(_SUBQUESTION_START_RE.finditer(section))
    if not matches:
        yield section
        return
    for index, _match in enumerate(matches):
        if subquestion := _exam_subquestion(section, matches, index):
            yield subquestion


def _exam_question_prefix(section: str, matches: Sequence[re.Match[str]]) -> str:
    return section[: matches[0].start()].strip()


def _exam_subquestion(
    section: str,
    matches: Sequence[re.Match[str]],
    index: int,
) -> str:
    match = matches[index]
    end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
    subquestion = section[match.start() : end].strip()
    if not subquestion:
        return ""
    return subquestion


def _exam_questions(source: str, sections: Iterable[str]) -> Iterator[PriorityExamQuestion]:
    for section in sections:
        prompt_text = _strip_structured_prompt_prefix(section)
        topic_text = _strip_leading_prompt_token(prompt_text)
        prompt = _topic_excerpt(prompt_text, "", max_chars=360)
        if not prompt:
            continue
        yield PriorityExamQuestion(
            source=source,
            prompt=prompt,
            marks=_mark_weight(section),
            topics=tuple(_topic_terms("", topic_text, keep_sparse_labels=True)[:5]),
        )


def _strip_structured_prompt_prefix(text: str) -> str:
    return _STRUCTURED_PROMPT_PREFIX_RE.sub("", text.strip(), count=1)


def _strip_leading_prompt_token(text: str) -> str:
    tokens = list(_WORD_SPLIT_RE.finditer(text))
    if len(tokens) < 2:
        return text
    first = tokens[0]
    if first.group(0)[:1].isupper():
        return text[first.end() :].lstrip()
    return text


def _topic_evidence(chunk: PriorityChunk, term: str, marks: int) -> PriorityTopicEvidence:
    return PriorityTopicEvidence(
        source=chunk.source,
        heading=chunk.heading,
        excerpt=_topic_excerpt(chunk.text, term, heading=chunk.heading),
        marks=marks,
    )


def _topic_excerpt(text: str, term: str, *, heading: str = "", max_chars: int = 260) -> str:
    normalized = _clean_evidence_excerpt(text, heading=heading)
    if len(normalized) <= max_chars:
        return normalized
    idx = normalized.lower().find(term.lower())
    if idx < 0:
        return f"{normalized[: max_chars - 1]}…"
    start = max(0, idx - max_chars // 3)
    end = min(len(normalized), start + max_chars)
    start = max(0, end - max_chars)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(normalized) else ""
    return f"{prefix}{normalized[start:end]}{suffix}"


def _clean_evidence_excerpt(text: str, *, heading: str = "") -> str:
    cleaned_lines = []
    previous_line = ""
    for raw_line in text.splitlines():
        line = _clean_evidence_line(raw_line)
        if not line or line == previous_line:
            continue
        line = _dedupe_evidence_line_prefix(line, previous_line)
        cleaned_lines.append(line)
        previous_line = line
    cleaned = _WHITESPACE_RE.sub(" ", " ".join(cleaned_lines)).strip()
    return _strip_evidence_heading_prefix(cleaned, heading)


def _clean_evidence_line(raw_line: str) -> str:
    line = _HEADING_PREFIX_RE.sub("", raw_line.strip())
    return _WHITESPACE_RE.sub(" ", line).strip()


def _dedupe_evidence_line_prefix(line: str, previous_line: str) -> str:
    if previous_line and line.lower().startswith(f"{previous_line.lower()} "):
        return line[len(previous_line) :].strip()
    return line


def _strip_evidence_heading_prefix(cleaned: str, heading: str) -> str:
    heading_text = _HEADING_PREFIX_RE.sub("", heading.strip())
    if heading_text and cleaned.lower().startswith(f"{heading_text.lower()} "):
        return cleaned[len(heading_text) :].strip()
    return cleaned


def _prerequisites_for(
    term: str,
    prerequisite_hints: dict[str, Counter[str]],
    exam_counts: Counter[str],
) -> tuple[str, ...]:
    hints = prerequisite_hints.get(term)
    if not hints:
        return ()
    candidates = [
        (peer, count)
        for peer, count in hints.items()
        if _valid_prerequisite_peer(peer, term, exam_counts)
    ]
    candidates.sort(key=lambda item: -item[1])
    return tuple(peer for peer, _count in candidates[:3])


def _valid_prerequisite_peer(peer: str, term: str, exam_counts: Counter[str]) -> bool:
    return " " not in peer and peer not in exam_counts and term not in peer and peer not in term
