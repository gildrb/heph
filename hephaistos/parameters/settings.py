"""Typed access to persisted cross-session settings."""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

_DEFAULTS_FILE = Path(__file__).parent / "default.toml"
_USER_CONFIG_DIR = Path.home() / ".config" / "hephaistos"
_USER_CONFIG_FILE = _USER_CONFIG_DIR / "config.json"

DEFAULT_THEME: Final[str] = "forge"
THEME_PRESETS: Final[tuple[str, ...]] = ("forge", "light", "high_contrast")
BOOL_KEYS: Final[frozenset[str]] = frozenset(
    {"analytics_enabled", "crash_reports_enabled", "telemetry_notice_seen"}
)
STRING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "base_url",
        "model",
        "feature_flags",
        "theme",
        "default_armory_path",
    }
)
INT_KEYS: Final[frozenset[str]] = frozenset({"max_tokens", "rag_context_budget"})
PUBLIC_CONFIG_KEYS: Final[tuple[str, ...]] = (
    "base_url",
    "model",
    "max_tokens",
    "rag_context_budget",
    "feature_flags",
    "theme",
    "default_armory_path",
    "analytics_enabled",
    "crash_reports_enabled",
)
INTERNAL_CONFIG_KEYS: Final[tuple[str, ...]] = ("telemetry_notice_seen",)
ALLOWED_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    (*PUBLIC_CONFIG_KEYS, *INTERNAL_CONFIG_KEYS)
)
DEFAULT_INT_VALUES: Final[dict[str, int]] = {"max_tokens": 4096, "rag_context_budget": 2000}

_TRUE_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "no", "off"})


@dataclass(frozen=True)
class AppSettings:
    theme: str = DEFAULT_THEME
    default_armory_path: str = ""
    analytics_enabled: bool = False
    crash_reports_enabled: bool = False
    telemetry_notice_seen: bool = False


def parse_toml_simple(path: Path) -> dict[str, str]:
    """Minimal TOML parser for flat key=value files."""
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "[")):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value.startswith('"'):
            end = value.find('"', 1)
            if end != -1:
                value = value[1:end]
        elif "#" in value:
            value = value[: value.index("#")].strip()
        result[key] = value
    return result


def parse_feature_flags(raw: str) -> frozenset[str]:
    """Parse comma-separated feature-flag slugs into a frozenset."""
    return frozenset(slug.strip().lower() for slug in raw.split(",") if slug.strip())


def _coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_VALUES:
            return True
        if lowered in _FALSE_VALUES:
            return False
    return default


def normalize_setting_value(key: str, value: object) -> object:
    """Normalize a user-facing config value to a JSON-safe representation."""
    if key in BOOL_KEYS:
        return _coerce_bool(value)
    if key in INT_KEYS:
        if isinstance(value, int):
            return value
        return int(str(value).strip())
    if key == "theme":
        theme = str(value).strip().lower()
        if theme not in THEME_PRESETS:
            raise ValueError(f"theme must be one of: {', '.join(THEME_PRESETS)}")
        return theme
    if key == "default_armory_path":
        raw = str(value).strip()
        if not raw:
            return ""
        return str(Path(raw).expanduser().resolve())
    if key == "feature_flags":
        flags = parse_feature_flags(str(value))
        return ",".join(sorted(flags))
    if key in STRING_KEYS:
        return str(value)
    raise KeyError(key)


_settings_cache: dict[str, object] | None = None


def invalidate_settings_cache() -> None:
    """Clear the in-process settings cache (used by tests and edge cases)."""
    global _settings_cache
    _settings_cache = None


def load_raw_settings() -> dict[str, object]:
    """Load persisted settings from ``~/.config/hephaistos/config.json``.

    Results are cached in-process and reused until ``save_raw_settings()``
    or ``invalidate_settings_cache()`` is called.
    """
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
    if not _USER_CONFIG_FILE.is_file():
        _settings_cache = {}
        return _settings_cache
    with contextlib.suppress(Exception):
        raw = json.loads(_USER_CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            data = cast("dict[str, Any]", raw)
            _settings_cache = {str(k): v for k, v in data.items() if k in ALLOWED_CONFIG_KEYS}
            return _settings_cache
    _settings_cache = {}
    return _settings_cache


def save_raw_settings(settings: dict[str, object]) -> None:
    """Persist the full settings mapping to disk and update the in-process cache."""
    global _settings_cache
    _USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    filtered = {key: settings[key] for key in sorted(settings) if key in ALLOWED_CONFIG_KEYS}
    _USER_CONFIG_FILE.write_text(json.dumps(filtered, indent=2) + "\n", encoding="utf-8")
    _settings_cache = filtered


def save_setting(key: str, value: object) -> None:
    """Persist one normalized setting value."""
    settings = load_raw_settings()
    settings[key] = normalize_setting_value(key, value)
    save_raw_settings(settings)


def clear_setting(key: str) -> None:
    """Remove a persisted setting."""
    settings = load_raw_settings()
    settings.pop(key, None)
    save_raw_settings(settings)


def load_app_settings() -> AppSettings:
    """Return typed app settings for the shell and telemetry surfaces."""
    raw = load_raw_settings()
    theme = str(raw.get("theme", DEFAULT_THEME)).strip().lower() or DEFAULT_THEME
    if theme not in THEME_PRESETS:
        theme = DEFAULT_THEME
    default_armory = str(raw.get("default_armory_path", "")).strip()
    return AppSettings(
        theme=theme,
        default_armory_path=default_armory,
        analytics_enabled=_coerce_bool(raw.get("analytics_enabled"), default=False),
        crash_reports_enabled=_coerce_bool(raw.get("crash_reports_enabled"), default=False),
        telemetry_notice_seen=_coerce_bool(raw.get("telemetry_notice_seen"), default=False),
    )


def effective_config_value(key: str) -> object | None:
    """Return the raw persisted value for a config key."""
    return load_raw_settings().get(key)
