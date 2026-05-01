from __future__ import annotations

from pathlib import Path

from hephaistos.armory.storage import initialize
from hephaistos.materials import (
    count_material_files,
    infer_material_role,
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
    (armory / ".hephaistos" / "generated" / "draft.md").write_text("# Draft\n", encoding="utf-8")

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
    (armory / ".hephaistosignore").write_text(
        "materials/ignored.md\nmaterials/private/\n",
        encoding="utf-8",
    )
    (armory / "materials" / "visible.md").write_text("# Visible\n", encoding="utf-8")
    (armory / "materials" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (armory / "materials" / "private").mkdir()
    (armory / "materials" / "private" / "notes.md").write_text("# Private\n", encoding="utf-8")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == ["materials/visible.md"]


def test_empty_armory_has_no_materials(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)

    assert count_material_files(armory) == 0
    assert material_manifest(armory) == ()


def test_material_kind_from_relative_path() -> None:
    assert material_kind("materials/exam.md") == "materials"
    assert material_kind(".hephaistos/generated/ref.md") is None


def test_infer_material_role_uses_path_hints() -> None:
    cases = {
        "materials/past-exams/2023.pdf": "past_exam",
        "materials/homework/sheet-1.md": "assignment",
        "materials/vocab/french.md": "vocabulary",
        "materials/lectures/week-1.md": "lecture",
        "materials/slides/deck.pptx": "slides",
        "materials/book/chapter-2.pdf": "textbook",
        "materials/project/main.py": "codebase",
        "materials/misc/context.md": "reference",
    }

    for rel_path, expected_role in cases.items():
        role, confidence, reason = infer_material_role(rel_path)
        assert role == expected_role
        assert 0.0 <= confidence <= 1.0
        assert reason
