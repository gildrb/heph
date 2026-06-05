from __future__ import annotations

from pathlib import Path

import pytest
from armory.storage import initialize
from cli.main import build_parser, run_argv


def _make_armory(tmp_path: Path) -> Path:
    """Create a minimal armory with sample material files."""
    armory_path = tmp_path / "test-armory"
    initialize(armory_path)
    (armory_path / "materials" / "python.md").write_text(
        "# Python\n\nPython is a programming language.\n"
    )
    (armory_path / "materials" / "rust.md").write_text("# Rust\n\nRust is a systems language.\n")
    (armory_path / "materials" / "algorithms.md").write_text(
        "# Algorithms\n\nBinary search runs in O(log n).\n"
    )
    return armory_path


def test_source_list_shows_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    armory_path = _make_armory(tmp_path)
    parser = build_parser()

    run_argv(parser, ["source", "list", str(armory_path)])

    out = capsys.readouterr().out
    assert "materials/algorithms.md" in out
    assert "materials/python.md" in out
    assert "materials/rust.md" in out


def test_materials_list_shows_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    armory_path = _make_armory(tmp_path)
    parser = build_parser()

    run_argv(parser, ["materials", "list", str(armory_path)])

    out = capsys.readouterr().out
    assert "materials/algorithms.md" in out
    assert "materials/python.md" in out
    assert "materials/rust.md" in out


def test_source_list_empty_armory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    armory_path = tmp_path / "empty-armory"
    initialize(armory_path)
    parser = build_parser()

    run_argv(parser, ["source", "list", str(armory_path)])

    out = capsys.readouterr().out
    assert "No materials found." in out


def test_source_count_returns_file_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    armory_path = _make_armory(tmp_path)
    parser = build_parser()

    run_argv(parser, ["source", "count", str(armory_path)])

    out = capsys.readouterr().out
    assert "3" in out


def test_materials_count_returns_file_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    armory_path = _make_armory(tmp_path)
    parser = build_parser()

    run_argv(parser, ["materials", "count", str(armory_path)])

    out = capsys.readouterr().out
    assert "3" in out


def test_source_count_empty_armory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    armory_path = tmp_path / "empty-armory"
    initialize(armory_path)
    parser = build_parser()

    run_argv(parser, ["source", "count", str(armory_path)])

    out = capsys.readouterr().out
    assert "0" in out


def test_source_list_fails_for_invalid_armory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    bad_path = tmp_path / "not-an-armory"
    bad_path.mkdir(parents=True)

    with pytest.raises(SystemExit) as exc:
        run_argv(parser, ["source", "list", str(bad_path)])

    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "error:" in err


def test_source_count_fails_for_invalid_armory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    bad_path = tmp_path / "not-an-armory"
    bad_path.mkdir(parents=True)

    with pytest.raises(SystemExit) as exc:
        run_argv(parser, ["source", "count", str(bad_path)])

    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "error:" in err


def test_source_index_builds_index(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    armory_path = _make_armory(tmp_path)
    parser = build_parser()

    run_argv(parser, ["source", "index", str(armory_path)])

    out = capsys.readouterr().out
    assert "Indexed" in out
    assert "documents" in out
    assert "chunks" in out
    assert (armory_path / ".hephaion" / "rag_index.json").is_file()


def test_materials_index_builds_index(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    armory_path = _make_armory(tmp_path)
    parser = build_parser()

    run_argv(parser, ["materials", "index", str(armory_path)])

    out = capsys.readouterr().out
    assert "Indexed" in out
    assert "documents" in out
    assert "chunks" in out
    assert (armory_path / ".hephaion" / "rag_index.json").is_file()


def test_source_index_fails_for_invalid_armory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    bad_path = tmp_path / "not-an-armory"
    bad_path.mkdir(parents=True)

    with pytest.raises(SystemExit) as exc:
        run_argv(parser, ["source", "index", str(bad_path)])

    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "error:" in err


def test_source_list_ignores_dotfiles(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    armory_path = tmp_path / "dotfile-armory"
    initialize(armory_path)
    (armory_path / "materials" / "visible.md").write_text("# Visible\n")
    (armory_path / "materials" / ".hidden.md").write_text("# Hidden\n")
    parser = build_parser()

    run_argv(parser, ["source", "list", str(armory_path)])

    out = capsys.readouterr().out
    assert "materials/visible.md" in out
    assert ".hidden.md" not in out


def test_source_list_respects_armory_ignore(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    armory_path = tmp_path / "ignored-armory"
    initialize(armory_path)
    (armory_path / ".hephaionignore").write_text("materials/ignored.md\nmaterials/private/\n")
    (armory_path / "materials" / "visible.md").write_text("# Visible\n")
    (armory_path / "materials" / "ignored.md").write_text("# Ignored\n")
    private = armory_path / "materials" / "private"
    private.mkdir()
    (private / "notes.md").write_text("# Private\n")
    parser = build_parser()

    run_argv(parser, ["source", "list", str(armory_path)])

    out = capsys.readouterr().out
    assert "materials/visible.md" in out
    assert "materials/ignored.md" not in out
    assert "materials/private/notes.md" not in out
