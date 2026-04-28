"""Tests for cross-armory search indexing."""

from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.app.search_index import (
    CrossArmoryIndex,
    SearchResult,
    _chunk_text,
    add_known_armory,
    load_known_armories,
    remove_known_armory,
)
from hephaistos.armory.storage import initialize
from hephaistos.parameters.settings import invalidate_settings_cache


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Ensure settings cache is clean between tests."""
    invalidate_settings_cache()


def _make_source_file(armory: Path, name: str, content: str) -> Path:
    """Create a source file in an armory's source directory."""
    source_dir = armory / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    path = source_dir / name
    path.write_text(content, encoding="utf-8")
    return path


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
    assert result.source_path == tmp_path / "source" / "notes.md"


def test_cross_armory_index_search_finds_matches(tmp_path: Path) -> None:
    armory = tmp_path / "test-armory"
    initialize(armory)
    content = "Binary search is O(log n). Quick sort is O(n log n)."
    _make_source_file(armory, "algorithms.md", content)

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
    _make_source_file(armory, "notes.md", "The weather is nice today.")

    index = CrossArmoryIndex()
    index.build([armory])

    results = index.search("quantum computing")
    assert results == []


def test_known_armories_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    armory = tmp_path / "my-armory"
    armory.mkdir()

    raw_settings: dict[str, object] = {}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    def fake_save(key: str, value: object) -> None:
        raw_settings[key] = value

    monkeypatch.setattr("hephaistos.app.search_index.load_raw_settings", fake_load)
    monkeypatch.setattr("hephaistos.app.search_index.save_setting", fake_save)

    paths = add_known_armory(armory)
    assert len(paths) == 1
    assert paths[0] == armory

    loaded = load_known_armories()
    assert len(loaded) == 1

    paths = remove_known_armory(armory)
    assert len(paths) == 0


def test_add_known_armory_no_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    armory = tmp_path / "my-armory"
    armory.mkdir()

    raw_settings: dict[str, object] = {}

    def fake_load() -> dict[str, object]:
        return dict(raw_settings)

    def fake_save(key: str, value: object) -> None:
        raw_settings[key] = value

    monkeypatch.setattr("hephaistos.app.search_index.load_raw_settings", fake_load)
    monkeypatch.setattr("hephaistos.app.search_index.save_setting", fake_save)

    add_known_armory(armory)
    paths = add_known_armory(armory)
    assert len(paths) == 1
