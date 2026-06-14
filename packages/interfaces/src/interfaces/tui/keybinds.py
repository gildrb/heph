"""TUI keybind action metadata.

This module is the UI-facing inventory of shortcut actions. It keeps stable
action labels separate from key values so renderers can show consistent labels
while keybinds remain configurable later.
"""

from __future__ import annotations

from dataclasses import dataclass

from interfaces.terminal import menu_label_value
from interfaces.tui.cell_text import cell_width as _cell_width
from interfaces.tui.cell_text import pad_cell_right as _pad_cell_right
from interfaces.tui.keymap import (
    TUI_KEYMAP_ACTIONS,
    RuntimeKeymap,
    default_runtime_keymap,
    display_key,
)


@dataclass(frozen=True)
class TuiKeybind:
    keys: str
    action: str
    label: str
    description: str
    show: bool = True
    priority: bool = False
    display_key: str = ""


@dataclass(frozen=True)
class FooterKeybindHint:
    label: str
    key: str


_FOOTER_ACTIONS = (
    "open_armory_home",
    "open_materials",
    "command_palette",
    "cycle_reasoning_level",
)


def tui_keybinds(keymap: RuntimeKeymap | None = None) -> tuple[TuiKeybind, ...]:
    runtime = keymap or default_runtime_keymap()
    specs: list[TuiKeybind] = []
    for action in TUI_KEYMAP_ACTIONS:
        keys = runtime.keys_for_action(action.id)
        specs.append(
            TuiKeybind(
                ",".join(keys),
                action.id,
                action.label,
                action.description,
                show=action.show,
                priority=action.priority,
                display_key=display_key(keys[0]) if keys else "",
            )
        )
    specs.extend(
        (
            TuiKeybind("ctrl+c", "quit", "Quit", "Quit Heph.", priority=True),
            TuiKeybind("ctrl+d", "quit", "Quit", "Quit Heph.", priority=True),
        )
    )
    return tuple(specs)


def keybind_keys_text(spec: TuiKeybind) -> str:
    return spec.keys.replace(",", "/")


def keymap_text(keymap: RuntimeKeymap | None = None) -> str:
    runtime = keymap or default_runtime_keymap()
    specs = tui_keybinds(runtime)
    key_width = max((_cell_width(keybind_keys_text(spec)) for spec in specs), default=0)
    label_width = max((_cell_width(_keybind_label(spec)) for spec in specs), default=0)
    lines = [menu_label_value("keymap", "shortcuts")]
    for spec in specs:
        keys = keybind_keys_text(spec)
        label = _pad_cell_right(_keybind_label(spec), label_width)
        key_text = _pad_cell_right(keys, key_width)
        state = menu_label_value("state", _keybind_state(spec, runtime))
        lines.append(f"  {label}  {key_text}  {state}")
    return "\n".join(lines)


def _keybind_label(spec: TuiKeybind) -> str:
    return spec.label.strip().upper()


def _keybind_state(spec: TuiKeybind, keymap: RuntimeKeymap) -> str:
    if spec.action == "quit":
        return "builtin"
    return "custom" if spec.action in keymap.configured_actions else "default"


def footer_keybind_hints(keymap: RuntimeKeymap | None = None) -> tuple[FooterKeybindHint, ...]:
    specs_by_action = {spec.action: spec for spec in tui_keybinds(keymap)}
    hints: list[FooterKeybindHint] = []
    for action in _FOOTER_ACTIONS:
        spec = specs_by_action[action]
        key = spec.display_key or spec.keys.split(",", maxsplit=1)[0]
        hints.append(FooterKeybindHint(label=spec.label.upper(), key=key.lower()))
    return tuple(hints)
