"""Deterministic priority analysis over indexed materials."""

from __future__ import annotations

import html
import json
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
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn, Protocol, Self

from hephaion._types import is_string_mapping, parse_json_object_fragment
from hephaion.env import get_env
from hephaion.materials import infer_material_role_from_text, material_display_name
from hephaion.providers.endpoints import is_keyless_endpoint
from hephaion.runtime import (
    ChatConfig,
    Conversation,
    EngineError,
    RetryConfig,
    has_configured_access,
    stream_completion,
)
from hephaion.terminal.palette import LIGHT_THEME

_LETTER_RE = r"[^\W\d_]"
_WORD_BODY_RE = r"[\w+-]"
_TOKEN_RE = re.compile(rf"{_LETTER_RE}{_WORD_BODY_RE}{{2,}}")
_SENTENCE_RE = re.compile(r"[^.!?\n]+")
_TOPIC_SPAN_RE = re.compile(
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
    r"term|university|dozent|dozentin|hochschule|sommersemester|universität|"
    r"universitaet|wintersemester"
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
    r"student name|student id|candidate number|exam seat",
    re.IGNORECASE,
)
_LATEX_ENGINE_NAMES = ("latexmk", "lualatex", "xelatex", "pdflatex", "tectonic")
_LATEX_COMPILE_TIMEOUT_SECONDS = 30
_LATEX_MATH_COMMAND_RE = re.compile(r"\\([A-Za-z]+|.)")
_LATEX_MATH_UNSAFE_CHAR_RE = re.compile(r"[%#&~]")
_LATEX_MATH_DELIMITERS = (("$", "$"), (r"\(", r"\)"), (r"\[", r"\]"))
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
_WEB_PREREQ_ENV = "HEPHAION_PRIORITY_WEB_PREREQS"
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
        "nschen",
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
    practice_ok: bool
    issues: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return all(
            (
                self.extraction_ok,
                self.priority_ok,
                self.source_support_ok,
                self.latex_ok,
                self.pdf_ok,
                self.anti_regression_ok,
                self.practice_ok,
            )
        )


@dataclass(frozen=True, slots=True)
class _PriorityVerificationChecks:
    extraction_ok: bool
    priority_ok: bool
    source_support_ok: bool
    latex_ok: bool
    pdf_ok: bool
    anti_regression_ok: bool
    practice_ok: bool


@dataclass(frozen=True, slots=True)
class PriorityReport:
    path: Path
    used_model: bool
    topic_count: int
    source_count: int
    tex_path: Path | None = None
    sidecar_path: Path | None = None
    verification: PriorityVerificationReport | None = None


@dataclass(frozen=True, slots=True)
class _PriorityReportArtifacts:
    sheet: PriorityCheatSheet
    tex_text: str
    model_payload: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class _CheatSheetTopicSections:
    definitions: list[str]
    formulas: list[str]
    procedures: list[str]
    exam_tasks: list[str]
    pitfalls: list[str]


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
        return _render_priority_analysis_for_prompt(self, limit=limit)


def _render_priority_analysis_for_prompt(analysis: PriorityAnalysis, *, limit: int) -> str:
    if not analysis.topics:
        return "Local priority scan: no recurring indexed topics were found."

    lines = ["Local priority scan from indexed materials:"]
    lines.extend(_priority_source_summary_lines(analysis))
    lines.append("- Candidate priorities:")
    lines.extend(_priority_prompt_topic_line(topic) for topic in analysis.topics[:limit])
    return "\n".join(lines)


def _priority_source_summary_lines(analysis: PriorityAnalysis) -> Iterator[str]:
    if analysis.past_exam_sources:
        yield f"- Past exams scanned: {', '.join(analysis.past_exam_sources[:5])}"
    if analysis.material_sources:
        yield f"- Supporting materials scanned: {', '.join(analysis.material_sources[:5])}"


def _priority_prompt_topic_line(topic: PriorityTopic) -> str:
    return (
        f"  - {topic.topic}: {priority_tier(topic)}; "
        f"{_priority_prompt_exam_signal(topic)}; "
        f"sources: {', '.join(topic.sources[:3])}{_priority_prompt_prerequisites(topic)}"
    )


def _priority_prompt_exam_signal(topic: PriorityTopic) -> str:
    if topic.exam_marks:
        return f"{topic.exam_hits} exam hit(s), {topic.exam_marks} visible mark(s)"
    if topic.exam_hits:
        return f"{topic.exam_hits} exam hit(s), no explicit marks found"
    return "No past-exam hit found"


def _priority_prompt_prerequisites(topic: PriorityTopic) -> str:
    if topic.prerequisites:
        return f"; prerequisites to check: {', '.join(topic.prerequisites[:3])}"
    if topic.web_prerequisites:
        terms = ", ".join(item.term for item in topic.web_prerequisites[:3])
        return f"; web-backed prerequisite hints: {terms}"
    return ""


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
    for prerequisite in _iter_web_prerequisites(topic, search_results, seen):
        results.append(prerequisite)
        if len(results) >= 3:
            return tuple(results)
    return tuple(results)


def _iter_web_prerequisites(
    topic: str,
    search_results: Sequence[PriorityWebSearchResult],
    seen: set[str],
) -> Iterator[PriorityWebPrerequisite]:
    for result in search_results[:_WEB_PREREQ_RESULTS]:
        for term in _prerequisite_terms_from_web_result(topic, result):
            if term in seen:
                continue
            seen.add(term)
            yield PriorityWebPrerequisite(
                term=term,
                source_title=result.title,
                source_url=result.url,
            )


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
    yield from _claim_web_prerequisite_terms(
        (
            _web_prerequisite_phrase_term(match.group(0), topic_words)
            for match in _TOPIC_SPAN_RE.finditer(text)
        ),
        seen,
    )
    yield from _claim_web_prerequisite_terms(
        (
            _web_prerequisite_word_term(match.group(0), topic_words)
            for match in _TOKEN_RE.finditer(text)
        ),
        seen,
    )


def _claim_web_prerequisite_terms(candidates: Iterable[str], seen: set[str]) -> Iterator[str]:
    for candidate in candidates:
        if candidate and _claim_candidate(candidate, seen):
            yield candidate


def _web_prerequisite_phrase_term(text: str, topic_words: set[str]) -> str:
    useful = [word for word in _useful_topic_words(text) if word not in topic_words]
    return " ".join(useful[:3]) if useful else ""


def _web_prerequisite_word_term(word: str, topic_words: set[str]) -> str:
    term = word.lower()
    if term in _STOPWORDS or term in topic_words:
        return ""
    return term


def _claim_candidate(candidate: str, seen: set[str]) -> bool:
    if not candidate or candidate in seen:
        return False
    seen.add(candidate)
    return True


def _candidate_topic_phrases(raw: str) -> Iterator[str]:
    topic_text = _topic_candidate_text(raw)
    yield from _definition_head_candidates(topic_text)
    yield from _heading_candidates(topic_text)
    yield from _prompt_topic_candidates(topic_text)
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
        for part in _PROMPT_TOPIC_SPLIT_RE.split(text)
        if part.strip() and part.strip() != text
    ]


def _heading_word_candidates(cleaned: str) -> Iterator[str]:
    useful = _useful_topic_words(cleaned)
    if 2 <= len(useful) <= 6:
        yield " ".join(useful)
    elif len(useful) == 1 and len(useful[0]) >= 5:
        yield useful[0]


def _prompt_topic_candidates(text: str) -> Iterator[str]:
    for prompt_match in _PROMPT_TOPIC_RE.finditer(text):
        for part in _PROMPT_TOPIC_SPLIT_RE.split(prompt_match.group("tail")):
            yield from _prompt_part_topic_candidates(part)


def _prompt_part_topic_candidates(part: str) -> Iterator[str]:
    useful = _useful_topic_words(part)
    if len(useful) == 1:
        yield from _single_prompt_topic_candidate(useful[0])
        return
    if len(useful) < 2:
        return
    if len(useful[0]) >= 5:
        yield useful[0]
    if len(useful) > 2:
        yield " ".join(useful[:2])
    yield " ".join(useful[:3])


def _single_prompt_topic_candidate(word: str) -> Iterator[str]:
    if len(word) >= 5:
        yield word


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


def _definition_head_candidates(text: str) -> Iterator[str]:
    seen: set[str] = set()
    for line in text.splitlines():
        for term in _definition_terms_from_line(line):
            if not _record_definition_candidate(term, seen):
                continue
            yield term


def _record_definition_candidate(term: str, seen: set[str]) -> bool:
    if not term or term in seen:
        return False
    seen.add(term)
    return True


def _definition_terms_from_line(line: str) -> Iterator[str]:
    if not line.strip():
        return
    yield from _definition_prefix_terms(line)
    yield from _definition_pattern_terms(line)


def _definition_prefix_terms(line: str) -> Iterator[str]:
    for match in _DEFINITION_VERB_RE.finditer(line):
        prefix = line[: match.start()].strip(" .:-;")
        if prefix:
            yield _definition_term_candidate(prefix)


def _definition_pattern_terms(line: str) -> Iterator[str]:
    for pattern in (_DEFINITION_SUBJECT_RE, _DEFINED_OBJECT_RE):
        for match in pattern.finditer(line):
            yield _definition_term_candidate(match.group("term"))


def _definition_term_candidate(raw: str) -> str:
    words = [word.lower() for word in _WORD_SPLIT_RE.findall(raw)]
    kept: list[str] = []
    for word in words:
        if _definition_word_stops_empty_candidate(word, kept):
            continue
        if _definition_word_stops_completed_candidate(word, kept):
            break
        kept.append(word)
        if len(kept) >= 3:
            break
    return " ".join(kept)


def _definition_word_stops_empty_candidate(word: str, kept: list[str]) -> bool:
    return not kept and _definition_word_stops_candidate(word)


def _definition_word_stops_completed_candidate(word: str, kept: list[str]) -> bool:
    return bool(kept) and _definition_word_stops_candidate(word)


def _definition_word_stops_candidate(word: str) -> bool:
    return word in _DEFINITION_TERM_STOPWORDS or word in _STOPWORDS


def _useful_topic_words(text: str) -> list[str]:
    return [
        word.lower()
        for word in _WORD_SPLIT_RE.findall(text)
        if word.lower() not in _STOPWORDS and not word.isdigit()
    ]


def _topic_candidate_text(raw: str) -> str:
    return "\n".join(
        unit for line in raw.splitlines() for unit in _topic_candidate_line_units(line)
    )


def _topic_candidate_line_units(line: str) -> Iterator[str]:
    if not line.strip():
        return
    for unit in re.split(r"(?<=[.!?])\s+", line):
        cleaned = unit.strip()
        if cleaned and not _is_boilerplate_line(cleaned):
            yield cleaned


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
    return bool(
        words
        and not _invalid_topic_phrase(candidate)
        and not _invalid_topic_words(words)
        and len(words) <= 5
    )


def _invalid_topic_phrase(candidate: str) -> bool:
    return candidate in _BOILERPLATE_TOPIC_PHRASES or any(
        fragment in candidate
        for fragment in ("not-decoded", "formula-not", "image-not", "ocr-noise")
    )


def _invalid_topic_words(words: list[str]) -> bool:
    return any(_invalid_topic_word(word) for word in words) or _single_word_topic_too_short(words)


def _invalid_topic_word(word: str) -> bool:
    return (
        word in _STOPWORDS
        or len(word) <= 1
        or _SYMBOLIC_TOPIC_TOKEN_RE.fullmatch(word) is not None
    )


def _single_word_topic_too_short(words: Sequence[str]) -> bool:
    return len(words) == 1 and len(words[0]) < 4


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
    terms: list[str] = []
    for line in text.splitlines():
        if not re.search(r"\bprerequisites?\b", line, flags=re.IGNORECASE):
            continue
        _label, _sep, rest = line.partition(":")
        terms.extend(_prerequisite_tokens(rest or line))
    return terms


def _dependency_prerequisites(text: str, terms: set[str]) -> dict[str, Counter[str]]:
    hints: dict[str, Counter[str]] = {}
    for term, prerequisites in _iter_dependency_prerequisite_hints(text, terms):
        hints.setdefault(term, Counter()).update(prerequisites)
    return hints


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
    for term in (term for term in terms if term in before):
        yield term, _prerequisite_tokens(after)


def _dependency_sentence_parts(sentence: str) -> tuple[str, str] | None:
    lowered = sentence.lower()
    positions = [
        lowered.find(marker)
        for marker in ("depends on", "requires", "builds on", "needs")
        if marker in lowered
    ]
    if not positions:
        return None
    marker = min(positions)
    return lowered[:marker], lowered[marker:]


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
    question_mark = _mark_weight(_exam_question_prefix(section, matches))
    for index, _match in enumerate(matches):
        if subquestion := _exam_subquestion(section, matches, index, question_mark):
            yield subquestion


def _exam_question_prefix(section: str, matches: Sequence[re.Match[str]]) -> str:
    return section[: matches[0].start()].strip()


def _exam_subquestion(
    section: str,
    matches: Sequence[re.Match[str]],
    index: int,
    question_mark: int,
) -> str:
    match = matches[index]
    end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
    subquestion = section[match.start() : end].strip()
    if not subquestion:
        return ""
    if question_mark and not _mark_weight(subquestion):
        return f"{subquestion} [{question_mark} marks]"
    return subquestion


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
    candidates.sort(key=lambda item: (-item[1], item[0]))
    return tuple(peer for peer, _count in candidates[:3])


def _valid_prerequisite_peer(peer: str, term: str, exam_counts: Counter[str]) -> bool:
    return " " not in peer and peer not in exam_counts and term not in peer and peer not in term


_PRIORITY_SCHEMA = """
{
  "summary": "1-2 sentence source-grounded overview",
  "topics": [
    {
      "name": "exact topic name from the materials",
      "importance": "critical|high|medium|low",
      "why": "why this is important based only on supplied evidence",
      "learning_actions": ["concrete, measurable goal grounded in the material"],
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
  "learning_plan": ["ordered next steps grounded in evidence"],
  "unknowns": ["important detail missing from indexed materials"]
}
""".strip()


_PRIORITY_SYSTEM_PROMPT = """
You are Heph priority analysis. Produce a priority report using only the supplied
indexed material excerpts for topics, exam claims, marks, and source evidence. Do not add outside
facts for those sections. Web-backed prerequisite hints may be used only when they are explicitly
listed in the local scan context; label them as web-backed if you mention them. If the material
does not specify a detail, write that it is unknown. Favor exact topic names from the evidence
over filename fragments. Make each learning action a concrete, checkable goal rather than a vague
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
    analysis = _analysis_with_optional_web_prerequisites(analysis, config, progress)
    artifacts = _build_priority_report_artifacts(analysis, config, focus, progress)
    path = output_dir / f"hephaion-priority-{datetime.now(UTC):%Y%m%d-%H%M%S}.pdf"
    sidecar_path = path.with_suffix(".json")
    compiler = compiler or ExternalLatexCompiler.discover()
    tex_path = _compile_priority_report_pdf(
        analysis,
        artifacts.sheet,
        artifacts.tex_text,
        path=path,
        sidecar_path=sidecar_path,
        compiler=compiler,
        keep_tex=keep_tex,
        progress=progress,
    )
    verification = _verify_priority_report_artifacts(
        analysis,
        artifacts,
        path=path,
        sidecar_path=sidecar_path,
        progress=progress,
    )
    _emit_progress(
        progress,
        f"Priority report verified in {_format_elapsed_since(report_started_at)}.",
    )
    return PriorityReport(
        path=path,
        used_model=artifacts.model_payload is not None,
        topic_count=len(analysis.topics),
        source_count=len(set(analysis.past_exam_sources) | set(analysis.material_sources)),
        tex_path=tex_path,
        sidecar_path=sidecar_path,
        verification=verification,
    )


def _analysis_with_optional_web_prerequisites(
    analysis: PriorityAnalysis,
    config: ChatConfig | None,
    progress: PriorityProgressReporter | None,
) -> PriorityAnalysis:
    if not _web_prerequisites_enabled(config):
        return analysis
    _emit_progress(progress, "Checking web-backed prerequisite hints for top topics...")
    return replace(
        analysis,
        topics=tuple(_with_web_prerequisites(list(analysis.topics), _duckduckgo_search)),
    )


def _web_prerequisites_enabled(config: ChatConfig | None) -> bool:
    env_enabled = get_env(_WEB_PREREQ_ENV, "").lower() in {"1", "true", "yes", "on"}
    return env_enabled or (
        config is not None and config.is_feature_enabled("priority_web_prereqs")
    )


def _build_priority_report_artifacts(
    analysis: PriorityAnalysis,
    config: ChatConfig | None,
    focus: str,
    progress: PriorityProgressReporter | None,
) -> _PriorityReportArtifacts:
    _emit_progress(progress, "Building report sections from indexed evidence...")
    model_payload = _priority_report_model_payload(analysis, config, focus, progress)
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
    return _PriorityReportArtifacts(sheet=sheet, tex_text=tex_text, model_payload=model_payload)


def _priority_report_model_payload(
    analysis: PriorityAnalysis,
    config: ChatConfig | None,
    focus: str,
    progress: PriorityProgressReporter | None,
) -> dict[str, object] | None:
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
    _emit_model_payload_progress(model_payload, can_use_model, progress)
    return model_payload


def _emit_model_payload_progress(
    model_payload: dict[str, object] | None,
    can_use_model: bool,
    progress: PriorityProgressReporter | None,
) -> None:
    if model_payload is not None:
        _emit_progress(progress, "Model synthesis complete; grounding to indexed evidence.")
    elif can_use_model:
        _emit_progress(progress, "Model synthesis unavailable; using deterministic local output.")
    else:
        _emit_progress(progress, "Using deterministic local output (no model configured).")


def _verify_priority_report_artifacts(
    analysis: PriorityAnalysis,
    artifacts: _PriorityReportArtifacts,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> PriorityVerificationReport:
    _emit_progress(progress, f"Read compiled PDF {path} for verification.")
    verify_started_at = time.perf_counter()
    verification = verify_priority_output(
        analysis,
        artifacts.sheet,
        artifacts.tex_text,
        pdf_path=path,
    )
    _emit_progress(
        progress,
        f"Ran priority verification checks in {_format_elapsed_since(verify_started_at)}.",
    )
    _write_priority_sidecar(sidecar_path, verification, progress=progress)
    if not verification.passed:
        issue_text = "; ".join(verification.issues) or "verification failed"
        raise PriorityPdfError(f"Priority PDF verification failed: {issue_text}")
    return verification


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
    _emit_model_context_progress(context_chunks, progress)
    conversation = _priority_model_conversation(analysis, focus=focus, chunks=context_chunks)
    _emit_progress(
        progress,
        f"Ran model synthesis {model_name} with {len(context_chunks)} evidence excerpt(s).",
    )
    raw_payload = _read_model_priority_response(
        config,
        conversation,
        model_name,
        progress=progress,
    )
    if raw_payload is None:
        return None
    return _parse_model_priority_payload(raw_payload, progress)


def _parse_model_priority_payload(
    raw_payload: str,
    progress: PriorityProgressReporter | None,
) -> dict[str, object] | None:
    parsed = parse_json_object_fragment(raw_payload)
    if parsed is None:
        _emit_progress(
            progress,
            "Model response was not valid JSON; using deterministic fallback.",
        )
        return None
    _emit_progress(progress, "Parsed model JSON priority payload.")
    return parsed


def _emit_model_context_progress(
    context_chunks: Sequence[PriorityChunk],
    progress: PriorityProgressReporter | None,
) -> None:
    for index, chunk in enumerate(context_chunks, start=1):
        _emit_progress(
            progress,
            f"Read model context {index}/{len(context_chunks)}: "
            f"{_priority_chunk_progress_label(chunk)}.",
        )


def _priority_model_conversation(
    analysis: PriorityAnalysis,
    *,
    focus: str,
    chunks: Sequence[PriorityChunk],
) -> Conversation:
    conversation = Conversation()
    conversation.add("system", f"{_PRIORITY_SYSTEM_PROMPT}\n{_PRIORITY_SCHEMA}")
    conversation.add("user", _priority_model_context(analysis, focus=focus, chunks=chunks))
    return conversation


def _priority_chunk_progress_label(chunk: PriorityChunk) -> str:
    label = (
        f"@{material_display_name(chunk.source)} chunk {chunk.index} "
        f"chars {chunk.char_start}-{chunk.char_end}"
    )
    if chunk.heading:
        label += f' heading "{_truncate(chunk.heading, 56)}"'
    return label


def _read_model_priority_response(
    config: ChatConfig,
    conversation: Conversation,
    model_name: str,
    *,
    progress: PriorityProgressReporter | None,
) -> str | None:
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
                last_progress_at = _emit_model_stream_progress(
                    heartbeat,
                    model_name,
                    started_at=started_at,
                    last_progress_at=last_progress_at,
                    chunk_count=chunk_count,
                    char_count=char_count,
                    progress=progress,
                )
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
    return raw_payload


def _emit_model_stream_progress(
    heartbeat: _ProgressHeartbeat,
    model_name: str,
    *,
    started_at: float,
    last_progress_at: float,
    chunk_count: int,
    char_count: int,
    progress: PriorityProgressReporter | None,
) -> float:
    now = time.perf_counter()
    if chunk_count == 1:
        heartbeat.stop()
        _emit_progress(
            progress,
            f"Read first model delta from {model_name} in {_format_elapsed_since(started_at)}.",
        )
        return now
    if now - last_progress_at < _MODEL_STREAM_PROGRESS_SECONDS:
        return last_progress_at
    _emit_progress(
        progress,
        f"Read {char_count} model character(s) from {model_name} "
        f"across {chunk_count} delta(s) in {_format_elapsed_since(started_at)}.",
    )
    return now


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
    focus_line = f"User focus: {focus}\n" if focus else ""
    return "\n\n".join(
        (
            focus_line + analysis.render_for_prompt(limit=10),
            "Indexed excerpts to analyze:",
            "\n\n".join(_priority_model_evidence_lines(context_chunks)),
        )
    )


def _priority_model_evidence_lines(chunks: Iterable[PriorityChunk]) -> Iterator[str]:
    for idx, chunk in enumerate(chunks, start=1):
        role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
        yield "\n".join(
            (
                f"Evidence {idx}",
                f"Source: {chunk.source}",
                f"Role: {role}",
                f"Heading: {chunk.heading or 'none'}",
                f"Text: {_compact_model_evidence_text(chunk.text)}",
            )
        )


def _compact_model_evidence_text(text: str) -> str:
    compact_text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(compact_text) > 900:
        return f"{compact_text[:899]}…"
    return compact_text


def _representative_chunks(
    analysis: PriorityAnalysis,
    *,
    limit: int = 28,
) -> tuple[PriorityChunk, ...]:
    topic_names = {topic.topic.lower() for topic in analysis.topics}
    preferred_chunks = (
        chunk for chunk in analysis.chunks if _is_priority_model_context(chunk, topic_names)
    )
    return _first_unique_priority_chunks((*preferred_chunks, *analysis.chunks), limit=limit)


def _is_priority_model_context(chunk: PriorityChunk, topic_names: set[str]) -> bool:
    role, _confidence, _reason = infer_material_role_from_text(chunk.source, chunk.text)
    return role == "past_exam" or any(topic in chunk.text.lower() for topic in topic_names)


def _first_unique_priority_chunks(
    chunks: Iterable[PriorityChunk],
    *,
    limit: int,
) -> tuple[PriorityChunk, ...]:
    selected: list[PriorityChunk] = []
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        key = (chunk.source, chunk.text[:120])
        if key in seen:
            continue
        selected.append(chunk)
        seen.add(key)
        if len(selected) >= limit:
            return tuple(selected)
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
        _raise_missing_priority_pdf_engine(
            analysis,
            sheet,
            tex_text,
            path=path,
            sidecar_path=sidecar_path,
            progress=progress,
        )

    with tempfile.TemporaryDirectory(prefix="heph-priority-") as temp_dir_name:
        temp_tex_path = Path(temp_dir_name) / path.with_suffix(".tex").name
        _write_text_artifact(temp_tex_path, tex_text, progress=progress, label="temporary LaTeX")
        try:
            _run_priority_pdf_compiler(compiler, temp_tex_path, path, progress=progress)
        except (OSError, subprocess.CalledProcessError, PriorityPdfError) as exc:
            _raise_priority_pdf_compile_failed(
                exc,
                analysis,
                sheet,
                tex_text,
                path=path,
                sidecar_path=sidecar_path,
                progress=progress,
            )

    if not keep_tex:
        return None
    return _save_priority_tex_source(path, tex_text, progress=progress)


def _raise_missing_priority_pdf_engine(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> NoReturn:
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


def _run_priority_pdf_compiler(
    compiler: PriorityPdfCompiler,
    temp_tex_path: Path,
    path: Path,
    *,
    progress: PriorityProgressReporter | None,
) -> None:
    compile_started_at = time.perf_counter()
    if isinstance(compiler, ExternalLatexCompiler):
        compiler.compile(temp_tex_path, path, progress=progress)
    else:
        _emit_progress(
            progress,
            f"Ran {compiler.__class__.__name__}.compile({temp_tex_path}, {path}).",
        )
        compiler.compile(temp_tex_path, path)
    _emit_progress(
        progress,
        f"PDF compile finished in {_format_elapsed_since(compile_started_at)}.",
    )
    if path.is_file() and not isinstance(compiler, ExternalLatexCompiler):
        _emit_progress(progress, f"Wrote PDF {path} ({path.stat().st_size} bytes).")


def _raise_priority_pdf_compile_failed(
    exc: Exception,
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> NoReturn:
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


def _save_priority_tex_source(
    path: Path,
    tex_text: str,
    *,
    progress: PriorityProgressReporter | None,
) -> Path:
    tex_path = path.with_suffix(".tex")
    _write_text_artifact(tex_path, tex_text, progress=progress, label="LaTeX source")
    return tex_path


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
    checks = _priority_verification_checks(analysis, sheet, tex_text, pdf_path=pdf_path)
    return PriorityVerificationReport(
        extraction_ok=checks.extraction_ok,
        priority_ok=checks.priority_ok,
        source_support_ok=checks.source_support_ok,
        latex_ok=checks.latex_ok,
        pdf_ok=checks.pdf_ok,
        anti_regression_ok=checks.anti_regression_ok,
        practice_ok=checks.practice_ok,
        issues=tuple(_priority_verification_issues(checks)),
        warnings=_priority_verification_warnings(analysis),
    )


def _priority_verification_checks(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    pdf_path: Path | None,
) -> _PriorityVerificationChecks:
    return _PriorityVerificationChecks(
        extraction_ok=bool(analysis.chunks),
        priority_ok=_verify_priority_order(analysis),
        source_support_ok=_verify_sheet_source_support(sheet),
        latex_ok=_verify_latex_text(tex_text),
        pdf_ok=_verify_pdf_artifact(pdf_path),
        anti_regression_ok=_verify_report_text_has_no_forbidden_patterns(tex_text),
        practice_ok=_verify_priority_prompt_context(analysis),
    )


def _verify_sheet_source_support(sheet: PriorityCheatSheet) -> bool:
    return all(topic.source_ids or topic.uncertainty for topic in sheet.topics)


def _verify_pdf_artifact(pdf_path: Path | None) -> bool:
    return pdf_path is not None and pdf_path.is_file() and pdf_path.stat().st_size > 0


def _verify_report_text_has_no_forbidden_patterns(tex_text: str) -> bool:
    return "HEPHAION PRIORITY" not in tex_text and not _FORBIDDEN_REPORT_RE.search(tex_text)


def _verify_priority_prompt_context(analysis: PriorityAnalysis) -> bool:
    return bool(analysis.topics) and not _RAW_METRIC_RE.search(analysis.render_for_prompt(limit=8))


def _priority_verification_issues(checks: _PriorityVerificationChecks) -> Iterator[str]:
    issue_specs = (
        (checks.extraction_ok, "no indexed chunks were available"),
        (checks.priority_ok, "top priorities are not supported by past-exam signals"),
        (
            checks.source_support_ok,
            "one or more topic sections lack source IDs or uncertainty labels",
        ),
        (checks.latex_ok, "generated LaTeX failed syntax or anti-debug checks"),
        (checks.pdf_ok, "compiled PDF was not produced"),
        (
            checks.anti_regression_ok,
            "report text contains a forbidden raw metric or boilerplate pattern",
        ),
        (checks.practice_ok, "priority context is empty or exposes raw metric strings"),
    )
    yield from (message for passed, message in issue_specs if not passed)


def _priority_verification_warnings(analysis: PriorityAnalysis) -> tuple[str, ...]:
    if analysis.past_exam_sources:
        return ()
    return ("no past-exam sources were identified from content",)


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
    source_labels = tuple(source_ids[source] for source in topic.sources if source in source_ids)
    sections = _cheat_sheet_topic_sections(topic, analysis, model_payload=model_payload)
    return PriorityCheatSheetTopic(
        title=topic.topic,
        tier=priority_tier(topic),
        source_ids=source_labels,
        prerequisites=_topic_prerequisites(topic),
        definitions=tuple(sections.definitions[:3]),
        formulas=tuple(sections.formulas[:4]),
        procedures=tuple(sections.procedures[:3]),
        exam_tasks=tuple(sections.exam_tasks[:4]),
        pitfalls=tuple(sections.pitfalls[:3]),
        uncertainty=_topic_uncertainty(
            topic,
            definitions=sections.definitions,
            formulas=sections.formulas,
            procedures=sections.procedures,
        ),
    )


def _cheat_sheet_topic_sections(
    topic: PriorityTopic,
    analysis: PriorityAnalysis,
    *,
    model_payload: dict[str, object] | None,
) -> _CheatSheetTopicSections:
    payload = _topic_model_payload(topic, model_payload)
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
    return _CheatSheetTopicSections(
        definitions=definitions,
        formulas=formulas,
        procedures=procedures,
        exam_tasks=exam_tasks,
        pitfalls=pitfalls,
    )


def _topic_model_payload(
    topic: PriorityTopic,
    model_payload: dict[str, object] | None,
) -> dict[str, object] | None:
    raw_topics = model_payload.get("topics") if model_payload is not None else None
    if not isinstance(raw_topics, list):
        return None
    topic_name = topic.topic.lower()
    for raw_topic in raw_topics:
        if matched_topic := _payload_topic_entry(raw_topic, topic_name):
            return matched_topic
    return None


def _payload_topic_entry(raw_topic: object, topic_name: str) -> dict[str, object] | None:
    if not is_string_mapping(raw_topic):
        return None
    raw_name = raw_topic.get("name")
    if isinstance(raw_name, str) and raw_name.strip().lower() == topic_name:
        return dict(raw_topic)
    return None


def _topic_uncertainty(
    topic: PriorityTopic,
    *,
    definitions: list[str],
    formulas: list[str],
    procedures: list[str],
) -> tuple[str, ...]:
    uncertainty: list[str] = []
    if not definitions and not formulas and not procedures:
        uncertainty.append(
            "Indexed materials do not expose enough factual content for this topic."
        )
    if topic.confidence < 0.45:
        uncertainty.append("Extraction confidence is limited; verify against the cited sources.")
    return tuple(uncertainty)


def _analysis_uncertainties(
    analysis: PriorityAnalysis,
    topics: tuple[PriorityCheatSheetTopic, ...],
) -> tuple[str, ...]:
    if not analysis.past_exam_sources:
        return ("No past exams were identified; ranking falls back to material coverage.",)
    return tuple(_analysis_uncertainty_items(analysis, topics))


def _analysis_uncertainty_items(
    analysis: PriorityAnalysis,
    topics: tuple[PriorityCheatSheetTopic, ...],
) -> Iterator[str]:
    if not analysis.exam_questions:
        yield "Past exams were found, but question extraction was incomplete."
    if any(topic.uncertainty for topic in topics):
        yield "Some topics lack enough local factual support for full cheat-sheet blocks."


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
    selected = [sentence for sentence in sentences if _sentence_has_keyword(sentence, keywords)]
    if selected or not fallback:
        return selected
    return sentences[:2]


def _sentence_has_keyword(sentence: str, keywords: tuple[str, ...]) -> bool:
    lowered = sentence.lower()
    return any(keyword in lowered for keyword in keywords)


def _select_formula_lines(topic: PriorityTopic) -> list[str]:
    lines: list[str] = []
    for evidence in topic.evidence:
        lines.extend(
            line
            for unit in re.split(r"(?<=[.!?])\s+|\n", evidence.excerpt)
            if (line := _formula_line(unit))
        )
    return lines


def _formula_line(text: str) -> str:
    line = _WHITESPACE_RE.sub(" ", text).strip()
    return line if line and _looks_like_formula_line(line) else ""


def _looks_like_formula_line(line: str) -> bool:
    return "$" in line or "\\" in line or re.search(r"[=∑∫√≤≥→]", line) is not None


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
    for predicate, tier in _PRIORITY_TIER_RULES:
        if predicate(topic):
            return tier
    return "Supporting"


def _exam_core_topic(topic: PriorityTopic) -> bool:
    return topic.exam_marks >= 12 or topic.exam_hits >= 3


def _high_yield_topic(topic: PriorityTopic) -> bool:
    return topic.exam_marks >= 6 or topic.exam_hits >= 2


def _foundation_topic(topic: PriorityTopic) -> bool:
    return bool(topic.exam_hits)


def _prerequisite_topic(topic: PriorityTopic) -> bool:
    return topic.supporting_material_coverage >= 2 or topic.material_hits >= 3


_PRIORITY_TIER_RULES: tuple[tuple[Callable[[PriorityTopic], bool], str], ...] = (
    (_exam_core_topic, "Exam core"),
    (_high_yield_topic, "High-yield"),
    (_foundation_topic, "Foundation"),
    (_prerequisite_topic, "Prerequisite"),
)


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
    return any(
        value.startswith(open_delimiter) and value.endswith(close_delimiter)
        for open_delimiter, close_delimiter in _LATEX_MATH_DELIMITERS
    )


def _is_safe_latex_math(value: str) -> bool:
    if not _looks_like_latex_math(value):
        return False
    content = _latex_math_content(value)
    if not content or _LATEX_MATH_UNSAFE_CHAR_RE.search(content):
        return False
    return all(
        _allowed_latex_math_command(match) for match in _LATEX_MATH_COMMAND_RE.finditer(content)
    )


def _allowed_latex_math_command(match: re.Match[str]) -> bool:
    command = match.group(1)
    if command.isalpha():
        return command in _ALLOWED_LATEX_MATH_COMMANDS
    return command in _ALLOWED_LATEX_MATH_SYMBOL_COMMANDS


def _latex_math_content(value: str) -> str:
    for open_delimiter, close_delimiter in _LATEX_MATH_DELIMITERS:
        if value.startswith(open_delimiter) and value.endswith(close_delimiter):
            return value[len(open_delimiter) : -len(close_delimiter)]
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
    value = _payload_list_value(payload, key)
    if not isinstance(value, list):
        return []
    return [item for item in (_payload_string_item(item) for item in value) if item]


def _payload_list_value(payload: dict[str, object] | None, key: str) -> object:
    return payload.get(key) if payload is not None else None


def _payload_string_item(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
