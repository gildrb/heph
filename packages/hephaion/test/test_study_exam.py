from __future__ import annotations

import random

from hephaion.rag.chunker import Chunk
from hephaion.study.exam import select_exam_question, supporting_source_refs


def _chunk(source: str, text: str) -> Chunk:
    return Chunk(
        text=text,
        source=source,
        index=0,
        char_start=0,
        char_end=len(text),
        heading="",
    )


def test_select_exam_question_extracts_marked_past_exam_line() -> None:
    question = select_exam_question(
        [
            _chunk("materials/lecture.md", "Explain gradient descent."),
            _chunk("materials/past-exam-2025.md", "Question 1 [12 marks]: Explain chain rule."),
        ],
        rng=random.Random(0),
    )

    assert question is not None
    assert question.question == "Explain chain rule. [12 marks]"
    assert question.marks == 12
    assert question.time_limit_minutes == 12
    assert question.source_ref == "materials/past-exam-2025.md#chunk=0"


def test_select_exam_question_can_filter_by_topic() -> None:
    question = select_exam_question(
        [
            _chunk(
                "materials/past-exam-2025.md",
                "Question 1 [4 marks]: Define validation set.\n"
                "Question 2 [10 marks]: Explain neural networks.",
            )
        ],
        topic="neural",
        rng=random.Random(0),
    )

    assert question is not None
    assert "neural" in question.question


def test_select_exam_question_includes_parent_stem_for_subquestion() -> None:
    question = select_exam_question(
        [
            _chunk(
                "materials/past-exam-2025.md",
                "4. (5+7+2 Punkte) Es sei\n"
                "f : D -> R, f(x,y) = ln(1 + xy)\n"
                "für den Definitionsbereich D = { (x,y) in R^2 : xy > -1 }.\n"
                "(a) Bestimmen Sie alle kritischen Punkte von f auf D.\n"
                "(b) Entscheiden Sie, ob lokale Extrema vorliegen.\n"
                "(c) Kann f auf D ein globales Maximum besitzen? Begründen Sie Ihre Antwort!",
            )
        ],
        topic="globales Maximum",
        rng=random.Random(0),
    )

    assert question is not None
    assert "f : D -> R" in question.question
    assert "f(x,y) = ln(1 + xy)" in question.question
    assert "xy > -1" in question.question
    assert "(c) Kann f auf D ein globales Maximum besitzen?" in question.question


def test_select_exam_question_recovers_parent_stem_across_split_chunks() -> None:
    question = select_exam_question(
        [
            Chunk(
                text="4. Let f: D -> R, f(x,y) = ln(1 + xy), where D = {xy > -1}.\n"
                "(a) Find all critical points.",
                source="materials/past-exam-2025.pdf",
                index=0,
                char_start=0,
                char_end=90,
                heading="",
            ),
            Chunk(
                text="(b) Classify the critical points.\n"
                "(c) Can f have a global maximum on D? Justify your answer.",
                source="materials/past-exam-2025.pdf",
                index=1,
                char_start=90,
                char_end=180,
                heading="",
            ),
        ],
        topic="global maximum",
        rng=random.Random(0),
    )

    assert question is not None
    assert question.source_ref == "materials/past-exam-2025.pdf#chunk=1"
    assert "f: D -> R" in question.question
    assert "f(x,y) = ln(1 + xy)" in question.question
    assert "(c) Can f have a global maximum on D?" in question.question


def test_select_exam_question_does_not_emit_orphaned_context_dependent_subquestion() -> None:
    question = select_exam_question(
        [
            _chunk(
                "materials/past-exam-2025.md",
                "(c) Can f have a global maximum on D? Justify your answer.",
            )
        ],
        rng=random.Random(0),
    )

    assert question is None


def test_select_exam_question_skips_obvious_ocr_noise_prompt() -> None:
    question = select_exam_question(
        [
            _chunk(
                "materials/past-exam-2025.md",
                "1. (6 points) Calculate the following integral:\n"
                "(a) Pape\n"
                "9 @?-7r+10\n"
                "2. (4 points) Define a stable equilibrium.",
            )
        ],
        rng=random.Random(0),
    )

    assert question is not None
    assert "stable equilibrium" in question.question
    assert "@" not in question.question


def test_supporting_source_refs_prefers_overlapping_non_exam_chunks() -> None:
    chunks = [
        _chunk("materials/past-exam-2025.md", "Explain neural network backpropagation."),
        _chunk("materials/neural-networks.md", "Backpropagation uses derivatives."),
        _chunk("materials/unrelated.md", "Hash tables store key value data."),
    ]

    refs = supporting_source_refs(chunks, "Explain neural network backpropagation.")

    assert refs == ["materials/neural-networks.md#chunk=0"]
