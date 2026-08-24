from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest
from harness.parameters import settings


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

    assert settings.load_raw_settings() == {"model": "initial-model"}

    config_file.write_text(json.dumps({"model": "updated-model"}), encoding="utf-8")

    assert settings.load_raw_settings() == {"model": "updated-model"}


def test_app_settings_default_activity_trace_mode_is_minimal_tool_calls() -> None:
    s = settings.AppSettings()
    assert (
        s.activity_trace_mode
        == settings.DEFAULT_ACTIVITY_TRACE_MODE
        == settings.ACTIVITY_TRACE_MINIMAL_TOOL_CALLS
    )


def test_app_settings_default_theme_is_dark() -> None:
    s = settings.AppSettings()
    assert s.theme == settings.DEFAULT_THEME == "dark"




def test_app_settings_default_live_usage_visibility_is_off() -> None:
    s = settings.AppSettings()

    assert s.live_tokens_visible is False
    assert s.live_cost_visible is False


def test_app_settings_default_thinking_visibility_is_minimal() -> None:
    s = settings.AppSettings()

    assert s.thinking_visibility == settings.DEFAULT_THINKING_VISIBILITY == "minimal"


def test_load_app_settings_ignores_removed_interface_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"interface_mode": "classic"}), encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)

    assert settings.load_raw_settings() == {}


def test_load_app_settings_ignores_removed_privacy_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(
            {
                "analytics_enabled": True,
                "crash_reports_enabled": True,
                "privacy_notice_seen": True,
                "theme": "light",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)

    assert settings.load_raw_settings() == {"theme": "light"}
    assert settings.load_app_settings().theme == "light"


def test_activity_trace_mode_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)

    settings.save_setting("activity_trace_mode", settings.ACTIVITY_TRACE_HIDDEN_TOOL_CALLS)

    assert settings.load_app_settings().activity_trace_mode == (
        settings.ACTIVITY_TRACE_HIDDEN_TOOL_CALLS
    )


def test_live_usage_visibility_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)

    settings.save_setting("live_tokens_visible", True)
    settings.save_setting("live_cost_visible", "true")

    app_settings = settings.load_app_settings()
    assert app_settings.live_tokens_visible is True
    assert app_settings.live_cost_visible is True


def test_thinking_visibility_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)

    settings.save_setting("thinking_visibility", "all")

    assert settings.load_app_settings().thinking_visibility == "all"


@pytest.mark.parametrize("removed_theme", ["forge", "high_contrast"])
def test_load_app_settings_maps_removed_themes_to_dark(
    removed_theme: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"theme": removed_theme}), encoding="utf-8")

    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)

    assert settings.load_app_settings().theme == "dark"


@pytest.mark.parametrize("removed_theme", ["forge", "high_contrast"])
def test_normalize_theme_rejects_removed_presets(removed_theme: str) -> None:
    with pytest.raises(ValueError, match="theme"):
        settings.normalize_setting_value("theme", removed_theme)


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not portable on Windows")
def test_save_setting_writes_private_config_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings, "_USER_CONFIG_FILE", config_file)

    settings.save_setting("model", "gpt-5.5")

    assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o600


def test_normalize_activity_trace_mode_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="activity_trace_mode"):
        settings.normalize_setting_value("activity_trace_mode", "verbose")


def test_normalize_thinking_visibility_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="thinking_visibility"):
        settings.normalize_setting_value("thinking_visibility", "verbose")
