from __future__ import annotations

import random

from hephaistos.rag.chunker import Chunk
from hephaistos.study.exam import select_exam_question, supporting_source_refs


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


def test_supporting_source_refs_prefers_overlapping_non_exam_chunks() -> None:
    chunks = [
        _chunk("materials/past-exam-2025.md", "Explain neural network backpropagation."),
        _chunk("materials/neural-networks.md", "Backpropagation uses derivatives."),
        _chunk("materials/unrelated.md", "Hash tables store key value data."),
    ]

    refs = supporting_source_refs(chunks, "Explain neural network backpropagation.")

    assert refs == ["materials/neural-networks.md#chunk=0"]
