"""Typed access to persisted cross-session settings."""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from hephaistos._types import is_string_mapping

_DEFAULTS_FILE = Path(__file__).parent / "default.toml"
_USER_CONFIG_DIR = Path.home() / ".config" / "hephaistos"
_USER_CONFIG_FILE = _USER_CONFIG_DIR / "config.json"

DEFAULT_THEME: Final[str] = "forge"
THEME_PRESETS: Final[tuple[str, ...]] = ("forge", "light", "high_contrast")
INTERFACE_MODES: Final[tuple[str, ...]] = ("tui",)
DEFAULT_INTERFACE_MODE: Final[str] = "tui"
BOOL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "analytics_enabled",
        "crash_reports_enabled",
        "supermemory_enabled",
        "supermemory_onboarding_seen",
        "telemetry_notice_seen",
    }
)
STRING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "base_url",
        "model",
        "feature_flags",
        "supermemory_profile",
        "theme",
        "default_armory_path",
        "interface_mode",
    }
)
INT_KEYS: Final[frozenset[str]] = frozenset({"max_tokens", "rag_context_budget", "session_count"})
PUBLIC_CONFIG_KEYS: Final[tuple[str, ...]] = (
    "base_url",
    "model",
    "max_tokens",
    "rag_context_budget",
    "feature_flags",
    "supermemory_profile",
    "theme",
    "default_armory_path",
    "interface_mode",
    "analytics_enabled",
    "crash_reports_enabled",
    "supermemory_enabled",
)
INTERNAL_CONFIG_KEYS: Final[tuple[str, ...]] = (
    "known_armories",
    "supermemory_onboarding_seen",
    "telemetry_notice_seen",
    "session_count",
)
ALLOWED_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    (*PUBLIC_CONFIG_KEYS, *INTERNAL_CONFIG_KEYS)
)
DEFAULT_INT_VALUES: Final[dict[str, int]] = {
    "max_tokens": 4096,
    "rag_context_budget": 2000,
    "session_count": 0,
}

_TRUE_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "no", "off"})


@dataclass(frozen=True)
class AppSettings:
    theme: str = DEFAULT_THEME
    default_armory_path: str = ""
    interface_mode: str = DEFAULT_INTERFACE_MODE
    analytics_enabled: bool = False
    crash_reports_enabled: bool = False
    supermemory_enabled: bool = False
    supermemory_profile: str = "heph-study"
    supermemory_onboarding_seen: bool = False
    telemetry_notice_seen: bool = False
    session_count: int = 0


@dataclass
class _SettingsCache:
    path: Path | None = None
    stamp: tuple[bool, int | None, int | None] | None = None
    data: dict[str, object] | None = None


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
    if isinstance(value, int | float):
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
    if key == "interface_mode":
        mode = str(value).strip().lower()
        if mode not in INTERFACE_MODES:
            raise ValueError(f"interface_mode must be one of: {', '.join(INTERFACE_MODES)}")
        return mode
    if key == "default_armory_path":
        raw = str(value).strip()
        if not raw:
            return ""
        return str(Path(raw).expanduser().resolve())
    if key == "feature_flags":
        flags = parse_feature_flags(str(value))
        return ",".join(sorted(flags))
    if key == "supermemory_profile":
        profile = str(value).strip()
        return profile or "heph-study"
    if key in STRING_KEYS:
        return str(value)
    if key == "known_armories":
        if isinstance(value, list):
            return [str(v) for v in value]  # type: ignore[reportUnknownArgumentType,reportUnknownVariableType]
        return []
    raise KeyError(key)


_settings_cache = _SettingsCache()


def _settings_file_stamp(path: Path) -> tuple[bool, int | None, int | None]:
    try:
        stat = path.stat()
    except OSError:
        return (False, None, None)
    return (True, stat.st_mtime_ns, stat.st_size)


def _cached_settings_for(path: Path) -> dict[str, object] | None:
    if _settings_cache.data is None or _settings_cache.path != path:
        return None
    if _settings_cache.stamp != _settings_file_stamp(path):
        return None
    return _settings_cache.data


def _update_settings_cache(path: Path, settings: dict[str, object]) -> dict[str, object]:
    _settings_cache.path = path
    _settings_cache.stamp = _settings_file_stamp(path)
    _settings_cache.data = settings
    return settings


def invalidate_settings_cache() -> None:
    """Clear the in-process settings cache (used by tests and edge cases)."""
    _settings_cache.path = None
    _settings_cache.stamp = None
    _settings_cache.data = None


def load_raw_settings() -> dict[str, object]:
    """Load persisted settings from ``~/.config/hephaistos/config.json``.

    Results are cached in-process and refreshed automatically when the
    config path or backing file changes.
    """
    path = _USER_CONFIG_FILE
    cached = _cached_settings_for(path)
    if cached is not None:
        return cached
    if not path.is_file():
        return _update_settings_cache(path, {})
    with contextlib.suppress(Exception):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if is_string_mapping(raw):
            filtered = {key: value for key, value in raw.items() if key in ALLOWED_CONFIG_KEYS}
            return _update_settings_cache(path, filtered)
    return _update_settings_cache(path, {})


def save_raw_settings(settings: dict[str, object]) -> None:
    """Persist the full settings mapping to disk and update the in-process cache."""
    _USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    filtered = {key: settings[key] for key in sorted(settings) if key in ALLOWED_CONFIG_KEYS}
    _USER_CONFIG_FILE.write_text(json.dumps(filtered, indent=2) + "\n", encoding="utf-8")
    _update_settings_cache(_USER_CONFIG_FILE, filtered)


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
    interface_mode = str(raw.get("interface_mode", DEFAULT_INTERFACE_MODE)).strip().lower()
    if interface_mode not in INTERFACE_MODES:
        interface_mode = DEFAULT_INTERFACE_MODE
    return AppSettings(
        theme=theme,
        default_armory_path=default_armory,
        interface_mode=interface_mode,
        analytics_enabled=_coerce_bool(raw.get("analytics_enabled"), default=False),
        crash_reports_enabled=_coerce_bool(raw.get("crash_reports_enabled"), default=False),
        supermemory_enabled=_coerce_bool(raw.get("supermemory_enabled"), default=False),
        supermemory_profile=str(raw.get("supermemory_profile", "heph-study")).strip()
        or "heph-study",
        supermemory_onboarding_seen=_coerce_bool(
            raw.get("supermemory_onboarding_seen"), default=False
        ),
        telemetry_notice_seen=_coerce_bool(raw.get("telemetry_notice_seen"), default=False),
        session_count=int(raw.get("session_count", 0) or 0),  # type: ignore[reportArgumentType]
    )


def effective_config_value(key: str) -> object | None:
    """Return the raw persisted value for a config key."""
    return load_raw_settings().get(key)
