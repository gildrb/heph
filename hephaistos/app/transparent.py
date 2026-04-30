# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportUnknownVariableType=false, reportInvalidTypeArguments=false, reportInvalidTypeForm=false
# pyright: reportOptionalCall=false, reportUnknownParameterType=false
"""Shared transparent rendering helpers for Textual screens.

Centralises the strip-manipulation logic needed by all modal screens
(ArmoryBrowserScreen, SearchScreen, …) and the main TUI so they
respect the active theme's transparency setting consistently.
"""

from __future__ import annotations

try:
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from textual.strip import Strip
    from textual.widgets import RichLog
except ImportError:
    Segment = None  # type: ignore[assignment]
    _RichStyle = None  # type: ignore[assignment]
    Strip = None  # type: ignore[assignment]
    RichLog = None  # type: ignore[assignment]


def style_without_black_background(style: _RichStyle | None) -> _RichStyle:
    """Return *style* with synthetic ``rgb(0,0,0)`` backgrounds stripped."""
    if _RichStyle is None:
        raise RuntimeError("Rich is not available")
    if style is None:
        return _RichStyle()
    bgcolor = style.bgcolor
    triplet = bgcolor.triplet if bgcolor is not None else None
    if triplet is None or (triplet.red, triplet.green, triplet.blue) != (0, 0, 0):
        return style
    return _RichStyle(
        color=style.color,
        bold=style.bold,
        dim=style.dim,
        italic=style.italic,
        underline=style.underline,
        blink=style.blink,
        blink2=style.blink2,
        reverse=style.reverse,
        conceal=style.conceal,
        strike=style.strike,
        underline2=style.underline2,
        frame=style.frame,
        encircle=style.encircle,
        overline=style.overline,
        link=style.link,
        meta=style.meta or None,
    )


def transparent_strip(strip: Strip, cell_length: int) -> Strip:
    """Drop synthetic black backgrounds and pad short rows with transparent cells."""
    if Segment is None or _RichStyle is None:
        raise RuntimeError("Rich / Textual is not available")
    changed = False
    segments: list[Segment] = []
    for segment in strip:
        new_style = style_without_black_background(segment.style)
        changed = changed or new_style is not segment.style
        segments.append(segment._replace(style=new_style))
    if not changed:
        return strip.extend_cell_length(cell_length, _RichStyle())
    return Strip(segments, strip.cell_length).extend_cell_length(cell_length, _RichStyle())


def make_blank_background_cls(base_cls: type) -> type:
    """Return a subclass that renders empty cells with no background."""
    if Strip is None or _RichStyle is None:
        raise RuntimeError("Rich / Textual is not available")
    strip_class = Strip
    transparent_style = _RichStyle()

    class BlankBackgroundWidget(base_cls):  # type: ignore[misc]
        def render_line(self, _y: int) -> Strip:
            return strip_class.blank(self.size.width, transparent_style)

    return BlankBackgroundWidget


def make_transparent_cls(base_cls: type) -> type:
    """Return a subclass that strips synthetic black backgrounds."""
    if Strip is None or _RichStyle is None:
        raise RuntimeError("Rich / Textual is not available")

    class TransparentWidget(base_cls):  # type: ignore[misc]
        def render_line(self, y: int) -> Strip:
            return transparent_strip(super().render_line(y), self.size.width)

    return TransparentWidget


def nonfocus_rich_log_class() -> type[RichLog]:
    """Return a non-focusable ``RichLog`` subclass."""
    if RichLog is None:
        raise RuntimeError("Textual is not available")

    class NonFocusRichLog(RichLog):  # type: ignore[misc]
        can_focus = False

    return NonFocusRichLog
