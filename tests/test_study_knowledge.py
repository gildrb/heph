from __future__ import annotations

from dataclasses import dataclass

from hephaistos.study.knowledge import (
    AcademicItem,
    AcademicItemKind,
    build_course_knowledge_graph,
    extract_academic_items,
    generate_grounded_study_questions,
)


@dataclass(frozen=True, slots=True)
class Chunk:
    source: str
    index: int
    text: str


def test_extract_academic_items_preserves_source_refs() -> None:
    chunks = [
        Chunk(
            source="materials/lecture.md",
            index=2,
            text=(
                "# Long-term potentiation\n"
                "Long-term potentiation is a persistent strengthening of synapses.\n"
                "Formula: delta w = eta x y\n"
                "Example: high-frequency stimulation increases later response.\n"
                "Figure 2: NMDA receptor opening after coincident stimulation.\n"
                "Table 1: stimulation frequency and response amplitude.\n"
                "Common misconception: LTP is only a structural change.\n"
                "Learning objective: explain why NMDA receptors are coincidence detectors.\n"
            ),
        )
    ]

    items = extract_academic_items(chunks)

    assert [(item.kind, item.source_ref) for item in items] == [
        (AcademicItemKind.CONCEPT, "materials/lecture.md#chunk=2"),
        (AcademicItemKind.DEFINITION, "materials/lecture.md#chunk=2"),
        (AcademicItemKind.FORMULA, "materials/lecture.md#chunk=2"),
        (AcademicItemKind.EXAMPLE, "materials/lecture.md#chunk=2"),
        (AcademicItemKind.FIGURE, "materials/lecture.md#chunk=2"),
        (AcademicItemKind.TABLE, "materials/lecture.md#chunk=2"),
        (AcademicItemKind.COMMON_MISCONCEPTION, "materials/lecture.md#chunk=2"),
        (AcademicItemKind.LEARNING_OBJECTIVE, "materials/lecture.md#chunk=2"),
    ]
    assert items[0].concept == "Long-term potentiation"
    assert items[1].text == ("Long-term potentiation: a persistent strengthening of synapses")


def test_extract_academic_items_finds_exam_skill_and_dedupes_per_source() -> None:
    chunks = [
        Chunk(
            source="materials/exam.md",
            index=0,
            text=(
                "Question 3. Explain the mechanism of LTP.\n"
                "Rubric: name NMDA receptor, calcium influx, and AMPA insertion.\n"
                "Rubric: name NMDA receptor, calcium influx, and AMPA insertion.\n"
            ),
        )
    ]

    items = extract_academic_items(chunks)

    assert [(item.kind, item.text) for item in items] == [
        (AcademicItemKind.EXAM_QUESTION, "Explain the mechanism of LTP"),
        (
            AcademicItemKind.EXAM_SKILL,
            "name NMDA receptor, calcium influx, and AMPA insertion",
        ),
        (
            AcademicItemKind.RUBRIC_POINT,
            "name NMDA receptor, calcium influx, and AMPA insertion",
        ),
    ]
    assert all(item.source_ref == "materials/exam.md#chunk=0" for item in items)


def test_extract_academic_items_finds_answers_figures_and_tables() -> None:
    chunks = [
        Chunk(
            source="materials/solutions.md",
            index=1,
            text=(
                "# Enzyme kinetics\n"
                "Question 1 [12 points]: Explain Michaelis Menten saturation.\n"
                "Answer: velocity approaches Vmax as substrate concentration rises.\n"
                "Figure 1: saturation curve with a plateau at high substrate.\n"
                "Table 2: substrate concentration and initial velocity values.\n"
            ),
        )
    ]

    items = extract_academic_items(chunks)

    assert [(item.kind, item.text) for item in items] == [
        (AcademicItemKind.CONCEPT, "Enzyme kinetics"),
        (AcademicItemKind.EXAM_QUESTION, "Explain Michaelis Menten saturation"),
        (AcademicItemKind.ANSWER, "velocity approaches Vmax as substrate concentration rises"),
        (AcademicItemKind.FIGURE, "saturation curve with a plateau at high substrate"),
        (AcademicItemKind.TABLE, "substrate concentration and initial velocity values"),
    ]
    assert all(item.source_ref == "materials/solutions.md#chunk=1" for item in items)


def test_extract_academic_items_respects_limit_per_chunk() -> None:
    chunks = [
        Chunk(
            source="materials/notes.md",
            index=0,
            text=(
                "# Topic A\n"
                "Topic A is the first tested idea.\n"
                "Example: apply Topic A to a short scenario.\n"
            ),
        )
    ]

    items = extract_academic_items(chunks, limit_per_chunk=2)

    assert [item.kind for item in items] == [
        AcademicItemKind.CONCEPT,
        AcademicItemKind.DEFINITION,
    ]


def test_build_course_knowledge_graph_groups_items_by_concept() -> None:
    items = [
        AcademicItem(
            kind=AcademicItemKind.CONCEPT,
            text="Long-term potentiation",
            source_ref="materials/lecture.md#chunk=2",
            concept="Long-term potentiation",
        ),
        AcademicItem(
            kind=AcademicItemKind.DEFINITION,
            text="Long-term potentiation: persistent strengthening of synapses",
            source_ref="materials/lecture.md#chunk=2",
            concept="Long-term potentiation",
        ),
        AcademicItem(
            kind=AcademicItemKind.EXAMPLE,
            text="high-frequency stimulation increases later response",
            source_ref="materials/lecture.md#chunk=2",
        ),
        AcademicItem(
            kind=AcademicItemKind.TABLE,
            text="stimulation frequency and response amplitude",
            source_ref="materials/lecture.md#chunk=2",
        ),
        AcademicItem(
            kind=AcademicItemKind.RUBRIC_POINT,
            text="compare LTP and LTD for 6 marks",
            source_ref="materials/exam.md#chunk=0",
            concept="Long-term potentiation",
        ),
        AcademicItem(
            kind=AcademicItemKind.COMMON_MISCONCEPTION,
            text="LTP is only a structural change",
            source_ref="materials/lecture.md#chunk=2",
        ),
        AcademicItem(
            kind=AcademicItemKind.EXAM_SKILL,
            text="compare LTP and LTD",
            source_ref="materials/exam.md#chunk=0",
            concept="Long-term potentiation",
        ),
    ]

    graph = build_course_knowledge_graph(items)

    assert graph.unassigned_items == ()
    assert len(graph.nodes) == 1
    node = graph.nodes[0]
    assert node.concept == "Long-term potentiation"
    assert node.source_refs == ("materials/lecture.md#chunk=2", "materials/exam.md#chunk=0")
    assert node.definitions == ("Long-term potentiation: persistent strengthening of synapses",)
    assert node.examples == ("high-frequency stimulation increases later response",)
    assert node.tables == ("stimulation frequency and response amplitude",)
    assert node.rubric_points == ("compare LTP and LTD for 6 marks",)
    assert node.common_misconceptions == ("LTP is only a structural change",)
    assert node.exam_skills == ("compare LTP and LTD",)


def test_build_course_knowledge_graph_keeps_unassigned_items_visible() -> None:
    item = AcademicItem(
        kind=AcademicItemKind.FORMULA,
        text="x = y + 1",
        source_ref="materials/formula.md#chunk=0",
    )

    graph = build_course_knowledge_graph([item])

    assert graph.nodes == ()
    assert graph.unassigned_items == (item,)


def test_generate_grounded_study_questions_preserves_grounding() -> None:
    graph = build_course_knowledge_graph(
        [
            AcademicItem(
                kind=AcademicItemKind.CONCEPT,
                text="Long-term potentiation",
                source_ref="materials/lecture.md#chunk=2",
                concept="Long-term potentiation",
            ),
            AcademicItem(
                kind=AcademicItemKind.DEFINITION,
                text="Long-term potentiation: persistent strengthening of synapses",
                source_ref="materials/lecture.md#chunk=2",
                concept="Long-term potentiation",
            ),
            AcademicItem(
                kind=AcademicItemKind.COMMON_MISCONCEPTION,
                text="LTP is only a structural change",
                source_ref="materials/lecture.md#chunk=2",
            ),
            AcademicItem(
                kind=AcademicItemKind.TABLE,
                text="stimulation frequency and response amplitude",
                source_ref="materials/lecture.md#chunk=2",
            ),
            AcademicItem(
                kind=AcademicItemKind.EXAM_SKILL,
                text="compare LTP and LTD",
                source_ref="materials/exam.md#chunk=0",
                concept="Long-term potentiation",
            ),
        ]
    )

    questions = generate_grounded_study_questions(graph, limit_per_concept=8)

    assert [question.question_type for question in questions] == [
        "free_recall",
        "cloze_deletion",
        "short_answer",
        "data_interpretation",
        "error_correction",
        "multiple_choice",
        "past_exam_style",
        "compare_and_contrast",
    ]
    assert all(question.grounding_source_refs for question in questions)
    assert questions[0].grounding_source_refs == (
        "materials/lecture.md#chunk=2",
        "materials/exam.md#chunk=0",
    )
    assert any("LTP is only a structural change" in question.question for question in questions)


def test_generate_grounded_study_questions_skips_ungrounded_nodes() -> None:
    graph = build_course_knowledge_graph(
        [
            AcademicItem(
                kind=AcademicItemKind.FORMULA,
                text="x = y + 1",
                source_ref="materials/formula.md#chunk=0",
            )
        ]
    )

    assert generate_grounded_study_questions(graph) == []
