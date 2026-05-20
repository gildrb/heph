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
ACTIVITY_TRACE_TOOL_CALLS: Final[str] = "tool_calls"
ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: Final[str] = "minimal_tool_calls"
ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: Final[str] = "hidden_tool_calls"
ACTIVITY_TRACE_MODES: Final[tuple[str, ...]] = (
    ACTIVITY_TRACE_TOOL_CALLS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
)
DEFAULT_ACTIVITY_TRACE_MODE: Final[str] = ACTIVITY_TRACE_TOOL_CALLS
ACTIVITY_TRACE_LABELS: Final[dict[str, str]] = {
    ACTIVITY_TRACE_TOOL_CALLS: "Tool calls",
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: "Minimal tool calls",
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: "Hidden tool calls",
}
VOCAB_STRICTNESS_STRICT: Final[str] = "strict"
VOCAB_STRICTNESS_LENIENT: Final[str] = "lenient"
VOCAB_STRICTNESS_MODES: Final[tuple[str, ...]] = (
    VOCAB_STRICTNESS_STRICT,
    VOCAB_STRICTNESS_LENIENT,
)
VOCAB_STRICTNESS_LABELS: Final[dict[str, str]] = {
    VOCAB_STRICTNESS_STRICT: "Strict",
    VOCAB_STRICTNESS_LENIENT: "Lenient punctuation",
}
DEFAULT_VOCAB_STRICTNESS: Final[str] = VOCAB_STRICTNESS_STRICT
BOOL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "analytics_enabled",
        "crash_reports_enabled",
        "privacy_notice_seen",
    }
)
STRING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "base_url",
        "model",
        "feature_flags",
        "theme",
        "default_armory_path",
        "last_armory_path",
        "activity_trace_mode",
        "vocab_strictness",
    }
)
INT_KEYS: Final[frozenset[str]] = frozenset({"max_tokens", "rag_context_budget", "session_count"})
PUBLIC_CONFIG_KEYS: Final[tuple[str, ...]] = (
    "base_url",
    "model",
    "max_tokens",
    "rag_context_budget",
    "feature_flags",
    "theme",
    "default_armory_path",
    "activity_trace_mode",
    "vocab_strictness",
    "analytics_enabled",
    "crash_reports_enabled",
)
INTERNAL_CONFIG_KEYS: Final[tuple[str, ...]] = (
    "known_armories",
    "recent_armories",
    "last_armory_path",
    "privacy_notice_seen",
    "session_count",
)
ALLOWED_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    (*PUBLIC_CONFIG_KEYS, *INTERNAL_CONFIG_KEYS)
)
_TRUE_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "no", "off"})


def user_config_dir() -> Path:
    return _USER_CONFIG_DIR


@dataclass(frozen=True)
class AppSettings:
    theme: str = DEFAULT_THEME
    default_armory_path: str = ""
    last_armory_path: str = ""
    activity_trace_mode: str = DEFAULT_ACTIVITY_TRACE_MODE
    vocab_strictness: str = DEFAULT_VOCAB_STRICTNESS
    analytics_enabled: bool = False
    crash_reports_enabled: bool = False
    privacy_notice_seen: bool = False
    session_count: int = 0


def parse_toml_simple(path: Path) -> dict[str, str]:
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
    if key == "activity_trace_mode":
        mode = str(value).strip().lower()
        if mode not in ACTIVITY_TRACE_MODES:
            raise ValueError(
                f"activity_trace_mode must be one of: {', '.join(ACTIVITY_TRACE_MODES)}"
            )
        return mode
    if key == "vocab_strictness":
        mode = str(value).strip().lower()
        if mode not in VOCAB_STRICTNESS_MODES:
            raise ValueError(
                f"vocab_strictness must be one of: {', '.join(VOCAB_STRICTNESS_MODES)}"
            )
        return mode
    if key in {"default_armory_path", "last_armory_path"}:
        raw = str(value).strip()
        if not raw:
            return ""
        return str(Path(raw).expanduser().resolve())
    if key == "feature_flags":
        flags = parse_feature_flags(str(value))
        return ",".join(sorted(flags))
    if key in STRING_KEYS:
        return str(value)
    if key in ("known_armories", "recent_armories"):
        if isinstance(value, list):
            return [str(v) for v in value]
        return []
    raise KeyError(key)


def load_raw_settings() -> dict[str, object]:
    path = _USER_CONFIG_FILE
    if not path.is_file():
        return {}
    with contextlib.suppress(Exception):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if is_string_mapping(raw):
            return {key: value for key, value in raw.items() if key in ALLOWED_CONFIG_KEYS}
    return {}


def save_raw_settings(settings: dict[str, object]) -> None:
    _USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    filtered = {key: settings[key] for key in sorted(settings) if key in ALLOWED_CONFIG_KEYS}
    _USER_CONFIG_FILE.write_text(json.dumps(filtered, indent=2) + "\n", encoding="utf-8")


def save_setting(key: str, value: object) -> None:
    settings = load_raw_settings()
    settings[key] = normalize_setting_value(key, value)
    save_raw_settings(settings)


def clear_setting(key: str) -> None:
    settings = load_raw_settings()
    settings.pop(key, None)
    save_raw_settings(settings)


def load_app_settings() -> AppSettings:
    raw = load_raw_settings()
    theme = str(raw.get("theme", DEFAULT_THEME)).strip().lower() or DEFAULT_THEME
    if theme not in THEME_PRESETS:
        theme = DEFAULT_THEME
    default_armory = str(raw.get("default_armory_path", "")).strip()
    last_armory = str(raw.get("last_armory_path", "")).strip()
    activity_trace_mode = (
        str(raw.get("activity_trace_mode", DEFAULT_ACTIVITY_TRACE_MODE)).strip().lower()
    )
    if activity_trace_mode not in ACTIVITY_TRACE_MODES:
        activity_trace_mode = DEFAULT_ACTIVITY_TRACE_MODE
    vocab_strictness = str(raw.get("vocab_strictness", DEFAULT_VOCAB_STRICTNESS)).strip().lower()
    if vocab_strictness not in VOCAB_STRICTNESS_MODES:
        vocab_strictness = DEFAULT_VOCAB_STRICTNESS
    raw_session_count = raw.get("session_count")
    session_count = 0
    if isinstance(raw_session_count, bool | int | float):
        session_count = int(raw_session_count)
    elif isinstance(raw_session_count, str):
        with contextlib.suppress(ValueError):
            session_count = int(raw_session_count.strip())
    return AppSettings(
        theme=theme,
        default_armory_path=default_armory,
        last_armory_path=last_armory,
        activity_trace_mode=activity_trace_mode,
        vocab_strictness=vocab_strictness,
        analytics_enabled=_coerce_bool(raw.get("analytics_enabled"), default=False),
        crash_reports_enabled=_coerce_bool(raw.get("crash_reports_enabled"), default=False),
        privacy_notice_seen=_coerce_bool(raw.get("privacy_notice_seen"), default=False),
        session_count=session_count,
    )
