"""Deterministic priority analysis over indexed study materials."""

from __future__ import annotations

import html
import json
import os
import re
import textwrap
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, TypeGuard

from hephaistos.materials import infer_material_role
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.runtime import (
    ChatConfig,
    Conversation,
    EngineError,
    RetryConfig,
    stream_completion,
)

_TOKEN_RE = re.compile(r"[^\W\d_][^\W_+-]{2,}")
_SENTENCE_RE = re.compile(r"[^.!?\n]+")
_TOPIC_TOKEN_PATTERN = r"[^\W\d_][^\W_+-]*"
_TOPIC_PHRASE_RE = re.compile(rf"\b{_TOPIC_TOKEN_PATTERN}(?:\s+{_TOPIC_TOKEN_PATTERN}){{1,5}}\b")
_QUESTION_START_RE = re.compile(r"\b(?:question|q|aufgabe)\s*\d+[A-Za-z]?\b", re.IGNORECASE)
_HEADING_PREFIX_RE = re.compile(r"^(?:#+\s*|\d+(?:\.\d+)*[.)]?\s*|[-*]\s*)")
_WHITESPACE_RE = re.compile(r"\s+")
_WORD_SPLIT_RE = re.compile(_TOPIC_TOKEN_PATTERN)
_WEB_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>'
    r".{0,1800}?"
    r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_WEB_PREREQ_CLAUSE_RE = re.compile(
    r"\b(?:prerequisites?|requires?|need(?:ed)?|before learning|familiar with|"
    r"understand(?:ing)?)\b[^.?!:;]{0,48}[:;\-]?\s*(?P<tail>[^.?!]{0,180})",
    re.IGNORECASE,
)
_KNOWN_SINGLE_WORD_TOPICS = frozenset({"dijkstra", "graph", "heap", "heaps"})
_KNOWN_TOPIC_PHRASES = frozenset(
    {
        "binary search",
        "chain rule",
        "dynamic programming",
        "gradient descent",
        "hash table",
        "neural network",
        "shortest paths",
        "validation set",
        "dijkstra shortest",
        "dijkstra shortest paths",
        "graph shortest paths",
        "archimedisches prinzip",
        "bestimmte divergenz",
        "cosinus",
        "differenzierbare funktionen",
        "exponential logarithmus",
        "geometrische reihe",
        "grenzwert",
        "höhere ableitungen",
        "hoehere ableitungen",
        "konvergenz",
        "lineare approximation",
        "monotonie",
        "partialbruchzerlegung",
        "potenzreihenentwicklung",
        "potenzreihenentwicklung des kosinus",
        "stetige funktionen",
        "trigonometrische funktionen",
    }
)
_MARK_RE = re.compile(
    r"(?:\[\s*(\d{1,2})\s*(?:marks?|pts?|points?)\s*\]|"
    r"\((\d{1,2})\s*(?:marks?|pts?|points?)\)|"
    r"\b(\d{1,2})\s*(?:marks?|pts?|points?|punkte?|pkt\.?)\b|"
    r"(?:punkte?|pkt\.?)\s*[:=]?\s*(\d{1,2})\b)",
    re.IGNORECASE,
)
_NO_PREREQUISITE_TEXT = "No explicit prerequisite found in indexed materials."
_WEB_PREREQ_ENV = "HEPHAISTOS_PRIORITY_WEB_PREREQS"
_WEB_PREREQ_TIMEOUT = 8
_WEB_PREREQ_TOPICS = 6
_WEB_PREREQ_RESULTS = 4
_WEB_PREREQ_USER_AGENT = "Hephaistos/0.1 priority prerequisites"
_WEB_PREREQ_SEARCH_URL = "https://duckduckgo.com/html/"
_ROLE_LABELS: dict[str, str] = {
    "assignment": "assignment",
    "codebase": "codebase",
    "lecture": "lecture notes",
    "past_exam": "past exam",
    "reference": "reference material",
    "slides": "lecture slides",
    "textbook": "textbook",
    "vocabulary": "vocabulary material",
}

_STOPWORDS = frozenset(
    {
        "about",
        "after",
        "am",
        "an",
        "also",
        "and",
        "answer",
        "are",
        "against",
        "auf",
        "alle",
        "alles",
        "als",
        "analog",
        "april",
        "basic",
        "basics",
        "because",
        "beispiel",
        "beispiele",
        "bekannte",
        "bekannten",
        "beliebiges",
        "before",
        "berechnen",
        "beweis",
        "brief",
        "briefly",
        "daher",
        "damit",
        "dann",
        "dass",
        "calculate",
        "connected",
        "der",
        "des",
        "define",
        "dem",
        "den",
        "denn",
        "depend",
        "depends",
        "describe",
        "eine",
        "einem",
        "einen",
        "einer",
        "eines",
        "existiert",
        "does",
        "each",
        "exam",
        "explain",
        "falls",
        "following",
        "from",
        "folgt",
        "for",
        "für",
        "fuer",
        "gilt",
        "give",
        "given",
        "gegen",
        "have",
        "haben",
        "hilfsmittel",
        "heißt",
        "heisst",
        "hier",
        "informatiker",
        "identify",
        "into",
        "klausur",
        "können",
        "konnen",
        "marks",
        "mathematik",
        "matrikelnummer",
        "maximal",
        "mit",
        "mittig",
        "module",
        "modul",
        "muss",
        "nach",
        "nachname",
        "nicht",
        "ohne",
        "one",
        "past",
        "punkte",
        "punkt",
        "question",
        "questions",
        "ratzkin",
        "semester",
        "sei",
        "seien",
        "sie",
        "sommersemester",
        "show",
        "somit",
        "state",
        "that",
        "teil",
        "the",
        "their",
        "then",
        "this",
        "through",
        "two",
        "über",
        "ueber",
        "using",
        "use",
        "uses",
        "von",
        "vorname",
        "what",
        "when",
        "where",
        "which",
        "with",
        "womit",
        "würzburg",
        "wuerzburg",
        "your",
        "zur",
        "formula",
        "not",
        "decoded",
        "image",
        "ocr",
        "noise",
        "die",
        "das",
        "universität",
        "universitaet",
        "university",
        "universit",
        "ist",
        "januar",
        "februar",
        "märz",
        "maerz",
        "mai",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "dezember",
        "january",
        "february",
        "march",
        "may",
        "june",
        "july",
        "october",
        "december",
        "und",
        "wir",
        "wahr",
        "wählen",
        "waehlen",
        "algorithm",
        "algorithms",
        "article",
        "course",
        "example",
        "examples",
        "guide",
        "implementation",
        "introduction",
        "learn",
        "learning",
        "overview",
        "should",
        "tutorial",
        "untersuchen",
        "understand",
        "understanding",
    }
)


class PriorityChunk(Protocol):
    """Minimal chunk shape needed for local priority analysis."""

    source: str
    heading: str
    text: str


@dataclass(frozen=True, slots=True)
class PriorityTopicEvidence:
    source: str
    heading: str
    excerpt: str
    marks: int = 0


@dataclass(frozen=True, slots=True)
class PriorityWebSearchResult:
    title: str
    url: str
    snippet: str


@dataclass(frozen=True, slots=True)
class PriorityWebPrerequisite:
    term: str
    source_title: str
    source_url: str


PriorityWebSearcher = Callable[[str], Iterable[PriorityWebSearchResult]]


@dataclass(frozen=True, slots=True)
class PriorityExamQuestion:
    source: str
    prompt: str
    marks: int
    topics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PriorityMaterialSignal:
    source: str
    role: str
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class PriorityTopic:
    """A locally observed priority topic."""

    topic: str
    score: float
    exam_hits: int
    exam_marks: int
    material_hits: int
    sources: tuple[str, ...]
    prerequisites: tuple[str, ...] = ()
    web_prerequisites: tuple[PriorityWebPrerequisite, ...] = ()
    evidence: tuple[PriorityTopicEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class PriorityReport:
    path: Path
    used_model: bool
    topic_count: int
    source_count: int


@dataclass(frozen=True, slots=True)
class PriorityAnalysis:
    """Deterministic priority scan result."""

    topics: tuple[PriorityTopic, ...]
    past_exam_sources: tuple[str, ...]
    material_sources: tuple[str, ...]
    chunks: tuple[PriorityChunk, ...] = ()
    exam_questions: tuple[PriorityExamQuestion, ...] = ()
    material_signals: tuple[PriorityMaterialSignal, ...] = ()

    def render_for_prompt(self, *, limit: int = 6) -> str:
        """Render concise context for the model-facing priority request."""
        if not self.topics:
            return "Local priority scan: no recurring indexed topics were found."

        lines = ["Local priority scan from indexed materials:"]
        if self.past_exam_sources:
            lines.append(f"- Past exams scanned: {', '.join(self.past_exam_sources[:5])}")
        if self.material_sources:
            lines.append(f"- Supporting materials scanned: {', '.join(self.material_sources[:5])}")
        if self.material_signals:
            lines.append("- Material classification:")
            for signal in self.material_signals[:8]:
                label = _ROLE_LABELS.get(signal.role, signal.role.replace("_", " "))
                lines.append(
                    f"  - {signal.source}: {label} ({signal.confidence:.2f}; {signal.reason})"
                )
        lines.append("- Candidate priorities:")
        for topic in self.topics[:limit]:
            sources = ", ".join(topic.sources[:3])
            prerequisites = _prompt_prerequisite_summary(topic)
            lines.append(
                f"  - {topic.topic}: score {topic.score:.1f}, "
                f"exam hits {topic.exam_hits}, exam marks {topic.exam_marks}, "
                f"material hits {topic.material_hits}; "
                f"sources: {sources}{prerequisites}"
            )
        return "\n".join(lines)


def _prompt_prerequisite_summary(topic: PriorityTopic) -> str:
    if topic.prerequisites:
        return f"; prerequisites to check: {', '.join(topic.prerequisites[:3])}"
    if topic.web_prerequisites:
        terms = ", ".join(item.term for item in topic.web_prerequisites[:3])
        return f"; web-backed prerequisite hints: {terms}"
    return ""


def analyze_priority(
    chunks: Iterable[PriorityChunk],
    *,
    limit: int = 8,
    web_searcher: PriorityWebSearcher | None = None,
) -> PriorityAnalysis:
    """Rank recurring topics, weighting past-exam occurrences most heavily."""
    chunk_list = list(chunks)
    exam_counts: Counter[str] = Counter()
    exam_marks: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    prerequisite_hints: dict[str, Counter[str]] = {}
    sources_by_topic: dict[str, set[str]] = {}
    evidence_by_topic: dict[str, list[PriorityTopicEvidence]] = {}
    past_exam_sources: set[str] = set()
    material_sources: set[str] = set()
    exam_questions: list[PriorityExamQuestion] = []
    material_signal_by_source: dict[str, PriorityMaterialSignal] = {}
    seen_exam_sections: set[tuple[str, str]] = set()

    for chunk in chunk_list:
        role, confidence, reason = _priority_material_role(chunk)
        material_signal_by_source.setdefault(
            chunk.source,
            PriorityMaterialSignal(
                source=chunk.source,
                role=role,
                confidence=confidence,
                reason=reason,
            ),
        )
        exam_sections = tuple(_exam_sections(chunk.text)) if role == "past_exam" else ()
        if role == "past_exam":
            past_exam_sources.add(chunk.source)
            new_sections = []
            for section in exam_sections:
                fingerprint = _exam_section_fingerprint(section)
                key = (chunk.source, fingerprint)
                if key in seen_exam_sections:
                    continue
                seen_exam_sections.add(key)
                new_sections.append(section)
            exam_questions.extend(_exam_questions(chunk.source, new_sections))
            for section in new_sections:
                marks = _mark_weight(section)
                for term in set(_topic_terms("", section)):
                    exam_counts[term] += 1
                    if marks:
                        exam_marks[term] += marks
                    sources_by_topic.setdefault(term, set()).add(chunk.source)
                    evidence_by_topic.setdefault(term, [])
                    if len(evidence_by_topic[term]) < 4:
                        evidence_by_topic[term].append(
                            PriorityTopicEvidence(
                                source=chunk.source,
                                heading=chunk.heading,
                                excerpt=_topic_excerpt(section, term, heading=chunk.heading),
                                marks=marks,
                            )
                        )
            continue
        material_sources.add(chunk.source)
        terms = set(_topic_terms(chunk.heading, chunk.text))
        if not terms:
            continue
        prerequisites = _explicit_prerequisites(chunk.text)
        for term in terms:
            material_counts[term] += 1
            sources_by_topic.setdefault(term, set()).add(chunk.source)
            evidence_by_topic.setdefault(term, [])
            if len(evidence_by_topic[term]) < 4:
                evidence_by_topic[term].append(_topic_evidence(chunk, term, 0))
        dependency_prerequisites = _dependency_prerequisites(chunk.text, terms)
        for term in terms:
            if prerequisites:
                prerequisite_hints.setdefault(term, Counter()).update(prerequisites)
            if term in dependency_prerequisites:
                prerequisite_hints.setdefault(term, Counter()).update(
                    dependency_prerequisites[term]
                )

    topics: list[PriorityTopic] = []
    for term in sorted(set(exam_counts) | set(material_counts)):
        exam_hits = exam_counts[term]
        marks = exam_marks[term]
        material_hits = material_counts[term]
        score = exam_hits * 8.0 + marks * 1.0 + min(material_hits, 6) * 0.5
        if score <= 0:
            continue
        topics.append(
            PriorityTopic(
                topic=term,
                score=score,
                exam_hits=exam_hits,
                exam_marks=marks,
                material_hits=material_hits,
                sources=tuple(sorted(sources_by_topic.get(term, set()))),
                prerequisites=_prerequisites_for(term, prerequisite_hints, exam_counts),
                evidence=tuple(evidence_by_topic.get(term, ())),
            )
        )

    topics.sort(
        key=lambda topic: (
            topic.exam_hits == 0,
            -topic.exam_marks,
            -topic.exam_hits,
            -topic.score,
            topic.topic,
        )
    )
    topics = _collapse_component_topics(topics)
    topics = _with_web_prerequisites(topics[:limit], web_searcher)
    return PriorityAnalysis(
        topics=tuple(topics),
        past_exam_sources=tuple(sorted(past_exam_sources)),
        material_sources=tuple(sorted(material_sources)),
        chunks=tuple(chunk_list),
        exam_questions=tuple(exam_questions),
        material_signals=tuple(
            material_signal_by_source[source] for source in sorted(material_signal_by_source)
        ),
    )


def _priority_material_role(chunk: PriorityChunk) -> tuple[str, float, str]:
    role, confidence, reason = infer_material_role(chunk.source)
    if role == "past_exam":
        return role, confidence, reason
    text = _repair_pdf_unicode_spacing(chunk.text[:2000]).casefold()
    if _exam_like_text(text):
        return "past_exam", max(confidence, 0.92), "content contains exam instructions/questions"
    return role, confidence, reason


def _exam_like_text(text: str) -> bool:
    signals = (
        "klausur",
        "punkte",
        "aufgabe",
        "aufgabennummer",
        "maximal",
        "bestehen",
        "hilfsmittel",
        "bearbeitungen",
        "matrikelnummer",
    )
    hits = sum(1 for signal in signals if signal in text)
    question_signal = re.search(r"\b(?:aufgabe|question|q)\s*\d+", text, re.IGNORECASE)
    mark_signal = _MARK_RE.search(text) is not None
    return hits >= 3 or (question_signal is not None and mark_signal)


def _topic_terms(heading: str, text: str) -> list[str]:
    raw = _repair_pdf_unicode_spacing(f"{heading}\n{text}")
    seen: set[str] = set()
    terms: list[str] = []
    for candidate in _candidate_topic_phrases(raw):
        if _valid_topic(candidate) and candidate not in seen:
            terms.append(candidate)
            seen.add(candidate)
    return terms


def _with_web_prerequisites(
    topics: list[PriorityTopic],
    web_searcher: PriorityWebSearcher | None,
) -> list[PriorityTopic]:
    if web_searcher is None:
        return topics
    enriched: list[PriorityTopic] = []
    for index, topic in enumerate(topics):
        if index >= _WEB_PREREQ_TOPICS or topic.prerequisites:
            enriched.append(topic)
            continue
        web_prerequisites = _web_prerequisites_for(topic.topic, web_searcher)
        enriched.append(
            PriorityTopic(
                topic=topic.topic,
                score=topic.score,
                exam_hits=topic.exam_hits,
                exam_marks=topic.exam_marks,
                material_hits=topic.material_hits,
                sources=topic.sources,
                prerequisites=topic.prerequisites,
                web_prerequisites=web_prerequisites,
                evidence=topic.evidence,
            )
        )
    return enriched


def _web_prerequisites_for(
    topic: str,
    web_searcher: PriorityWebSearcher,
) -> tuple[PriorityWebPrerequisite, ...]:
    results: list[PriorityWebPrerequisite] = []
    seen: set[str] = set()
    try:
        search_results = tuple(web_searcher(f"{topic} prerequisites"))
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        return ()
    for result in search_results[:_WEB_PREREQ_RESULTS]:
        for term in _prerequisite_terms_from_web_result(topic, result):
            if term in seen:
                continue
            seen.add(term)
            results.append(
                PriorityWebPrerequisite(
                    term=term,
                    source_title=result.title,
                    source_url=result.url,
                )
            )
            if len(results) >= 3:
                return tuple(results)
    return tuple(results)


def _prerequisite_terms_from_web_result(
    topic: str,
    result: PriorityWebSearchResult,
) -> Iterator[str]:
    text = f"{result.title}. {result.snippet}"
    matches = list(_WEB_PREREQ_CLAUSE_RE.finditer(text))
    candidate_texts = [match.group("tail") for match in matches]
    if not candidate_texts:
        candidate_texts = [result.snippet]
    topic_words = set(topic.split())
    for candidate_text in candidate_texts:
        yield from _candidate_web_prerequisite_terms(candidate_text, topic_words)


def _candidate_web_prerequisite_terms(text: str, topic_words: set[str]) -> Iterator[str]:
    seen: set[str] = set()
    for phrase_match in _TOPIC_PHRASE_RE.finditer(text):
        words = _normalized_words(phrase_match.group(0))
        useful = [word for word in words if _useful_topic_word(word) and word not in topic_words]
        if not useful:
            continue
        term = " ".join(useful[:3])
        if term not in seen:
            seen.add(term)
            yield term
    for word_match in _TOKEN_RE.finditer(text):
        term = _normalize_word(word_match.group(0))
        if not _useful_topic_word(term) or term in topic_words or term in seen:
            continue
        seen.add(term)
        yield term


def _candidate_topic_phrases(raw: str) -> Iterator[str]:
    yield from _heading_candidates(raw)
    for phrase_match in _TOPIC_PHRASE_RE.finditer(raw):
        words = _normalized_words(phrase_match.group(0))
        useful = [word for word in words if _useful_topic_word(word)]
        if len(useful) >= 2:
            if len(useful) <= 4 and _topic_phrase_is_known(useful):
                yield " ".join(useful)
            yield from _known_phrases_in(useful)
        for word in useful:
            if word in _KNOWN_SINGLE_WORD_TOPICS:
                yield word


def _heading_candidates(raw: str) -> Iterator[str]:
    for line in raw.splitlines():
        cleaned = _HEADING_PREFIX_RE.sub("", line.strip())
        if not cleaned or len(cleaned) > 90 or _metadata_heading(cleaned):
            continue
        if _line_looks_like_question_or_sentence(cleaned):
            continue
        words = _normalized_words(cleaned)
        useful = [word for word in words if _useful_topic_word(word)]
        if 1 <= len(useful) <= 6 and _candidate_has_concept_signal(useful):
            yield " ".join(useful)


def _normalized_words(value: str) -> list[str]:
    return [_normalize_word(word) for word in _WORD_SPLIT_RE.findall(value)]


def _normalize_word(word: str) -> str:
    lowered = word.casefold()
    return unicodedata.normalize("NFC", lowered)


def _useful_topic_word(word: str) -> bool:
    return len(word) >= 2 and word not in _STOPWORDS and not word.isdigit()


def _metadata_heading(value: str) -> bool:
    words = _normalized_words(value)
    if not words:
        return True
    metadata_words = {
        "april",
        "emester",
        "er",
        "mathematik",
        "matiker",
        "informatiker",
        "jesse",
        "ratzkin",
        "rmatiker",
        "sommersemester",
        "universität",
        "universitaet",
        "würzburg",
        "wuerzburg",
    }
    metadata_hits = len(set(words) & metadata_words)
    if len(words) <= 12 and metadata_hits >= 2:
        return True
    has_year = re.search(r"\b(?:19|20)\d{2}\b", value) is not None
    return has_year and len(words) <= 8 and metadata_hits >= 1


def _line_looks_like_question_or_sentence(value: str) -> bool:
    if _MARK_RE.search(value):
        return True
    if re.search(r"\b(?:aufgabe|question|q)\s*\d+\b", value, re.IGNORECASE):
        return True
    words = _normalized_words(value)
    return len(words) > 4 and value.endswith((".", "?", "!"))


def _path_contains_metadata(value: str) -> bool:
    words = set(_normalized_words(value.replace("/", " ").replace("_", " ")))
    metadata_words = {"jesse", "ratzkin", "universität", "universitaet", "würzburg", "wuerzburg"}
    return bool(words & metadata_words)


def _candidate_has_concept_signal(words: list[str]) -> bool:
    term = " ".join(words)
    if term in _KNOWN_TOPIC_PHRASES:
        return True
    if len(words) == 1:
        return words[0] in _KNOWN_SINGLE_WORD_TOPICS
    banned = {
        "aussage",
        "aufgaben",
        "aufgabennummer",
        "begründen",
        "begruenden",
        "bearbeitungen",
        "dirfen",
        "dürfen",
        "erreichen",
        "erzielen",
        "hilfsmittel",
        "matrikelnummer",
        "maximal",
        "name",
        "nomen",
        "vorname",
        "widerspruch",
    }
    if any(word in banned for word in words):
        return False
    concept_endings = (
        "heit",
        "keit",
        "tion",
        "ung",
        "ungen",
        "enz",
        "anz",
        "mus",
        "men",
        "reihe",
        "reihen",
        "funktion",
        "funktionen",
        "satz",
        "prinzip",
        "regel",
        "wert",
        "werte",
        "logarithmus",
        "kosinus",
        "sinus",
    )
    return any(word.endswith(concept_endings) for word in words)


def _topic_phrase_is_known(words: list[str]) -> bool:
    return " ".join(words) in _KNOWN_TOPIC_PHRASES


def _known_phrases_in(words: list[str]) -> Iterator[str]:
    for phrase in _KNOWN_TOPIC_PHRASES:
        phrase_words = phrase.split()
        size = len(phrase_words)
        for start in range(len(words) - size + 1):
            if words[start : start + size] == phrase_words:
                yield phrase


def _valid_topic(candidate: str) -> bool:
    words = candidate.split()
    if not words:
        return False
    if any(word in _STOPWORDS for word in words):
        return False
    if len(words) == 1 and len(words[0]) < 4 and words[0] not in _KNOWN_SINGLE_WORD_TOPICS:
        return False
    return len(words) <= 5


def _collapse_component_topics(topics: list[PriorityTopic]) -> list[PriorityTopic]:
    collapsed: list[PriorityTopic] = []
    for topic in topics:
        if _covered_by_preferred_topic(topic, topics):
            continue
        collapsed.append(topic)
    return collapsed


def _covered_by_preferred_topic(topic: PriorityTopic, topics: list[PriorityTopic]) -> bool:
    for candidate in topics:
        if candidate.topic == topic.topic:
            continue
        if not _same_topic_signal(topic, candidate):
            continue
        if _topic_is_preferred(candidate.topic, topic.topic):
            return True
    return False


def _same_topic_signal(left: PriorityTopic, right: PriorityTopic) -> bool:
    return (
        left.exam_hits == right.exam_hits
        and left.exam_marks == right.exam_marks
        and left.material_hits == right.material_hits
        and left.sources == right.sources
    )


def _topic_is_preferred(candidate: str, current: str) -> bool:
    candidate_words = set(candidate.split())
    current_words = set(current.split())
    if candidate_words.isdisjoint(current_words):
        return False
    candidate_single_known = candidate in _KNOWN_SINGLE_WORD_TOPICS
    current_single_known = current in _KNOWN_SINGLE_WORD_TOPICS
    if candidate_single_known != current_single_known:
        return candidate_single_known
    candidate_known = candidate in _KNOWN_TOPIC_PHRASES
    current_known = current in _KNOWN_TOPIC_PHRASES
    if candidate_known != current_known:
        return candidate_known
    return len(candidate_words) > len(current_words)


def _explicit_prerequisites(text: str) -> list[str]:
    terms: list[str] = []
    for line in text.splitlines():
        if not re.search(r"\bprerequisites?\b", line, flags=re.IGNORECASE):
            continue
        _label, _sep, rest = line.partition(":")
        raw = rest or line
        terms.extend(
            _normalize_word(token)
            for token in _TOKEN_RE.findall(raw)
            if _useful_topic_word(_normalize_word(token))
        )
    return terms


def _dependency_prerequisites(text: str, terms: set[str]) -> dict[str, Counter[str]]:
    hints: dict[str, Counter[str]] = {}
    for sentence_match in _SENTENCE_RE.finditer(text):
        sentence = sentence_match.group(0)
        lowered = sentence.lower()
        marker = _dependency_marker(lowered)
        if marker is None:
            continue
        before, after = lowered[:marker], lowered[marker:]
        sentence_terms = {term for term in terms if term in before}
        if not sentence_terms:
            continue
        prerequisites = [
            _normalize_word(token)
            for token in _TOKEN_RE.findall(after)
            if _useful_topic_word(_normalize_word(token))
        ]
        for term in sentence_terms:
            hints.setdefault(term, Counter()).update(prerequisites)
    return hints


def _dependency_marker(sentence: str) -> int | None:
    markers = ("depends on", "requires", "builds on", "needs")
    positions = [sentence.find(marker) for marker in markers if marker in sentence]
    if not positions:
        return None
    return min(position for position in positions if position >= 0)


def _mark_weight(text: str) -> int:
    marks = []
    for match in _MARK_RE.finditer(text):
        context = text[max(0, match.start() - 16) : match.start()].casefold()
        if any(word in context for word in ("maximal", "total", "insgesamt")):
            continue
        for group in match.groups():
            if group is not None:
                marks.append(int(group))
                break
    return max(marks, default=0)


def _exam_sections(text: str) -> Iterator[str]:
    matches = sorted(_exam_question_matches(text), key=lambda match: match.start())
    if not matches:
        yield text
        return
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.start() : end].strip()
        if section:
            yield section


def _exam_question_matches(text: str) -> Iterator[re.Match[str]]:
    matches = list(_QUESTION_START_RE.finditer(text))
    explicit_question_starts_by_number: dict[str, int] = {}
    for match in matches:
        number_match = re.search(r"\d{1,2}", match.group(0))
        if number_match is not None:
            explicit_question_starts_by_number.setdefault(number_match.group(0), match.start())
    question_mark_pattern = r"(?<!\d)\d{1,2}\.\s*\([^)]*?(?:punkte?|marks?|pts?)[^)]*\)"
    for match in re.finditer(question_mark_pattern, text, re.IGNORECASE):
        number = match.group(0).split(".", 1)[0]
        explicit_start = explicit_question_starts_by_number.get(number)
        if explicit_start is not None and explicit_start < match.start():
            continue
        if all(existing.start() != match.start() for existing in matches):
            matches.append(match)
    yield from sorted(matches, key=lambda match: match.start())


def _exam_section_terms(sections: Iterable[str]) -> dict[str, int]:
    marks_by_term: dict[str, int] = {}
    for section in sections:
        marks = _mark_weight(section)
        if not marks:
            continue
        for term in _topic_terms("", section):
            marks_by_term[term] = max(marks_by_term.get(term, 0), marks)
    return marks_by_term


def _exam_section_fingerprint(section: str) -> str:
    normalized = _repair_pdf_unicode_spacing(section).casefold()
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
    match = _exam_question_matches(normalized)
    first_match = next(match, None)
    if first_match is not None:
        normalized = normalized[first_match.start() :]
    return normalized


def _exam_questions(source: str, sections: Iterable[str]) -> Iterator[PriorityExamQuestion]:
    for section in sections:
        topics = tuple(_topic_terms("", section)[:5])
        if not topics and _exam_section_is_score_only(section):
            continue
        prompt = _topic_excerpt(section, "", max_chars=360)
        if not prompt:
            continue
        yield PriorityExamQuestion(
            source=source,
            prompt=prompt,
            marks=_mark_weight(section),
            topics=topics,
        )


def _exam_section_is_score_only(section: str) -> bool:
    without_marks = _MARK_RE.sub(" ", _repair_pdf_unicode_spacing(section))
    words = _normalized_words(without_marks)
    return not any(_useful_topic_word(word) for word in words)


def _topic_evidence(chunk: PriorityChunk, term: str, marks: int) -> PriorityTopicEvidence:
    text = _evidence_text_for_term(chunk.text, term) if marks else chunk.text
    return PriorityTopicEvidence(
        source=chunk.source,
        heading=chunk.heading,
        excerpt=_topic_excerpt(text, term, heading=chunk.heading),
        marks=marks,
    )


def _evidence_text_for_term(text: str, term: str) -> str:
    for section in _exam_sections(text):
        if term in set(_topic_terms("", section)):
            return section
    return text


def _topic_excerpt(text: str, term: str, *, heading: str = "", max_chars: int = 260) -> str:
    normalized = _clean_evidence_excerpt(text, heading=heading)
    idx = normalized.casefold().find(term.casefold())
    if idx < 0:
        if len(normalized) <= max_chars:
            return normalized
        return f"{normalized[: max_chars - 1]}…"
    if _metadata_heading(normalized[:idx]):
        normalized = normalized[idx:]
        idx = 0
    start = max(0, idx - max_chars // 3)
    end = min(len(normalized), start + max_chars)
    start = max(0, end - max_chars)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(normalized) else ""
    return f"{prefix}{normalized[start:end]}{suffix}"


def _clean_evidence_excerpt(text: str, *, heading: str = "") -> str:
    cleaned_lines = []
    previous_line = ""
    repaired = _repair_pdf_unicode_spacing(text)
    for raw_line in repaired.splitlines():
        line = _HEADING_PREFIX_RE.sub("", raw_line.strip())
        line = _WHITESPACE_RE.sub(" ", line).strip()
        if not line or line == previous_line:
            continue
        if previous_line and line.casefold().startswith(f"{previous_line.casefold()} "):
            line = line[len(previous_line) :].strip()
        cleaned_lines.append(line)
        previous_line = line
    cleaned = _WHITESPACE_RE.sub(" ", " ".join(cleaned_lines)).strip()
    heading_text = _HEADING_PREFIX_RE.sub("", _repair_pdf_unicode_spacing(heading).strip())
    if heading_text and cleaned.casefold().startswith(f"{heading_text.casefold()} "):
        cleaned = cleaned[len(heading_text) :].strip()
    return _strip_metadata_prefix(cleaned)


def _strip_metadata_prefix(value: str) -> str:
    value = re.sub(r"(?<=[a-zäöüß])(?=[A-ZÄÖÜ])", ". ", value)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", value) if part.strip()]
    while sentences and _metadata_heading(sentences[0]):
        sentences.pop(0)
    return " ".join(sentences) if sentences else value


def _repair_pdf_unicode_spacing(value: str) -> str:
    repaired = value
    replacements = {
        "a¨": "ä",
        "A¨": "Ä",
        "o¨": "ö",
        "O¨": "Ö",
        "u¨": "ü",
        "U¨": "Ü",
        "¨ a": "ä",
        "¨ A": "Ä",
        "¨ o": "ö",
        "¨ O": "Ö",
        "¨ u": "ü",
        "¨ U": "Ü",
        "¨ s": "ß",
    }
    for source, replacement in replacements.items():
        repaired = repaired.replace(source, replacement)
    return unicodedata.normalize("NFC", repaired)


def _prerequisites_for(
    term: str,
    prerequisite_hints: dict[str, Counter[str]],
    exam_counts: Counter[str],
) -> tuple[str, ...]:
    hints = prerequisite_hints.get(term)
    if hints:
        candidates = [
            (peer, count)
            for peer, count in hints.items()
            if (
                " " not in peer
                and peer not in exam_counts
                and term not in peer
                and peer not in term
            )
        ]
        candidates.sort(key=lambda item: (-item[1], item[0]))
        if candidates:
            return tuple(peer for peer, _count in candidates[:3])
    return ()


_PRIORITY_SCHEMA = """
{
  "summary": "1-2 sentence source-grounded overview",
  "topics": [
    {
      "name": "exact topic name from the materials",
      "importance": "critical|high|medium|low",
      "why": "why this is important based only on supplied evidence",
      "study_actions": ["concrete, measurable goal grounded in the material"],
      "prerequisites": ["required prerequisite found in evidence or marked as web-backed"]
    }
  ],
  "past_exams": [
    {
      "source": "materials/...",
      "focus": "what the exam asked about",
      "marks": "visible mark distribution or unknown"
    }
  ],
  "study_plan": ["ordered next steps grounded in evidence"],
  "unknowns": ["important detail missing from indexed materials"]
}
""".strip()


_PRIORITY_SYSTEM_PROMPT = """
You are Hephaistos priority analysis. Produce a study-priority report using only the supplied
indexed material excerpts for topics, exam claims, marks, and source evidence. Do not add outside
facts for those sections. Web-backed prerequisite hints may be used only when they are explicitly
listed in the local scan context; label them as web-backed if you mention them. If the material
does not specify a detail, write that it is unknown. Favor exact topic names from the evidence
over filename fragments. Make each study action a concrete, checkable goal rather than a vague
instruction to review the topic.
Return JSON only, matching this schema:
""".strip()


def generate_priority_report(
    analysis: PriorityAnalysis,
    output_dir: Path,
    *,
    config: ChatConfig | None = None,
    focus: str = "",
) -> PriorityReport:
    """Write a printable source-grounded priority HTML report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if _web_prerequisite_search_enabled(config):
        analysis = _analysis_with_web_prerequisites(analysis)
    analysis = _analysis_for_full_report(analysis)
    model_payload = _model_priority_payload(analysis, config=config, focus=focus)
    html_text = _render_priority_html(analysis, model_payload=model_payload, focus=focus)
    path = output_dir / _priority_report_filename()
    path.write_text(html_text, encoding="utf-8")
    return PriorityReport(
        path=path,
        used_model=model_payload is not None,
        topic_count=len(analysis.topics),
        source_count=len(set(analysis.past_exam_sources) | set(analysis.material_sources)),
    )


def _web_prerequisite_search_enabled(config: ChatConfig | None) -> bool:
    env_value = os.environ.get(_WEB_PREREQ_ENV, "")
    if env_value.lower() in {"1", "true", "yes", "on"}:
        return True
    return config is not None and config.is_feature_enabled("priority_web_prereqs")


def _analysis_with_web_prerequisites(analysis: PriorityAnalysis) -> PriorityAnalysis:
    topics = _with_web_prerequisites(list(analysis.topics), _duckduckgo_search)
    return PriorityAnalysis(
        topics=tuple(topics),
        past_exam_sources=analysis.past_exam_sources,
        material_sources=analysis.material_sources,
        chunks=analysis.chunks,
        exam_questions=analysis.exam_questions,
        material_signals=analysis.material_signals,
    )


def _analysis_for_full_report(analysis: PriorityAnalysis) -> PriorityAnalysis:
    if len(analysis.topics) >= 18:
        return analysis
    expanded = analyze_priority(analysis.chunks, limit=40)
    web_by_topic = {topic.topic: topic.web_prerequisites for topic in analysis.topics}
    topics = [
        PriorityTopic(
            topic=topic.topic,
            score=topic.score,
            exam_hits=topic.exam_hits,
            exam_marks=topic.exam_marks,
            material_hits=topic.material_hits,
            sources=topic.sources,
            prerequisites=topic.prerequisites,
            web_prerequisites=web_by_topic.get(topic.topic, ()),
            evidence=topic.evidence,
        )
        for topic in expanded.topics
    ]
    return PriorityAnalysis(
        topics=tuple(topics),
        past_exam_sources=expanded.past_exam_sources,
        material_sources=expanded.material_sources,
        chunks=expanded.chunks,
        exam_questions=expanded.exam_questions,
        material_signals=expanded.material_signals,
    )


def _duckduckgo_search(query: str) -> Iterable[PriorityWebSearchResult]:
    params = urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        f"{_WEB_PREREQ_SEARCH_URL}?{params}",
        headers={"User-Agent": _WEB_PREREQ_USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=_WEB_PREREQ_TIMEOUT) as response:  # nosec B310
        raw_html = response.read().decode("utf-8", errors="replace")
    return tuple(_parse_duckduckgo_results(raw_html))


def _parse_duckduckgo_results(raw_html: str) -> Iterator[PriorityWebSearchResult]:
    for match in _WEB_RESULT_RE.finditer(raw_html):
        url = html.unescape(match.group("url"))
        title = _clean_web_text(match.group("title"))
        snippet = _clean_web_text(match.group("snippet"))
        if title and url and snippet:
            yield PriorityWebSearchResult(title=title, url=url, snippet=snippet)


def _clean_web_text(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value)
    return _WHITESPACE_RE.sub(" ", html.unescape(no_tags)).strip()


def _model_priority_payload(
    analysis: PriorityAnalysis,
    *,
    config: ChatConfig | None,
    focus: str,
) -> dict[str, object] | None:
    if config is None or not _can_use_model(config):
        return None
    conversation = Conversation()
    conversation.add("system", f"{_PRIORITY_SYSTEM_PROMPT}\n{_PRIORITY_SCHEMA}")
    conversation.add("user", _priority_model_context(analysis, focus=focus))
    parts: list[str] = []
    try:
        parts.extend(
            delta.content
            for delta in stream_completion(config, conversation, retry=RetryConfig(max_retries=1))
            if delta.content
        )
    except EngineError:
        return None
    return _parse_json_object("".join(parts))


def _can_use_model(config: ChatConfig) -> bool:
    if not config.base_url or not config.model:
        return False
    return is_keyless_endpoint(config.base_url) or bool(config.resolved_api_key)


def _priority_model_context(analysis: PriorityAnalysis, *, focus: str) -> str:
    chunks = list(_representative_chunks(analysis))
    evidence_lines = []
    role_by_source = {signal.source: signal for signal in analysis.material_signals}
    for idx, chunk in enumerate(chunks, start=1):
        role_signal = role_by_source.get(chunk.source)
        if role_signal is None:
            role, confidence, reason = _priority_material_role(chunk)
        else:
            role = role_signal.role
            confidence = role_signal.confidence
            reason = role_signal.reason
        evidence_lines.append(
            "\n".join(
                (
                    f"Evidence {idx}",
                    f"Source: {chunk.source}",
                    f"Role: {role} ({confidence:.2f}; {reason})",
                    f"Heading: {chunk.heading or 'none'}",
                    f"Text: {_compact_evidence_text(chunk.text)}",
                )
            )
        )
    focus_line = f"User focus: {focus}\n" if focus else ""
    return "\n\n".join(
        (
            focus_line + analysis.render_for_prompt(limit=10),
            "Indexed excerpts to analyze:",
            "\n\n".join(evidence_lines),
        )
    )


def _representative_chunks(
    analysis: PriorityAnalysis,
    *,
    limit: int = 28,
) -> tuple[PriorityChunk, ...]:
    selected: list[PriorityChunk] = []
    seen: set[tuple[str, str]] = set()
    topic_names = {topic.topic for topic in analysis.topics}
    for chunk in analysis.chunks:
        key = (chunk.source, chunk.text[:120])
        if key in seen:
            continue
        role, _confidence, _reason = infer_material_role(chunk.source)
        text = chunk.text.lower()
        if role == "past_exam" or any(topic in text for topic in topic_names):
            selected.append(chunk)
            seen.add(key)
        if len(selected) >= limit:
            return tuple(selected)
    for chunk in analysis.chunks:
        key = (chunk.source, chunk.text[:120])
        if key not in seen:
            selected.append(chunk)
            seen.add(key)
        if len(selected) >= limit:
            break
    return tuple(selected)


def _compact_evidence_text(text: str, *, max_chars: int = 900) -> str:
    compact = _WHITESPACE_RE.sub(" ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return f"{compact[: max_chars - 1]}…"


def _parse_json_object(text: str) -> dict[str, object] | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _render_priority_html(
    analysis: PriorityAnalysis,
    *,
    model_payload: dict[str, object] | None,
    focus: str,
) -> str:
    summary = _payload_string(model_payload, "summary") or _fallback_summary(analysis)
    return textwrap.dedent(
        f"""
        <!doctype html>
        <html lang="de">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Study priorities</title>
          <style>{_priority_css()}</style>
        </head>
        <body>
          <main>
            <header class="hero">
              <h1>Study priority report</h1>
              <p>{_escape(summary)}</p>
              {_focus_html(focus)}
              <p class="meta">Generated {_report_timestamp()}. Source-grounded from indexed
              materials only.</p>
            </header>
            {_topics_html(analysis, model_payload)}
            {_study_map_html(analysis)}
            {_past_exams_html(analysis, model_payload)}
            {_material_inventory_html(analysis)}
            {_plan_html(model_payload)}
            {_sources_html(analysis)}
          </main>
        </body>
        </html>
        """
    ).strip()


def _report_timestamp() -> str:
    return _escape(datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"))


def _priority_css() -> str:
    return """
:root {
  color: #111;
  background: #fff;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; color: #111; background: #fff; font-size: 16px; }
main { width: min(920px, calc(100% - 48px)); margin: 0 auto; padding: 40px 0 64px; }
.hero { border-bottom: 2px solid #111; padding-bottom: 22px; margin-bottom: 30px; }
h1 { font-size: clamp(2.2rem, 5vw, 3.5rem); line-height: 1; margin: 0 0 18px; }
h2 {
  font-size: 1.45rem;
  margin: 36px 0 16px;
}
h3 { font-size: 1.16rem; margin: 0 0 8px; }
h4 { font-size: .95rem; margin: 16px 0 8px; }
p { line-height: 1.55; }
.meta, .source, .evidence, .unknown { color: #333; font-size: .94rem; }
.topic-list { display: flex; flex-direction: column; gap: 28px; }
.topic {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 12rem;
  gap: 20px;
  padding-bottom: 24px;
  border-bottom: 1px solid #ddd;
  break-inside: avoid;
}
.topic:last-child { border-bottom: 0; }
.topic-main > :first-child, .topic-side > :first-child { margin-top: 0; }
ul { padding-left: 1.2rem; }
li { margin: 6px 0; }
blockquote {
  margin: 12px 0 0;
  padding: 0 0 0 12px;
  border-left: 2px solid #aaa;
}
table { width: 100%; border-collapse: collapse; }
th, td { border-bottom: 1px solid #ddd; padding: 9px 0; vertical-align: top; text-align: left; }
th { border-bottom-color: #111; }
@media print {
  main { width: 100%; padding: 0; }
  .topic { page-break-inside: avoid; }
}
@media (max-width: 760px) {
  .topic { grid-template-columns: 1fr; }
}
""".strip()


def _focus_html(focus: str) -> str:
    if not focus:
        return ""
    return f'<p class="meta"><strong>Focus:</strong> {_escape(focus)}</p>'


def _topics_html(analysis: PriorityAnalysis, model_payload: dict[str, object] | None) -> str:
    payload_topics = _payload_topics(model_payload)
    items: list[str] = []
    for index, topic in enumerate(analysis.topics, start=1):
        payload = payload_topics.get(topic.topic.lower())
        importance = _topic_importance(topic, payload)
        why = _payload_string(payload, "why") or _fallback_topic_why(topic)
        actions = _payload_string_list(payload, "study_actions") or _fallback_study_actions(topic)
        prerequisites = _payload_string_list(payload, "prerequisites") or list(topic.prerequisites)
        prerequisites_html = _prerequisite_section_html(prerequisites, topic.web_prerequisites)
        items.append(
            "\n".join(
                (
                    '<article class="topic">',
                    '<div class="topic-main">',
                    f"<h3>{index}. {_escape(topic.topic)}</h3>",
                    f"<p><strong>Priority:</strong> {_escape(importance)}. {_escape(why)}</p>",
                    _list_html("What to study", actions),
                    _topic_evidence_html(topic),
                    "</div>",
                    '<aside class="topic-side">',
                    _topic_metric_html(topic),
                    prerequisites_html,
                    "</aside>",
                    "</article>",
                )
            )
        )
    if not items:
        items.append('<p class="unknown">No recurring indexed topics were found.</p>')
    topic_html = "".join(items)
    return (
        '<section><h2>Topics to prioritize</h2><div class="topic-list">'
        f"{topic_html}</div></section>"
    )


def _prerequisite_section_html(
    prerequisites: list[str],
    web_prerequisites: tuple[PriorityWebPrerequisite, ...],
) -> str:
    if prerequisites:
        return _list_html("Prerequisites", prerequisites)
    if web_prerequisites:
        return _web_prerequisite_html(web_prerequisites)
    return _list_html("Prerequisites", [_NO_PREREQUISITE_TEXT])


def _web_prerequisite_html(web_prerequisites: tuple[PriorityWebPrerequisite, ...]) -> str:
    items = []
    for prerequisite in web_prerequisites:
        label = _escape(prerequisite.term)
        source_title = _escape(prerequisite.source_title)
        source_url = _escape(prerequisite.source_url)
        items.append(
            f'<li>{label}<br><span class="source">web prerequisite hint: '
            f'<a href="{source_url}">{source_title}</a></span></li>'
        )
    return "<h4>Prerequisites</h4><ul>" + "".join(items) + "</ul>"


def _topic_metric_html(topic: PriorityTopic) -> str:
    metrics = (
        f"Score {topic.score:.1f} · exam hits {topic.exam_hits} · "
        f"exam marks {topic.exam_marks} · material hits {topic.material_hits}"
    )
    return f'<p class="meta">{_escape(metrics)}</p>'


def _study_map_html(analysis: PriorityAnalysis) -> str:
    if not analysis.topics:
        return ""
    rows = [
        (
            "<tr>"
            f"<td>{_escape(topic.topic)}</td>"
            f"<td>{_escape(_topic_short_description(topic))}</td>"
            f"<td>{_escape(_topic_exam_signal(topic))}</td>"
            f"<td>{_escape(_topic_source_signal(topic))}</td>"
            "</tr>"
        )
        for topic in analysis.topics
    ]
    return (
        "<section><h2>Factual study map</h2>"
        '<p class="meta">Every row is derived from the enabled indexed materials. '
        "Descriptions are intentionally short and source-grounded.</p>"
        "<table><thead><tr><th>Topic</th><th>What it is here</th><th>Exam signal</th>"
        "<th>Where it appears</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _topic_short_description(topic: PriorityTopic) -> str:
    if not topic.evidence:
        return "Found in indexed materials; no clean excerpt available."
    excerpt = topic.evidence[0].excerpt
    for sentence_match in _SENTENCE_RE.finditer(excerpt):
        sentence = _WHITESPACE_RE.sub(" ", sentence_match.group(0)).strip()
        if topic.topic in sentence.lower():
            return _truncate(sentence, 180)
    return _truncate(excerpt, 180)


def _topic_exam_signal(topic: PriorityTopic) -> str:
    if topic.exam_marks:
        return f"{topic.exam_hits} exam hit(s), {topic.exam_marks} visible mark(s)"
    if topic.exam_hits:
        return f"{topic.exam_hits} exam hit(s), no explicit marks found"
    return "No past-exam hit found"


def _topic_source_signal(topic: PriorityTopic) -> str:
    source_count = len(topic.sources)
    first_sources = ", ".join(topic.sources[:3])
    suffix = f" (+{source_count - 3} more)" if source_count > 3 else ""
    return f"{first_sources}{suffix}" if first_sources else "No source recorded"


def _material_inventory_html(analysis: PriorityAnalysis) -> str:
    if not analysis.material_signals:
        return ""
    rows = []
    for signal in analysis.material_signals:
        if signal.role != "past_exam" and _path_contains_metadata(signal.source):
            reason = "path metadata; not treated as a study topic"
        else:
            reason = signal.reason
        label = _ROLE_LABELS.get(signal.role, signal.role.replace("_", " "))
        rows.append(
            "<tr>"
            f"<td>{_escape(signal.source)}</td>"
            f"<td>{_escape(label)}</td>"
            f"<td>{_escape(f'{signal.confidence:.2f}')}</td>"
            f"<td>{_escape(reason)}</td>"
            "</tr>"
        )
    return (
        "<section><h2>What was checked</h2>"
        '<p class="meta">These file roles are part of the analysis. Exam ranking only uses '
        "files classified as past exams.</p>"
        "<table><thead><tr><th>Source</th><th>Role</th><th>Confidence</th>"
        "<th>Why</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></section>"
    )


def _truncate(value: str, max_chars: int) -> str:
    value = _WHITESPACE_RE.sub(" ", value).strip()
    if len(value) <= max_chars:
        return value
    return f"{value[: max_chars - 1]}…"


def _string_object_mapping(value: object) -> TypeGuard[dict[str, object]]:
    if not isinstance(value, dict):
        return False
    return all(isinstance(key, str) for key in value)


def _payload_topics(model_payload: dict[str, object] | None) -> dict[str, dict[str, object]]:
    topics: dict[str, dict[str, object]] = {}
    raw_topics = model_payload.get("topics") if model_payload is not None else None
    if not isinstance(raw_topics, list):
        return topics
    for raw in raw_topics:
        if not _string_object_mapping(raw):
            continue
        raw_name = raw.get("name")
        if isinstance(raw_name, str) and raw_name.strip():
            topics[raw_name.strip().lower()] = raw
    return topics


def _topic_importance(topic: PriorityTopic, payload: dict[str, object] | None) -> str:
    payload_value = _payload_string(payload, "importance")
    if payload_value in {"critical", "high", "medium", "low"}:
        return payload_value
    if topic.exam_marks >= 10 or topic.exam_hits >= 3:
        return "critical"
    if topic.exam_hits > 0 or topic.exam_marks >= 6:
        return "high"
    if topic.material_hits >= 2:
        return "medium"
    return "low"


def _fallback_topic_why(topic: PriorityTopic) -> str:
    parts = []
    if topic.exam_marks:
        parts.append(f"{topic.exam_marks} visible past-exam mark(s)")
    if topic.exam_hits:
        parts.append(f"{topic.exam_hits} past-exam hit(s)")
    if topic.material_hits:
        parts.append(f"{topic.material_hits} supporting-material excerpt(s)")
    if not parts:
        return "Observed in the indexed material excerpts."
    if topic.exam_hits or topic.exam_marks:
        return "Ranked here because it has " + " and ".join(parts) + "."
    return "Included as a supporting-material concept, but below exam-linked topics."


def _fallback_study_actions(topic: PriorityTopic) -> list[str]:
    actions = [
        f"Make a concise definition card for {topic.topic}: definition, one worked example, "
        "and the exact source excerpt that supports it."
    ]
    if topic.exam_marks or topic.exam_hits:
        mark_text = f" for {topic.exam_marks} visible marks" if topic.exam_marks else ""
        actions.append(
            f"Write a timed answer for every cited exam prompt about {topic.topic}{mark_text}; "
            "then compare each sentence against the cited material."
        )
    else:
        actions.append(
            "Do not treat this as high priority unless it supports an exam-linked topic or your "
            "lecturer emphasized it."
        )
    if topic.prerequisites:
        actions.append(
            f"Before attempting exam practice, prove you can define and use: "
            f"{', '.join(topic.prerequisites[:3])}."
        )
    elif topic.web_prerequisites:
        terms = ", ".join(item.term for item in topic.web_prerequisites[:3])
        actions.append(
            "Use the web-backed prerequisite hints only as a prep checklist, then verify "
            f"against course material where possible: {terms}."
        )
    return actions


def _topic_evidence_html(topic: PriorityTopic) -> str:
    items = []
    for evidence in topic.evidence[:3]:
        marks = f" · {evidence.marks} marks" if evidence.marks else ""
        heading = f" · {evidence.heading}" if evidence.heading else ""
        items.append(
            f'<blockquote class="evidence"><p>{_escape(evidence.excerpt)}</p>'
            f'<p class="source">{_escape(evidence.source)}{_escape(heading)}{marks}</p>'
            "</blockquote>"
        )
    return "".join(items)


def _past_exams_html(analysis: PriorityAnalysis, model_payload: dict[str, object] | None) -> str:
    payload_exams = _payload_exam_rows(model_payload)
    rows = []
    for source in analysis.past_exam_sources:
        payload = payload_exams.get(source, {})
        focus = _payload_string(payload, "focus") or _fallback_exam_focus(analysis, source)
        marks = _payload_string(payload, "marks") or _fallback_exam_marks(analysis, source)
        rows.append(
            f"<tr><td>{_escape(source)}</td><td>{_escape(focus)}</td><td>{_escape(marks)}</td></tr>"
        )
    if not rows:
        rows.append(
            '<tr><td colspan="3" class="unknown">No past-exam sources were identified.</td></tr>'
        )
    return (
        "<section><h2>Past exams scanned</h2><table><thead><tr>"
        "<th>Source</th><th>What it tested</th><th>Scoring signals</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        + _exam_questions_html(analysis.exam_questions)
        + "</section>"
    )


def _exam_questions_html(exam_questions: tuple[PriorityExamQuestion, ...]) -> str:
    if not exam_questions:
        return ""
    rows = []
    for question in exam_questions[:40]:
        marks = f"{question.marks} marks" if question.marks else "marks not found"
        topics = ", ".join(question.topics) if question.topics else "No topic signal extracted"
        rows.append(
            "<tr>"
            f"<td>{_escape(question.source)}</td>"
            f"<td>{_escape(question.prompt)}</td>"
            f"<td>{_escape(marks)}</td>"
            f"<td>{_escape(topics)}</td>"
            "</tr>"
        )
    return (
        "<h3>Exam questions and points</h3>"
        "<table><thead><tr><th>Source</th><th>Question / prompt</th><th>Points</th>"
        "<th>Detected topics</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _payload_exam_rows(model_payload: dict[str, object] | None) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    raw_exams = model_payload.get("past_exams") if model_payload is not None else None
    if not isinstance(raw_exams, list):
        return rows
    for raw in raw_exams:
        if not _string_object_mapping(raw):
            continue
        raw_source = raw.get("source")
        if isinstance(raw_source, str) and raw_source.strip():
            rows[raw_source.strip()] = raw
    return rows


def _fallback_exam_focus(analysis: PriorityAnalysis, source: str) -> str:
    marked_topics = [
        topic.topic
        for topic in analysis.topics
        if source in topic.sources and (topic.exam_marks or topic.exam_hits)
    ]
    topics = marked_topics or [topic.topic for topic in analysis.topics if source in topic.sources]
    return ", ".join(topics[:5]) if topics else "No topic signal extracted from indexed chunks."


def _fallback_exam_marks(analysis: PriorityAnalysis, source: str) -> str:
    marked = [
        f"{topic.topic}: {topic.exam_marks}"
        for topic in analysis.topics
        if source in topic.sources and topic.exam_marks
    ]
    return ", ".join(marked[:6]) if marked else "No explicit mark values found."


def _plan_html(model_payload: dict[str, object] | None) -> str:
    plan = _payload_string_list(model_payload, "study_plan")
    unknowns = _payload_string_list(model_payload, "unknowns")
    if not plan:
        plan = [
            "Start with critical/high topics that appear in past exams or carry visible marks.",
            "Patch prerequisites before attempting exam-style questions.",
            "Use the cited source excerpts to verify every claim before moving on.",
        ]
    return "\n".join(
        (
            "<section><h2>Study plan</h2>",
            _ordered_list_html(plan),
            _list_html("Unknown or missing in indexed materials", unknowns) if unknowns else "",
            "</section>",
        )
    )


def _sources_html(analysis: PriorityAnalysis) -> str:
    sources = [*analysis.past_exam_sources, *analysis.material_sources]
    if not sources:
        return (
            '<section><h2>Sources</h2><p class="unknown">'
            "No indexed sources available.</p></section>"
        )
    items = "".join(f"<li>{_escape(source)}</li>" for source in sources)
    return f"<section><h2>Sources</h2><ul>{items}</ul></section>"


def _list_html(title: str, items: list[str]) -> str:
    if not items:
        return ""
    return (
        f"<h4>{_escape(title)}</h4><ul>"
        + "".join(f"<li>{_escape(item)}</li>" for item in items)
        + "</ul>"
    )


def _ordered_list_html(items: list[str]) -> str:
    return "<ol>" + "".join(f"<li>{_escape(item)}</li>" for item in items) + "</ol>"


def _payload_string(payload: dict[str, object] | None, key: str) -> str:
    if payload is None:
        return ""
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def _payload_string_list(payload: dict[str, object] | None, key: str) -> list[str]:
    if payload is None:
        return []
    value = payload.get(key)
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _fallback_summary(analysis: PriorityAnalysis) -> str:
    if not analysis.topics:
        return "No study concepts could be separated from the indexed materials."
    exam_topics = [topic.topic for topic in analysis.topics if topic.exam_hits or topic.exam_marks]
    if exam_topics:
        top = ", ".join(exam_topics[:3])
        return (
            f"Exam-linked priorities: {top}. Ranking puts visible exam questions and marks before "
            "lecture-only coverage."
        )
    top = ", ".join(topic.topic for topic in analysis.topics[:3])
    return (
        f"Material concepts found: {top}. No indexed past-exam hits were detected, so ranking is "
        "based only on supporting-material coverage."
    )


def _priority_report_filename() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"hephaistos-priority-{stamp}.html"


def _escape(value: str) -> str:
    return html.escape(value, quote=True)
