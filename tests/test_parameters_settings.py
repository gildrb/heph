from __future__ import annotations

import json
from pathlib import Path

import pytest

from hephaistos.parameters import settings


def test_load_raw_settings_refreshes_when_config_path_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_dir = tmp_path / "first"
    first_file = first_dir / "config.json"
    first_dir.mkdir(parents=True, exist_ok=True)
    first_file.write_text(json.dumps({"model": "first-model"}), encoding="utf-8")

    second_dir = tmp_path / "second"
    second_file = second_dir / "config.json"
    second_dir.mkdir(parents=True, exist_ok=True)
    second_file.write_text(json.dumps({"model": "second-model"}), encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", first_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", first_file)
    settings.invalidate_settings_cache()

    assert settings.load_raw_settings() == {"model": "first-model"}

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", second_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", second_file)

    assert settings.load_raw_settings() == {"model": "second-model"}


def test_load_raw_settings_refreshes_after_external_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"model": "initial-model"}), encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)
    settings.invalidate_settings_cache()

    assert settings.load_raw_settings() == {"model": "initial-model"}

    config_file.write_text(json.dumps({"model": "updated-model"}), encoding="utf-8")

    assert settings.load_raw_settings() == {"model": "updated-model"}
