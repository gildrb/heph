from __future__ import annotations

from dataclasses import dataclass

from harness.documents.knowledge import (
    AcademicItem,
    AcademicItemKind,
    GroundedQuestion,
    build_course_knowledge_graph,
    extract_academic_items,
    generate_grounded_questions,
    grounded_question_quality_issues,
)


@dataclass(frozen=True, slots=True)
class Chunk:
    source: str
    index: int
    text: str
    heading: str = ""


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


def test_extract_academic_items_strips_lecture_prefix_from_heading_concepts() -> None:
    chunks = [
        Chunk(
            source="materials/softwaretechnik.md",
            index=0,
            text=(
                "# Lecture 3 - Requirements Engineering\n"
                "Requirements Engineering is systematic handling of requirements.\n"
            ),
        )
    ]

    items = extract_academic_items(chunks)

    assert items[0].kind is AcademicItemKind.CONCEPT
    assert items[0].text == "Requirements Engineering"
    assert items[0].concept == "Requirements Engineering"
    assert items[1].concept == "Requirements Engineering"
    assert all(item.source_label == "3 Requirements Engineering" for item in items)


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


def test_generate_grounded_questions_preserves_grounding() -> None:
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
                kind=AcademicItemKind.EXAMPLE,
                text="high-frequency stimulation increases later response",
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

    questions = generate_grounded_questions(graph, limit_per_concept=9)

    assert [question.question_type for question in questions] == [
        "free_recall",
        "cloze_deletion",
        "short_answer",
        "application_scenario",
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
    assert questions[0].source_label == "lecture; exam"
    assert any("LTP is only a structural change" in question.question for question in questions)
    assert not any("and explain why it fits" in question.question for question in questions)
    assert any(
        question.question == "Why does this example fit Long-term potentiation: "
        "high-frequency stimulation increases later response?"
        for question in questions
    )
    assert any(
        question.question == "What key pattern does the table show for Long-term potentiation?"
        for question in questions
    )
    assert not any("source-backed" in question.question for question in questions)
    assert not any("source-supported" in question.question for question in questions)
    assert not any("source question" in question.question for question in questions)
    assert all(not grounded_question_quality_issues(question) for question in questions)


def test_generate_grounded_questions_skips_metadata_trivia_nodes() -> None:
    graph = build_course_knowledge_graph(
        [
            AcademicItem(
                kind=AcademicItemKind.CONCEPT,
                text="Professor Example",
                source_ref="materials/lecture.md#chunk=0",
                concept="Professor Example",
            ),
            AcademicItem(
                kind=AcademicItemKind.DEFINITION,
                text="Professor Example: course instructor",
                source_ref="materials/lecture.md#chunk=0",
                concept="Professor Example",
            ),
            AcademicItem(
                kind=AcademicItemKind.CONCEPT,
                text="Requirements Engineering",
                source_ref="materials/lecture.md#chunk=1",
                concept="Requirements Engineering",
            ),
            AcademicItem(
                kind=AcademicItemKind.DEFINITION,
                text="Requirements Engineering: systematic handling of requirements",
                source_ref="materials/lecture.md#chunk=1",
                concept="Requirements Engineering",
            ),
        ]
    )

    questions = generate_grounded_questions(graph)

    assert questions
    assert all("Professor Example" not in question.question for question in questions)
    assert any("Requirements Engineering" in question.question for question in questions)


def test_generate_grounded_questions_skips_ungrounded_nodes() -> None:
    graph = build_course_knowledge_graph(
        [
            AcademicItem(
                kind=AcademicItemKind.FORMULA,
                text="x = y + 1",
                source_ref="materials/formula.md#chunk=0",
            )
        ]
    )

    assert generate_grounded_questions(graph) == []


def test_grounded_question_quality_rejects_metadata_and_internal_source_text() -> None:
    question = GroundedQuestion(
        question=(
            "What does slide 7 say about source-backed claims in materials/lecture.pdf#chunk=2?"
        ),
        question_type="free_recall",
        concept="Lecture date",
        grounding_source_refs=("materials/lecture.pdf#chunk=2",),
    )

    issues = grounded_question_quality_issues(question)

    assert "contains metadata or internal source wording" in issues
    assert "uses metadata-like concept" in issues


def test_grounded_question_quality_rejects_ungrounded_passive_prompt() -> None:
    question = GroundedQuestion(
        question="Summarize the document.",
        question_type="summary",
        concept="Enzyme kinetics",
        grounding_source_refs=(),
    )

    assert grounded_question_quality_issues(question) == (
        "missing grounding source refs",
        "missing canonical source label",
        "not framed as active recall",
    )


def test_grounded_question_quality_rejects_multi_part_prompt() -> None:
    question = GroundedQuestion(
        question="Define enzyme kinetics and explain why substrate concentration matters?",
        question_type="free_recall",
        concept="Enzyme kinetics",
        grounding_source_refs=("materials/biochem-lecture.md#chunk=1",),
        source_label="biochem lecture",
    )

    assert grounded_question_quality_issues(question) == ("asks more than one thing",)
