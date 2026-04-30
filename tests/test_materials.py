from __future__ import annotations

from pathlib import Path

from hephaistos.armory.storage import initialize
from hephaistos.materials import (
    count_material_files,
    iter_material_files,
    material_kind,
    material_manifest,
)


def _make_armory(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    initialize(armory)
    return armory


def test_iter_material_files_discovers_source_and_library(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "source" / "exam.md").write_text("# Exam\n", encoding="utf-8")
    (armory / "library" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    (armory / "notes" / "draft.md").write_text("# Draft\n", encoding="utf-8")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == ["source/exam.md", "library/notes.md"]


def test_material_manifest_classifies_material_kind(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "source" / "exam.md").write_text("# Exam\n", encoding="utf-8")
    (armory / "library" / "notes.md").write_text("# Notes\n", encoding="utf-8")

    manifest = material_manifest(armory)

    assert [(item.rel_path, item.kind) for item in manifest] == [
        ("source/exam.md", "source"),
        ("library/notes.md", "library"),
    ]


def test_hidden_files_are_skipped(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / "source" / "visible.md").write_text("# Visible\n", encoding="utf-8")
    (armory / "source" / ".hidden.md").write_text("# Hidden\n", encoding="utf-8")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == ["source/visible.md"]


def test_armory_ignore_is_respected(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)
    (armory / ".hephaistosignore").write_text(
        "source/ignored.md\nlibrary/private/\n",
        encoding="utf-8",
    )
    (armory / "source" / "visible.md").write_text("# Visible\n", encoding="utf-8")
    (armory / "source" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (armory / "library" / "private").mkdir()
    (armory / "library" / "private" / "notes.md").write_text("# Private\n", encoding="utf-8")

    rels = [str(path.relative_to(armory)) for path in iter_material_files(armory)]

    assert rels == ["source/visible.md"]


def test_empty_armory_has_no_materials(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path)

    assert count_material_files(armory) == 0
    assert material_manifest(armory) == ()


def test_material_kind_from_relative_path() -> None:
    assert material_kind("source/exam.md") == "source"
    assert material_kind("library/ref.md") == "library"
    assert material_kind("notes/draft.md") is None
