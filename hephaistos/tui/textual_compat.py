from __future__ import annotations

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
