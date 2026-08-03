from __future__ import annotations

import contextlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ai.runtime.thinking import (
    THINKING_VISIBILITY_ALL,
    THINKING_VISIBILITY_MINIMAL,
    THINKING_VISIBILITY_MODES,
    THINKING_VISIBILITY_OFF,
)

from harness._types import is_string_mapping

_DEFAULTS_FILE = Path(__file__).parent / "default.toml"
_USER_CONFIG_DIR = Path.home() / ".config" / "harness"
_USER_CONFIG_FILE = _USER_CONFIG_DIR / "config.json"

DEFAULT_THEME: Final[str] = "dark"
THEME_PRESETS: Final[tuple[str, ...]] = ("dark", "light")
THEME_LABELS: Final[dict[str, str]] = {
    "dark": "Dark",
    "light": "Light",
}
ACTIVITY_TRACE_TOOL_CALLS: Final[str] = "tool_calls"
ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: Final[str] = "minimal_tool_calls"
ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: Final[str] = "hidden_tool_calls"
ACTIVITY_TRACE_MODES: Final[tuple[str, ...]] = (
    ACTIVITY_TRACE_TOOL_CALLS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
)
DEFAULT_ACTIVITY_TRACE_MODE: Final[str] = ACTIVITY_TRACE_MINIMAL_TOOL_CALLS
ACTIVITY_TRACE_LABELS: Final[dict[str, str]] = {
    ACTIVITY_TRACE_TOOL_CALLS: "All tool calls",
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
DEFAULT_THINKING_VISIBILITY: Final[str] = THINKING_VISIBILITY_MINIMAL
THINKING_VISIBILITY_LABELS: Final[dict[str, str]] = {
    THINKING_VISIBILITY_OFF: "Hidden",
    THINKING_VISIBILITY_MINIMAL: "Minimal",
    THINKING_VISIBILITY_ALL: "All",
}
BOOL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "live_cost_visible",
        "live_tokens_visible",
    }
)
OBJECT_KEYS: Final[frozenset[str]] = frozenset({"tui_keymap"})
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
        "thinking_visibility",
    }
)
INT_KEYS: Final[frozenset[str]] = frozenset({"max_tokens", "rag_context_budget", "session_count"})
FLOAT_KEYS: Final[frozenset[str]] = frozenset({"temperature"})
PUBLIC_CONFIG_KEYS: Final[tuple[str, ...]] = (
    "base_url",
    "model",
    "max_tokens",
    "rag_context_budget",
    "temperature",
    "feature_flags",
    "theme",
    "default_armory_path",
    "activity_trace_mode",
    "vocab_strictness",
    "thinking_visibility",
    "live_tokens_visible",
    "live_cost_visible",
)
INTERNAL_CONFIG_KEYS: Final[tuple[str, ...]] = (
    "known_armories",
    "recent_armories",
    "last_armory_path",
    "session_count",
    "tui_keymap",
)
ALLOWED_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    (*PUBLIC_CONFIG_KEYS, *INTERNAL_CONFIG_KEYS)
)
_TRUE_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "no", "off"})
type SettingNormalizer = Callable[[object], object]


def _ensure_private_config_dir() -> None:
    _USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    _USER_CONFIG_DIR.chmod(0o700)


def _write_private_text(path: Path, text: str) -> None:
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
    except Exception:
        os.close(fd)
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(text)


def user_config_dir() -> Path:
    return _USER_CONFIG_DIR


@dataclass(frozen=True)
class AppSettings:
    theme: str = DEFAULT_THEME
    default_armory_path: str = ""
    last_armory_path: str = ""
    activity_trace_mode: str = DEFAULT_ACTIVITY_TRACE_MODE
    vocab_strictness: str = DEFAULT_VOCAB_STRICTNESS
    thinking_visibility: str = DEFAULT_THINKING_VISIBILITY
    live_tokens_visible: bool = False
    live_cost_visible: bool = False
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


def _normalize_int(value: object) -> int:
    if isinstance(value, int):
        return value
    return int(str(value).strip())


def _normalize_float(value: object) -> float:
    return float(str(value).strip())


def _normalize_choice(key: str, value: object, choices: tuple[str, ...]) -> str:
    normalized = str(value).strip().lower()
    if normalized not in choices:
        raise ValueError(f"{key} must be one of: {', '.join(choices)}")
    return normalized


def _normalize_path(value: object) -> str:
    raw = str(value).strip()
    if not raw:
        return ""
    return str(Path(raw).expanduser().resolve())


def _normalize_feature_flags(value: object) -> str:
    flags = parse_feature_flags(str(value))
    return ",".join(sorted(flags))


def _normalize_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _normalize_object(value: object) -> dict[str, object]:
    if is_string_mapping(value):
        return dict(value)
    return {}


def _setting_normalizers() -> dict[str, SettingNormalizer]:
    normalizers: dict[str, SettingNormalizer] = {
        "theme": lambda value: _normalize_choice("theme", value, THEME_PRESETS),
        "activity_trace_mode": lambda value: _normalize_choice(
            "activity_trace_mode", value, ACTIVITY_TRACE_MODES
        ),
        "vocab_strictness": lambda value: _normalize_choice(
            "vocab_strictness", value, VOCAB_STRICTNESS_MODES
        ),
        "thinking_visibility": lambda value: _normalize_choice(
            "thinking_visibility", value, THINKING_VISIBILITY_MODES
        ),
        "default_armory_path": _normalize_path,
        "last_armory_path": _normalize_path,
        "feature_flags": _normalize_feature_flags,
        "known_armories": _normalize_string_list,
        "recent_armories": _normalize_string_list,
    }
    normalizers.update(dict.fromkeys(BOOL_KEYS, _coerce_bool))
    normalizers.update(dict.fromkeys(INT_KEYS, _normalize_int))
    normalizers.update(dict.fromkeys(FLOAT_KEYS, _normalize_float))
    normalizers.update(dict.fromkeys(OBJECT_KEYS, _normalize_object))
    normalizers.update(dict.fromkeys(STRING_KEYS - normalizers.keys(), str))
    return normalizers


def normalize_setting_value(key: str, value: object) -> object:
    normalizer = _setting_normalizers().get(key)
    if normalizer is None:
        raise KeyError(key)
    return normalizer(value)


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
    _ensure_private_config_dir()
    filtered = {key: settings[key] for key in sorted(settings) if key in ALLOWED_CONFIG_KEYS}
    _write_private_text(_USER_CONFIG_FILE, json.dumps(filtered, indent=2) + "\n")


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
    thinking_visibility = (
        str(raw.get("thinking_visibility", DEFAULT_THINKING_VISIBILITY)).strip().lower()
    )
    if thinking_visibility not in THINKING_VISIBILITY_MODES:
        thinking_visibility = DEFAULT_THINKING_VISIBILITY
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
        thinking_visibility=thinking_visibility,
        live_tokens_visible=_coerce_bool(raw.get("live_tokens_visible"), default=False),
        live_cost_visible=_coerce_bool(raw.get("live_cost_visible"), default=False),
        session_count=session_count,
    )
