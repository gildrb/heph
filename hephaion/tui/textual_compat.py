from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from textual.geometry import Size

try:
    from rich.text import Text as RichText
    from textual.widgets import Input, OptionList, RichLog, Static
except ImportError:
    RichText = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]

WidgetT = TypeVar("WidgetT")


class ClassableWidget(Protocol):
    size: Size

    def add_class(self, *_class_names: str) -> object: ...

    def remove_class(self, *_class_names: str) -> object: ...


_SIDEBAR_INDENT = "  "
_SIDEBAR_CONTENT_WIDTH_FALLBACK = 44


def sidebar_text(content: str, *, width: int = 0) -> str:
    lines: list[str] = []
    for line in content.splitlines():
        if not line:
            lines.append("")
            continue
        lines.extend(_sidebar_wrapped_line(line, width=width))
    return "\n".join(lines)


def sidebar_content_width(widget: ClassableWidget) -> int:
    if widget.size.width > len(_SIDEBAR_INDENT):
        return widget.size.width - len(_SIDEBAR_INDENT)
    return _SIDEBAR_CONTENT_WIDTH_FALLBACK


def _sidebar_wrapped_line(line: str, *, width: int) -> list[str]:
    if width <= len(_SIDEBAR_INDENT) + 1:
        return [f"{_SIDEBAR_INDENT}{line}"]
    wrapper = textwrap.TextWrapper(
        width=width,
        initial_indent=_SIDEBAR_INDENT,
        subsequent_indent=_SIDEBAR_INDENT,
        break_long_words=True,
        break_on_hyphens=False,
    )
    return wrapper.wrap(line) or [f"{_SIDEBAR_INDENT}{line}"]
