from __future__ import annotations

from pathlib import Path

from hephaistos.rag.chunker import Chunk, ChunkedDocument
from hephaistos.rag.index import ArmoryIndex
from hephaistos.study.priority import (
    PriorityWebSearchResult,
    analyze_priority,
    generate_priority_report,
)


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
    assert analysis.topics[0].score == 8.5


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


def test_priority_analysis_keeps_inline_question_marks_with_matching_topics(
    tmp_path: Path,
) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exams/mock-2025.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exams/mock-2025.md",
                    "Question 1 [12 marks]: Explain Dijkstra shortest paths and graph relaxation. "
                    "Question 2 [4 marks]: Explain heaps and priority queues. "
                    "Question 3 [2 marks]: Image. Formula not decoded. Die und wir ist OCR noise.",
                )
            ],
        ),
    ]

    topics = {topic.topic: topic for topic in analyze_priority(index.all_chunks).topics}

    assert topics["dijkstra"].exam_marks == 12
    assert topics["graph"].exam_marks == 12
    assert topics["heaps"].exam_marks == 4
    assert topics["heaps"].score < topics["dijkstra"].score
    assert "ocr noise" not in topics


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


def test_priority_report_writes_printable_html_from_local_evidence(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exam-2026.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exam-2026.md",
                    "Question 1 [10 marks]: Explain dynamic programming recurrence tables.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/lecture-dp.md",
            content_hash="notes",
            chunks=[
                _chunk(
                    "materials/lecture-dp.md",
                    "Dynamic programming requires recurrence relations and base cases.\n"
                    "Prerequisites: recursion, induction.",
                )
            ],
        ),
    ]

    report = generate_priority_report(analyze_priority(index.all_chunks), tmp_path / "Downloads")
    html = report.path.read_text(encoding="utf-8")

    assert report.path.parent == tmp_path / "Downloads"
    assert report.path.suffix == ".html"
    assert report.used_model is False
    assert "background: #fff" in html
    assert "color: #111" in html
    assert "box-shadow" not in html
    assert 'class="topic-list"' in html
    assert 'class="card"' not in html
    assert 'class="grid"' not in html
    assert "dynamic programming" in html
    assert "materials/past-exam-2026.md" in html
    assert "10 marks" in html
    assert "recursion" in html
    assert "definition card" in html
    assert "timed answer" in html
    assert "Factual study map" in html
    assert "Exam questions and points" in html
    assert "Explain dynamic programming recurrence tables" in html


def test_priority_analysis_prefers_meaningful_phrases_over_artifacts(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/Folien_2026_04_13.pdf",
            content_hash="slides",
            chunks=[
                _chunk(
                    "materials/Folien_2026_04_13.pdf",
                    "Formula not decoded. Image. Die und wir ist noise. "
                    "Gradient descent optimization uses learning rates.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/mock-exam.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/mock-exam.md",
                    "Question [8 marks]: Explain gradient descent optimization.",
                )
            ],
        ),
    ]

    topics = {topic.topic: topic for topic in analyze_priority(index.all_chunks).topics}

    assert "formula-not-decoded" not in topics
    assert "image" not in topics
    assert "die" not in topics
    assert "ocr noise" not in topics
    assert "gradient descent" in topics


def test_priority_report_cleans_repeated_headings_in_evidence(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/lectures/graphs.md",
            content_hash="graphs",
            chunks=[
                _chunk(
                    "materials/lectures/graphs.md",
                    "# Graph Algorithms\n"
                    "Graph Algorithms Dijkstra shortest paths use graph relaxation.",
                    heading="Graph Algorithms",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/past-exams/mock.md",
            content_hash="exam",
            chunks=[_chunk("materials/past-exams/mock.md", "Question [12 marks]: Explain graph.")],
        ),
    ]

    report = generate_priority_report(analyze_priority(index.all_chunks), tmp_path / "Downloads")
    html = report.path.read_text(encoding="utf-8")

    assert "Graph Algorithms Dijkstra" not in html
    assert "Dijkstra shortest paths use graph relaxation" in html


def test_priority_analysis_can_add_web_backed_prerequisite_hints(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exams/mock.md",
            content_hash="exam",
            chunks=[_chunk("materials/past-exams/mock.md", "Question [12 marks]: Explain graph.")],
        )
    ]

    def web_searcher(_query: str) -> tuple[PriorityWebSearchResult, ...]:
        return (
            PriorityWebSearchResult(
                title="Graph theory prerequisites",
                url="https://example.test/graph",
                snippet="Prerequisites: set notation, vertices, edges, and proof basics.",
            ),
        )

    analysis = analyze_priority(index.all_chunks, web_searcher=web_searcher)
    topic = next(topic for topic in analysis.topics if topic.topic == "graph")
    report = generate_priority_report(analysis, tmp_path / "Downloads")
    html = report.path.read_text(encoding="utf-8")

    assert topic.web_prerequisites[0].term == "set notation"
    assert "web-backed prerequisite hints" in analysis.render_for_prompt()
    assert "web prerequisite hint" in html
    assert "https://example.test/graph" in html


def test_priority_analysis_filters_metadata_and_preserves_german_concepts(
    tmp_path: Path,
) -> None:
    index = ArmoryIndex(tmp_path)
    slide_header = "Jesse Ratzkin Universit¨ at W¨ urzburg April 2026"
    index.documents = [
        ChunkedDocument(
            source="materials/Folien_2026_04_13.pdf",
            content_hash="slides-1",
            chunks=[
                _chunk(
                    "materials/Folien_2026_04_13.pdf",
                    f"{slide_header}\n"
                    "Mathematik f¨ ur Informatiker 2 Sommersemester 2026\n"
                    "## Exponential Logarithmus\n"
                    "Der Exponential Logarithmus ist wichtig für Potenzreihenentwicklung.",
                    heading="Mathematik f¨ ur Informatiker 2 Sommersemester 2026",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/Folien_2026_04_22.pdf",
            content_hash="slides-2",
            chunks=[
                _chunk(
                    "materials/Folien_2026_04_22.pdf",
                    "## Beispiel: Potenzreihenentwicklung des Kosinus\n"
                    "Die Potenzreihenentwicklung des Kosinus nutzt geometrische Reihen.",
                    heading="Beispiel: Potenzreihenentwicklung des Kosinus",
                )
            ],
        ),
    ]

    topics = {topic.topic: topic for topic in analyze_priority(index.all_chunks, limit=20).topics}

    assert "jesse ratzkin" not in topics
    assert "mathematik informatiker sommersemester" not in topics
    assert "universität würzburg" not in topics
    assert "exponential logarithmus" in topics
    assert "potenzreihenentwicklung kosinus" in topics or "potenzreihenentwicklung" in topics


def test_priority_report_ranks_exam_topics_before_repeated_metadata(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/Folien_2026_04_13.pdf",
            content_hash="slides",
            chunks=[
                _chunk(
                    "materials/Folien_2026_04_13.pdf",
                    "Jesse Ratzkin Universit¨ at W¨ urzburg April 2026\n"
                    "Mathematik f¨ ur Informatiker 2 Sommersemester 2026",
                )
                for _index in range(8)
            ]
            + [
                _chunk(
                    "materials/Folien_2026_04_20.pdf",
                    "Geometrische Reihe beschreibt Konvergenz von Partialsummen.",
                    heading="Geometrische Reihe",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/past-exams/klausur.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exams/klausur.md",
                    "Aufgabe 1 [10 Punkte]: Untersuchen Sie eine geometrische Reihe "
                    "auf Konvergenz.",
                )
            ],
        ),
    ]

    analysis = analyze_priority(index.all_chunks, limit=20)
    report = generate_priority_report(analysis, tmp_path / "Downloads")
    html = report.path.read_text(encoding="utf-8")

    assert analysis.topics[0].topic == "geometrische reihe"
    assert analysis.topics[0].exam_marks == 10
    assert "jesse ratzkin" not in html.casefold()
    assert "universität würzburg" not in html.casefold()
    assert "mathematik f ur informatiker" not in html
    assert "geometrische Reihe" in html
    assert "<title>Study priorities</title>" in html
    assert "Hephaistos priority" not in html


def test_priority_report_classifies_realistic_german_exam_by_content(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/Mathematik+fur+Informatiker+2-Ratzkin-SS23.pdf",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/Mathematik+fur+Informatiker+2-Ratzkin-SS23.pdf",
                    "Klausur zur Mathematik 2 fir Informatiker. "
                    "Sie konnen maximal 80 Punkte erreichen. "
                    "Aufgabennummer Nachname Vorname Matrikelnummer. "
                    "1.(4+4+4 Punkte) Berechnen Sie die folgenden Grenzwerte. "
                    "2.(8 Punkte) Untersuchen Sie eine geometrische Reihe auf Konvergenz.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/Folien_2026_04_20.pdf",
            content_hash="slides",
            chunks=[
                _chunk(
                    "materials/Folien_2026_04_20.pdf",
                    "Geometrische Reihe und Konvergenz von Partialsummen.",
                    heading="Geometrische Reihe",
                )
            ],
        ),
    ]

    analysis = analyze_priority(index.all_chunks, limit=20)
    report = generate_priority_report(analysis, tmp_path / "Downloads")
    html = report.path.read_text(encoding="utf-8")

    assert analysis.past_exam_sources == (
        "materials/Mathematik+fur+Informatiker+2-Ratzkin-SS23.pdf",
    )
    signals = {signal.source: signal for signal in analysis.material_signals}
    assert signals["materials/Mathematik+fur+Informatiker+2-Ratzkin-SS23.pdf"].role == "past_exam"
    assert "What was checked" in html
    assert "path suggests an exam or past paper" in html
    assert "past exam" in html
    assert "aufgabennummer nachname vorname matrikelnummer" not in html.casefold()


def test_priority_report_ignores_exam_filename_and_question_sentence_topics(
    tmp_path: Path,
) -> None:
    index = ArmoryIndex(tmp_path)
    source = "materials/Mathematik+fur+Informatiker+2-Ratzkin-SS23.pdf"
    index.documents = [
        ChunkedDocument(
            source=source,
            content_hash="exam",
            chunks=[
                _chunk(
                    source,
                    "Klausur zur Mathematik 2 für Informatiker. "
                    "Sie können maximal 80 Punkte erreichen. "
                    "Aufgabennummer Nachname Vorname Matrikelnummer. "
                    "1.(4+4+4 Punkte) Berechnen Sie die folgenden Grenzwerte und begründen "
                    "Sie die Konvergenz. "
                    "2.(8 Punkte) Untersuchen Sie eine geometrische Reihe auf Konvergenz. "
                    "3.(6 Punkte) Bestimmen Sie die Potenzreihenentwicklung des Kosinus.",
                ),
                _chunk(
                    source,
                    "ometrische Reihe auf Konvergenz. "
                    "3.(6 Punkte) Bestimmen Sie die Potenzreihenentwicklung des Kosinus.",
                    index=1,
                ),
            ],
        ),
        ChunkedDocument(
            source="materials/Folien_2026_04_13.pdf",
            content_hash="slides",
            chunks=[
                _chunk(
                    "materials/Folien_2026_04_13.pdf",
                    "Jesse Ratzkin Universit¨ at W¨ urzburg April 2026\n"
                    "Mathematik f¨ ur Informatiker 2 Sommersemester 2026.\n"
                    "Geometrische Reihe und Konvergenz von Partialsummen.",
                )
            ],
        ),
    ]

    analysis = analyze_priority(index.all_chunks, limit=20)
    topics = {topic.topic: topic for topic in analysis.topics}
    html = generate_priority_report(analysis, tmp_path / "Downloads").path.read_text(
        encoding="utf-8"
    )

    assert "mathematik-fur-informatiker-ratzkin" not in topics
    assert "bestimmen sie potenzreihenentwicklung kosinus" not in topics
    assert "untersuchen sie geometrische reihe konvergenz" not in topics
    assert topics["potenzreihenentwicklung"].exam_marks == 6
    assert topics["potenzreihenentwicklung"].exam_hits == 1
    assert topics["geometrische reihe"].exam_marks == 8
    assert "mathematik-fur-informatiker-ratzkin" not in html.casefold()
    assert "bestimmen sie potenzreihenentwicklung kosinus" not in html.casefold()
    assert "untersuchen sie geometrische reihe konvergenz" not in html.casefold()
