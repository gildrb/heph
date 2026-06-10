"""TUI keybind action metadata.

This module is the UI-facing inventory of shortcut actions. It keeps stable
action labels separate from key values so renderers can show consistent labels
while keybinds remain configurable later.
"""

from __future__ import annotations

from dataclasses import dataclass

from interfaces.tui.keymap import armory_binding_keys, armory_shortcut_key


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


_FOOTER_ACTIONS = ("open_armory_home", "command_palette", "cycle_reasoning_level")


def tui_keybinds() -> tuple[TuiKeybind, ...]:
    return (
        TuiKeybind("tab", "complete", "Complete", "Complete the current input."),
        TuiKeybind(
            "shift+tab",
            "cycle_reasoning_level",
            "Reasoning",
            "Cycle the reasoning level.",
            show=False,
            priority=True,
        ),
        TuiKeybind(
            "ctrl+p",
            "command_palette",
            "Commands",
            "Open the command palette.",
            show=False,
            priority=True,
        ),
        TuiKeybind(
            armory_binding_keys(),
            "open_armory_home",
            "Armory",
            "Open the armory home.",
            show=False,
            priority=True,
            display_key=armory_shortcut_key(),
        ),
        TuiKeybind(
            "ctrl+s",
            "open_search",
            "Search",
            "Search across armories.",
            show=False,
            priority=True,
        ),
        TuiKeybind(
            "f8",
            "evidence",
            "Evidence",
            "Show evidence details.",
            show=False,
            priority=True,
        ),
        TuiKeybind(
            "shift+enter,ctrl+enter,alt+enter,ctrl+j",
            "insert_composer_newline",
            "Newline",
            "Insert a composer newline.",
            show=False,
            priority=True,
        ),
        TuiKeybind("ctrl+c", "quit", "Quit", "Quit Heph.", priority=True),
        TuiKeybind("ctrl+l", "clear_transcript", "Screen", "Clear the screen.", priority=True),
        TuiKeybind("ctrl+d", "quit", "Quit", "Quit Heph.", priority=True),
    )


def footer_keybind_hints() -> tuple[FooterKeybindHint, ...]:
    specs_by_action = {spec.action: spec for spec in tui_keybinds()}
    hints: list[FooterKeybindHint] = []
    for action in _FOOTER_ACTIONS:
        spec = specs_by_action[action]
        key = spec.display_key or spec.keys.split(",", maxsplit=1)[0]
        hints.append(FooterKeybindHint(label=spec.label.upper(), key=key.lower()))
    return tuple(hints)
