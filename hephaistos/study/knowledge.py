"""Source-traceable academic item extraction from indexed study chunks."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Protocol, cast

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
_METADATA_TERMS = (
    r"all rights reserved|copyright|date|dozent|dozentin|email|instructor|lecturer|"
    r"page|professor|seite|semester|slide"
)
_SOURCE_INTERNAL_TERMS = (
    r"source[-\s]?backed|source[-\s]?supported|source field|chunk|filename|file name"
)
_METADATA_CONCEPT_RE = re.compile(
    rf"\b(?:{_METADATA_TERMS}|universität|university|www|http)\b",
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
    rf"\b(?:{_METADATA_TERMS}|{_SOURCE_INTERNAL_TERMS}|source question|www|http)\b"
    r"|#chunk=|\bmaterials[/\\]",
    re.IGNORECASE,
)
_SOURCE_LABEL_METADATA_RE = re.compile(
    rf"\b(?:{_METADATA_TERMS}|{_SOURCE_INTERNAL_TERMS}|www|http)\b"
    r"|#chunk=|\bmaterials[/\\]|[.](?:md|pdf|pptx?|docx?|txt)\b",
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
    source: str
    index: int
    text: str


class AcademicItemKind(StrEnum):
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


_PARAGRAPH_ITEM_PATTERNS: tuple[tuple[re.Pattern[str], AcademicItemKind], ...] = (
    (_EXAMPLE_RE, AcademicItemKind.EXAMPLE),
    (_MISCONCEPTION_RE, AcademicItemKind.COMMON_MISCONCEPTION),
    (_OBJECTIVE_RE, AcademicItemKind.LEARNING_OBJECTIVE),
    (_RUBRIC_RE, AcademicItemKind.EXAM_SKILL),
    (_FIGURE_RE, AcademicItemKind.FIGURE),
    (_TABLE_RE, AcademicItemKind.TABLE),
    (_EXAM_QUESTION_RE, AcademicItemKind.EXAM_QUESTION),
    (_ANSWER_RE, AcademicItemKind.ANSWER),
)
_NODE_ITEM_FIELDS = {
    AcademicItemKind.DEFINITION: "definitions",
    AcademicItemKind.FORMULA: "formulas",
    AcademicItemKind.EXAMPLE: "examples",
    AcademicItemKind.FIGURE: "figures",
    AcademicItemKind.TABLE: "tables",
    AcademicItemKind.EXAM_QUESTION: "exam_questions",
    AcademicItemKind.ANSWER: "answers",
    AcademicItemKind.RUBRIC_POINT: "rubric_points",
    AcademicItemKind.COMMON_MISCONCEPTION: "common_misconceptions",
    AcademicItemKind.LEARNING_OBJECTIVE: "learning_objectives",
    AcademicItemKind.EXAM_SKILL: "exam_skills",
}


@dataclass(frozen=True, slots=True)
class AcademicItem:
    kind: AcademicItemKind
    text: str
    source_ref: str
    concept: str = ""
    source_label: str = ""


@dataclass(frozen=True, slots=True)
class CourseKnowledgeNode:
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
    nodes: tuple[CourseKnowledgeNode, ...]
    unassigned_items: tuple[AcademicItem, ...] = ()


@dataclass(frozen=True, slots=True)
class GroundedStudyQuestion:
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
        definition_match = _DEFINITION_RE.match(paragraph)
        if definition_match is not None:
            concept = _clean(definition_match.group("term")).rstrip(":")
            body = _clean(definition_match.group("body"))
            if (
                concept
                and body
                and "," not in concept
                and len(concept.split()) <= 8
                and concept.casefold() not in _BAD_DEFINITION_TERMS
            ):
                items.append(
                    AcademicItem(
                        kind=AcademicItemKind.DEFINITION,
                        text=f"{concept}: {body}",
                        source_ref=source_ref,
                        concept=concept,
                        source_label=source_label,
                    )
                )
        formula_match = _FORMULA_RE.search(paragraph)
        if formula_match is not None:
            formula_text = _clean(
                formula_match.group("labelled") or formula_match.group("symbolic") or ""
            )
            if len(formula_text) >= 4:
                items.append(
                    AcademicItem(
                        kind=AcademicItemKind.FORMULA,
                        text=formula_text,
                        source_ref=source_ref,
                        source_label=source_label,
                    )
                )
        for pattern, kind in _PARAGRAPH_ITEM_PATTERNS:
            match = pattern.search(paragraph)
            if match is not None and (item_text := _clean(match.group("body"))):
                item = AcademicItem(
                    kind=kind,
                    text=item_text,
                    source_ref=source_ref,
                    source_label=source_label,
                )
                items.append(item)
                if kind is AcademicItemKind.EXAM_SKILL:
                    items.append(
                        AcademicItem(
                            kind=AcademicItemKind.RUBRIC_POINT,
                            text=item.text,
                            source_ref=item.source_ref,
                            concept=item.concept,
                            source_label=item.source_label,
                        )
                    )
    return items


def _heading(line: str) -> str | None:
    match = _HEADING_RE.match(line)
    if match is None:
        return None
    heading = _clean(_HEADING_CONTEXT_PREFIX_RE.sub("", _clean(match.group("text")), count=1))
    if len(heading) < 3 or len(heading.split()) > 10:
        return None
    return heading


def _source_label_for_chunk(chunk: KnowledgeChunk) -> str:
    heading = _clean(str(getattr(chunk, "heading", "")))
    if heading:
        return _canonical_source_label_text(heading)
    for line in chunk.text.splitlines():
        if match := _HEADING_RE.match(line):
            return _canonical_source_label_text(match.group("text"))
    return _source_label_from_ref(f"{chunk.source}#chunk={chunk.index}")


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

    def add(text: str, question_type: str, difficulty: str) -> None:
        questions.append(
            _question(text, question_type=question_type, node=node, difficulty=difficulty)
        )

    if node.definitions:
        add(f"Define {node.concept} using the course material.", "free_recall", "core")
        add(f"Cloze deletion: {node.concept} is _____. Fill the blank.", "cloze_deletion", "core")
        add(
            f"In one or two sentences, state the key idea of {node.concept}.",
            "short_answer",
            "core",
        )
    if node.formulas:
        add(
            f"State the formula or formal condition associated with {node.concept}.",
            "formula_recall",
            "core",
        )
    if node.examples:
        add(
            f"Why does this example fit {node.concept}: {node.examples[0]}?",
            "application_scenario",
            "transfer",
        )
    if node.tables:
        add(
            f"What key pattern does the table show for {node.concept}?",
            "data_interpretation",
            "transfer",
        )
    if node.exam_questions:
        add(f"Past-exam style: {node.exam_questions[0]}", "past_exam_style", "exam")
    if node.common_misconceptions:
        add(
            f"Correct this misconception about {node.concept}: {node.common_misconceptions[0]}",
            "error_correction",
            "misconception",
        )
        if node.definitions:
            add(
                f"Multiple choice: which statement best matches {node.concept}? "
                f"A. {node.definitions[0]} B. {node.common_misconceptions[0]}",
                "multiple_choice",
                "misconception",
            )
    if node.exam_skills:
        add(f"Past-exam style: {node.exam_skills[0]}", "past_exam_style", "exam")
        if "compar" in node.exam_skills[0].casefold():
            add(f"Compare and contrast: {node.exam_skills[0]}", "compare_and_contrast", "transfer")
    if node.learning_objectives:
        add(
            f"Explain the learning objective for {node.concept}: {node.learning_objectives[0]}",
            "explain_the_mechanism",
            "core",
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
    if node.source_labels:
        source_label = "; ".join(node.source_labels)
    else:
        labels = tuple(_source_label_from_ref(ref) for ref in node.source_refs)
        source_label = "; ".join(dict.fromkeys(label for label in labels if label))
    return GroundedStudyQuestion(
        question=text,
        question_type=question_type,
        concept=node.concept,
        grounding_source_refs=node.source_refs,
        source_label=source_label,
        difficulty=difficulty,
    )


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
        field_name = _NODE_ITEM_FIELDS.get(item.kind)
        if field_name is not None:
            _append_unique(cast("list[str]", getattr(self, field_name)), item.text)

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
