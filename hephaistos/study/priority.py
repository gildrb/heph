"""Deterministic priority analysis over indexed materials."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, Self

from hephaistos._types import is_string_mapping, parse_json_object_fragment
from hephaistos.materials import infer_material_role_from_text, material_display_name
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.runtime import (
    ChatConfig,
    Conversation,
    EngineError,
    RetryConfig,
    has_configured_access,
    stream_completion,
)
from hephaistos.terminal.palette import LIGHT_THEME

_LETTER_RE = r"[^\W\d_]"
_WORD_BODY_RE = r"[\w+-]"
_TOKEN_RE = re.compile(rf"{_LETTER_RE}{_WORD_BODY_RE}{{2,}}")
_SENTENCE_RE = re.compile(r"[^.!?\n]+")
_TOPIC_PHRASE_RE = re.compile(
    rf"\b{_LETTER_RE}{_WORD_BODY_RE}*(?:\s+{_LETTER_RE}{_WORD_BODY_RE}*){{1,5}}\b"
)
_QUESTION_START_RE = re.compile(
    rf"\b(?:aufgabe|question|problem|q)\s*\.?\s*\d+{_LETTER_RE}?\b",
    re.IGNORECASE,
)
_SUBQUESTION_START_RE = re.compile(
    rf"(?:(?<=\n)\s*(?:\({_LETTER_RE}\)|{_LETTER_RE}\))|"
    rf"(?<!{_LETTER_RE})(?:\({_LETTER_RE}\))\s+|"
    rf"(?<=\n)\s*teilaufgabe\s+{_LETTER_RE}\b)",
    re.IGNORECASE,
)
_PROMPT_TOPIC_RE = re.compile(
    r"\b(?:"
    r"analyze|berechnen|calculate|compare|compute|define|derive|describe|discuss|"
    r"evaluate|explain|prove|show|sketch|state|untersuchen"
    r")\b\s+(?P<tail>[^.?!:\n]{3,180})",
    re.IGNORECASE,
)
_PROMPT_TOPIC_SPLIT_RE = re.compile(r"\s+(?:and|und|or|oder)\s+|[,;]")
_HEADING_PREFIX_RE = re.compile(r"^(?:#+\s*|\d+(?:\.\d+)*[.)]?\s*|[-*]\s*)")
_WHITESPACE_RE = re.compile(r"\s+")
_WORD_SPLIT_RE = re.compile(rf"{_LETTER_RE}{_WORD_BODY_RE}*")
_BOILERPLATE_LINE_RE = re.compile(
    r"\b(?:"
    r"all\s+rights\s+reserved|candidate\s+number|copyright|course|department|"
    r"e-?mail|exam\s+seat|faculty|institute|instructor|lecturer|office\s+hours|"
    r"prof(?:essor)?|school|semester|student\s+id|student\s+name|student\s+number|"
    r"term|university|aufgabennummer|dozent|dozentin|hochschule|matrikelnummer|"
    r"nachname|sommersemester|universität|universitaet|vorname|"
    r"wintersemester"
    r")\b|@",
    re.IGNORECASE,
)
_PAGE_OR_SLIDE_LINE_RE = re.compile(r"\b(?:page|slide|folie)\s+\d+\b", re.IGNORECASE)
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
_TOPIC_INTRO_RE = re.compile(
    r"\b(?:"
    r"definition|defined|definiert|bezeichnet|bezeichnen|heisst|heißt|nennt|setzen|"
    r"we\s+call|we\s+define|is\s+called|is\s+defined"
    r")\b",
    re.IGNORECASE,
)
_DEFINITION_SUBJECT_RE = re.compile(
    rf"\b(?P<term>(?:the|a|an|der|die|das|den|dem|ein|eine|einen|einer)?\s*"
    rf"{_LETTER_RE}{_WORD_BODY_RE}{{2,}}"
    rf"(?:\s+{_LETTER_RE}{_WORD_BODY_RE}{{2,}}){{0,4}})"
    r"\s+(?:is|are|ist|sind|means|denotes|bezeichnet|heisst|heißt|nennt|"
    r"refers\s+to)\b",
    re.IGNORECASE,
)
_DEFINED_OBJECT_RE = re.compile(
    rf"\b(?:the|a|an|der|die|das|den|dem|ein|eine|einen|einer)\s+"
    rf"(?P<term>{_LETTER_RE}{_WORD_BODY_RE}{{2,}}"
    rf"(?:\s+{_LETTER_RE}{_WORD_BODY_RE}{{2,}}){{0,4}})"
    r"\b[^.?!]{0,80}\b(?:defined|definiert|definition)\b",
    re.IGNORECASE,
)
_DEFINITION_VERB_RE = re.compile(
    r"\b(?:is|are|ist|sind|means|denotes|bezeichnet|heisst|heißt|nennt|"
    r"refers\s+to|defined|definiert)\b",
    re.IGNORECASE,
)
_DEFINITION_TERM_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "der",
        "die",
        "das",
        "den",
        "dem",
        "ein",
        "eine",
        "einen",
        "einer",
        "eines",
        "of",
        "von",
        "in",
        "im",
        "on",
        "for",
        "für",
        "to",
        "als",
    }
)
_MARK_RE = re.compile(
    r"(?:\[\s*(\d{1,2})\s*(?:marks?|pts?|points?|punkte?)\s*\]|"
    r"\((\d{1,2})\s*(?:marks?|pts?|points?|punkte?)\)|"
    r"\b(\d{1,2})\s*(?:marks?|pts?|points?|punkte?)\b|"
    r"\b(?:marks?|pts?|points?|punkte?)\s*[:=]\s*(\d{1,2})\b)",
    re.IGNORECASE,
)
_RAW_METRIC_RE = re.compile(
    r"\b(?:Score\s+\d|exam hits|exam marks|material hits)\b",
    re.IGNORECASE,
)
_FORBIDDEN_REPORT_RE = re.compile(
    r"Score\s+\d|exam hits|exam marks|material hits|"
    r"formula-not-decoded|image not decoded|ocr noise|"
    r"student name|student id|candidate number|exam seat|"
    r"matrikelnummer|aufgabennummer",
    re.IGNORECASE,
)
_LATEX_ENGINE_NAMES = ("latexmk", "lualatex", "xelatex", "pdflatex", "tectonic")
_LATEX_COMPILE_TIMEOUT_SECONDS = 30
_LATEX_MATH_COMMAND_RE = re.compile(r"\\([A-Za-z]+|.)")
_LATEX_MATH_UNSAFE_CHAR_RE = re.compile(r"[%#&~]")
_ALLOWED_LATEX_MATH_COMMANDS = frozenset(
    {
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "varepsilon",
        "zeta",
        "eta",
        "theta",
        "vartheta",
        "iota",
        "kappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "pi",
        "rho",
        "sigma",
        "tau",
        "upsilon",
        "phi",
        "varphi",
        "chi",
        "psi",
        "omega",
        "Gamma",
        "Delta",
        "Theta",
        "Lambda",
        "Xi",
        "Pi",
        "Sigma",
        "Upsilon",
        "Phi",
        "Psi",
        "Omega",
        "cdot",
        "times",
        "div",
        "pm",
        "mp",
        "le",
        "leq",
        "ge",
        "geq",
        "neq",
        "approx",
        "sim",
        "equiv",
        "propto",
        "to",
        "rightarrow",
        "leftarrow",
        "Rightarrow",
        "Leftarrow",
        "leftrightarrow",
        "in",
        "notin",
        "subset",
        "subseteq",
        "supset",
        "supseteq",
        "cup",
        "cap",
        "emptyset",
        "forall",
        "exists",
        "nabla",
        "partial",
        "infty",
        "sum",
        "prod",
        "int",
        "lim",
        "log",
        "ln",
        "exp",
        "sin",
        "cos",
        "tan",
        "min",
        "max",
        "arg",
        "sqrt",
        "frac",
        "left",
        "right",
        "cdots",
        "ldots",
        "dots",
        "text",
    }
)
_ALLOWED_LATEX_MATH_SYMBOL_COMMANDS = frozenset({",", ";", ":", "!", " ", "_"})
_WEB_PREREQ_ENV = "HEPHAISTOS_PRIORITY_WEB_PREREQS"
_WEB_PREREQ_TIMEOUT = 8
_WEB_PREREQ_TOPICS = 6
_WEB_PREREQ_RESULTS = 4
_WEB_PREREQ_USER_AGENT = "Heph/0.1 priority prerequisites"
_WEB_PREREQ_SEARCH_URL = "https://duckduckgo.com/html/"
_MODEL_HEARTBEAT_SECONDS = 10.0
_MODEL_STREAM_PROGRESS_SECONDS = 8.0

_STOPWORDS = frozenset(
    {
        "about",
        "achtung",
        "aber",
        "after",
        "also",
        "and",
        "andernfalls",
        "answer",
        "are",
        "against",
        "als",
        "analyze",
        "at",
        "auf",
        "aufgabe",
        "aufgabennummer",
        "aus",
        "basic",
        "basics",
        "because",
        "before",
        "beispiel",
        "beispiele",
        "berechnen",
        "bestehen",
        "bestimmen",
        "bestimmten",
        "brief",
        "briefly",
        "bzw",
        "calculate",
        "can",
        "cheat-sheets",
        "compare",
        "compute",
        "connected",
        "define",
        "defined",
        "depend",
        "depends",
        "derive",
        "describe",
        "definition",
        "definiert",
        "der",
        "des",
        "dann",
        "das",
        "discuss",
        "dokumente",
        "does",
        "each",
        "ein",
        "eine",
        "einer",
        "eines",
        "exam",
        "examination",
        "es",
        "erste",
        "erwartungsgemäß",
        "euro",
        "falls",
        "explain",
        "folien",
        "folgenden",
        "folgt",
        "following",
        "from",
        "for",
        "für",
        "give",
        "given",
        "gilt",
        "called",
        "denotes",
        "handschriftlich",
        "have",
        "hilfsmittel",
        "identify",
        "ihre",
        "insbesondere",
        "in",
        "into",
        "is",
        "marks",
        "maximal",
        "midterm",
        "means",
        "muss",
        "nach",
        "nicht",
        "notizen",
        "n-te",
        "one",
        "oder",
        "past",
        "points",
        "pro",
        "problem",
        "pts",
        "question",
        "questions",
        "bezeichne",
        "bezeichnen",
        "bezeichnet",
        "setzen",
        "show",
        "sketch",
        "sn",
        "state",
        "sowie",
        "that",
        "the",
        "their",
        "then",
        "this",
        "through",
        "two",
        "untersuchen",
        "using",
        "use",
        "uses",
        "taschenrechner",
        "von",
        "what",
        "when",
        "where",
        "which",
        "with",
        "your",
        "zur",
        "zugelassen",
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
        "januar",
        "februar",
        "märz",
        "maerz",
        "mai",
        "juni",
        "juli",
        "oktober",
        "dezember",
        "formula",
        "ihnen",
        "jeweils",
        "klausur",
        "not",
        "decoded",
        "image",
        "ocr",
        "noise",
        "ohne",
        "punkte",
        "punkten",
        "punkt",
        "sei",
        "seien",
        "sommersemester",
        "sie",
        "sind",
        "die",
        "ist",
        "und",
        "universität",
        "viel",
        "w",
        "wintersemester",
        "wir",
        "wunschen",
        "wünschen",
        "x0",
        "wenn",
        "verfasste",
        "viele",
        "wie",
        "matrikelnummer",
        "nachname",
        "nschen",
        "vorname",
        "vorlesung",
        "article",
        "course",
        "example",
        "examples",
        "guide",
        "implementation",
        "introduction",
        "learn",
        "learning",
        "lecture",
        "lectures",
        "notes",
        "overview",
        "should",
        "tutorial",
        "understand",
        "understanding",
        "ur",
    }
)
_BOILERPLATE_TOPIC_PHRASES = frozenset(
    {
        "a f x in e",
        "chapter",
        "chapters",
        "concept",
        "concepts",
        "definitions",
        "administrative block",
        "administrative header",
        "administrative header sommersemester",
        "administrative line",
        "administrative title sommersemester",
        "administrative unit",
        "exercises",
        "problems",
        "proof",
        "proofs",
        "theorem",
        "theorems",
        "topics",
        "ohne beweis",
    }
)
_SYMBOLIC_TOPIC_TOKEN_RE = re.compile(
    rf"^(?:{_LETTER_RE}{{1,2}}\d*|\d+|{_LETTER_RE}-{_LETTER_RE})$"
)


class PriorityChunk(Protocol):
    source: str
    index: int
    char_start: int
    char_end: int
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
PriorityProgressReporter = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class PriorityExamQuestion:
    source: str
    prompt: str
    marks: int
    topics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PrioritySource:
    source_id: str
    path: str
    role: str


@dataclass(frozen=True, slots=True)
class PriorityTopic:
    topic: str
    score: float
    exam_hits: int
    exam_marks: int
    material_hits: int
    sources: tuple[str, ...]
    exam_source_frequency: int = 0
    supporting_material_coverage: int = 0
    confidence: float = 0.0
    prerequisites: tuple[str, ...] = ()
    web_prerequisites: tuple[PriorityWebPrerequisite, ...] = ()
    evidence: tuple[PriorityTopicEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class PriorityCheatSheetTopic:
    title: str
    tier: str
    source_ids: tuple[str, ...]
    prerequisites: tuple[str, ...]
    definitions: tuple[str, ...]
    formulas: tuple[str, ...]
    procedures: tuple[str, ...]
    exam_tasks: tuple[str, ...]
    pitfalls: tuple[str, ...]
    uncertainty: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PriorityCheatSheet:
    title: str
    generated_at: str
    focus: str
    sources: tuple[PrioritySource, ...]
    topics: tuple[PriorityCheatSheetTopic, ...]
    exam_questions: tuple[PriorityExamQuestion, ...]
    uncertainties: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PriorityVerificationReport:
    extraction_ok: bool
    priority_ok: bool
    source_support_ok: bool
    latex_ok: bool
    pdf_ok: bool
    anti_regression_ok: bool
    autopilot_ok: bool
    issues: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (
            self.extraction_ok
            and self.priority_ok
            and self.source_support_ok
            and self.latex_ok
            and self.pdf_ok
            and self.anti_regression_ok
            and self.autopilot_ok
        )


@dataclass(frozen=True, slots=True)
class PriorityReport:
    path: Path
    used_model: bool
    topic_count: int
    source_count: int
    tex_path: Path | None = None
    sidecar_path: Path | None = None
    verification: PriorityVerificationReport | None = None


class PriorityPdfError(RuntimeError):
    pass


class PriorityPdfCompiler(Protocol):
    def compile(self, tex_path: Path, pdf_path: Path) -> None: ...


@dataclass(frozen=True, slots=True)
class PriorityAnalysis:
    topics: tuple[PriorityTopic, ...]
    past_exam_sources: tuple[str, ...]
    material_sources: tuple[str, ...]
    chunks: tuple[PriorityChunk, ...] = ()
    exam_questions: tuple[PriorityExamQuestion, ...] = ()

    def render_for_prompt(self, *, limit: int = 6) -> str:
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
            prerequisites = ""
            if topic.prerequisites:
                prerequisites = f"; prerequisites to check: {', '.join(topic.prerequisites[:3])}"
            elif topic.web_prerequisites:
                terms = ", ".join(item.term for item in topic.web_prerequisites[:3])
                prerequisites = f"; web-backed prerequisite hints: {terms}"
            if topic.exam_marks:
                exam_signal = f"{topic.exam_hits} exam hit(s), {topic.exam_marks} visible mark(s)"
            elif topic.exam_hits:
                exam_signal = f"{topic.exam_hits} exam hit(s), no explicit marks found"
            else:
                exam_signal = "No past-exam hit found"
            lines.append(
                f"  - {topic.topic}: {priority_tier(topic)}; "
                f"{exam_signal}; "
                f"sources: {sources}{prerequisites}"
            )
        return "\n".join(lines)


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
    role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
    if role == "past_exam":
        _record_exam_chunk(state, chunk, chunk_label, chunk_started_at, progress)
        return
    _record_material_chunk(state, chunk, role, chunk_label, chunk_started_at, progress)


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
) -> None:
    state.past_exam_sources.add(chunk.source)
    questions = tuple(_exam_questions(chunk.source, tuple(_exam_sections(chunk.text))))
    for question in questions:
        state.record_exam_question(question)
    topic_signal_count = len({term for question in questions for term in question.topics})
    _emit_progress(
        progress,
        f"Read {chunk_label}: role past_exam, {len(questions)} question(s), "
        f"{topic_signal_count} topic signal(s) in {_format_elapsed_since(chunk_started_at)}.",
    )


def _record_material_chunk(
    state: _PriorityScanState,
    chunk: PriorityChunk,
    role: str,
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
        f"Read {chunk_label}: role {role}, {len(terms)} topic signal(s) in "
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


def _emit_progress(progress: PriorityProgressReporter | None, message: str) -> None:
    if progress is not None:
        progress(message)


class _ProgressHeartbeat:
    def __init__(
        self,
        progress: PriorityProgressReporter | None,
        message: str,
        *,
        interval_seconds: float = _MODEL_HEARTBEAT_SECONDS,
    ) -> None:
        self._progress = progress
        self._message = message
        self._interval_seconds = interval_seconds
        self._started_at = time.perf_counter()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> Self:
        if self._progress is None:
            return self
        self._thread = threading.Thread(target=self._run, name="priority-progress", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.stop()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.2)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(self._interval_seconds):
            _emit_progress(
                self._progress,
                f"{self._message} ({_format_elapsed_since(self._started_at)} elapsed).",
            )


def _format_elapsed_since(started_at: float) -> str:
    seconds = max(0.0, time.perf_counter() - started_at)
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.1f}s"


def _write_text_artifact(
    path: Path,
    text: str,
    *,
    progress: PriorityProgressReporter | None,
    label: str,
) -> None:
    started_at = time.perf_counter()
    path.write_text(text, encoding="utf-8")
    _emit_progress(
        progress,
        f"Wrote {label} {path} ({len(text.encode('utf-8'))} bytes) "
        f"in {_format_elapsed_since(started_at)}.",
    )


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


def _topic_terms(heading: str, text: str) -> list[str]:
    raw = f"{heading}\n{text}"
    seen: set[str] = set()
    terms: list[str] = []
    candidates = [*_heading_candidates(heading), *_candidate_topic_phrases(raw)]
    for candidate in candidates:
        canonical = " ".join(candidate.casefold().split())
        if _valid_topic(canonical) and canonical not in seen:
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
        enriched.append(replace(topic, web_prerequisites=web_prerequisites))
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
        useful = [
            word for word in _useful_topic_words(phrase_match.group(0)) if word not in topic_words
        ]
        if not useful:
            continue
        term = " ".join(useful[:3])
        if term not in seen:
            seen.add(term)
            yield term
    for word_match in _TOKEN_RE.finditer(text):
        term = word_match.group(0).lower()
        if term in _STOPWORDS or term in topic_words or term in seen:
            continue
        seen.add(term)
        yield term


def _candidate_topic_phrases(raw: str) -> Iterator[str]:
    topic_text = _topic_candidate_text(raw)
    yield from _definition_head_candidates(topic_text)
    yield from _heading_candidates(topic_text)
    yield from _prompt_topic_candidates(topic_text)
    for phrase_match in _TOPIC_PHRASE_RE.finditer(topic_text):
        phrase = phrase_match.group(0)
        parts = [
            part.strip()
            for part in _PROMPT_TOPIC_SPLIT_RE.split(phrase)
            if part.strip() and part.strip() != phrase
        ]
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
    for line in raw.splitlines():
        cleaned = _HEADING_PREFIX_RE.sub("", line.strip())
        if not cleaned or len(cleaned) > 90 or _is_boilerplate_line(cleaned):
            continue
        parts = [
            part.strip()
            for part in _PROMPT_TOPIC_SPLIT_RE.split(cleaned)
            if part.strip() and part.strip() != cleaned
        ]
        if parts:
            for part in parts:
                yield from _topic_part_candidates(part)
            continue
        useful = _useful_topic_words(cleaned)
        if 2 <= len(useful) <= 6:
            yield " ".join(useful)
        elif len(useful) == 1 and len(useful[0]) >= 5:
            yield useful[0]


def _prompt_topic_candidates(text: str) -> Iterator[str]:
    for prompt_match in _PROMPT_TOPIC_RE.finditer(text):
        for part in _PROMPT_TOPIC_SPLIT_RE.split(prompt_match.group("tail")):
            useful = _useful_topic_words(part)
            if len(useful) >= 2:
                if len(useful[0]) >= 5:
                    yield useful[0]
                if len(useful) > 2:
                    yield " ".join(useful[:2])
                yield " ".join(useful[:3])
            elif len(useful) == 1 and len(useful[0]) >= 5:
                yield useful[0]


def _content_phrase_candidates(phrase: str, words: list[str]) -> Iterator[str]:
    if len(words) < 2:
        return
    first_token_match = _WORD_SPLIT_RE.search(phrase)
    if (
        first_token_match is not None
        and first_token_match.group(0)[:1].isupper()
        and first_token_match.group(0).lower() == words[0]
        and len(words[0]) >= 5
        and not _SYMBOLIC_TOPIC_TOKEN_RE.fullmatch(words[1])
    ):
        yield words[0]
    for size in (2, 3):
        for start in range(len(words) - size + 1):
            yield " ".join(words[start : start + size])


def _definition_head_candidates(text: str) -> Iterator[str]:
    seen: set[str] = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        for term in _definition_terms_from_line(line):
            if not term or term in seen:
                continue
            seen.add(term)
            yield term


def _definition_terms_from_line(line: str) -> Iterator[str]:
    for match in _DEFINITION_VERB_RE.finditer(line):
        prefix = line[: match.start()].strip(" .:-;")
        if prefix:
            yield _definition_term_candidate(prefix)
    for pattern in (_DEFINITION_SUBJECT_RE, _DEFINED_OBJECT_RE):
        for match in pattern.finditer(line):
            yield _definition_term_candidate(match.group("term"))


def _definition_term_candidate(raw: str) -> str:
    words = [word.lower() for word in _WORD_SPLIT_RE.findall(raw)]
    kept: list[str] = []
    for word in words:
        if word in _DEFINITION_TERM_STOPWORDS:
            if kept:
                break
            continue
        if word in _STOPWORDS:
            if kept:
                break
            continue
        kept.append(word)
        if len(kept) >= 3:
            break
    return " ".join(kept)


def _useful_topic_words(text: str) -> list[str]:
    return [
        word.lower()
        for word in _WORD_SPLIT_RE.findall(text)
        if word.lower() not in _STOPWORDS and not word.isdigit()
    ]


def _topic_candidate_text(raw: str) -> str:
    lines: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        kept_units = [
            unit.strip()
            for unit in re.split(r"(?<=[.!?])\s+", line)
            if unit.strip() and not _is_boilerplate_line(unit)
        ]
        lines.extend(kept_units)
    return "\n".join(lines)


def _is_boilerplate_line(line: str) -> bool:
    cleaned = _HEADING_PREFIX_RE.sub("", line.strip())
    if not cleaned:
        return True
    return bool(
        _BOILERPLATE_LINE_RE.search(cleaned)
        or _PAGE_OR_SLIDE_LINE_RE.search(cleaned)
        or _looks_like_person_name_sentence(cleaned)
    )


def _looks_like_person_name_sentence(text: str) -> bool:
    if not text.endswith("."):
        return False
    tokens = re.findall(rf"{_LETTER_RE}(?:{_WORD_BODY_RE}|')*", text[:-1])
    if not 2 <= len(tokens) <= 5:
        return False
    return all(token[:1].isupper() and token.lower() not in _STOPWORDS for token in tokens)


def _valid_topic(candidate: str) -> bool:
    words = candidate.split()
    if not words:
        return False
    if any(
        fragment in candidate
        for fragment in ("not-decoded", "formula-not", "image-not", "ocr-noise")
    ):
        return False
    if candidate in _BOILERPLATE_TOPIC_PHRASES:
        return False
    if any(word in _STOPWORDS for word in words):
        return False
    if any(_SYMBOLIC_TOPIC_TOKEN_RE.fullmatch(word) for word in words):
        return False
    if any(len(word) <= 1 for word in words):
        return False
    if len(words) == 1 and len(words[0]) < 4:
        return False
    return len(words) <= 5


def _covered_by_preferred_topic(topic: PriorityTopic, topics: list[PriorityTopic]) -> bool:
    for candidate in topics:
        if candidate.topic == topic.topic:
            continue
        if (
            topic.exam_hits,
            topic.exam_marks,
            topic.material_hits,
            topic.sources,
        ) != (
            candidate.exam_hits,
            candidate.exam_marks,
            candidate.material_hits,
            candidate.sources,
        ):
            continue
        if _topic_is_preferred(candidate.topic, topic.topic):
            return True
    return False


def _topic_is_preferred(candidate: str, current: str) -> bool:
    candidate_words = set(candidate.split())
    current_words = set(current.split())
    if candidate_words.isdisjoint(current_words):
        return False
    if len(candidate_words) >= 2 and candidate_words < current_words:
        return True
    if len(current_words) >= 2 and current_words < candidate_words:
        return False
    return len(current_words) == 1 and current_words < candidate_words


def _explicit_prerequisites(text: str) -> list[str]:
    terms: list[str] = []
    for line in text.splitlines():
        if not re.search(r"\bprerequisites?\b", line, flags=re.IGNORECASE):
            continue
        _label, _sep, rest = line.partition(":")
        terms.extend(_prerequisite_tokens(rest or line))
    return terms


def _dependency_prerequisites(text: str, terms: set[str]) -> dict[str, Counter[str]]:
    hints: dict[str, Counter[str]] = {}
    markers = ("depends on", "requires", "builds on", "needs")
    for sentence_match in _SENTENCE_RE.finditer(text):
        sentence = sentence_match.group(0)
        lowered = sentence.lower()
        positions = [lowered.find(marker) for marker in markers if marker in lowered]
        if not positions:
            continue
        marker = min(positions)
        before, after = lowered[:marker], lowered[marker:]
        sentence_terms = {term for term in terms if term in before}
        if not sentence_terms:
            continue
        for term in sentence_terms:
            hints.setdefault(term, Counter()).update(_prerequisite_tokens(after))
    return hints


def _prerequisite_tokens(text: str) -> list[str]:
    return [
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if token.lower() not in _STOPWORDS and not token.isdigit()
    ]


def _mark_weight(text: str) -> int:
    return max(
        (int(group) for match in _MARK_RE.finditer(text) for group in match.groups() if group),
        default=0,
    )


def _exam_sections(text: str) -> Iterator[str]:
    matches = list(_QUESTION_START_RE.finditer(text))
    if not matches:
        yield text
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
    prefix = section[: matches[0].start()].strip()
    question_mark = _mark_weight(prefix)
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        subquestion = section[match.start() : end].strip()
        if not subquestion:
            continue
        if question_mark and not _mark_weight(subquestion):
            subquestion = f"{subquestion} [{question_mark} marks]"
        yield subquestion


def _exam_questions(source: str, sections: Iterable[str]) -> Iterator[PriorityExamQuestion]:
    for section in sections:
        prompt = _topic_excerpt(section, "", max_chars=360)
        if not prompt:
            continue
        yield PriorityExamQuestion(
            source=source,
            prompt=prompt,
            marks=_mark_weight(section),
            topics=tuple(_topic_terms("", section)[:5]),
        )


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
        line = _HEADING_PREFIX_RE.sub("", raw_line.strip())
        line = _WHITESPACE_RE.sub(" ", line).strip()
        if not line or line == previous_line:
            continue
        if previous_line and line.lower().startswith(f"{previous_line.lower()} "):
            line = line[len(previous_line) :].strip()
        cleaned_lines.append(line)
        previous_line = line
    cleaned = _WHITESPACE_RE.sub(" ", " ".join(cleaned_lines)).strip()
    heading_text = _HEADING_PREFIX_RE.sub("", heading.strip())
    if heading_text and cleaned.lower().startswith(f"{heading_text.lower()} "):
        cleaned = cleaned[len(heading_text) :].strip()
    return cleaned


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
You are Heph priority analysis. Produce a priority report using only the supplied
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
    compiler: PriorityPdfCompiler | None = None,
    keep_tex: bool = False,
    progress: PriorityProgressReporter | None = None,
) -> PriorityReport:
    report_started_at = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    _emit_progress(
        progress,
        f"Ran priority.report --topics {len(analysis.topics)} --output {output_dir}.",
    )
    if os.environ.get(_WEB_PREREQ_ENV, "").lower() in {"1", "true", "yes", "on"} or (
        config is not None and config.is_feature_enabled("priority_web_prereqs")
    ):
        _emit_progress(progress, "Checking web-backed prerequisite hints for top topics...")
        analysis = replace(
            analysis,
            topics=tuple(_with_web_prerequisites(list(analysis.topics), _duckduckgo_search)),
        )
    _emit_progress(progress, "Building report sections from indexed evidence...")
    can_use_model = config is not None and _can_use_model(config)
    if can_use_model:
        model_name = config.model or "configured model"
        _emit_progress(progress, f"Requesting model synthesis from {model_name}...")
    model_payload = _model_priority_payload(
        analysis,
        config=config,
        focus=focus,
        progress=progress,
    )
    if model_payload is None:
        if can_use_model:
            _emit_progress(
                progress,
                "Model synthesis unavailable; using deterministic local output.",
            )
        else:
            _emit_progress(progress, "Using deterministic local output (no model configured).")
    else:
        _emit_progress(progress, "Model synthesis complete; grounding to indexed evidence.")
    sheet_started_at = time.perf_counter()
    sheet = build_priority_cheat_sheet(analysis, model_payload=model_payload, focus=focus)
    _emit_progress(
        progress,
        f"Built priority sheet IR ({len(sheet.topics)} topics, {len(sheet.sources)} sources) "
        f"in {_format_elapsed_since(sheet_started_at)}.",
    )
    render_started_at = time.perf_counter()
    tex_text = render_priority_latex(sheet)
    _emit_progress(
        progress,
        f"Rendered LaTeX priority sheet ({len(tex_text.encode('utf-8'))} bytes) "
        f"in {_format_elapsed_since(render_started_at)}.",
    )
    path = output_dir / f"hephaistos-priority-{datetime.now(UTC):%Y%m%d-%H%M%S}.pdf"
    sidecar_path = path.with_suffix(".json")
    compiler = compiler or ExternalLatexCompiler.discover()
    tex_path = _compile_priority_report_pdf(
        analysis,
        sheet,
        tex_text,
        path=path,
        sidecar_path=sidecar_path,
        compiler=compiler,
        keep_tex=keep_tex,
        progress=progress,
    )
    _emit_progress(progress, f"Read compiled PDF {path} for verification.")
    verify_started_at = time.perf_counter()
    verification = verify_priority_output(analysis, sheet, tex_text, pdf_path=path)
    _emit_progress(
        progress,
        f"Ran priority verification checks in {_format_elapsed_since(verify_started_at)}.",
    )
    _write_priority_sidecar(sidecar_path, verification, progress=progress)
    if not verification.passed:
        issue_text = "; ".join(verification.issues) or "verification failed"
        raise PriorityPdfError(f"Priority PDF verification failed: {issue_text}")
    _emit_progress(
        progress,
        f"Priority report verified in {_format_elapsed_since(report_started_at)}.",
    )
    return PriorityReport(
        path=path,
        used_model=model_payload is not None,
        topic_count=len(analysis.topics),
        source_count=len(set(analysis.past_exam_sources) | set(analysis.material_sources)),
        tex_path=tex_path,
        sidecar_path=sidecar_path,
        verification=verification,
    )


def duckduckgo_search(query: str) -> Iterable[PriorityWebSearchResult]:
    params = urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        f"{_WEB_PREREQ_SEARCH_URL}?{params}",
        headers={"User-Agent": _WEB_PREREQ_USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=_WEB_PREREQ_TIMEOUT) as response:  # nosec B310
        raw_html = response.read().decode("utf-8", errors="replace")
    return tuple(_parse_duckduckgo_results(raw_html))


_duckduckgo_search = duckduckgo_search


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
    progress: PriorityProgressReporter | None = None,
) -> dict[str, object] | None:
    if config is None or not _can_use_model(config):
        return None
    model_name = config.model or "configured model"
    context_chunks = _representative_chunks(analysis)
    for index, chunk in enumerate(context_chunks, start=1):
        chunk_label = (
            f"@{material_display_name(chunk.source)} chunk {chunk.index} "
            f"chars {chunk.char_start}-{chunk.char_end}"
        )
        if chunk.heading:
            chunk_label += f' heading "{_truncate(chunk.heading, 56)}"'
        _emit_progress(
            progress,
            f"Read model context {index}/{len(context_chunks)}: {chunk_label}.",
        )
    conversation = Conversation()
    conversation.add("system", f"{_PRIORITY_SYSTEM_PROMPT}\n{_PRIORITY_SCHEMA}")
    conversation.add("user", _priority_model_context(analysis, focus=focus, chunks=context_chunks))
    _emit_progress(
        progress,
        f"Ran model synthesis {model_name} with {len(context_chunks)} evidence excerpt(s).",
    )
    parts: list[str] = []
    started_at = time.perf_counter()
    last_progress_at = started_at
    chunk_count = 0
    char_count = 0
    try:
        with _ProgressHeartbeat(progress, f"Waiting on {model_name} model stream") as heartbeat:
            for delta in stream_completion(
                config,
                conversation,
                retry=RetryConfig(max_retries=1),
            ):
                if not delta.content:
                    continue
                parts.append(delta.content)
                chunk_count += 1
                char_count += len(delta.content)
                now = time.perf_counter()
                if chunk_count == 1:
                    heartbeat.stop()
                    _emit_progress(
                        progress,
                        f"Read first model delta from {model_name} "
                        f"in {_format_elapsed_since(started_at)}.",
                    )
                    last_progress_at = now
                elif now - last_progress_at >= _MODEL_STREAM_PROGRESS_SECONDS:
                    _emit_progress(
                        progress,
                        f"Read {char_count} model character(s) from {model_name} "
                        f"across {chunk_count} delta(s) in {_format_elapsed_since(started_at)}.",
                    )
                    last_progress_at = now
    except EngineError:
        _emit_progress(
            progress,
            f"Model synthesis failed after {_format_elapsed_since(started_at)}; "
            "using deterministic local output.",
        )
        return None
    raw_payload = "".join(parts)
    _emit_progress(
        progress,
        f"Read complete model response from {model_name}: {len(raw_payload)} character(s) "
        f"across {chunk_count} delta(s) in {_format_elapsed_since(started_at)}.",
    )
    parsed = parse_json_object_fragment(raw_payload)
    if parsed is None:
        _emit_progress(
            progress,
            "Model response was not valid JSON; using deterministic fallback.",
        )
        return None
    _emit_progress(progress, "Parsed model JSON priority payload.")
    return parsed


def _can_use_model(config: ChatConfig) -> bool:
    if not config.base_url or not config.model:
        return False
    return is_keyless_endpoint(config.base_url) or has_configured_access(config)


def _priority_model_context(
    analysis: PriorityAnalysis,
    *,
    focus: str,
    chunks: Iterable[PriorityChunk] | None = None,
) -> str:
    context_chunks = tuple(chunks) if chunks is not None else _representative_chunks(analysis)
    evidence_lines = []
    for idx, chunk in enumerate(context_chunks, start=1):
        role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
        compact_text = _WHITESPACE_RE.sub(" ", chunk.text).strip()
        if len(compact_text) > 900:
            compact_text = f"{compact_text[:899]}…"
        evidence_lines.append(
            "\n".join(
                (
                    f"Evidence {idx}",
                    f"Source: {chunk.source}",
                    f"Role: {role}",
                    f"Heading: {chunk.heading or 'none'}",
                    f"Text: {compact_text}",
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
    topic_names = {topic.topic.lower() for topic in analysis.topics}
    for chunk in analysis.chunks:
        key = (chunk.source, chunk.text[:120])
        if key in seen:
            continue
        role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
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


class ExternalLatexCompiler:
    def __init__(self, executable: Path) -> None:
        self._executable = executable

    @classmethod
    def discover(cls) -> ExternalLatexCompiler | None:
        for name in _LATEX_ENGINE_NAMES:
            resolved = shutil.which(name)
            if resolved:
                return cls(Path(resolved))
        return None

    def compile(
        self,
        tex_path: Path,
        pdf_path: Path,
        *,
        progress: PriorityProgressReporter | None = None,
    ) -> None:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        work_dir = tex_path.parent
        command, runs = self._compile_command(tex_path, work_dir)
        _emit_progress(progress, f"Ran {' '.join(command)} (cwd {work_dir}).")
        compile_started_at = time.perf_counter()
        for run_index in range(runs):
            run_started_at = time.perf_counter()
            try:
                subprocess.run(
                    command,
                    cwd=work_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=_LATEX_COMPILE_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                raise PriorityPdfError(
                    "LaTeX engine timed out while compiling the priority report."
                ) from exc
            _emit_progress(
                progress,
                f"Ran LaTeX pass {run_index + 1}/{runs} in "
                f"{_format_elapsed_since(run_started_at)}.",
            )
        built_pdf = work_dir / tex_path.with_suffix(".pdf").name
        if not built_pdf.is_file():
            raise PriorityPdfError(f"LaTeX engine did not produce {built_pdf}.")
        shutil.copy2(built_pdf, pdf_path)
        _emit_progress(
            progress,
            f"Wrote PDF {pdf_path} ({pdf_path.stat().st_size} bytes) "
            f"in {_format_elapsed_since(compile_started_at)}.",
        )

    def _compile_command(self, tex_path: Path, work_dir: Path) -> tuple[list[str], int]:
        engine = self._executable.name
        if engine == "latexmk":
            command = [
                str(self._executable),
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-outdir=.",
                tex_path.name,
            ]
            return command, 1
        if engine == "tectonic":
            command = [
                str(self._executable),
                "--keep-logs",
                "--outdir",
                str(work_dir),
                str(tex_path),
            ]
            return command, 1
        command = [
            str(self._executable),
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={work_dir}",
            str(tex_path),
        ]
        return command, 2


def _compile_priority_report_pdf(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    compiler: PriorityPdfCompiler | None,
    keep_tex: bool,
    progress: PriorityProgressReporter | None,
) -> Path | None:
    if compiler is None:
        tex_path = _save_priority_draft(
            analysis,
            sheet,
            tex_text,
            path=path,
            sidecar_path=sidecar_path,
            progress=progress,
        )
        _emit_progress(progress, f"No LaTeX engine found; saved draft to {tex_path}.")
        raise PriorityPdfError(
            "No LaTeX PDF engine found. Install latexmk, lualatex, xelatex, pdflatex, "
            f"or tectonic; LaTeX draft saved to {tex_path}."
        )

    with tempfile.TemporaryDirectory(prefix="heph-priority-") as temp_dir_name:
        temp_tex_path = Path(temp_dir_name) / path.with_suffix(".tex").name
        _write_text_artifact(temp_tex_path, tex_text, progress=progress, label="temporary LaTeX")
        try:
            _run_priority_pdf_compiler(
                compiler,
                temp_tex_path,
                path,
                progress=progress,
            )
        except (OSError, subprocess.CalledProcessError, PriorityPdfError) as exc:
            tex_path = _save_priority_draft(
                analysis,
                sheet,
                tex_text,
                path=path,
                sidecar_path=sidecar_path,
                progress=progress,
            )
            raise PriorityPdfError(
                f"Priority PDF compile failed; LaTeX draft saved to {tex_path}."
            ) from exc

    if not keep_tex:
        return None
    tex_path = path.with_suffix(".tex")
    _write_text_artifact(tex_path, tex_text, progress=progress, label="LaTeX source")
    return tex_path


def _run_priority_pdf_compiler(
    compiler: PriorityPdfCompiler,
    tex_path: Path,
    pdf_path: Path,
    *,
    progress: PriorityProgressReporter | None,
) -> None:
    compile_started_at = time.perf_counter()
    if isinstance(compiler, ExternalLatexCompiler):
        compiler.compile(tex_path, pdf_path, progress=progress)
    else:
        _emit_progress(
            progress,
            f"Ran {compiler.__class__.__name__}.compile({tex_path}, {pdf_path}).",
        )
        compiler.compile(tex_path, pdf_path)
    _emit_progress(
        progress,
        f"PDF compile finished in {_format_elapsed_since(compile_started_at)}.",
    )
    if pdf_path.is_file() and not isinstance(compiler, ExternalLatexCompiler):
        _emit_progress(progress, f"Wrote PDF {pdf_path} ({pdf_path.stat().st_size} bytes).")


def build_priority_cheat_sheet(
    analysis: PriorityAnalysis,
    *,
    model_payload: dict[str, object] | None,
    focus: str,
) -> PriorityCheatSheet:
    sources = _priority_sources(analysis)
    source_ids = {source.path: source.source_id for source in sources}
    topics = tuple(
        _cheat_sheet_topic(topic, analysis, source_ids, model_payload=model_payload)
        for topic in analysis.topics
    )
    uncertainties = _analysis_uncertainties(analysis, topics)
    return PriorityCheatSheet(
        title="Heph priority sheet",
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        focus=focus.strip(),
        sources=sources,
        topics=topics,
        exam_questions=analysis.exam_questions,
        uncertainties=uncertainties,
    )


def render_priority_latex(sheet: PriorityCheatSheet) -> str:
    body = [
        r"\documentclass[10pt,a4paper,landscape]{article}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{amsmath,amssymb,mathtools}",
        r"\usepackage{geometry}",
        r"\usepackage{multicol}",
        r"\usepackage{array,booktabs,tabularx}",
        r"\usepackage{enumitem}",
        r"\usepackage{microtype}",
        r"\usepackage{xcolor}",
        r"\geometry{margin=8mm}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{1.5pt}",
        r"\setlist[itemize]{leftmargin=*,topsep=1pt,itemsep=1pt,parsep=0pt}",
        r"\setlist[enumerate]{leftmargin=*,topsep=1pt,itemsep=1pt,parsep=0pt}",
        r"\definecolor{hephSourceText}{HTML}{"
        + LIGHT_THEME.text_muted.removeprefix("#").upper()
        + "}",
        r"\newcommand{\sourceids}[1]{\textcolor{hephSourceText}{\footnotesize #1}}",
        r"\newcommand{\topicrule}{\vspace{2pt}\hrule\vspace{3pt}}",
        r"\pagestyle{empty}",
        r"\begin{document}",
        _latex_header(sheet),
        r"\begin{multicols*}{2}",
    ]
    for topic in sheet.topics:
        body.extend(_latex_topic(topic))
    body.append(r"\end{multicols*}")
    body.extend(_latex_exam_patterns(sheet.exam_questions))
    body.extend(_latex_sources(sheet.sources))
    if sheet.uncertainties:
        body.extend((r"\section*{Uncertainty}", r"\begin{itemize}"))
        body.extend(r"\item " + _latex_text(item) for item in sheet.uncertainties)
        body.append(r"\end{itemize}")
    body.append(r"\end{document}")
    return "\n".join(body) + "\n"


def verify_priority_output(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    pdf_path: Path | None,
) -> PriorityVerificationReport:
    issues: list[str] = []
    warnings: list[str] = []
    extraction_ok = bool(analysis.chunks)
    if not extraction_ok:
        issues.append("no indexed chunks were available")
    if not analysis.past_exam_sources:
        warnings.append("no past-exam sources were identified from content")
    priority_ok = _verify_priority_order(analysis)
    if not priority_ok:
        issues.append("top priorities are not supported by past-exam signals")
    source_support_ok = all(topic.source_ids or topic.uncertainty for topic in sheet.topics)
    if not source_support_ok:
        issues.append("one or more topic sections lack source IDs or uncertainty labels")
    latex_ok = _verify_latex_text(tex_text)
    if not latex_ok:
        issues.append("generated LaTeX failed syntax or anti-debug checks")
    pdf_ok = pdf_path is not None and pdf_path.is_file() and pdf_path.stat().st_size > 0
    if not pdf_ok:
        issues.append("compiled PDF was not produced")
    anti_regression_ok = "HEPHAISTOS PRIORITY" not in tex_text and not _FORBIDDEN_REPORT_RE.search(
        tex_text
    )
    if not anti_regression_ok:
        issues.append("report text contains a forbidden raw metric or boilerplate pattern")
    autopilot_ok = bool(analysis.topics) and not _RAW_METRIC_RE.search(
        analysis.render_for_prompt(limit=8)
    )
    if not autopilot_ok:
        issues.append("priority context is empty or exposes raw metric strings")
    return PriorityVerificationReport(
        extraction_ok=extraction_ok,
        priority_ok=priority_ok,
        source_support_ok=source_support_ok,
        latex_ok=latex_ok,
        pdf_ok=pdf_ok,
        anti_regression_ok=anti_regression_ok,
        autopilot_ok=autopilot_ok,
        issues=tuple(issues),
        warnings=tuple(warnings),
    )


def _write_priority_sidecar(
    path: Path,
    report: PriorityVerificationReport,
    *,
    progress: PriorityProgressReporter | None = None,
) -> None:
    _write_text_artifact(
        path,
        json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
        progress=progress,
        label="verification sidecar",
    )


def _save_priority_draft(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> Path:
    tex_path = path.with_suffix(".tex")
    _write_text_artifact(tex_path, tex_text, progress=progress, label="LaTeX draft")
    verification = verify_priority_output(analysis, sheet, tex_text, pdf_path=None)
    _write_priority_sidecar(sidecar_path, verification, progress=progress)
    return tex_path


def _priority_sources(analysis: PriorityAnalysis) -> tuple[PrioritySource, ...]:
    ordered = [*analysis.past_exam_sources, *analysis.material_sources]
    deduped = tuple(dict.fromkeys(ordered))
    sources: list[PrioritySource] = []
    for index, source in enumerate(deduped, start=1):
        role = "past exam" if source in analysis.past_exam_sources else "supporting material"
        sources.append(PrioritySource(source_id=f"S{index}", path=source, role=role))
    return tuple(sources)


def _cheat_sheet_topic(
    topic: PriorityTopic,
    analysis: PriorityAnalysis,
    source_ids: dict[str, str],
    *,
    model_payload: dict[str, object] | None,
) -> PriorityCheatSheetTopic:
    payload: dict[str, object] | None = None
    raw_topics = model_payload.get("topics") if model_payload is not None else None
    if isinstance(raw_topics, list):
        for raw_topic in raw_topics:
            if not is_string_mapping(raw_topic):
                continue
            raw_name = raw_topic.get("name")
            if isinstance(raw_name, str) and raw_name.strip().lower() == topic.topic.lower():
                payload = dict(raw_topic)
                break
    source_labels = tuple(source_ids[source] for source in topic.sources if source in source_ids)
    evidence_sentences = _topic_sentences(topic)
    definitions = _payload_string_list(payload, "definitions") or _select_by_keywords(
        evidence_sentences,
        (" is ", " are ", " heißt ", " bedeutet ", "definition", "satz", "theorem"),
        fallback=True,
    )
    formulas = _payload_string_list(payload, "formulas") or _select_formula_lines(topic)
    procedures = _payload_string_list(payload, "procedures") or _select_by_keywords(
        evidence_sentences,
        ("step", "algorithm", "procedure", "compute", "berechnen", "show", "prove", "derive"),
    )
    exam_tasks = _exam_tasks_for_topic(topic, analysis.exam_questions)
    pitfalls = _select_by_keywords(
        evidence_sentences,
        ("not ", "except", "avoid", "pitfall", "common mistake", "confuse", "but "),
    )
    uncertainty: list[str] = []
    if not definitions and not formulas and not procedures:
        uncertainty.append(
            "Indexed materials do not expose enough factual content for this topic."
        )
    if topic.confidence < 0.45:
        uncertainty.append("Extraction confidence is limited; verify against the cited sources.")
    return PriorityCheatSheetTopic(
        title=topic.topic,
        tier=priority_tier(topic),
        source_ids=source_labels,
        prerequisites=_topic_prerequisites(topic),
        definitions=tuple(definitions[:3]),
        formulas=tuple(formulas[:4]),
        procedures=tuple(procedures[:3]),
        exam_tasks=tuple(exam_tasks[:4]),
        pitfalls=tuple(pitfalls[:3]),
        uncertainty=tuple(uncertainty),
    )


def _analysis_uncertainties(
    analysis: PriorityAnalysis,
    topics: tuple[PriorityCheatSheetTopic, ...],
) -> tuple[str, ...]:
    uncertainties: list[str] = []
    if not analysis.past_exam_sources:
        uncertainties.append(
            "No past exams were identified; ranking falls back to material coverage."
        )
    if not analysis.exam_questions and analysis.past_exam_sources:
        uncertainties.append("Past exams were found, but question extraction was incomplete.")
    if any(topic.uncertainty for topic in topics):
        uncertainties.append(
            "Some topics lack enough local factual support for full cheat-sheet blocks."
        )
    return tuple(uncertainties)


def _topic_sentences(topic: PriorityTopic) -> list[str]:
    sentences: list[str] = []
    seen: set[str] = set()
    for evidence in topic.evidence:
        for sentence_match in _SENTENCE_RE.finditer(evidence.excerpt):
            sentence = _WHITESPACE_RE.sub(" ", sentence_match.group(0)).strip()
            if len(sentence) < 12 or sentence.lower() in seen:
                continue
            seen.add(sentence.lower())
            sentences.append(sentence)
    return sentences


def _select_by_keywords(
    sentences: list[str],
    keywords: tuple[str, ...],
    *,
    fallback: bool = False,
) -> list[str]:
    selected = [
        sentence
        for sentence in sentences
        if any(keyword in sentence.lower() for keyword in keywords)
    ]
    if selected or not fallback:
        return selected
    return sentences[:2]


def _select_formula_lines(topic: PriorityTopic) -> list[str]:
    lines: list[str] = []
    for evidence in topic.evidence:
        for unit in re.split(r"(?<=[.!?])\s+|\n", evidence.excerpt):
            stripped = _WHITESPACE_RE.sub(" ", unit).strip()
            if not stripped:
                continue
            if "$" in stripped or "\\" in stripped or re.search(r"[=∑∫√≤≥→]", stripped):
                lines.append(stripped)
    return lines


def _exam_tasks_for_topic(
    topic: PriorityTopic,
    exam_questions: tuple[PriorityExamQuestion, ...],
) -> list[str]:
    tasks: list[str] = []
    for question in exam_questions:
        if topic.topic not in question.topics:
            continue
        marks = f" ({question.marks} visible points)" if question.marks else ""
        tasks.append(f"{question.prompt}{marks}")
    return tasks


def _topic_prerequisites(topic: PriorityTopic) -> tuple[str, ...]:
    if topic.prerequisites:
        return topic.prerequisites
    if topic.web_prerequisites:
        return tuple(
            f"{item.term} (external prerequisite hint; verify locally)"
            for item in topic.web_prerequisites
        )
    return ("No explicit local prerequisite found.",)


def priority_tier(topic: PriorityTopic) -> str:
    if topic.exam_marks >= 12 or topic.exam_hits >= 3:
        return "Exam core"
    if topic.exam_marks >= 6 or topic.exam_hits >= 2:
        return "High-yield"
    if topic.exam_hits:
        return "Foundation"
    if topic.supporting_material_coverage >= 2 or topic.material_hits >= 3:
        return "Prerequisite"
    return "Supporting"


def _latex_header(sheet: PriorityCheatSheet) -> str:
    focus = f"Focus: {_latex_text(sheet.focus)}. " if sheet.focus else ""
    source_count = len(sheet.sources)
    return "\n".join(
        (
            r"{\Large\textbf{" + _latex_text(sheet.title) + r"}}\\[-1pt]",
            r"\footnotesize "
            + focus
            + f"Generated {_latex_text(sheet.generated_at)}. "
            + f"{source_count} source(s). "
            + r"Claims are grounded in local sources unless listed as uncertainty.\\",
            r"\vspace{2mm}",
        )
    )


def _latex_topic(topic: PriorityCheatSheetTopic) -> list[str]:
    source_text = ", ".join(f"[{source_id}]" for source_id in topic.source_ids)
    lines = [
        r"\topicrule",
        r"\textbf{"
        + _latex_text(topic.title)
        + r"} "
        + r"\sourceids{"
        + _latex_text(f"{topic.tier} {source_text}".strip())
        + r"}",
    ]
    lines.extend(_latex_item_block("Definitions", topic.definitions))
    lines.extend(_latex_item_block("Formulas", topic.formulas))
    lines.extend(_latex_item_block("Procedures", topic.procedures))
    lines.extend(_latex_item_block("Exam tasks", topic.exam_tasks))
    lines.extend(_latex_item_block("Pitfalls", topic.pitfalls))
    lines.extend(_latex_item_block("Before this", topic.prerequisites))
    lines.extend(_latex_item_block("Uncertainty", topic.uncertainty))
    return lines


def _latex_item_block(title: str, items: tuple[str, ...]) -> list[str]:
    if not items:
        return []
    lines = [r"\textit{" + _latex_text(title) + r"}"]
    lines.append(r"\begin{itemize}")
    lines.extend(r"\item " + _latex_mixed_text(item) for item in items)
    lines.append(r"\end{itemize}")
    return lines


def _latex_exam_patterns(exam_questions: tuple[PriorityExamQuestion, ...]) -> list[str]:
    if not exam_questions:
        return []
    lines = [
        r"\newpage",
        r"\section*{Past-exam pattern table}",
        r"\footnotesize",
        r"\begin{tabularx}{\linewidth}{p{0.24\linewidth}p{0.09\linewidth}p{0.2\linewidth}X}",
        r"\toprule",
        r"Source & Points & Topic & Tested skill \\",
        r"\midrule",
    ]
    for question in exam_questions[:60]:
        points = str(question.marks) if question.marks else "unknown"
        topics = ", ".join(question.topics[:3]) if question.topics else "unknown"
        lines.append(
            _latex_text(question.source)
            + " & "
            + _latex_text(points)
            + " & "
            + _latex_text(topics)
            + " & "
            + _latex_mixed_text(_truncate(question.prompt, 180))
            + r" \\"
        )
    lines.extend((r"\bottomrule", r"\end{tabularx}"))
    return lines


def _latex_sources(sources: tuple[PrioritySource, ...]) -> list[str]:
    if not sources:
        return []
    lines = [r"\section*{Source list}", r"\footnotesize", r"\begin{multicols}{2}"]
    source_lines = (
        r"\noindent ["
        + _latex_text(source.source_id)
        + "] "
        + _latex_text(source.path)
        + " -- "
        + _latex_text(source.role)
        + r"\\"
        for source in sources
    )
    lines.extend(source_lines)
    lines.append(r"\end{multicols}")
    return lines


def _latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def _latex_mixed_text(value: str) -> str:
    parts = re.split(r"(\$[^$\n]+\$|\\\([^)]*\\\)|\\\[[\s\S]*?\\\])", value)
    rendered: list[str] = []
    for part in parts:
        if not part:
            continue
        if _is_safe_latex_math(part):
            rendered.append(part)
        else:
            rendered.append(_latex_text(part))
    return "".join(rendered)


def _looks_like_latex_math(value: str) -> bool:
    return (
        (value.startswith("$") and value.endswith("$"))
        or (value.startswith(r"\(") and value.endswith(r"\)"))
        or (value.startswith(r"\[") and value.endswith(r"\]"))
    )


def _is_safe_latex_math(value: str) -> bool:
    if not _looks_like_latex_math(value):
        return False
    content = _latex_math_content(value)
    if not content or _LATEX_MATH_UNSAFE_CHAR_RE.search(content):
        return False
    for match in _LATEX_MATH_COMMAND_RE.finditer(content):
        command = match.group(1)
        if command.isalpha():
            if command not in _ALLOWED_LATEX_MATH_COMMANDS:
                return False
        elif command not in _ALLOWED_LATEX_MATH_SYMBOL_COMMANDS:
            return False
    return True


def _latex_math_content(value: str) -> str:
    if value.startswith("$") and value.endswith("$"):
        return value[1:-1]
    if value.startswith(r"\(") and value.endswith(r"\)"):
        return value[2:-2]
    if value.startswith(r"\[") and value.endswith(r"\]"):
        return value[2:-2]
    return value


def _verify_priority_order(analysis: PriorityAnalysis) -> bool:
    if not analysis.topics:
        return False
    if not analysis.past_exam_sources:
        return True
    top = analysis.topics[0]
    return top.exam_hits > 0 or top.exam_marks > 0


def _verify_latex_text(tex_text: str) -> bool:
    if _RAW_METRIC_RE.search(tex_text):
        return False
    if tex_text.count("{") != tex_text.count("}"):
        return False
    return r"\geometry{margin=8mm}" in tex_text and r"\begin{multicols*}{2}" in tex_text


def _truncate(value: str, max_chars: int) -> str:
    value = _WHITESPACE_RE.sub(" ", value).strip()
    if len(value) <= max_chars:
        return value
    return f"{value[: max_chars - 1]}…"


def _payload_string_list(payload: dict[str, object] | None, key: str) -> list[str]:
    if payload is None:
        return []
    value = payload.get(key)
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]
