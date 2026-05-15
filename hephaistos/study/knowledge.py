"""Source-traceable academic item extraction from indexed study chunks."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Protocol

_HEADING_RE = re.compile(r"^\s{0,3}(?:#{1,6}\s+|\d+(?:\.\d+)*[.)]\s+)(?P<text>.+?)\s*$")
_HEADING_CONTEXT_PREFIX_RE = re.compile(
    r"^(?:lecture|vorlesung|chapter|kapitel|unit|session)\s+\d+[a-z]?\s*[-:]\s*",
    re.IGNORECASE,
)
_SOURCE_LABEL_CONTEXT_RE = re.compile(
    r"^(?:lecture|vorlesung|chapter|kapitel|unit|session)\s+"
    r"(?P<number>\d+[a-z]?)\s*[-:]\s*(?P<title>.+)$",
    re.IGNORECASE,
)
_DEFINITION_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<term>[A-ZÀ-ÖØ-Þa-zà-öø-ÿ][^:.\n]{2,80}?)\s+"
    r"(?:is|are|means|refers to|describes|represents|studies|ist|sind|bedeutet)\s+"
    r"(?P<body>[^.\n]{8,260})(?:[.]|$)",
    re.IGNORECASE,
)
_FORMULA_RE = re.compile(
    r"(?:"
    r"\b(?:formula|equation|identity|rule|satz|gleichung)\b[^.\n:]{0,80}[:]\s*(?P<labelled>.+)"
    r"|(?P<symbolic>[A-Za-z][A-Za-z0-9_]*\s*(?:=|≈|≃|<=|>=|≤|≥|->|→)\s*[^.\n]{2,160})"
    r")",
    re.IGNORECASE,
)
_EXAMPLE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:example|beispiel)\s*[:.-]\s*(?P<body>[^.\n]{8,260})",
    re.IGNORECASE,
)
_MISCONCEPTION_RE = re.compile(
    r"\b(?:common misconception|misconception|pitfall|trap|fehler|falle)\b[:\s-]+"
    r"(?P<body>[^.\n]{8,260})",
    re.IGNORECASE,
)
_OBJECTIVE_RE = re.compile(
    r"\b(?:learning objective|lernziel|students should|you should be able to)\b[:\s-]+"
    r"(?P<body>[^.\n]{8,260})",
    re.IGNORECASE,
)
_RUBRIC_RE = re.compile(
    r"\b(?:rubric|mark scheme|marks?|points?|punkte?)\b[:\s-]+(?P<body>[^.\n]{4,260})",
    re.IGNORECASE,
)
_FIGURE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:figure|fig[.]?|abbildung)\s*\d*[.:)-]?\s*(?P<body>[^.\n]{4,260})",
    re.IGNORECASE,
)
_TABLE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:table|tab[.]?|tabelle)\s*\d*[.:)-]?\s*(?P<body>[^.\n]{4,260})",
    re.IGNORECASE,
)
_EXAM_QUESTION_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:question|frage|aufgabe)\s*\d*[^\]:.]{0,40}"
    r"(?:\[[^\]]+\])?\s*[:.-]\s*(?P<body>[^.\n]{4,260})",
    re.IGNORECASE,
)
_ANSWER_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:answer|solution|lösung|loesung|musterlösung|musterloesung)"
    r"\s*[:.-]\s*(?P<body>[^.\n]{4,260})",
    re.IGNORECASE,
)
_WHITESPACE_RE = re.compile(r"\s+")
_METADATA_CONCEPT_RE = re.compile(
    r"\b(?:"
    r"all rights reserved|copyright|date|dozent|dozentin|email|instructor|lecturer|"
    r"page|professor|seite|semester|slide|universität|university|www|http"
    r")\b",
    re.IGNORECASE,
)
_DATE_ONLY_RE = re.compile(
    r"^\s*(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+\w+\s+\d{4}|\d{4})\s*$",
    re.IGNORECASE,
)
_BAD_DEFINITION_TERMS = frozenset(
    {
        "als hilfsmittel",
        "this",
        "these",
        "that",
        "those",
        "it",
        "es",
        "dies",
        "diese",
    }
)
_QUESTION_METADATA_OR_INTERNAL_RE = re.compile(
    r"\b(?:"
    r"all rights reserved|copyright|date|dozent|dozentin|email|instructor|lecturer|"
    r"page|professor|seite|semester|slide|source[-\s]?backed|source[-\s]?supported|"
    r"source question|source field|chunk|filename|file name|www|http"
    r")\b|#chunk=|\bmaterials[/\\]",
    re.IGNORECASE,
)
_SOURCE_LABEL_METADATA_RE = re.compile(
    r"\b(?:"
    r"all rights reserved|copyright|date|dozent|dozentin|email|instructor|lecturer|"
    r"page|professor|seite|semester|slide|source[-\s]?backed|source[-\s]?supported|"
    r"source field|chunk|filename|file name|www|http"
    r")\b|#chunk=|\bmaterials[/\\]|[.](?:md|pdf|pptx?|docx?|txt)\b",
    re.IGNORECASE,
)
_ACTIVE_RECALL_PROMPT_RE = re.compile(
    r"^\s*(?:"
    r"cloze deletion|compare|correct|define|explain|fill|in one|multiple choice|"
    r"past[- ]exam style|state|what|why"
    r")\b|[?]",
    re.IGNORECASE,
)
_QUESTION_SECOND_TASK_RE = re.compile(
    r"\b(?:and|also|then)\s+(?:"
    r"calculate|compare|compute|define|derive|describe|determine|explain|give|"
    r"identify|justify|list|name|outline|show|state|summarize|what|when|why"
    r")\b",
    re.IGNORECASE,
)


class KnowledgeChunk(Protocol):
    """Minimal chunk shape needed to extract traceable academic items."""

    source: str
    index: int
    text: str


class AcademicItemKind(StrEnum):
    """Kinds of source-grounded academic items Hephaistos can extract locally."""

    CONCEPT = "concept"
    DEFINITION = "definition"
    FORMULA = "formula"
    EXAMPLE = "example"
    FIGURE = "figure"
    TABLE = "table"
    EXAM_QUESTION = "exam_question"
    ANSWER = "answer"
    RUBRIC_POINT = "rubric_point"
    COMMON_MISCONCEPTION = "common_misconception"
    LEARNING_OBJECTIVE = "learning_objective"
    EXAM_SKILL = "exam_skill"


@dataclass(frozen=True, slots=True)
class AcademicItem:
    """A small source-traceable unit suitable for later graph construction."""

    kind: AcademicItemKind
    text: str
    source_ref: str
    concept: str = ""
    source_label: str = ""


@dataclass(frozen=True, slots=True)
class CourseKnowledgeNode:
    """A concept-centered view of source-grounded academic items."""

    concept: str
    source_refs: tuple[str, ...] = ()
    source_labels: tuple[str, ...] = ()
    definitions: tuple[str, ...] = ()
    formulas: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    figures: tuple[str, ...] = ()
    tables: tuple[str, ...] = ()
    exam_questions: tuple[str, ...] = ()
    answers: tuple[str, ...] = ()
    rubric_points: tuple[str, ...] = ()
    common_misconceptions: tuple[str, ...] = ()
    learning_objectives: tuple[str, ...] = ()
    exam_skills: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CourseKnowledgeGraph:
    """Small deterministic course graph built only from extracted source items."""

    nodes: tuple[CourseKnowledgeNode, ...]
    unassigned_items: tuple[AcademicItem, ...] = ()


@dataclass(frozen=True, slots=True)
class GroundedStudyQuestion:
    """A generated study question with explicit source grounding."""

    question: str
    question_type: str
    concept: str
    grounding_source_refs: tuple[str, ...]
    source_label: str = ""
    difficulty: str = "core"


def extract_academic_items(
    chunks: Sequence[KnowledgeChunk],
    *,
    limit_per_chunk: int = 12,
) -> list[AcademicItem]:
    """Extract traceable academic items from indexed material chunks.

    This intentionally favors readable deterministic rules over broad recall:
    unsupported model knowledge is never used, and every item points back to the
    exact chunk that produced it.
    """
    items: list[AcademicItem] = []
    seen: set[tuple[AcademicItemKind, str, str]] = set()
    for chunk in chunks:
        source_ref = f"{chunk.source}#chunk={chunk.index}"
        source_label = _source_label_for_chunk(chunk)
        chunk_items = _items_from_chunk(chunk.text, source_ref, source_label)
        for item in chunk_items[: max(0, limit_per_chunk)]:
            key = (item.kind, item.text.casefold(), item.source_ref)
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
    return items


def build_course_knowledge_graph(items: Sequence[AcademicItem]) -> CourseKnowledgeGraph:
    """Group extracted academic items into concept-centered graph nodes.

    Items without an explicit concept are attached to the latest concept seen in
    the same source chunk. If no such concept exists, they stay unassigned so the
    caller can avoid pretending unsupported graph edges exist.
    """
    builders: dict[str, _NodeBuilder] = {}
    active_concept_by_source_ref: dict[str, str] = {}
    unassigned: list[AcademicItem] = []

    for item in items:
        concept = item.concept or active_concept_by_source_ref.get(item.source_ref, "")
        if item.kind is AcademicItemKind.CONCEPT:
            concept = item.concept or item.text
        if not concept:
            unassigned.append(item)
            continue
        active_concept_by_source_ref[item.source_ref] = concept
        builder = builders.setdefault(concept.casefold(), _NodeBuilder(concept=concept))
        builder.add(item)

    nodes = tuple(builder.to_node() for _key, builder in sorted(builders.items()))
    return CourseKnowledgeGraph(nodes=nodes, unassigned_items=tuple(unassigned))


def generate_grounded_study_questions(
    graph: CourseKnowledgeGraph,
    *,
    limit_per_concept: int = 4,
) -> list[GroundedStudyQuestion]:
    """Generate high-yield active-recall questions only from grounded graph nodes."""
    questions: list[GroundedStudyQuestion] = []
    seen: set[tuple[str, str]] = set()
    for node in graph.nodes:
        if not node.source_refs or not _node_is_question_worthy(node):
            continue
        candidates = _questions_for_node(node)
        for question in candidates[: max(0, limit_per_concept)]:
            key = (question.question_type, question.question.casefold())
            if key in seen:
                continue
            seen.add(key)
            questions.append(question)
    return questions


def grounded_study_question_quality_issues(question: GroundedStudyQuestion) -> tuple[str, ...]:
    """Return conservative quality issues for a generated active-recall question."""
    issues: list[str] = []
    text = question.question.strip()
    if not question.grounding_source_refs:
        issues.append("missing grounding source refs")
    if not question.source_label.strip():
        issues.append("missing canonical source label")
    elif _SOURCE_LABEL_METADATA_RE.search(question.source_label):
        issues.append("source label contains metadata or internal source wording")
    if not _ACTIVE_RECALL_PROMPT_RE.search(text):
        issues.append("not framed as active recall")
    if text.count("?") > 1:
        issues.append("asks more than one question")
    if _QUESTION_SECOND_TASK_RE.search(text):
        issues.append("asks more than one thing")
    if _QUESTION_METADATA_OR_INTERNAL_RE.search(text):
        issues.append("contains metadata or internal source wording")
    if _METADATA_CONCEPT_RE.search(question.concept):
        issues.append("uses metadata-like concept")
    return tuple(issues)


def _items_from_chunk(text: str, source_ref: str, source_label: str) -> list[AcademicItem]:
    items: list[AcademicItem] = []
    for line in text.splitlines():
        cleaned = _clean(line)
        if not cleaned:
            continue
        heading = _heading(cleaned)
        if heading is not None:
            items.append(
                AcademicItem(
                    kind=AcademicItemKind.CONCEPT,
                    text=heading,
                    source_ref=source_ref,
                    concept=heading,
                    source_label=source_label,
                )
            )
    for paragraph in _paragraphs(text):
        definition = _definition(paragraph, source_ref, source_label)
        if definition is not None:
            items.append(definition)
        formula = _formula(paragraph, source_ref, source_label)
        if formula is not None:
            items.append(formula)
        example = _captured_item(
            _EXAMPLE_RE,
            paragraph,
            source_ref,
            AcademicItemKind.EXAMPLE,
            source_label,
        )
        if example is not None:
            items.append(example)
        misconception = _captured_item(
            _MISCONCEPTION_RE,
            paragraph,
            source_ref,
            AcademicItemKind.COMMON_MISCONCEPTION,
            source_label,
        )
        if misconception is not None:
            items.append(misconception)
        objective = _captured_item(
            _OBJECTIVE_RE,
            paragraph,
            source_ref,
            AcademicItemKind.LEARNING_OBJECTIVE,
            source_label,
        )
        if objective is not None:
            items.append(objective)
        rubric = _captured_item(
            _RUBRIC_RE,
            paragraph,
            source_ref,
            AcademicItemKind.EXAM_SKILL,
            source_label,
        )
        if rubric is not None:
            items.append(rubric)
            items.append(
                AcademicItem(
                    kind=AcademicItemKind.RUBRIC_POINT,
                    text=rubric.text,
                    source_ref=rubric.source_ref,
                    concept=rubric.concept,
                    source_label=rubric.source_label,
                )
            )
        figure = _captured_item(
            _FIGURE_RE,
            paragraph,
            source_ref,
            AcademicItemKind.FIGURE,
            source_label,
        )
        if figure is not None:
            items.append(figure)
        table = _captured_item(
            _TABLE_RE,
            paragraph,
            source_ref,
            AcademicItemKind.TABLE,
            source_label,
        )
        if table is not None:
            items.append(table)
        exam_question = _captured_item(
            _EXAM_QUESTION_RE,
            paragraph,
            source_ref,
            AcademicItemKind.EXAM_QUESTION,
            source_label,
        )
        if exam_question is not None:
            items.append(exam_question)
        answer = _captured_item(
            _ANSWER_RE,
            paragraph,
            source_ref,
            AcademicItemKind.ANSWER,
            source_label,
        )
        if answer is not None:
            items.append(answer)
    return items


def _heading(line: str) -> str | None:
    match = _HEADING_RE.match(line)
    if match is None:
        return None
    heading = _heading_context_prefix_removed(_clean(match.group("text")))
    if len(heading) < 3 or len(heading.split()) > 10:
        return None
    return heading


def _heading_context_prefix_removed(heading: str) -> str:
    return _clean(_HEADING_CONTEXT_PREFIX_RE.sub("", heading, count=1))


def _definition(line: str, source_ref: str, source_label: str) -> AcademicItem | None:
    match = _DEFINITION_RE.match(line)
    if match is None:
        return None
    concept = _clean(match.group("term")).rstrip(":")
    body = _clean(match.group("body"))
    if (
        not concept
        or not body
        or "," in concept
        or len(concept.split()) > 8
        or concept.casefold() in _BAD_DEFINITION_TERMS
    ):
        return None
    return AcademicItem(
        kind=AcademicItemKind.DEFINITION,
        text=f"{concept}: {body}",
        source_ref=source_ref,
        concept=concept,
        source_label=source_label,
    )


def _formula(line: str, source_ref: str, source_label: str) -> AcademicItem | None:
    match = _FORMULA_RE.search(line)
    if match is None:
        return None
    text = _clean(match.group("labelled") or match.group("symbolic") or "")
    if not text or len(text) < 4:
        return None
    return AcademicItem(
        kind=AcademicItemKind.FORMULA,
        text=text,
        source_ref=source_ref,
        source_label=source_label,
    )


def _captured_item(
    pattern: re.Pattern[str],
    line: str,
    source_ref: str,
    kind: AcademicItemKind,
    source_label: str,
) -> AcademicItem | None:
    match = pattern.search(line)
    if match is None:
        return None
    text = _clean(match.group("body"))
    if not text:
        return None
    return AcademicItem(kind=kind, text=text, source_ref=source_ref, source_label=source_label)


def _source_label_for_chunk(chunk: KnowledgeChunk) -> str:
    heading = _clean(str(getattr(chunk, "heading", "")))
    if heading:
        return _canonical_source_label_text(heading)
    heading_label = _source_label_from_text_heading(chunk.text)
    if heading_label:
        return heading_label
    return _source_label_from_ref(f"{chunk.source}#chunk={chunk.index}")


def _source_label_from_text_heading(text: str) -> str:
    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if match is not None:
            return _canonical_source_label_text(match.group("text"))
    return ""


def _source_label_from_ref(source_ref: str) -> str:
    source = source_ref.split("#", maxsplit=1)[0]
    name = PurePosixPath(source.replace("\\", "/")).name or source
    stem = name.rsplit(".", maxsplit=1)[0]
    return _canonical_source_label_text(stem)


def _canonical_source_label_text(text: str) -> str:
    cleaned = _clean(text.replace("_", " "))
    match = _SOURCE_LABEL_CONTEXT_RE.match(cleaned)
    if match is not None:
        return _clean(f"{match.group('number')} {match.group('title')}")
    label = cleaned.replace("-", " ")
    return _clean(label) or cleaned


def _clean(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip(" \t-:;")


def _paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = _clean(raw_line)
        if not line:
            if current:
                paragraphs.append(_clean(" ".join(current)))
                current = []
            continue
        if _heading(line) is not None:
            if current:
                paragraphs.append(_clean(" ".join(current)))
                current = []
            continue
        if raw_line.lstrip().startswith(("- ", "* ", "+ ")):
            if current:
                paragraphs.append(_clean(" ".join(current)))
                current = []
            paragraphs.append(line)
            continue
        if _starts_cued_item(line):
            if current:
                paragraphs.append(_clean(" ".join(current)))
                current = []
            paragraphs.append(line)
            continue
        current.append(line)
    if current:
        paragraphs.append(_clean(" ".join(current)))
    return paragraphs


def _starts_cued_item(line: str) -> bool:
    return bool(
        re.match(
            r"^(?:example|beispiel|common misconception|misconception|pitfall|trap|"
            r"learning objective|lernziel|rubric|mark scheme|figure|fig[.]?|abbildung|"
            r"table|tab[.]?|tabelle|question|frage|aufgabe|answer|solution|lösung|"
            r"loesung|musterlösung|musterloesung)\b",
            line,
            re.IGNORECASE,
        )
    )


def _questions_for_node(node: CourseKnowledgeNode) -> list[GroundedStudyQuestion]:
    questions: list[GroundedStudyQuestion] = []
    if not _node_is_question_worthy(node):
        return questions
    if node.definitions:
        questions.append(
            _question(
                f"Define {node.concept} using the course material.",
                question_type="free_recall",
                node=node,
                difficulty="core",
            )
        )
        questions.append(
            _question(
                f"Cloze deletion: {node.concept} is _____. Fill the blank.",
                question_type="cloze_deletion",
                node=node,
                difficulty="core",
            )
        )
        questions.append(
            _question(
                f"In one or two sentences, state the key idea of {node.concept}.",
                question_type="short_answer",
                node=node,
                difficulty="core",
            )
        )
    if node.formulas:
        questions.append(
            _question(
                f"State the formula or formal condition associated with {node.concept}.",
                question_type="formula_recall",
                node=node,
                difficulty="core",
            )
        )
    if node.examples:
        questions.append(
            _question(
                f"Why does this example fit {node.concept}: {node.examples[0]}?",
                question_type="application_scenario",
                node=node,
                difficulty="transfer",
            )
        )
    if node.tables:
        questions.append(
            _question(
                f"What key pattern does the table show for {node.concept}?",
                question_type="data_interpretation",
                node=node,
                difficulty="transfer",
            )
        )
    if node.exam_questions:
        questions.append(
            _question(
                f"Past-exam style: {node.exam_questions[0]}",
                question_type="past_exam_style",
                node=node,
                difficulty="exam",
            )
        )
    if node.common_misconceptions:
        questions.append(
            _question(
                f"Correct this misconception about {node.concept}: "
                f"{node.common_misconceptions[0]}",
                question_type="error_correction",
                node=node,
                difficulty="misconception",
            )
        )
        if node.definitions:
            questions.append(
                _question(
                    f"Multiple choice: which statement best matches {node.concept}? "
                    f"A. {node.definitions[0]} B. {node.common_misconceptions[0]}",
                    question_type="multiple_choice",
                    node=node,
                    difficulty="misconception",
                )
            )
    if node.exam_skills:
        questions.append(
            _question(
                f"Past-exam style: {node.exam_skills[0]}",
                question_type="past_exam_style",
                node=node,
                difficulty="exam",
            )
        )
        if "compar" in node.exam_skills[0].casefold():
            questions.append(
                _question(
                    f"Compare and contrast: {node.exam_skills[0]}",
                    question_type="compare_and_contrast",
                    node=node,
                    difficulty="transfer",
                )
            )
    if node.learning_objectives:
        questions.append(
            _question(
                f"Explain the learning objective for {node.concept}: "
                f"{node.learning_objectives[0]}",
                question_type="explain_the_mechanism",
                node=node,
                difficulty="core",
            )
        )
    return questions


def _node_is_question_worthy(node: CourseKnowledgeNode) -> bool:
    concept = node.concept.strip()
    if not concept or _DATE_ONLY_RE.fullmatch(concept):
        return False
    return not _METADATA_CONCEPT_RE.search(concept)


def _question(
    text: str,
    *,
    question_type: str,
    node: CourseKnowledgeNode,
    difficulty: str,
) -> GroundedStudyQuestion:
    return GroundedStudyQuestion(
        question=text,
        question_type=question_type,
        concept=node.concept,
        grounding_source_refs=node.source_refs,
        source_label=_question_source_label(node),
        difficulty=difficulty,
    )


def _question_source_label(node: CourseKnowledgeNode) -> str:
    if node.source_labels:
        return "; ".join(node.source_labels)
    labels = tuple(_source_label_from_ref(ref) for ref in node.source_refs)
    return "; ".join(dict.fromkeys(label for label in labels if label))


@dataclass(slots=True)
class _NodeBuilder:
    concept: str
    source_refs: list[str] = field(default_factory=list)
    source_labels: list[str] = field(default_factory=list)
    definitions: list[str] = field(default_factory=list)
    formulas: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    exam_questions: list[str] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    rubric_points: list[str] = field(default_factory=list)
    common_misconceptions: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    exam_skills: list[str] = field(default_factory=list)

    def add(self, item: AcademicItem) -> None:
        _append_unique(self.source_refs, item.source_ref)
        _append_unique(self.source_labels, item.source_label)
        if item.kind is AcademicItemKind.DEFINITION:
            _append_unique(self.definitions, item.text)
        elif item.kind is AcademicItemKind.FORMULA:
            _append_unique(self.formulas, item.text)
        elif item.kind is AcademicItemKind.EXAMPLE:
            _append_unique(self.examples, item.text)
        elif item.kind is AcademicItemKind.FIGURE:
            _append_unique(self.figures, item.text)
        elif item.kind is AcademicItemKind.TABLE:
            _append_unique(self.tables, item.text)
        elif item.kind is AcademicItemKind.EXAM_QUESTION:
            _append_unique(self.exam_questions, item.text)
        elif item.kind is AcademicItemKind.ANSWER:
            _append_unique(self.answers, item.text)
        elif item.kind is AcademicItemKind.RUBRIC_POINT:
            _append_unique(self.rubric_points, item.text)
        elif item.kind is AcademicItemKind.COMMON_MISCONCEPTION:
            _append_unique(self.common_misconceptions, item.text)
        elif item.kind is AcademicItemKind.LEARNING_OBJECTIVE:
            _append_unique(self.learning_objectives, item.text)
        elif item.kind is AcademicItemKind.EXAM_SKILL:
            _append_unique(self.exam_skills, item.text)

    def to_node(self) -> CourseKnowledgeNode:
        return CourseKnowledgeNode(
            concept=self.concept,
            source_refs=tuple(self.source_refs),
            source_labels=tuple(self.source_labels),
            definitions=tuple(self.definitions),
            formulas=tuple(self.formulas),
            examples=tuple(self.examples),
            figures=tuple(self.figures),
            tables=tuple(self.tables),
            exam_questions=tuple(self.exam_questions),
            answers=tuple(self.answers),
            rubric_points=tuple(self.rubric_points),
            common_misconceptions=tuple(self.common_misconceptions),
            learning_objectives=tuple(self.learning_objectives),
            exam_skills=tuple(self.exam_skills),
        )


def _append_unique(target: list[str], value: str) -> None:
    if value and value not in target:
        target.append(value)
