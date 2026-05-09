from __future__ import annotations

from pathlib import Path

from hephaistos.rag.chunker import Chunk, ChunkedDocument
from hephaistos.rag.index import ArmoryIndex
from hephaistos.study.priority import analyze_priority


def _chunk(source: str, text: str, index: int = 0, heading: str = "") -> Chunk:
    return Chunk(
        text=text,
        source=source,
        index=index,
        char_start=0,
        char_end=len(text),
        heading=heading,
    )


def test_priority_analysis_weights_past_exam_occurrence(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    exam_chunk = _chunk(
        "materials/past-exams/2024.md",
        "Question: Explain Dijkstra shortest paths. Dijkstra graph weights.",
    )
    notes_chunk = _chunk(
        "materials/lecture-graphs.md",
        "Dijkstra shortest paths require priority queues and graph relaxation.",
    )
    index.documents = [
        ChunkedDocument(
            source="materials/past-exams/2024.md",
            content_hash="exam",
            chunks=[exam_chunk],
        ),
        ChunkedDocument(
            source="materials/lecture-graphs.md",
            content_hash="notes",
            chunks=[notes_chunk],
        ),
    ]

    analysis = analyze_priority(index.all_chunks)

    assert analysis.past_exam_sources == ("materials/past-exams/2024.md",)
    assert analysis.topics[0].topic == "dijkstra"
    assert analysis.topics[0].exam_hits == 1
    assert analysis.topics[0].exam_marks == 0
    assert analysis.topics[0].material_hits == 1
    assert analysis.topics[0].score == 4.0


def test_priority_analysis_render_includes_exam_and_material_sources(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/mock-exam.md",
            content_hash="exam",
            chunks=[_chunk("materials/mock-exam.md", "Explain dynamic programming recurrence.")],
        ),
        ChunkedDocument(
            source="materials/lecture-dp.md",
            content_hash="notes",
            chunks=[
                _chunk("materials/lecture-dp.md", "Dynamic programming uses recurrence tables.")
            ],
        ),
    ]

    rendered = analyze_priority(index.all_chunks).render_for_prompt()

    assert "Local priority scan" in rendered
    assert "Past exams scanned: materials/mock-exam.md" in rendered
    assert "Supporting materials scanned: materials/lecture-dp.md" in rendered
    assert "dynamic" in rendered


def test_priority_analysis_surfaces_prerequisite_candidates(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exams/2025.md",
            content_hash="exam",
            chunks=[_chunk("materials/past-exams/2025.md", "Explain gradient descent.")],
        ),
        ChunkedDocument(
            source="materials/lecture-optimization.md",
            content_hash="notes",
            chunks=[
                _chunk(
                    "materials/lecture-optimization.md",
                    "Gradient descent depends on derivatives and convex functions.",
                )
            ],
        ),
    ]

    topic = next(
        topic
        for topic in analyze_priority(index.all_chunks).topics
        if topic.topic == "gradient descent"
    )

    assert "derivatives" in topic.prerequisites
    assert "convex" in topic.prerequisites
    assert "prerequisites to check" in analyze_priority(index.all_chunks).render_for_prompt()


def test_priority_analysis_weights_exam_marks(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exams/2026.md",
            content_hash="exam",
            chunks=[
                _chunk("materials/past-exams/2026.md", "Explain heaps. [4 marks]"),
                _chunk("materials/past-exams/2026.md", "Explain graph shortest paths. [12 marks]"),
            ],
        ),
    ]

    topics = analyze_priority(index.all_chunks).topics
    graph = next(topic for topic in topics if topic.topic == "graph")
    heaps = next(topic for topic in topics if topic.topic == "heaps")

    assert graph.exam_marks == 12
    assert heaps.exam_marks == 4
    assert graph.score > heaps.score
    assert topics[0].topic == "graph"
    assert "exam marks 12" in analyze_priority(index.all_chunks).render_for_prompt()


def test_priority_analysis_filters_exam_boilerplate_and_uses_explicit_prerequisites(
    tmp_path: Path,
) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exam-2025.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exam-2025.md",
                    "Question 1 [12 marks]: Given a two-layer neural network, reason through "
                    "one gradient descent update using the chain rule.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/neural-networks.md",
            content_hash="notes",
            chunks=[
                _chunk(
                    "materials/neural-networks.md",
                    "A neural network is a model made of layers of connected units.\n"
                    "Prerequisites: calculus derivatives, matrix multiplication, probability "
                    "basics.",
                )
            ],
        ),
    ]

    analysis = analyze_priority(index.all_chunks)
    topics = {topic.topic: topic for topic in analysis.topics}

    assert "one" not in topics
    assert "through" not in topics
    assert "neural" not in topics
    assert "network" not in topics
    assert "neural network" in topics
    assert topics["neural network"].prerequisites[:3] == ("calculus", "derivatives", "matrix")
