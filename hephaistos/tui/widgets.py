from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from hephaistos.terminal import ThemePalette
from hephaistos.tui.transparent import make_blank_background_cls, make_transparent_cls

try:
    from textual import events
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.screen import Screen
    from textual.widgets import Input, OptionList, RichLog, Static
except ImportError:
    Binding = None  # ty:ignore[invalid-assignment]
    events = None  # ty:ignore[invalid-assignment]
    Horizontal = object  # ty:ignore[invalid-assignment]
    Vertical = object  # ty:ignore[invalid-assignment]
    Screen = object  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]


@dataclass
class WidgetClasses:
    screen: type
    vertical: type
    horizontal: type
    static: type
    rich_log: type
    input: type
    option_list: type

    @classmethod
    def from_palette(cls, _palette: ThemePalette) -> WidgetClasses:
        input_class = input_without_ctrl_a_class(Input)
        return cls(
            screen=make_blank_background_cls(Screen),
            vertical=make_transparent_cls(Vertical),
            horizontal=make_transparent_cls(Horizontal),
            static=make_transparent_cls(Static),
            rich_log=transparent_rich_log_class(),
            input=make_transparent_cls(input_class),
            option_list=make_transparent_cls(OptionList),
        )


def input_without_ctrl_a_class(base: type) -> type:
    input_bindings = cast(
        "list[tuple[str, Binding]]",
        base._merged_bindings,  # ty:ignore[unresolved-attribute]
    )
    bindings = [binding for key, binding in input_bindings if key != "ctrl+a"]

    class HephaistosInput(
        base,  # ty:ignore[unsupported-base]
        inherit_bindings=False,
    ):
        BINDINGS = bindings

        def on_key(self, event: events.Key) -> None:
            if event.key != "ctrl+a":
                return
            self.app.action_open_armory_home()
            event.prevent_default()
            event.stop()

    return HephaistosInput


def transparent_screen_class() -> type:
    return make_blank_background_cls(Screen)


def transparent_vertical_class() -> type:
    return make_transparent_cls(Vertical)


def transparent_horizontal_class() -> type:
    return make_transparent_cls(Horizontal)


def transparent_static_class() -> type:
    return make_transparent_cls(Static)


def transparent_rich_log_class() -> type:
    base = make_transparent_cls(RichLog)

    class TransparentNonFocusRichLog(base):  # ty:ignore[unsupported-base]
        can_focus = False

    return TransparentNonFocusRichLog


def transparent_input_class() -> type:
    return make_transparent_cls(input_without_ctrl_a_class(Input))


def transparent_option_list_class() -> type:
    return make_transparent_cls(OptionList)


_WidgetClasses = WidgetClasses
_input_without_ctrl_a_class = input_without_ctrl_a_class
_transparent_screen_class = transparent_screen_class
_transparent_vertical_class = transparent_vertical_class
_transparent_horizontal_class = transparent_horizontal_class
_transparent_static_class = transparent_static_class
_transparent_rich_log_class = transparent_rich_log_class
_transparent_input_class = transparent_input_class
_transparent_option_list_class = transparent_option_list_class
