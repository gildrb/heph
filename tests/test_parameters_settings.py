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


def test_default_interface_mode_is_tui() -> None:
    assert settings.DEFAULT_INTERFACE_MODE == "tui"
    assert settings.INTERFACE_MODES == ("tui",)


def test_app_settings_default_interface_mode_is_tui() -> None:
    s = settings.AppSettings()
    assert s.interface_mode == "tui"
    assert s.activity_trace_mode == settings.DEFAULT_ACTIVITY_TRACE_MODE


def test_load_app_settings_defaults_to_tui(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)
    settings.invalidate_settings_cache()

    assert settings.load_app_settings().interface_mode == "tui"


def test_load_app_settings_rejects_classic_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Classic mode is no longer supported — falls back to TUI."""
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"interface_mode": "classic"}), encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)
    settings.invalidate_settings_cache()

    assert settings.load_app_settings().interface_mode == "tui"


def test_normalize_interface_mode_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="interface_mode"):
        settings.normalize_setting_value("interface_mode", "gtk")


def test_normalize_interface_mode_rejects_classic() -> None:
    with pytest.raises(ValueError, match="interface_mode"):
        settings.normalize_setting_value("interface_mode", "classic")


def test_normalize_interface_mode_accepts_tui() -> None:
    assert settings.normalize_setting_value("interface_mode", "tui") == "tui"


def test_save_and_load_interface_mode_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)
    settings.invalidate_settings_cache()

    settings.save_setting("interface_mode", "tui")
    assert settings.load_app_settings().interface_mode == "tui"


def test_activity_trace_mode_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)
    settings.invalidate_settings_cache()

    settings.save_setting("activity_trace_mode", settings.ACTIVITY_TRACE_HIDDEN_TOOL_CALLS)

    assert settings.load_app_settings().activity_trace_mode == (
        settings.ACTIVITY_TRACE_HIDDEN_TOOL_CALLS
    )


def test_normalize_activity_trace_mode_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="activity_trace_mode"):
        settings.normalize_setting_value("activity_trace_mode", "verbose")
