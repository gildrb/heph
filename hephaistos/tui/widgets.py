from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from hephaistos.terminal import ThemePalette
from hephaistos.tui.transparent import (
    make_blank_background_cls,
    make_transparent_cls,
    selectable_text_strip,
)

try:
    from textual import events
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.screen import Screen
    from textual.selection import Selection
    from textual.strip import Strip
    from textual.widgets import Input, OptionList, RichLog, Static
except ImportError:
    Binding = None  # ty:ignore[invalid-assignment]
    events = None  # ty:ignore[invalid-assignment]
    Horizontal = object  # ty:ignore[invalid-assignment]
    Vertical = object  # ty:ignore[invalid-assignment]
    Screen = object  # ty:ignore[invalid-assignment]
    Selection = None  # ty:ignore[invalid-assignment]
    Strip = None  # ty:ignore[invalid-assignment]
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
            vertical=selection_passthrough_transparent_cls(Vertical),
            horizontal=selection_passthrough_transparent_cls(Horizontal),
            static=selectable_transparent_static_class(Static),
            rich_log=transparent_rich_log_class(),
            input=selectable_transparent_input_class(input_class),
            option_list=selectable_transparent_option_list_class(OptionList),
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
    return selection_passthrough_transparent_cls(Vertical)


def transparent_horizontal_class() -> type:
    return selection_passthrough_transparent_cls(Horizontal)


def transparent_static_class() -> type:
    return selectable_transparent_static_class(Static)


def transparent_rich_log_class() -> type:
    base = make_transparent_cls(RichLog)

    class TransparentNonFocusRichLog(base):  # ty:ignore[unsupported-base]
        can_focus = False

        @property
        def text_selection(self) -> None:
            return None

        def render_line(self, y: int) -> Strip:
            scroll_x, scroll_y = self.scroll_offset
            return selectable_text_strip(
                super().render_line(y),
                line_y=scroll_y + y,
                x_offset=scroll_x,
                selection=self.screen.selections.get(self),
                selection_style=self.screen.get_component_rich_style("screen--selection"),
            )

        def get_selection(self, selection: Selection) -> tuple[str, str]:
            lines = ["".join(segment.text for segment in line).rstrip() for line in self.lines]
            return selection.extract("\n".join(lines)), "\n"

    return TransparentNonFocusRichLog


def transparent_input_class() -> type:
    return selectable_transparent_input_class(input_without_ctrl_a_class(Input))


def transparent_option_list_class() -> type:
    return selectable_transparent_option_list_class(OptionList)


def selection_passthrough_transparent_cls(base: type) -> type:
    transparent_base = make_transparent_cls(base)

    class SelectionPassthroughTransparentWidget(transparent_base):  # ty:ignore[unsupported-base]
        ALLOW_SELECT = True

        @property
        def text_selection(self) -> None:
            return None

        def get_selection(self, selection: Selection) -> None:
            return None

    return SelectionPassthroughTransparentWidget


def selectable_transparent_static_class(base: type) -> type:
    transparent_base = make_transparent_cls(base)

    class SelectableTransparentStatic(transparent_base):  # ty:ignore[unsupported-base]
        @property
        def text_selection(self) -> None:
            return None

        def render_line(self, y: int) -> Strip:
            return selectable_text_strip(
                super().render_line(y),
                line_y=y,
                selection=self.screen.selections.get(self),
                selection_style=self.screen.get_component_rich_style("screen--selection"),
            )

    return SelectableTransparentStatic


def selectable_transparent_input_class(base: type) -> type:
    transparent_base = make_transparent_cls(base)

    class SelectableTransparentInput(transparent_base):  # ty:ignore[unsupported-base]
        ALLOW_SELECT = True

        @property
        def text_selection(self) -> None:
            return None

        async def _on_mouse_down(self, event: events.MouseDown) -> None:
            self._pause_blink(visible=True)
            event.prevent_default()
            event.stop()

        async def _on_click(self, event: events.Click) -> None:
            offset = event.get_content_offset(self)
            if offset is not None:
                self.cursor_position = self._cell_offset_to_index(offset.x)
            event.stop()

        def render_line(self, y: int) -> Strip:
            scroll_x, _ = self.scroll_offset
            return selectable_text_strip(
                super().render_line(y),
                line_y=y,
                x_offset=scroll_x,
                selection=self.screen.selections.get(self),
                selection_style=self.screen.get_component_rich_style("screen--selection"),
            )

        def get_selection(self, selection: Selection) -> tuple[str, str]:
            visible_text = self.value or self.placeholder
            return selection.extract(visible_text), "\n"

    return SelectableTransparentInput


def selectable_transparent_option_list_class(base: type) -> type:
    transparent_base = make_transparent_cls(base)

    class SelectableTransparentOptionList(transparent_base):  # ty:ignore[unsupported-base]
        ALLOW_SELECT = True

        @property
        def text_selection(self) -> None:
            return None

        def render_line(self, y: int) -> Strip:
            _, scroll_y = self.scroll_offset
            return selectable_text_strip(
                super().render_line(y),
                line_y=scroll_y + y,
                selection=self.screen.selections.get(self),
                selection_style=self.screen.get_component_rich_style("screen--selection"),
            )

        def get_selection(self, selection: Selection) -> tuple[str, str]:
            self._update_lines()
            lines = [
                "".join(
                    segment.text
                    for segment in self._get_line(
                        self.get_visual_style("option-list--option"),
                        line_number,
                    )
                ).rstrip()
                for line_number in range(len(self._lines))
            ]
            return selection.extract("\n".join(lines)), "\n"

    return SelectableTransparentOptionList


_WidgetClasses = WidgetClasses
_input_without_ctrl_a_class = input_without_ctrl_a_class
_nonselectable_transparent_cls = selection_passthrough_transparent_cls
_selection_passthrough_transparent_cls = selection_passthrough_transparent_cls
_selectable_transparent_static_class = selectable_transparent_static_class
_selectable_transparent_input_class = selectable_transparent_input_class
_selectable_transparent_option_list_class = selectable_transparent_option_list_class
_transparent_screen_class = transparent_screen_class
_transparent_vertical_class = transparent_vertical_class
_transparent_horizontal_class = transparent_horizontal_class
_transparent_static_class = transparent_static_class
_transparent_rich_log_class = transparent_rich_log_class
_transparent_input_class = transparent_input_class
_transparent_option_list_class = transparent_option_list_class
