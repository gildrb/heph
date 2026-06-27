"""Tests for TUI armory discovery helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from harness.armory.search import ArmoryEntry
from harness.armory.storage import MARKER_FILE, initialize
from interfaces.tui import armory_browser


def _make_dirs(parent: Path, *names: str) -> list[Path]:
    dirs: list[Path] = []
    for name in names:
        path = parent / name
        path.mkdir(parents=True, exist_ok=True)
        dirs.append(path)
    return dirs


def _make_armory(parent: Path, name: str) -> Path:
    path = parent / name
    initialize(path)
    return path


def test_list_entries_skips_hidden_and_files_by_default(tmp_path: Path) -> None:
    _make_dirs(tmp_path, "visible", ".hidden")
    (tmp_path / "a-file.txt").touch()

    dirs = armory_browser._list_entries(tmp_path)

    names = [path.name for path in dirs]
    assert "visible" in names
    assert ".hidden" not in names
    assert "a-file.txt" not in names


def test_is_armory_detects_marker(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path, "my-armory")
    plain = tmp_path / "plain-dir"
    plain.mkdir()

    assert armory_browser._is_armory(armory)
    assert not armory_browser._is_armory(plain)
    assert (armory / MARKER_FILE).exists()


def test_build_entries_include_recent_all_and_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))

    entries = armory_browser.build_entries(allow_create=True)

    assert entries[0].is_section
    assert entries[0].label == armory_browser._RECENT_HEADING
    all_index = next(
        index for index, entry in enumerate(entries) if entry.label == armory_browser._ALL_HEADING
    )
    assert entries[all_index + 1].is_create
    assert entries[all_index + 1].label == armory_browser._NEW_ARMORY_LABEL


def test_build_entries_without_create_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    _make_dirs(armory_home, "alpha", "beta")

    entries = armory_browser.build_entries(allow_create=False)
    labels = [entry.label for entry in entries]

    assert not any(entry.is_create for entry in entries)
    assert any("alpha" in label for label in labels)
    assert any("beta" in label for label in labels)


def test_build_entries_can_include_common_places(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))

    entries = armory_browser.build_entries(allow_create=True, show_places=True)

    place_entries = [entry for entry in entries if entry.is_place]
    assert any(entry.path == armory_home for entry in place_entries)
    assert all(
        entry.path is not None and armory_browser._is_within_armory_home(entry.path)
        for entry in place_entries
    )


def test_build_entries_filters_outside_recent_armories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    inside = _make_armory(armory_home, "inside")
    outside = _make_armory(tmp_path / "outside", "external")
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    monkeypatch.setattr(
        armory_browser,
        "load_remembered_armory_entries",
        lambda: [
            ArmoryEntry(outside, exists=True, valid=True),
            ArmoryEntry(inside, exists=True, valid=True),
        ],
    )

    entries = armory_browser.build_entries(allow_create=True)

    recent_paths = [entry.path for entry in entries if entry.is_recent]
    assert recent_paths == [inside]


def test_build_entries_discovers_armories_in_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    first = _make_armory(armory_home, "alpha")
    second = _make_armory(armory_home, "beta")
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))

    entries = armory_browser.build_entries(allow_create=True)

    all_paths = {entry.path for entry in entries if entry.path is not None}
    assert first.resolve() in all_paths
    assert second.resolve() in all_paths


def test_build_entries_filters_symlink_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    outside = tmp_path / "outside"
    armory_home.mkdir()
    outside.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    (armory_home / "outside-link").symlink_to(outside, target_is_directory=True)

    entries = armory_browser.build_entries(allow_create=True)

    assert not any(entry.path == armory_home / "outside-link" for entry in entries)


def test_default_start_path_rejects_outside_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))

    start = armory_browser._default_start_path(outside)

    assert start == armory_home


def test_new_armory_path_rejects_escape_names(tmp_path: Path) -> None:
    for name in ("../escape", "/tmp/escape", "nested/name"):
        path, error = armory_browser.new_armory_path(tmp_path, name)

        assert path is None
        assert error is not None


def test_new_armory_path_rejects_existing_folder(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()

    path, error = armory_browser.new_armory_path(tmp_path, "existing")

    assert path is None
    assert error is not None


def test_creation_parent_error_rejects_outside_armories_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))

    error = armory_browser._creation_parent_error(outside)

    assert error is not None
    assert "Armories can only be created" in error


def test_creation_parent_error_allows_inside_armories_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    inside = armory_home / "next"
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))

    error = armory_browser._creation_parent_error(inside)

    assert error is None


def test_armory_detail_uses_label_value_layout(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path, "exam")
    (armory / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")

    detail = armory_browser.armory_detail(armory)

    assert "STATE valid" in detail
    assert "FILES 1" in detail
    assert "MATERIALS materials/" in detail
    assert "STATE DIR .harness/" in detail
