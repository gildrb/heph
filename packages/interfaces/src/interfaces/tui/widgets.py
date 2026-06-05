from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from interfaces.terminal import Theme
from interfaces.tui.transparent import (
    make_blank_background_cls,
    make_transparent_cls,
    selectable_text_strip,
)

try:
    from rich.cells import get_character_cell_size
    from rich.text import Text
    from textual import events
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.geometry import Offset, Size
    from textual.screen import Screen
    from textual.selection import Selection
    from textual.strip import Strip
    from textual.widgets import Input, OptionList, RichLog, Static
except ImportError:
    Binding = None  # ty:ignore[invalid-assignment]
    get_character_cell_size = None  # ty:ignore[invalid-assignment]
    events = None  # ty:ignore[invalid-assignment]
    Horizontal = object  # ty:ignore[invalid-assignment]
    Offset = None  # ty:ignore[invalid-assignment]
    Size = None  # ty:ignore[invalid-assignment]
    Vertical = object  # ty:ignore[invalid-assignment]
    Screen = object  # ty:ignore[invalid-assignment]
    Selection = None  # ty:ignore[invalid-assignment]
    Strip = None  # ty:ignore[invalid-assignment]
    Text = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]

_MULTILINE_INPUT_MAX_VISIBLE_LINES = 6
_CSI_U_KEY_TEXT = {
    "apostrophe": "'",
    "at": "@",
    "backslash": "\\",
    "comma": ",",
    "equals_sign": "=",
    "full_stop": ".",
    "grave_accent": "`",
    "left_square_bracket": "[",
    "minus": "-",
    "plus": "+",
    "right_square_bracket": "]",
    "semicolon": ";",
    "slash": "/",
    "space": " ",
    "underscore": "_",
}
_SHIFTED_CSI_U_KEY_TEXT = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
    "apostrophe": '"',
    "backslash": "|",
    "comma": "<",
    "equals_sign": "+",
    "full_stop": ">",
    "grave_accent": "~",
    "left_square_bracket": "{",
    "minus": "_",
    "right_square_bracket": "}",
    "semicolon": ":",
    "slash": "?",
    "space": " ",
}


def csi_u_key_text(key: str) -> str | None:
    if not key.startswith("shift+"):
        if len(key) == 1:
            return key
        return _CSI_U_KEY_TEXT.get(key)

    base_key = key.removeprefix("shift+")
    if len(base_key) == 1 and base_key.isalpha():
        return base_key.upper()
    return _SHIFTED_CSI_U_KEY_TEXT.get(base_key)


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
    def from_palette(cls, _palette: Theme) -> WidgetClasses:
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

    class HephInput(
        base,  # ty:ignore[unsupported-base]
        inherit_bindings=False,
    ):
        BINDINGS = bindings

        @property
        def content_width(self) -> int:
            if "\n" not in self.value:
                return super().content_width
            if self.placeholder and not self.value:
                return len(self.placeholder)
            line_widths = (Text(line, end="").cell_len for line in self.value.split("\n"))
            return max(line_widths, default=0) + 1

        @property
        def cursor_screen_offset(self) -> Offset:
            if "\n" not in self.value:
                return super().cursor_screen_offset
            x, y, _width, _height = self.content_region
            scroll_x, scroll_y = self.scroll_offset
            cursor_y, cursor_x = self._cursor_line_column()
            return Offset(x + cursor_x - scroll_x, y + cursor_y - scroll_y)

        def on_key(self, event: events.Key) -> None:
            if event.key == "ctrl+a":
                self.app.action_open_armory_home()
                event.prevent_default()
                event.stop()
                return

            text = csi_u_key_text(event.key)
            if text is None:
                return
            if self.selection.is_empty:
                self.insert_text_at_cursor(text)
            else:
                self.replace(text, *self.selection)
            event.prevent_default()
            event.stop()

        def _watch_value(self, value: str) -> None:
            super()._watch_value(value)
            line_count = len(value.split("\n"))
            self.virtual_size = Size(self.content_width, line_count)
            self.styles.height = min(line_count, _MULTILINE_INPUT_MAX_VISIBLE_LINES)
            self.refresh(layout=True)

        def render_line(self, y: int) -> Strip:
            if "\n" not in self.value:
                return super().render_line(y)

            scroll_x, scroll_y = self.scroll_offset
            line_y = scroll_y + y
            lines = self.value.split("\n")
            if line_y >= len(lines):
                return Strip.blank(self.size.width, self.rich_style)

            line_start = sum(len(line) + 1 for line in lines[:line_y])
            line = lines[line_y]
            result = Text(line, no_wrap=True, overflow="ignore", end="")
            if self.highlighter is not None:
                result = self.highlighter(result)

            if self.has_focus:
                self._style_selection(result, line_start, len(line))
                if self._cursor_visible:
                    self._style_cursor(result, line_start, len(line))

            max_content_width = self.scrollable_content_region.width
            segments = list(
                self.app.console.render(
                    result,
                    self.app.console_options.update_width(self.content_width),
                )
            )
            strip = Strip(segments)
            strip = strip.crop(scroll_x, scroll_x + max_content_width + 1)
            strip = strip.extend_cell_length(max_content_width + 1)
            return strip.apply_style(self.rich_style)

        def cell_offset_to_index(self, offset_x: int, offset_y: int) -> int:
            if "\n" not in self.value:
                return self._cell_offset_to_index(offset_x)

            scroll_x, scroll_y = self.scroll_offset
            lines = self.value.split("\n")
            line_y = min(max(0, offset_y + scroll_y), len(lines) - 1)
            line_start = sum(len(line) + 1 for line in lines[:line_y])
            return line_start + self._line_cell_offset_to_index(lines[line_y], offset_x + scroll_x)

        def _cursor_line_column(self) -> tuple[int, int]:
            before_cursor = self.value[: self.cursor_position]
            line_y = before_cursor.count("\n")
            line_start = before_cursor.rfind("\n") + 1
            cursor_x = Text(before_cursor[line_start:], end="").cell_len
            return line_y, cursor_x

        def _style_selection(self, result: Text, line_start: int, line_length: int) -> None:
            if self.selection.is_empty:
                return
            start, end = sorted(self.selection)
            line_end = line_start + line_length
            selection_start = max(start, line_start) - line_start
            selection_end = min(end, line_end) - line_start
            if selection_start < selection_end:
                result.stylize_before(
                    self.get_component_rich_style("input--selection"),
                    selection_start,
                    selection_end,
                )

        def _style_cursor(self, result: Text, line_start: int, line_length: int) -> None:
            cursor = self.cursor_position
            if not line_start <= cursor <= line_start + line_length:
                return
            cursor_column = cursor - line_start
            if cursor_column == line_length:
                result.pad_right(1)
            result.stylize(
                self.get_component_rich_style("input--cursor"),
                cursor_column,
                cursor_column + 1,
            )

        @staticmethod
        def _line_cell_offset_to_index(line: str, offset: int) -> int:
            cell_offset = 0
            for index, char in enumerate(line):
                cell_width = get_character_cell_size(char)
                if cell_offset <= offset < cell_offset + cell_width:
                    return index
                cell_offset += cell_width
            return min(max(0, offset), len(line))

    return HephInput


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

        def get_selection(self, _selection: Selection) -> None:
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
                self.cursor_position = self.cell_offset_to_index(offset.x, offset.y)
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
_transparent_screen_class = transparent_screen_class
_transparent_vertical_class = transparent_vertical_class
_transparent_horizontal_class = transparent_horizontal_class
_transparent_static_class = transparent_static_class
_transparent_rich_log_class = transparent_rich_log_class
_transparent_input_class = transparent_input_class
_transparent_option_list_class = transparent_option_list_class
