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


class _FakePdfCompiler:
    def compile(self, tex_path: Path, pdf_path: Path) -> None:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% hephaistos fake test pdf\n")


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
    assert analysis.topics[0].topic == "dijkstra shortest"
    assert analysis.topics[0].exam_hits == 1
    assert analysis.topics[0].exam_marks == 0
    assert analysis.topics[0].material_hits == 1
    assert analysis.topics[0].score > 10.0


def test_priority_analysis_uses_extracted_text_to_classify_generic_sources(
    tmp_path: Path,
) -> None:
    index = ArmoryIndex(tmp_path)
    exam_chunk = _chunk(
        "materials/document-a.pdf",
        "Klausur Mathematik für Informatiker 2. Bearbeitungszeit 90 Minuten. "
        "Aufgabe 1 [10 Punkte]: Explain Dijkstra shortest paths.",
    )
    slides_chunk = _chunk(
        "materials/document-b.pdf",
        "Mathematik für Informatiker 2. Sommersemester 2026. Vorlesung. "
        "Table of contents. Dijkstra shortest paths use graph relaxation.",
    )
    index.documents = [
        ChunkedDocument(
            source="materials/document-a.pdf", content_hash="exam", chunks=[exam_chunk]
        ),
        ChunkedDocument(
            source="materials/document-b.pdf",
            content_hash="slides",
            chunks=[slides_chunk],
        ),
    ]

    analysis = analyze_priority(index.all_chunks)
    dijkstra = next(topic for topic in analysis.topics if topic.topic == "dijkstra shortest")

    assert analysis.past_exam_sources == ("materials/document-a.pdf",)
    assert analysis.material_sources == ("materials/document-b.pdf",)
    assert dijkstra.exam_hits == 1
    assert dijkstra.material_hits == 1


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


def test_priority_analysis_reports_source_progress(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exams/2024.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exams/2024.md",
                    "Question: Explain graph shortest paths.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/lecture-graphs.md",
            content_hash="notes",
            chunks=[_chunk("materials/lecture-graphs.md", "Graph shortest paths use Dijkstra.")],
        ),
    ]
    messages: list[str] = []

    analyze_priority(index.all_chunks, progress=messages.append)

    assert messages[0] == "Ran priority.scan --sources 2 --chunks 2."
    assert "Read source 1/2: @past-exams/2024.md (1 chunk(s))." in messages
    assert "Read source 2/2: @lecture-graphs.md (1 chunk(s))." in messages
    assert any(message.startswith("Read @past-exams/2024.md chunk 1/1") for message in messages)
    assert any(message.startswith("Read @lecture-graphs.md chunk 1/1") for message in messages)
    assert "Scoring topic recurrence from exams and support files..." in messages
    assert any(message.startswith("Ranked ") and message.endswith(".") for message in messages)


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
    graph = next(topic for topic in topics if topic.topic == "graph shortest")
    heaps = next(topic for topic in topics if topic.topic == "heaps")

    assert graph.exam_marks == 12
    assert heaps.exam_marks == 4
    assert graph.score > heaps.score
    assert topics[0].topic == "graph shortest"
    rendered = analyze_priority(index.all_chunks).render_for_prompt()
    assert "12 visible mark" in rendered
    assert "exam marks" not in rendered


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

    assert topics["dijkstra shortest"].exam_marks == 12
    assert topics["heaps"].exam_marks == 4
    assert topics["priority queues"].exam_marks == 4
    assert topics["priority queues"].score < topics["dijkstra shortest"].score
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


def test_priority_report_writes_printable_pdf_latex_from_local_evidence(tmp_path: Path) -> None:
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

    report = generate_priority_report(
        analyze_priority(index.all_chunks),
        tmp_path / "Downloads",
        compiler=_FakePdfCompiler(),
        keep_tex=True,
    )
    assert report.tex_path is not None
    tex = report.tex_path.read_text(encoding="utf-8")

    assert report.path.parent == tmp_path / "Downloads"
    assert report.path.suffix == ".pdf"
    assert report.path.is_file()
    assert report.used_model is False
    assert report.verification is not None
    assert report.verification.passed
    assert report.sidecar_path is not None
    assert report.sidecar_path.is_file()
    assert r"\documentclass[10pt,a4paper,landscape]{article}" in tex
    assert r"\geometry{margin=8mm}" in tex
    assert r"\begin{multicols*}{2}" in tex
    assert "lmodern" in tex
    assert "dynamic programming" in tex
    assert "materials/past-exam-2026.md" in tex
    assert "10 visible points" in tex
    assert "recursion" in tex
    assert "Past-exam pattern table" in tex
    assert "Explain dynamic programming recurrence tables" in tex
    assert "HEPHAISTOS PRIORITY" not in tex
    assert "Score " not in tex
    assert "exam hits" not in tex


def test_priority_report_escapes_unsafe_latex_math_from_materials(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exam-2026.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exam-2026.md",
                    r"Question [10 marks]: Compute $\input{/etc/passwd}$ for graph recurrence.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/lecture-graphs.md",
            content_hash="notes",
            chunks=[
                _chunk(
                    "materials/lecture-graphs.md",
                    r"Graph recurrence has safe formula $f(n)=\frac{n}{2}$ and "
                    r"unsafe formula $\immediate\openout15=/tmp/heph_marker$.",
                )
            ],
        ),
    ]

    report = generate_priority_report(
        analyze_priority(index.all_chunks),
        tmp_path / "Downloads",
        compiler=_FakePdfCompiler(),
        keep_tex=True,
    )
    assert report.tex_path is not None
    tex = report.tex_path.read_text(encoding="utf-8")

    assert r"$f(n)=\frac{n}{2}$" in tex
    assert r"$\input{/etc/passwd}$" not in tex
    assert r"$\immediate\openout15=/tmp/heph_marker$" not in tex
    assert r"\textbackslash{}input" in tex
    assert r"\textbackslash{}immediate" in tex


def test_priority_report_emits_stage_progress(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/past-exam-2026.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exam-2026.md",
                    "Question [6 marks]: Explain recursion.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/lecture-recursion.md",
            content_hash="notes",
            chunks=[
                _chunk(
                    "materials/lecture-recursion.md",
                    "Recursion uses base cases and an inductive step.",
                )
            ],
        ),
    ]
    progress_lines: list[str] = []

    generate_priority_report(
        analyze_priority(index.all_chunks),
        tmp_path / "Downloads",
        compiler=_FakePdfCompiler(),
        progress=progress_lines.append,
    )

    assert any(line.startswith("Ran priority.report --topics") for line in progress_lines)
    assert "Building report sections from indexed evidence..." in progress_lines
    assert "Using deterministic local output (no model configured)." in progress_lines
    assert any(line.startswith("Rendered LaTeX priority sheet") for line in progress_lines)
    assert any(line.startswith("Wrote temporary LaTeX") for line in progress_lines)
    assert any(line.startswith("Ran _FakePdfCompiler.compile") for line in progress_lines)
    assert any(line.startswith("PDF compile finished") for line in progress_lines)
    assert any(line.startswith("Wrote PDF") for line in progress_lines)
    assert any(line.startswith("Ran priority verification checks") for line in progress_lines)
    assert any(line.startswith("Wrote verification sidecar") for line in progress_lines)
    assert progress_lines[-1].startswith("Priority report verified in")


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


def test_priority_analysis_filters_repeated_lecture_boilerplate(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source=f"materials/Folien_2026_04_{day}.pdf",
            content_hash=str(day),
            chunks=[
                _chunk(
                    f"materials/Folien_2026_04_{day}.pdf",
                    "Mathematik f ur Informatiker Sommersemester. Jesse Ratzkin. "
                    "Universit at W urzburg. Beispiel. Ohne Beweis. "
                    "Geometrische Reihe und Konvergenz von Partialsummen.",
                )
            ],
        )
        for day in range(13, 18)
    ]
    index.documents.append(
        ChunkedDocument(
            source="materials/past-exams/mock.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/past-exams/mock.md",
                    "Aufgabe 1 [8 Punkte]: Untersuchen Sie eine geometrische Reihe.",
                )
            ],
        )
    )

    topics = {topic.topic: topic for topic in analyze_priority(index.all_chunks).topics}

    assert "jesse ratzkin" not in topics
    assert "mathematik f ur informatiker sommersemester" not in topics
    assert "universit at w urzburg" not in topics
    assert "ohne beweis" not in topics
    assert "geometrische reihe" in topics
    assert topics["geometrische reihe"].exam_marks == 8


def test_priority_analysis_filters_generic_course_boilerplate(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/biochemistry-lecture.md",
            content_hash="lecture",
            chunks=[
                _chunk(
                    "materials/biochemistry-lecture.md",
                    "# Biochemistry 201\n"
                    "Professor Amelia Carter. Northbridge University. "
                    "Department of Biochemistry. Fall semester.\n"
                    "## Enzyme Kinetics\n"
                    "Enzyme kinetics explains Michaelis Menten saturation and reaction velocity.\n"
                    "## Protein Folding\n"
                    "Protein folding depends on hydrogen bonds and hydrophobic interactions.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/biochemistry-midterm.md",
            content_hash="exam",
            chunks=[
                _chunk(
                    "materials/biochemistry-midterm.md",
                    "Midterm Exam. Student name. Student ID.\n"
                    "Question 1 [12 points]: Explain enzyme kinetics and Michaelis Menten "
                    "saturation.\n"
                    "Question 2 [6 points]: Describe protein folding.",
                )
            ],
        ),
    ]

    topics = {topic.topic: topic for topic in analyze_priority(index.all_chunks).topics}

    assert "amelia carter" not in topics
    assert "northbridge university" not in topics
    assert "department biochemistry" not in topics
    assert "student name student id" not in topics
    assert "enzyme kinetics" in topics
    assert "protein folding" in topics
    assert topics["enzyme kinetics"].exam_marks == 12


def test_priority_analysis_extracts_definition_heads_across_subjects(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    index.documents = [
        ChunkedDocument(
            source="materials/analysis.md",
            content_hash="math",
            chunks=[
                _chunk(
                    "materials/analysis.md",
                    "Mathematik für Informatiker 2. Ableitung definiert. "
                    "Eine Folge in M ist eine Abbildung von N nach M. "
                    "Die Reihe bezeichnet die Folge der Partialsummen.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/biochemistry.md",
            content_hash="bio",
            chunks=[
                _chunk(
                    "materials/biochemistry.md",
                    "Enzyme kinetics is the study of reaction rates. "
                    "Protein folding is the process that reaches a native state.",
                )
            ],
        ),
        ChunkedDocument(
            source="materials/data-structures.md",
            content_hash="cs",
            chunks=[
                _chunk(
                    "materials/data-structures.md",
                    "A hash table is a data structure for key value lookup.",
                )
            ],
        ),
    ]

    topics = {topic.topic for topic in analyze_priority(index.all_chunks, limit=20).topics}

    assert "ableitungen" in topics
    assert "folgen" in topics
    assert "reihen" in topics
    assert "enzyme kinetics" in topics
    assert "protein folding" in topics
    assert "hash table" in topics
    assert "mathematik für informatiker" not in topics
    assert "ableitung definiert" not in topics


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

    report = generate_priority_report(
        analyze_priority(index.all_chunks),
        tmp_path / "Downloads",
        compiler=_FakePdfCompiler(),
        keep_tex=True,
    )
    assert report.tex_path is not None
    tex = report.tex_path.read_text(encoding="utf-8")

    assert "Graph Algorithms Dijkstra" not in tex
    assert "Dijkstra shortest paths use graph relaxation" in tex


def test_priority_report_does_not_expand_beyond_requested_analysis(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    chunks = [
        _chunk("materials/past-exams/mock.md", "Question [8 marks]: Explain graph."),
        _chunk("materials/slides.md", "Graph shortest paths."),
    ]
    chunks.extend(
        _chunk("materials/slides.md", f"## Extra Topic {i}\nExtra Topic {i}.") for i in range(12)
    )
    index.documents = [
        ChunkedDocument(
            source="materials/past-exams/mock.md", content_hash="exam", chunks=chunks[:1]
        ),
        ChunkedDocument(source="materials/slides.md", content_hash="slides", chunks=chunks[1:]),
    ]

    analysis = analyze_priority(index.all_chunks, limit=2)
    report = generate_priority_report(
        analysis,
        tmp_path / "Downloads",
        compiler=_FakePdfCompiler(),
        keep_tex=True,
    )

    assert report.tex_path is not None
    tex = report.tex_path.read_text(encoding="utf-8")
    assert report.topic_count == 2
    assert "extra topic 2" not in tex.lower()


def test_priority_analysis_deduplicates_identical_evidence(tmp_path: Path) -> None:
    index = ArmoryIndex(tmp_path)
    repeated = "Graph shortest paths use Dijkstra relaxation."
    index.documents = [
        ChunkedDocument(
            source="materials/slides.md",
            content_hash="slides",
            chunks=[
                _chunk("materials/slides.md", repeated),
                _chunk("materials/slides.md", repeated, index=1),
            ],
        ),
        ChunkedDocument(
            source="materials/past-exams/mock.md",
            content_hash="exam",
            chunks=[_chunk("materials/past-exams/mock.md", "Question [8 marks]: Explain graph.")],
        ),
    ]

    graph = next(
        topic for topic in analyze_priority(index.all_chunks).topics if topic.topic == "graph"
    )

    assert [evidence.excerpt for evidence in graph.evidence].count(repeated) == 1


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
    report = generate_priority_report(
        analysis,
        tmp_path / "Downloads",
        compiler=_FakePdfCompiler(),
        keep_tex=True,
    )
    assert report.tex_path is not None
    tex = report.tex_path.read_text(encoding="utf-8")

    assert topic.web_prerequisites[0].term == "set notation"
    assert "web-backed prerequisite hints" in analysis.render_for_prompt()
    assert "external prerequisite hint" in tex
