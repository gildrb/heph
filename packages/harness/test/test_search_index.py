"""Tests for armory discovery and search indexing."""

from __future__ import annotations

from pathlib import Path

import pytest
from harness.armory.search import (
    CrossArmoryIndex,
    SearchResult,
    _chunk_text,
    discover_armory_home_entries,
    forget_armory,
    get_last_armory,
    load_available_armories,
    load_remembered_armories,
    load_remembered_armory_entries,
    remember_armory,
)
from harness.armory.storage import initialize


def _make_material_file(armory: Path, name: str, content: str) -> Path:
    """Create a material file in an armory's materials directory."""
    materials_dir = armory / "materials"
    materials_dir.mkdir(parents=True, exist_ok=True)
    path = materials_dir / name
    path.write_text(content, encoding="utf-8")
    return path


def _initialize_legacy_armory(path: Path) -> None:
    initialize(path)
    (path / ".harness").rename(path / ".hephaion")


def test_chunk_text_short_text_returns_single_chunk() -> None:
    chunks = _chunk_text("Hello world", max_chars=500)
    assert chunks == ["Hello world"]


def test_chunk_text_empty_text_returns_no_chunks() -> None:
    chunks = _chunk_text("")
    assert chunks == []


def test_chunk_text_long_text_returns_multiple_chunks() -> None:
    text = "Line one\n" * 100
    chunks = _chunk_text(text, max_chars=50, overlap=10)
    assert len(chunks) > 1


def test_search_result_properties(tmp_path: Path) -> None:
    result = SearchResult(
        armory_path=tmp_path,
        source_rel="notes.md",
        chunk_index=0,
        chunk_text="some text",
        score=0.9,
    )
    assert result.armory_name == tmp_path.name
    assert result.source_path == tmp_path / "materials" / "notes.md"


def test_cross_armory_index_search_finds_matches(tmp_path: Path) -> None:
    armory = tmp_path / "test-armory"
    initialize(armory)
    content = "Binary search is O(log n). Quick sort is O(n log n)."
    _make_material_file(armory, "algorithms.md", content)

    index = CrossArmoryIndex()
    index.build([armory])

    results = index.search("binary search")
    assert len(results) > 0
    assert any("binary" in r.chunk_text.lower() for r in results)


def test_cross_armory_index_search_empty_query_returns_empty() -> None:
    index = CrossArmoryIndex()
    assert index.search("") == []
    assert index.search("  ") == []


def test_cross_armory_index_search_no_results(tmp_path: Path) -> None:
    armory = tmp_path / "empty-armory"
    initialize(armory)
    _make_material_file(armory, "notes.md", "The weather is nice today.")

    index = CrossArmoryIndex()
    index.build([armory])

    results = index.search("quantum computing")
    assert results == []


def test_remembered_armories_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    armory = tmp_path / "my-armory"
    armory.mkdir()

    raw_settings: dict[str, object] = {}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    def fake_save(key: str, value: object) -> None:
        raw_settings[key] = value

    monkeypatch.setattr("harness.armory.search.load_raw_settings", fake_load)
    monkeypatch.setattr("harness.armory.search.save_setting", fake_save)

    paths = remember_armory(armory)
    assert len(paths) == 1
    assert paths[0] == armory

    loaded = load_remembered_armories()
    assert len(loaded) == 1

    paths = forget_armory(armory)
    assert len(paths) == 0


def test_remembered_armory_entries_include_missing_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = tmp_path / "existing"
    initialize(existing)
    missing = tmp_path / "missing"
    raw_settings: dict[str, object] = {"known_armories": [str(existing), str(missing)]}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    monkeypatch.setattr("harness.armory.search.load_raw_settings", fake_load)

    entries = load_remembered_armory_entries()

    assert entries[0].path == existing
    assert entries[0].exists is True
    assert entries[0].valid is True
    assert entries[1].path == missing
    assert entries[1].missing is True
    assert load_remembered_armories() == [existing]


def test_remember_armory_no_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    armory = tmp_path / "my-armory"
    armory.mkdir()

    raw_settings: dict[str, object] = {}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    def fake_save(key: str, value: object) -> None:
        raw_settings[key] = value

    monkeypatch.setattr("harness.armory.search.load_raw_settings", fake_load)
    monkeypatch.setattr("harness.armory.search.save_setting", fake_save)

    remember_armory(armory)
    paths = remember_armory(armory)
    assert len(paths) == 1


def test_available_armories_include_copied_armory_home_children(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    copied = armory_home / "copied-course"
    initialize(copied)
    not_armory = armory_home / "plain-folder"
    not_armory.mkdir()
    raw_settings: dict[str, object] = {}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    monkeypatch.setattr("harness.armory.search.load_raw_settings", fake_load)

    discovered = discover_armory_home_entries()

    assert [entry.path for entry in discovered] == [copied.resolve()]
    assert load_available_armories() == [copied.resolve()]


def test_available_armories_include_legacy_armory_home_children(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    legacy = armory_home / "legacy-course"
    _initialize_legacy_armory(legacy)
    raw_settings: dict[str, object] = {}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    monkeypatch.setattr("harness.armory.search.load_raw_settings", fake_load)

    discovered = discover_armory_home_entries()

    assert [entry.path for entry in discovered] == [legacy.resolve()]
    assert load_available_armories() == [legacy.resolve()]


def test_last_armory_accepts_legacy_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = tmp_path / "legacy-course"
    _initialize_legacy_armory(legacy)
    raw_settings: dict[str, object] = {"last_armory_path": str(legacy)}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    monkeypatch.setattr("harness.armory.search.load_raw_settings", fake_load)

    assert get_last_armory() == legacy.resolve()
