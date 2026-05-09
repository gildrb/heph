"""Deterministic priority analysis over indexed study materials."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import pairwise
from typing import Protocol

from hephaistos.materials import infer_material_role

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{2,}")
_SENTENCE_RE = re.compile(r"[^.!?\n]+")
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
    }
)
_MARK_RE = re.compile(
    r"(?:\[\s*(\d{1,2})\s*(?:marks?|pts?|points?)\s*\]|"
    r"\((\d{1,2})\s*(?:marks?|pts?|points?)\)|"
    r"\b(\d{1,2})\s*(?:marks?|pts?|points?)\b)",
    re.IGNORECASE,
)
_STOPWORDS = frozenset(
    {
        "about",
        "after",
        "also",
        "and",
        "answer",
        "are",
        "against",
        "basic",
        "basics",
        "because",
        "before",
        "brief",
        "briefly",
        "calculate",
        "connected",
        "define",
        "depend",
        "depends",
        "describe",
        "does",
        "each",
        "exam",
        "explain",
        "following",
        "from",
        "for",
        "give",
        "given",
        "have",
        "identify",
        "into",
        "marks",
        "one",
        "past",
        "question",
        "questions",
        "show",
        "state",
        "that",
        "the",
        "their",
        "then",
        "this",
        "through",
        "two",
        "using",
        "use",
        "uses",
        "what",
        "when",
        "where",
        "which",
        "with",
        "your",
    }
)


class PriorityChunk(Protocol):
    """Minimal chunk shape needed for local priority analysis."""

    source: str
    heading: str
    text: str


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


@dataclass(frozen=True, slots=True)
class PriorityAnalysis:
    """Deterministic priority scan result."""

    topics: tuple[PriorityTopic, ...]
    past_exam_sources: tuple[str, ...]
    material_sources: tuple[str, ...]

    def render_for_prompt(self, *, limit: int = 6) -> str:
        """Render concise context for the model-facing priority request."""
        if not self.topics:
            return "Local priority scan: no recurring indexed topics were found."

        lines = ["Local priority scan from indexed materials:"]
        if self.past_exam_sources:
            lines.append(f"- Past exams scanned: {', '.join(self.past_exam_sources[:5])}")
        if self.material_sources:
            lines.append(f"- Supporting materials scanned: {', '.join(self.material_sources[:5])}")
        lines.append("- Candidate priorities:")
        for topic in self.topics[:limit]:
            sources = ", ".join(topic.sources[:3])
            prerequisites = (
                f"; prerequisites to check: {', '.join(topic.prerequisites[:3])}"
                if topic.prerequisites
                else ""
            )
            lines.append(
                f"  - {topic.topic}: score {topic.score:.1f}, "
                f"exam hits {topic.exam_hits}, exam marks {topic.exam_marks}, "
                f"material hits {topic.material_hits}; "
                f"sources: {sources}{prerequisites}"
            )
        return "\n".join(lines)


def analyze_priority(chunks: Iterable[PriorityChunk], *, limit: int = 8) -> PriorityAnalysis:
    """Rank recurring topics, weighting past-exam occurrences most heavily."""
    exam_counts: Counter[str] = Counter()
    exam_marks: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    prerequisite_hints: dict[str, Counter[str]] = {}
    sources_by_topic: dict[str, set[str]] = {}
    past_exam_sources: set[str] = set()
    material_sources: set[str] = set()

    for chunk in chunks:
        role, _confidence, _reason = infer_material_role(chunk.source)
        terms = set(_topic_terms(chunk.heading, chunk.text))
        if not terms:
            continue
        prerequisites: list[str] = []
        if role == "past_exam":
            past_exam_sources.add(chunk.source)
            target = exam_counts
            marks = _mark_weight(chunk.text)
        else:
            material_sources.add(chunk.source)
            target = material_counts
            marks = 0
            prerequisites = _explicit_prerequisites(chunk.text)
        for term in terms:
            target[term] += 1
            if marks:
                exam_marks[term] += marks
            sources_by_topic.setdefault(term, set()).add(chunk.source)
        if role != "past_exam":
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
        score = exam_hits * 3.0 + marks * 0.4 + material_hits
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
            )
        )

    topics.sort(key=lambda topic: (-topic.score, -topic.exam_marks, -topic.exam_hits, topic.topic))
    topics = _collapse_component_topics(topics)
    return PriorityAnalysis(
        topics=tuple(topics[:limit]),
        past_exam_sources=tuple(sorted(past_exam_sources)),
        material_sources=tuple(sorted(material_sources)),
    )


def _topic_terms(heading: str, text: str) -> list[str]:
    raw = f"{heading}\n{text}"
    tokens = [
        token.lower()
        for token in _TOKEN_RE.findall(raw)
        if token.lower() not in _STOPWORDS and not token.isdigit()
    ]
    terms = list(tokens)
    for left, right in pairwise(tokens):
        if left != right:
            terms.append(f"{left} {right}")
    return terms


def _collapse_component_topics(topics: list[PriorityTopic]) -> list[PriorityTopic]:
    collapsed: list[PriorityTopic] = []
    for topic in topics:
        if " " not in topic.topic and _covered_by_phrase(topic, topics):
            continue
        collapsed.append(topic)
    return collapsed


def _covered_by_phrase(topic: PriorityTopic, topics: list[PriorityTopic]) -> bool:
    topic_words = frozenset(topic.topic.split())
    for candidate in topics:
        if candidate.topic not in _KNOWN_TOPIC_PHRASES:
            continue
        if topic_words.isdisjoint(candidate.topic.split()):
            continue
        if (
            candidate.exam_hits == topic.exam_hits
            and candidate.exam_marks == topic.exam_marks
            and candidate.material_hits == topic.material_hits
            and candidate.sources == topic.sources
        ):
            return True
    return False


def _explicit_prerequisites(text: str) -> list[str]:
    terms: list[str] = []
    for line in text.splitlines():
        if not re.search(r"\bprerequisites?\b", line, flags=re.IGNORECASE):
            continue
        _label, _sep, rest = line.partition(":")
        raw = rest or line
        terms.extend(
            token.lower()
            for token in _TOKEN_RE.findall(raw)
            if token.lower() not in _STOPWORDS and not token.isdigit()
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
            token.lower()
            for token in _TOKEN_RE.findall(after)
            if token.lower() not in _STOPWORDS and not token.isdigit()
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
        for group in match.groups():
            if group is not None:
                marks.append(int(group))
                break
    return max(marks, default=0)


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
