from __future__ import annotations

import json
from pathlib import Path

from hephaistos.terminal.history import InputHistory


def test_add_trims_skips_blank_and_skips_consecutive_duplicates() -> None:
    history = InputHistory()

    history.add("  first  ")
    history.add("   ")
    history.add("first")
    history.add("second")

    assert history.entries == ["first", "second"]


def test_add_caps_history_at_1000_entries() -> None:
    history = InputHistory([f"item {i}" for i in range(1000)])

    history.add("item 1000")

    assert len(history.entries) == 1000
    assert history.entries[0] == "item 1"
    assert history.entries[-1] == "item 1000"


def test_save_creates_parent_dirs_and_truncates_to_last_500(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "history.json"
    history = InputHistory([f"item {i}" for i in range(600)])

    history.save(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent.is_dir()
    assert len(data) == 500
    assert data[0] == "item 100"
    assert data[-1] == "item 599"


def test_load_returns_empty_history_for_missing_file(tmp_path: Path) -> None:
    history = InputHistory.load(tmp_path / "missing.json")

    assert history.entries == []


def test_load_returns_empty_history_for_malformed_or_non_list_json(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    not_a_list = tmp_path / "config.json"
    not_a_list.write_text('{"entries": ["a"]}', encoding="utf-8")

    assert InputHistory.load(malformed).entries == []
    assert InputHistory.load(not_a_list).entries == []


def test_load_coerces_loaded_values_to_strings(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text('[1, true, "three"]', encoding="utf-8")

    history = InputHistory.load(path)

    assert history.entries == ["1", "True", "three"]
