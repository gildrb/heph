"""Shared transparent rendering helpers for Textual screens.

Centralises the strip-manipulation logic needed by all modal screens
(ArmoryBrowserScreen, SearchScreen, …) and the main TUI so they
respect the active theme's transparency setting consistently.
"""

from __future__ import annotations

try:
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from textual.geometry import Region
    from textual.strip import Strip
    from textual.widgets import RichLog
except ImportError:
    Segment = None  # ty:ignore[invalid-assignment]
    _RichStyle = None  # ty:ignore[invalid-assignment]
    Region = None  # ty:ignore[invalid-assignment]
    Strip = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]


def style_without_black_background(style: _RichStyle | None) -> _RichStyle:
    """Return *style* with synthetic ``rgb(0,0,0)`` backgrounds stripped."""
    if _RichStyle is None:
        raise RuntimeError("Rich is not available")
    if style is None:
        return _RichStyle()
    bgcolor = style.bgcolor
    triplet = bgcolor.triplet if bgcolor is not None else None
    is_standard_black = bgcolor is not None and bgcolor.name == "black" and bgcolor.number == 0
    is_truecolor_black = triplet is not None and (triplet.red, triplet.green, triplet.blue) == (
        0,
        0,
        0,
    )
    if not is_standard_black and not is_truecolor_black:
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
    """Return a subclass that strips synthetic ``rgb(0,0,0)`` backgrounds.

    The Textual ``Screen`` compositor fills any uncovered cells -- including
    the gaps between sibling widgets -- with ``rgb(0,0,0)`` before children's
    ``render_line`` overrides have a chance to remove it. Returning blank
    strips here would discard that composited content entirely; instead we
    delegate to the base class and run the resulting strip through
    :func:`transparent_strip` so the seams between children come out
    transparent. ``render_lines`` is also overridden because
    ``StylesCache.render_line`` pads content using ``inner.rich_style``,
    which collapses ``Color(0,0,0,a=0)`` (transparent CSS background) into
    the opaque rich color ``#000000`` -- the per-line override only touches
    content cells, so the cache-padded cells need a second pass.
    """
    if Strip is None or _RichStyle is None or Region is None:
        raise RuntimeError("Rich / Textual is not available")

    class BlankBackgroundWidget(base_cls):  # ty:ignore[unsupported-base]
        def render_line(self, y: int) -> Strip:
            return transparent_strip(super().render_line(y), self.size.width)

        def render_lines(self, crop: Region) -> list[Strip]:
            strips = super().render_lines(crop)
            return [transparent_strip(strip, crop.width) for strip in strips]

    return BlankBackgroundWidget


def make_transparent_cls(base_cls: type) -> type:
    """Return a subclass that strips synthetic black backgrounds.

    Both ``render_line`` (the per-line content callback used by Textual's
    ``StylesCache``) and ``render_lines`` (the plural entry point the
    compositor and parent widgets actually consume) are overridden. The
    ``render_lines`` pass is required because the styles cache pads content
    to the widget's content width using ``inner.rich_style`` -- a style
    derived from the widget's resolved background colours. Textual collapses
    ``Color(0,0,0,a=0)`` (produced by ``background: transparent`` in CSS)
    into the rich color ``#000000`` when building that style, so without
    the second pass the padding cells flood the widget with opaque black.
    """
    if Strip is None or _RichStyle is None or Region is None:
        raise RuntimeError("Rich / Textual is not available")

    class TransparentWidget(base_cls):  # ty:ignore[unsupported-base]
        def render_line(self, y: int) -> Strip:
            if y < 0 or y >= self.size.height:
                return Strip.blank(self.size.width, self.rich_style)
            strip = super().render_line(y).extend_cell_length(self.size.width, self.rich_style)
            return transparent_strip(strip, self.size.width)

        def render_lines(self, crop: Region) -> list[Strip]:
            strips: list[Strip] = []
            for y in range(crop.y, crop.y + crop.height):
                strip = self.render_line(y).crop_extend(
                    crop.x, crop.x + crop.width, self.rich_style
                )
                strips.append(transparent_strip(strip, crop.width))
            return strips

    return TransparentWidget


def nonfocus_rich_log_class() -> type[RichLog]:
    """Return a non-focusable ``RichLog`` subclass."""
    if RichLog is None:
        raise RuntimeError("Textual is not available")

    class NonFocusRichLog(RichLog):
        can_focus = False

    return NonFocusRichLog
