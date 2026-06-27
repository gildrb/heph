"""Runtime keymap resolution for the Textual TUI."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from harness._types import JSONValue, is_string_mapping
from harness.parameters.settings import load_raw_settings, save_raw_settings

KEYMAP_SETTING_KEY: Final[str] = "tui_keymap"
MAX_FUNCTION_KEY: Final[int] = 24

_CONTEXT_APP: Final[str] = "app"
_CONTEXT_COMPOSER: Final[str] = "composer"
_CONTEXT_TURN: Final[str] = "turn"


@dataclass(frozen=True)
class TuiKeymapAction:
    id: str
    context: str
    label: str
    description: str
    default_keys: tuple[str, ...]
    show: bool = False
    priority: bool = True
    footer: bool = False


@dataclass(frozen=True)
class RuntimeKeymap:
    bindings: dict[str, tuple[str, ...]]
    configured_actions: frozenset[str]
    errors: tuple[str, ...] = ()

    def keys_for_action(self, action_id: str) -> tuple[str, ...]:
        return self.bindings.get(action_id, ())

    def primary_key(self, action_id: str) -> str:
        keys = self.keys_for_action(action_id)
        return display_key(keys[0]) if keys else ""

    def action_for_key(self, key: str) -> str | None:
        try:
            normalized = normalize_key_spec(key)
        except ValueError:
            return None
        for action in TUI_KEYMAP_ACTIONS:
            if normalized in self.keys_for_action(action.id):
                return action.id
        return None


@dataclass(frozen=True)
class KeymapSaveResult:
    saved: bool
    message: str
    key: str = ""


@dataclass(frozen=True)
class _ModifierPrefix:
    modifier: str
    remaining: str


TUI_KEYMAP_ACTIONS: Final[tuple[TuiKeymapAction, ...]] = (
    TuiKeymapAction(
        "command_palette",
        _CONTEXT_APP,
        "Commands",
        "Open the command palette.",
        ("ctrl+alt+p",),
        footer=True,
    ),
    TuiKeymapAction(
        "open_armory_home",
        _CONTEXT_APP,
        "Armory",
        "Open the armory home.",
        ("ctrl+alt+a",),
        footer=True,
    ),
    TuiKeymapAction(
        "open_materials",
        _CONTEXT_APP,
        "Materials",
        "Choose which materials are used for retrieval.",
        ("ctrl+alt+m",),
        footer=True,
    ),
    TuiKeymapAction(
        "open_search",
        _CONTEXT_APP,
        "Search",
        "Search across armories.",
        ("ctrl+alt+f",),
    ),
    TuiKeymapAction(
        "evidence",
        _CONTEXT_APP,
        "Evidence",
        "Show evidence details.",
        ("ctrl+alt+e",),
    ),
    TuiKeymapAction(
        "clear_transcript",
        _CONTEXT_APP,
        "Screen",
        "Clear the screen.",
        ("ctrl+l",),
    ),
    TuiKeymapAction(
        "complete",
        _CONTEXT_COMPOSER,
        "Complete",
        "Complete the current input.",
        ("tab",),
    ),
    TuiKeymapAction(
        "cycle_reasoning_level",
        _CONTEXT_COMPOSER,
        "Reasoning",
        "Cycle the reasoning level.",
        ("shift+tab",),
        footer=True,
    ),
    TuiKeymapAction(
        "insert_composer_newline",
        _CONTEXT_COMPOSER,
        "Newline",
        "Insert a composer newline.",
        ("shift+enter", "ctrl+enter", "alt+enter", "ctrl+j"),
    ),
    TuiKeymapAction(
        "cancel_turn",
        _CONTEXT_TURN,
        "Stop",
        "Interrupt the active request.",
        ("escape",),
    ),
)
_ACTIONS_BY_ID: Final[dict[str, TuiKeymapAction]] = {
    action.id: action for action in TUI_KEYMAP_ACTIONS
}
_ACTION_CONTEXTS: Final[frozenset[str]] = frozenset(
    action.context for action in TUI_KEYMAP_ACTIONS
)
_MODIFIER_ALIASES: Final[dict[str, str]] = {
    "alt": "alt",
    "control": "ctrl",
    "ctrl": "ctrl",
    "option": "alt",
    "shift": "shift",
}
_MODIFIER_ORDER: Final[tuple[str, ...]] = ("ctrl", "alt", "shift")
_KEY_ALIASES: Final[dict[str, str]] = {
    "del": "delete",
    "esc": "escape",
    "page-down": "pagedown",
    "page-up": "pageup",
    "pagedown": "pagedown",
    "pageup": "pageup",
    "pgdn": "pagedown",
    "pgup": "pageup",
    "return": "enter",
    "spacebar": "space",
}
_NAMED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "apostrophe",
        "at",
        "backslash",
        "backspace",
        "comma",
        "delete",
        "down",
        "end",
        "enter",
        "equals_sign",
        "escape",
        "full_stop",
        "grave_accent",
        "home",
        "left",
        "left_square_bracket",
        "minus",
        "pagedown",
        "pageup",
        "plus",
        "right",
        "right_square_bracket",
        "semicolon",
        "slash",
        "space",
        "tab",
        "up",
        "underscore",
    }
)
_DISPLAY_KEY_ALIASES: Final[dict[str, str]] = {
    "escape": "esc",
    "pagedown": "page-down",
    "pageup": "page-up",
}
_RESERVED_KEY_REASONS: Final[dict[str, str]] = {
    "alt+m": "alt+m is reserved by macOS in common app workflows.",
    "ctrl+c": "ctrl+c is reserved for quitting Heph.",
    "ctrl+d": "ctrl+d is reserved for quitting Heph.",
    "ctrl+m": "ctrl+m reaches terminals as Enter, so it cannot be a reliable shortcut.",
    "ctrl+t": "ctrl+t can clear terminal state in some shells and terminal setups.",
}


def default_runtime_keymap() -> RuntimeKeymap:
    return RuntimeKeymap(
        bindings={action.id: action.default_keys for action in TUI_KEYMAP_ACTIONS},
        configured_actions=frozenset(),
    )


def load_runtime_keymap() -> RuntimeKeymap:
    configured, errors = _load_configured_bindings()
    bindings = {action.id: action.default_keys for action in TUI_KEYMAP_ACTIONS}
    configured_actions: set[str] = set()
    for action in TUI_KEYMAP_ACTIONS:
        context_bindings = configured.get(action.context, {})
        if action.id not in context_bindings:
            continue
        bindings[action.id] = context_bindings[action.id]
        configured_actions.add(action.id)
    errors.extend(_duplicate_binding_errors(bindings))
    return RuntimeKeymap(
        bindings=bindings,
        configured_actions=frozenset(configured_actions),
        errors=tuple(errors),
    )


def keymap_action(action_id: str) -> TuiKeymapAction | None:
    return _ACTIONS_BY_ID.get(action_id)


def default_keys_for_action(action: TuiKeymapAction) -> tuple[str, ...]:
    return action.default_keys


def default_keys_for_action_id(action_id: str) -> tuple[str, ...]:
    action = _ACTIONS_BY_ID.get(action_id)
    if action is None:
        return ()
    return default_keys_for_action(action)


def normalize_key_spec(raw: str) -> str:
    key = raw.strip().casefold().replace(" ", "")
    if not key:
        raise ValueError("keybinding cannot be empty")

    modifiers, key_token = _parse_keybinding_parts(key, raw)
    key_name = _normalize_key_name(key_token, raw)
    parts = [modifier for modifier in _MODIFIER_ORDER if modifier in modifiers]
    parts.append(key_name)
    return "+".join(parts)


def _parse_keybinding_parts(key: str, raw: str) -> tuple[set[str], str]:
    modifiers: set[str] = set()
    remaining = key
    while remaining:
        prefix = _next_modifier_prefix(remaining, modifiers, raw)
        if prefix is None:
            break
        modifiers.add(prefix.modifier)
        remaining = prefix.remaining

    if not remaining:
        raise ValueError(f"missing key in keybinding {raw!r}")
    if "+" in remaining:
        raise ValueError(f"invalid keybinding {raw!r}")
    return modifiers, remaining


def _next_modifier_prefix(
    remaining: str,
    modifiers: set[str],
    raw: str,
) -> _ModifierPrefix | None:
    for alias, canonical in _MODIFIER_ALIASES.items():
        for separator in ("+", "-"):
            prefix = f"{alias}{separator}"
            if not remaining.startswith(prefix):
                continue
            if canonical in modifiers:
                raise ValueError(f"duplicate modifier in keybinding {raw!r}")
            return _ModifierPrefix(canonical, remaining.removeprefix(prefix))
    return None


def display_key(key: str) -> str:
    parts = key.split("+")
    parts[-1] = _DISPLAY_KEY_ALIASES.get(parts[-1], parts[-1])
    return "+".join(parts)


def keymap_config_summary(keymap: RuntimeKeymap | None = None) -> str:
    runtime = keymap or load_runtime_keymap()
    changed = sum(1 for action in TUI_KEYMAP_ACTIONS if action.id in runtime.configured_actions)
    return f"{changed} custom" if changed else "defaults"


def action_label_for_key(key: str, keymap: RuntimeKeymap | None = None) -> str:
    runtime = keymap or load_runtime_keymap()
    action_id = runtime.action_for_key(key)
    if action_id is None:
        return ""
    action = _ACTIONS_BY_ID[action_id]
    return action.label


def save_keymap_binding(action_id: str, raw_key: str) -> KeymapSaveResult:
    action = _ACTIONS_BY_ID.get(action_id)
    if action is None:
        return KeymapSaveResult(False, f"Unknown keymap action: {action_id}")
    try:
        key = normalize_key_spec(raw_key)
    except ValueError as exc:
        return KeymapSaveResult(False, str(exc))

    validation_error = _binding_validation_error(action, key)
    if validation_error:
        return KeymapSaveResult(False, validation_error)

    runtime = load_runtime_keymap()
    conflict = _conflicting_action(action.id, key, runtime)
    if conflict is not None:
        return KeymapSaveResult(
            False,
            f"{display_key(key)} is already bound to {conflict.label}.",
        )

    raw = _raw_keymap_object()
    context = _context_object(raw, action.context)
    context[action.id] = key
    _save_raw_keymap(raw)
    return KeymapSaveResult(True, f"{action.label} bound to {display_key(key)}.", key)


def reset_keymap_action(action_id: str) -> KeymapSaveResult:
    action = _ACTIONS_BY_ID.get(action_id)
    if action is None:
        return KeymapSaveResult(False, f"Unknown keymap action: {action_id}")
    raw = _raw_keymap_object()
    context_value = raw.get(action.context)
    if is_string_mapping(context_value):
        context_value.pop(action.id, None)
        if not context_value:
            raw.pop(action.context, None)
    _save_raw_keymap(raw)
    return KeymapSaveResult(True, f"{action.label} reset to default.")


def reset_keymap() -> KeymapSaveResult:
    settings = load_raw_settings()
    settings.pop(KEYMAP_SETTING_KEY, None)
    save_raw_settings(settings)
    return KeymapSaveResult(True, "Keymap reset to defaults.")


def armory_binding_keys() -> str:
    return ",".join(default_keys_for_action_id("open_armory_home"))


def armory_shortcut_key() -> str:
    keys = default_keys_for_action_id("open_armory_home")
    return display_key(keys[0]) if keys else ""


def _normalize_key_name(key: str, original: str) -> str:
    alias = _KEY_ALIASES.get(key, key)
    if len(alias) == 1:
        character = alias[0]
        if character.isascii() and character.isprintable() and character != "+":
            return alias
    if alias in _NAMED_KEYS:
        return alias
    if _is_function_key_name(alias):
        return alias
    raise ValueError(f"unknown key {key!r} in keybinding {original!r}")


def _binding_validation_error(action: TuiKeymapAction, key: str) -> str:
    if reason := _RESERVED_KEY_REASONS.get(key):
        return reason
    if _binding_uses_function_key(key):
        return "function keys can trigger hardware or desktop actions; use ctrl+alt+<key> instead."
    if key == "enter":
        return "enter is reserved for submitting text and selecting rows."
    if key == "escape" and action.id != "cancel_turn":
        return "escape is reserved for closing surfaces and stopping active turns."
    if len(key) == 1:
        return "plain character shortcuts would steal typing; use ctrl+<key> instead."
    if key.startswith("shift+") and len(key.removeprefix("shift+")) == 1:
        return "shift+letter shortcuts would steal uppercase typing; use ctrl+<key> instead."
    return ""


def _binding_uses_function_key(key: str) -> bool:
    return _is_function_key_name(key.rsplit("+", maxsplit=1)[-1])


def _is_function_key_name(key: str) -> bool:
    if not key.startswith("f"):
        return False
    number = key[1:]
    return number.isdecimal() and 1 <= int(number) <= MAX_FUNCTION_KEY


def _load_configured_bindings() -> tuple[dict[str, dict[str, tuple[str, ...]]], list[str]]:
    raw = load_raw_settings().get(KEYMAP_SETTING_KEY)
    if not is_string_mapping(raw):
        return {}, []

    configured: dict[str, dict[str, tuple[str, ...]]] = {}
    errors: list[str] = []
    for context, raw_context in raw.items():
        context_bindings, context_errors = _configured_context_bindings(context, raw_context)
        errors.extend(context_errors)
        if context_bindings:
            configured[context] = context_bindings
    return configured, errors


def _configured_context_bindings(
    context: str,
    raw_context: object,
) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    if context not in _ACTION_CONTEXTS:
        return {}, [f"Unknown keymap context: {context}"]
    if not is_string_mapping(raw_context):
        return {}, [f"Keymap context {context} must be an object."]

    context_bindings: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    for action_id, raw_keys in raw_context.items():
        action = _ACTIONS_BY_ID.get(action_id)
        if action is None or action.context != context:
            errors.append(f"Unknown keymap action: {context}.{action_id}")
            continue
        keys, key_errors = _configured_keys(action, raw_keys)
        errors.extend(f"{context}.{action_id}: {error}" for error in key_errors)
        if keys or not key_errors:
            context_bindings[action_id] = keys
    return context_bindings, errors


def _configured_keys(
    action: TuiKeymapAction,
    value: object,
) -> tuple[tuple[str, ...], list[str]]:
    raw_keys: list[object]
    if isinstance(value, str):
        raw_keys = [value]
    elif isinstance(value, list):
        raw_keys = list(value)
    else:
        return (), ["binding must be a string or list of strings"]

    keys: list[str] = []
    errors: list[str] = []
    for raw_key in raw_keys:
        if not isinstance(raw_key, str):
            errors.append("binding list values must be strings")
            continue
        try:
            key = normalize_key_spec(raw_key)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if validation_error := _binding_validation_error(action, key):
            errors.append(validation_error)
            continue
        keys.append(key)
    return tuple(dict.fromkeys(keys)), errors


def _duplicate_binding_errors(bindings: Mapping[str, Sequence[str]]) -> list[str]:
    owners: dict[str, str] = {}
    errors: list[str] = []
    for action in TUI_KEYMAP_ACTIONS:
        for key in bindings.get(action.id, ()):
            previous = owners.get(key)
            if previous is None:
                owners[key] = action.id
                continue
            previous_action = _ACTIONS_BY_ID[previous]
            errors.append(
                f"{display_key(key)} is bound to both {previous_action.label} and {action.label}."
            )
    return errors


def _conflicting_action(
    action_id: str,
    key: str,
    runtime: RuntimeKeymap,
) -> TuiKeymapAction | None:
    for action in TUI_KEYMAP_ACTIONS:
        if action.id == action_id:
            continue
        if key in runtime.keys_for_action(action.id):
            return action
    return None


def _raw_keymap_object() -> dict[str, object]:
    raw = load_raw_settings().get(KEYMAP_SETTING_KEY)
    return dict(raw) if is_string_mapping(raw) else {}


def _context_object(raw: dict[str, object], context: str) -> dict[str, object]:
    value = raw.get(context)
    if is_string_mapping(value):
        return value
    context_value: dict[str, object] = {}
    raw[context] = context_value
    return context_value


def _save_raw_keymap(raw_keymap: dict[str, object]) -> None:
    settings = load_raw_settings()
    if raw_keymap:
        settings[KEYMAP_SETTING_KEY] = _json_safe_object(raw_keymap)
    else:
        settings.pop(KEYMAP_SETTING_KEY, None)
    save_raw_settings(settings)


def _json_safe_object(value: dict[str, object]) -> dict[str, JSONValue]:
    result: dict[str, JSONValue] = {}
    for key, raw_value in value.items():
        if isinstance(raw_value, str | int | float | bool) or raw_value is None:
            result[key] = raw_value
        elif isinstance(raw_value, list):
            result[key] = [str(item) for item in raw_value]
        elif is_string_mapping(raw_value):
            result[key] = _json_safe_object(raw_value)
    return result
