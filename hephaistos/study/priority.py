"""Deterministic priority analysis over indexed study materials."""

from __future__ import annotations

import html
import json
import re
import textwrap
from collections import Counter
from collections.abc import Iterable, Iterator
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

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{2,}")
_SENTENCE_RE = re.compile(r"[^.!?\n]+")
_TOPIC_PHRASE_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_+-]*(?:\s+[A-Za-z][A-Za-z0-9_+-]*){1,5}\b")
_HEADING_PREFIX_RE = re.compile(r"^(?:#+\s*|\d+(?:\.\d+)*[.)]?\s*|[-*]\s*)")
_WHITESPACE_RE = re.compile(r"\s+")
_WORD_SPLIT_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]*")
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
    }
)
_MARK_RE = re.compile(
    r"(?:\[\s*(\d{1,2})\s*(?:marks?|pts?|points?)\s*\]|"
    r"\((\d{1,2})\s*(?:marks?|pts?|points?)\)|"
    r"\b(\d{1,2})\s*(?:marks?|pts?|points?)\b)",
    re.IGNORECASE,
)
_NO_PREREQUISITE_TEXT = "No explicit prerequisite found in indexed materials."

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
        "formula",
        "not",
        "decoded",
        "image",
        "die",
        "ist",
        "und",
        "wir",
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
class PriorityTopic:
    """A locally observed priority topic."""

    topic: str
    score: float
    exam_hits: int
    exam_marks: int
    material_hits: int
    sources: tuple[str, ...]
    prerequisites: tuple[str, ...] = ()
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
    chunk_list = list(chunks)
    exam_counts: Counter[str] = Counter()
    exam_marks: Counter[str] = Counter()
    material_counts: Counter[str] = Counter()
    prerequisite_hints: dict[str, Counter[str]] = {}
    sources_by_topic: dict[str, set[str]] = {}
    evidence_by_topic: dict[str, list[PriorityTopicEvidence]] = {}
    past_exam_sources: set[str] = set()
    material_sources: set[str] = set()

    for chunk in chunk_list:
        role, _confidence, _reason = infer_material_role(chunk.source)
        if role == "past_exam":
            past_exam_sources.add(chunk.source)
        else:
            material_sources.add(chunk.source)
        terms = set(_topic_terms(chunk.heading, chunk.text))
        if not terms:
            continue
        prerequisites: list[str] = []
        if role == "past_exam":
            target = exam_counts
            marks = _mark_weight(chunk.text)
        else:
            target = material_counts
            marks = 0
            prerequisites = _explicit_prerequisites(chunk.text)
        for term in terms:
            target[term] += 1
            if marks:
                exam_marks[term] += marks
            sources_by_topic.setdefault(term, set()).add(chunk.source)
            evidence_by_topic.setdefault(term, [])
            if len(evidence_by_topic[term]) < 4:
                evidence_by_topic[term].append(_topic_evidence(chunk, term, marks))
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
                evidence=tuple(evidence_by_topic.get(term, ())),
            )
        )

    topics.sort(key=lambda topic: (-topic.score, -topic.exam_marks, -topic.exam_hits, topic.topic))
    topics = _collapse_component_topics(topics)
    return PriorityAnalysis(
        topics=tuple(topics[:limit]),
        past_exam_sources=tuple(sorted(past_exam_sources)),
        material_sources=tuple(sorted(material_sources)),
        chunks=tuple(chunk_list),
    )


def _topic_terms(heading: str, text: str) -> list[str]:
    raw = f"{heading}\n{text}"
    seen: set[str] = set()
    terms: list[str] = []
    for candidate in _candidate_topic_phrases(raw):
        if _valid_topic(candidate) and candidate not in seen:
            terms.append(candidate)
            seen.add(candidate)
    return terms


def _candidate_topic_phrases(raw: str) -> Iterator[str]:
    yield from _heading_candidates(raw)
    for phrase_match in _TOPIC_PHRASE_RE.finditer(raw):
        words = [word.lower() for word in _WORD_SPLIT_RE.findall(phrase_match.group(0))]
        useful = [word for word in words if word not in _STOPWORDS and not word.isdigit()]
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
        if not cleaned or len(cleaned) > 90:
            continue
        words = [word.lower() for word in _WORD_SPLIT_RE.findall(cleaned)]
        useful = [word for word in words if word not in _STOPWORDS and not word.isdigit()]
        if 2 <= len(useful) <= 6:
            yield " ".join(useful)


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


def _topic_evidence(chunk: PriorityChunk, term: str, marks: int) -> PriorityTopicEvidence:
    return PriorityTopicEvidence(
        source=chunk.source,
        heading=chunk.heading,
        excerpt=_topic_excerpt(chunk.text, term),
        marks=marks,
    )


def _topic_excerpt(text: str, term: str, *, max_chars: int = 260) -> str:
    normalized = _WHITESPACE_RE.sub(" ", text).strip()
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
      "study_actions": ["concrete action grounded in the material"],
      "prerequisites": ["required prerequisite found in evidence"]
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
indexed material excerpts. Do not add outside facts. If the material does not specify a detail,
write that it is unknown. Favor exact topic names from the evidence over filename fragments.
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
    for idx, chunk in enumerate(chunks, start=1):
        role, _confidence, _reason = infer_material_role(chunk.source)
        evidence_lines.append(
            "\n".join(
                (
                    f"Evidence {idx}",
                    f"Source: {chunk.source}",
                    f"Role: {role}",
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
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Hephaistos Priority Report</title>
          <style>{_priority_css()}</style>
        </head>
        <body>
          <main>
            <header class="hero">
              <p class="eyebrow">Hephaistos priority</p>
              <h1>Study priority report</h1>
              <p>{_escape(summary)}</p>
              {_focus_html(focus)}
              <p class="meta">Generated {_report_timestamp()}. Source-grounded from indexed
              materials only.</p>
            </header>
            {_topics_html(analysis, model_payload)}
            {_past_exams_html(analysis, model_payload)}
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
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; color: #111; background: #fff; }
main { width: min(1120px, calc(100% - 40px)); margin: 0 auto; padding: 42px 0 64px; }
.hero {
  border: 2px solid #111;
  padding: 28px;
  margin-bottom: 28px;
  box-shadow: 8px 8px 0 #e8874f;
}
.eyebrow {
  color: #9b4a2e;
  text-transform: uppercase;
  letter-spacing: .12em;
  font-weight: 800;
  margin: 0 0 8px;
}
h1 { font-size: clamp(2.2rem, 5vw, 4.2rem); line-height: .95; margin: 0 0 18px; }
h2 {
  font-size: 1.7rem;
  margin: 34px 0 14px;
  border-bottom: 3px solid #111;
  padding-bottom: 8px;
}
h3 { font-size: 1.2rem; margin: 0 0 8px; }
p { line-height: 1.55; }
.meta, .source, .evidence, .unknown { color: #444; font-size: .94rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }
.card { border: 1.5px solid #111; padding: 18px; break-inside: avoid; background: #fff; }
.badge {
  display: inline-block;
  border: 1px solid #111;
  padding: 3px 8px;
  font-size: .78rem;
  font-weight: 800;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.critical { background: #111; color: #fff; }
.high { background: #e8874f; }
.medium { background: #f6d9c6; }
.low { background: #eee; }
ul { padding-left: 1.2rem; }
li { margin: 6px 0; }
blockquote {
  margin: 10px 0 0;
  padding: 10px 12px;
  border-left: 4px solid #e8874f;
  background: #fafafa;
}
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #111; padding: 10px; vertical-align: top; text-align: left; }
th { background: #f6d9c6; }
@media print {
  main { width: 100%; padding: 0; }
  .hero { box-shadow: none; }
  .card { page-break-inside: avoid; }
}
""".strip()


def _focus_html(focus: str) -> str:
    if not focus:
        return ""
    return f'<p class="meta"><strong>Focus:</strong> {_escape(focus)}</p>'


def _topics_html(analysis: PriorityAnalysis, model_payload: dict[str, object] | None) -> str:
    payload_topics = _payload_topics(model_payload)
    cards: list[str] = []
    for index, topic in enumerate(analysis.topics, start=1):
        payload = payload_topics.get(topic.topic.lower())
        importance = _topic_importance(topic, payload)
        why = _payload_string(payload, "why") or _fallback_topic_why(topic)
        actions = _payload_string_list(payload, "study_actions") or _fallback_study_actions(topic)
        prerequisites = _payload_string_list(payload, "prerequisites") or list(topic.prerequisites)
        cards.append(
            "\n".join(
                (
                    '<article class="card">',
                    _importance_badge(index, importance),
                    f"<h3>{_escape(topic.topic)}</h3>",
                    f"<p>{_escape(why)}</p>",
                    _topic_metric_html(topic),
                    _list_html("What to study", actions),
                    _list_html("Prerequisites", prerequisites or [_NO_PREREQUISITE_TEXT]),
                    _topic_evidence_html(topic),
                    "</article>",
                )
            )
        )
    if not cards:
        cards.append('<p class="unknown">No recurring indexed topics were found.</p>')
    card_html = "".join(cards)
    return f'<section><h2>Topics to prioritize</h2><div class="grid">{card_html}</div></section>'


def _importance_badge(index: int, importance: str) -> str:
    escaped = _escape(importance)
    return f'<span class="badge {escaped}">#{index} {escaped}</span>'


def _topic_metric_html(topic: PriorityTopic) -> str:
    metrics = (
        f"Score {topic.score:.1f} · exam hits {topic.exam_hits} · "
        f"exam marks {topic.exam_marks} · material hits {topic.material_hits}"
    )
    return f'<p class="meta">{_escape(metrics)}</p>'


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
        parts.append(f"visible past-exam marks total {topic.exam_marks}")
    if topic.exam_hits:
        parts.append(f"appears in {topic.exam_hits} past-exam excerpt(s)")
    if topic.material_hits:
        parts.append(f"appears in {topic.material_hits} supporting-material excerpt(s)")
    if not parts:
        return "Observed in the indexed material excerpts."
    return "Prioritize because it " + " and ".join(parts) + "."


def _fallback_study_actions(topic: PriorityTopic) -> list[str]:
    actions = [f"Explain {topic.topic} from memory, then verify against the cited excerpts."]
    if topic.exam_marks or topic.exam_hits:
        actions.append("Practice the past-exam style prompts where this topic appears.")
    if topic.prerequisites:
        actions.append(f"Check prerequisites first: {', '.join(topic.prerequisites[:3])}.")
    return actions


def _topic_evidence_html(topic: PriorityTopic) -> str:
    items = []
    for evidence in topic.evidence[:3]:
        marks = f" · {evidence.marks} marks" if evidence.marks else ""
        heading = f" · {evidence.heading}" if evidence.heading else ""
        items.append(
            f"<blockquote><p>{_escape(evidence.excerpt)}</p>"
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
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></section>"
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
    topics = [topic.topic for topic in analysis.topics if source in topic.sources][:5]
    return ", ".join(topics) if topics else "No topic signal extracted from indexed chunks."


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
        return "No recurring priority topics were found in the indexed materials."
    top = ", ".join(topic.topic for topic in analysis.topics[:3])
    return (
        f"Top indexed priorities are {top}. Scores combine past-exam appearances, "
        "visible marks, and supporting-material coverage."
    )


def _priority_report_filename() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"hephaistos-priority-{stamp}.html"


def _escape(value: str) -> str:
    return html.escape(value, quote=True)
