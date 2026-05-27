from __future__ import annotations

from pathlib import Path

import pytest

from hephaion.armory.storage import initialize
from hephaion.materials import (
    count_material_files,
    infer_material_role,
    infer_material_role_from_text,
    iter_material_files,
    material_kind,
    material_manifest,
)


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    return armory


def test_iter_material_files_discovers_materials(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "exam.md").write_text("# Exam\n", encoding="utf-8")
    (armory / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    (armory / ".hephaion" / "generated" / "draft.md").write_text("# Draft\n", encoding="utf-8")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == ["materials/exam.md", "materials/notes.md"]


def test_material_manifest_classifies_material_kind(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "exam.md").write_text("# Exam\n", encoding="utf-8")
    (armory / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")

    manifest = material_manifest(armory)

    assert [(item.rel_path, item.kind, item.role) for item in manifest] == [
        ("materials/exam.md", "materials", "past_exam"),
        ("materials/notes.md", "materials", "reference"),
    ]
    assert manifest[0].confidence > manifest[1].confidence


def test_hidden_files_are_skipped(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "materials" / "visible.md").write_text("# Visible\n", encoding="utf-8")
    (armory / "materials" / ".hidden.md").write_text("# Hidden\n", encoding="utf-8")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == ["materials/visible.md"]


def test_armory_ignore_is_respected(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / ".hephaionignore").write_text(
        "materials/ignored.md\nmaterials/private/\n",
        encoding="utf-8",
    )
    (armory / "materials" / "visible.md").write_text("# Visible\n", encoding="utf-8")
    (armory / "materials" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (armory / "materials" / "private").mkdir()
    (armory / "materials" / "private" / "notes.md").write_text("# Private\n", encoding="utf-8")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == ["materials/visible.md"]


def test_symlinked_material_files_are_skipped(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    outside = tmp_path / "outside-secret.md"
    outside.write_text("# Secret\n", encoding="utf-8")
    link = armory / "materials" / "linked.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == []


def test_symlinked_material_directory_is_skipped(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    outside_materials = tmp_path / "outside-materials"
    outside_materials.mkdir()
    (outside_materials / "secret.md").write_text("# Secret\n", encoding="utf-8")
    materials = armory / "materials"
    materials.rmdir()
    try:
        materials.symlink_to(outside_materials, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")

    assert list(iter_material_files(armory)) == []


def test_empty_armory_has_no_materials(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)

    assert count_material_files(armory) == 0
    assert material_manifest(armory) == ()


def test_material_kind_from_relative_path() -> None:
    assert material_kind("materials/exam.md") == "materials"
    assert material_kind(".hephaion/generated/ref.md") is None


def test_infer_material_role_uses_path_hints() -> None:
    cases = {
        "materials/past-exams/2023.pdf": "past_exam",
        "materials/homework/sheet-1.md": "assignment",
        "materials/vocab/french.md": "vocabulary",
        "materials/lectures/week-1.md": "lecture",
        "materials/slides/deck.pptx": "slides",
        "materials/Folien_2026_04_13.pdf": "slides",
        "materials/Klausur_WorkspaceFixture2_WS2024.pdf": "past_exam",
        "materials/book/chapter-2.pdf": "textbook",
        "materials/public-course/summary.html": "reference",
        "materials/project/main.py": "codebase",
        "materials/misc/context.md": "reference",
    }

    for rel_path, expected_role in cases.items():
        role, confidence, reason = infer_material_role(rel_path)
        assert role == expected_role
        assert 0.0 <= confidence <= 1.0
        assert reason


def test_infer_material_role_does_not_treat_semester_marker_as_exam() -> None:
    role, confidence, reason = infer_material_role("materials/Linear-Algebra-SS23.pdf")

    assert role == "reference"
    assert confidence == 0.5
    assert reason == "default material role"


def test_infer_material_role_from_text_detects_generic_exam_file() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/document.pdf",
        """
        Administrative Header 2
        Klausur SS23
        Bearbeitungszeit: 90 Minuten
        Instructions: answer every problem.
        Aufgabe 1. Beweisen Sie die Aussage. [10 Punkte]
        Aufgabe 2. Berechnen Sie das Integral. [8 Punkte]
        """,
    )

    assert role == "past_exam"
    assert confidence >= 0.8
    assert "exam" in reason


def test_infer_material_role_from_text_detects_structured_exam_parts() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/generic-ss23.pdf",
        """
        Sommersemester 2023
        Für den Definitionsbereich D = {(x,y) in R2 : xy > -1}.
        - (a) Bestimmen Sie alle kritischen Punkte von f auf D.
        - (b) Entscheiden Sie, ob ein lokales Minimum vorliegt.
        """,
    )

    assert role == "past_exam"
    assert confidence >= 0.8
    assert "exam" in reason


def test_infer_material_role_from_text_detects_generic_lecture_slides() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/document.pdf",
        """
        Introduction to Statistical Learning
        Spring semester 2026
        Lecture notes
        Table of contents
        Welcome to the course
        Lecture schedule and tutorial sessions
        """,
    )

    assert role == "slides"
    assert confidence >= 0.75
    assert "lecture slides" in reason


def test_infer_material_role_from_text_detects_public_textbook_html_before_exam_cues() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/public-academic/uc-berkeley-cs188/search/agents.html",
        """
        <link rel="canonical"
              href="https://inst.eecs.berkeley.edu/~cs188/textbook/search/agents.html" />
        <title>1.1 Agents | Introduction to Artificial Intelligence</title>
        <a href="/~cs188/textbook/search/">1. Search</a>
        <p>Problem formulation and question answering appear in the navigation.</p>
        """,
    )

    assert role == "textbook"
    assert confidence >= 0.8
    assert "textbook" in reason


def test_infer_material_role_from_text_detects_numbered_public_textbook_chunks() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/public-academic/course/search/agents.html",
        """
        1.1 Agents | Introduction to Artificial Intelligence
        Skip to main content
        1. Search 1.1 Agents 1.2 State Spaces and Search Problems
        In artificial intelligence, the central problem is a rational agent.
        """,
    )

    assert role == "textbook"
    assert confidence >= 0.8
    assert "numbered textbook" in reason


def test_infer_material_role_from_text_keeps_public_textbook_summaries_as_reference() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/public-academic/course/search/summary.html",
        """
        <link rel="canonical"
              href="https://example.edu/textbook/search/summary.html" />
        <title>1.6 Summary | Introduction to Artificial Intelligence</title>
        """,
    )

    assert role == "reference"
    assert confidence >= 0.75
    assert "summary" in reason


def test_infer_material_role_from_text_detects_public_course_notes_before_slides() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/public-academic/stanford-cs231n/classification/index.html",
        """
        <meta name="description" content="Course materials and notes for Stanford class CS231n.">
        <p>This is an introductory lecture designed to introduce image classification.</p>
        <p>The Table of Contents lists nearest-neighbor classifiers.</p>
        """,
    )

    assert role == "lecture"
    assert confidence >= 0.8
    assert "course notes" in reason


def test_infer_material_role_from_text_detects_public_video_lecture_page() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/public-academic/mit-missing-semester/2020/course-shell/index.html",
        """
        <span class="nav-link"><a href="/2026/">lectures</a></span>
        <div class="youtube-wrapper">
        <h1 class="title">Course Overview + The Shell</h1>
        """,
    )

    assert role == "lecture"
    assert confidence >= 0.8
    assert "lectures" in reason


def test_infer_material_role_from_text_detects_generic_exercise_sheet() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/document.pdf",
        """
        Exercise Sheet 4
        Due date: Friday

        Exercise 1. Prove the recurrence relation.
        Exercise 2. Compute the matrix product.
        Exercise 3. Explain the boundary condition.
        """,
    )

    assert role == "assignment"
    assert confidence >= 0.75
    assert "exercises" in reason


def test_infer_material_role_from_text_detects_german_exercise_sheet() -> None:
    role, confidence, reason = infer_material_role_from_text(
        "materials/document.pdf",
        """
        Übungsblatt 6
        Abgabe: Mittwoch

        Aufgabe 1. Erklären Sie den Algorithmus.
        Aufgabe 2. Vergleichen Sie zwei Verfahren.
        Aufgabe 3. Begründen Sie Ihre Antwort.
        """,
    )

    assert role == "assignment"
    assert confidence >= 0.75
    assert "exercises" in reason
