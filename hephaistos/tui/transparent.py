"""Shared transparent rendering helpers for Textual screens.

Centralises the strip-manipulation logic needed by all modal screens
(ArmoryBrowserScreen, SearchScreen, …) and the main TUI so they
respect the active theme's transparency setting consistently.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hephaistos.terminal import Theme, current_palette
from hephaistos.terminal.palette import BLACK_RGB, RICH_BLACK_COLOR_NAME

try:
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from textual.geometry import Region
    from textual.selection import Selection
    from textual.strip import Strip
    from textual.widgets import RichLog
except ImportError:
    Segment = None  # ty:ignore[invalid-assignment]
    _RichStyle = None  # ty:ignore[invalid-assignment]
    Region = None  # ty:ignore[invalid-assignment]
    Selection = None  # ty:ignore[invalid-assignment]
    Strip = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from rich.segment import ControlType

    SegmentControl = (
        Sequence[tuple[ControlType] | tuple[ControlType, int | str] | tuple[ControlType, int, int]]
        | None
    )
else:
    SegmentControl = object


def style_without_black_background(style: _RichStyle | None) -> _RichStyle:
    """Return *style* with synthetic ``rgb(0,0,0)`` backgrounds stripped."""
    if _RichStyle is None:
        raise RuntimeError("Rich is not available")
    if style is None:
        return _RichStyle()
    bgcolor = style.bgcolor
    triplet = bgcolor.triplet if bgcolor is not None else None
    is_standard_black = (
        bgcolor is not None
        and bgcolor.name == RICH_BLACK_COLOR_NAME
        and bgcolor.number == BLACK_RGB[0]
    )
    is_truecolor_black = (
        triplet is not None and (triplet.red, triplet.green, triplet.blue) == BLACK_RGB
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


def style_with_offset(style: _RichStyle | None, x: int, y: int) -> _RichStyle:
    """Return *style* with Textual text-selection offset metadata attached."""
    if _RichStyle is None:
        raise RuntimeError("Rich is not available")
    base = style or _RichStyle()
    return base + _RichStyle(meta={**base.meta, "offset": (x, y)})


def text_effects_style(style: _RichStyle | None) -> _RichStyle:
    """Return *style* without foreground or background colours."""
    if _RichStyle is None:
        raise RuntimeError("Rich is not available")
    if style is None:
        return _RichStyle()
    return _RichStyle(
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
    )


def _style_color_hex(style: _RichStyle | None) -> str | None:
    color = None if style is None else style.color
    triplet = None if color is None else color.triplet
    if triplet is None:
        return None
    return f"#{triplet.red:02x}{triplet.green:02x}{triplet.blue:02x}"


def normalize_selected_text_style(
    style: _RichStyle | None,
    palette: Theme | None = None,
) -> _RichStyle | None:
    """Return selected *style* with neutral UI colours promoted to readable text.

    Selection uses reverse video, so dim labels would otherwise become dim
    gray highlight blocks. Semantic colours stay untouched; neutral chrome
    colours share the same selected colour.
    """
    if _RichStyle is None:
        raise RuntimeError("Rich is not available")
    if style is None:
        return style
    palette = palette or current_palette()
    neutral_colours = {
        palette.text_primary.lower(),
        palette.text_muted.lower(),
        palette.text_secondary.lower(),
        palette.border_subtle.lower(),
    }
    colour = _style_color_hex(style)
    if colour not in neutral_colours:
        return style
    return style + _RichStyle(color=palette.text_primary)


@dataclass(frozen=True, slots=True)
class SelectableTextRange:
    start: int
    end: int

    @property
    def empty(self) -> bool:
        return self.start >= self.end


def _selectable_text_range(text: str) -> SelectableTextRange:
    return SelectableTextRange(
        start=len(text) - len(text.lstrip(" ")),
        end=len(text.rstrip(" ")),
    )


def _selected_text_range(
    *,
    selectable_range: SelectableTextRange,
    selected_span: tuple[int, int] | None,
    segment_x: int,
) -> SelectableTextRange:
    if selected_span is None:
        return SelectableTextRange(selectable_range.end, selectable_range.start)

    selected_start, selected_end = selected_span
    overlap_start = max(selectable_range.start, selected_start - segment_x)
    overlap_end = (
        selectable_range.end
        if selected_end == -1
        else min(selectable_range.end, selected_end - segment_x)
    )
    return SelectableTextRange(overlap_start, overlap_end)


def _append_selectable_part(
    segments: list[Segment],
    *,
    text: str,
    part_start: int,
    line_y: int,
    segment_x: int,
    base_style: _RichStyle | None,
    segment_control: SegmentControl,
    selected: bool,
    palette: Theme,
    selection_style: _RichStyle | None,
    selection_effect: _RichStyle,
) -> None:
    if not text:
        return
    if selected:
        base_style = normalize_selected_text_style(base_style, palette)
    part_style = style_with_offset(base_style, segment_x + part_start, line_y)
    if selected and selection_style is not None:
        part_style += selection_effect
    segments.append(Segment(text, part_style, segment_control))


def _append_unselected_selectable_text(
    segments: list[Segment],
    *,
    text: str,
    selectable_range: SelectableTextRange,
    line_y: int,
    segment_x: int,
    segment_style: _RichStyle | None,
    segment_control: SegmentControl,
    palette: Theme,
    selection_style: _RichStyle | None,
    selection_effect: _RichStyle,
) -> None:
    _append_selectable_part(
        segments,
        text=text[: selectable_range.start],
        part_start=0,
        line_y=line_y,
        segment_x=segment_x,
        base_style=segment_style,
        segment_control=segment_control,
        selected=False,
        palette=palette,
        selection_style=selection_style,
        selection_effect=selection_effect,
    )
    _append_selectable_part(
        segments,
        text=text[selectable_range.start : selectable_range.end],
        part_start=selectable_range.start,
        line_y=line_y,
        segment_x=segment_x,
        base_style=segment_style,
        segment_control=segment_control,
        selected=False,
        palette=palette,
        selection_style=selection_style,
        selection_effect=selection_effect,
    )


def _append_selected_selectable_text(
    segments: list[Segment],
    *,
    text: str,
    selectable_range: SelectableTextRange,
    selected_range: SelectableTextRange,
    line_y: int,
    segment_x: int,
    segment_style: _RichStyle | None,
    segment_control: SegmentControl,
    palette: Theme,
    selection_style: _RichStyle | None,
    selection_effect: _RichStyle,
) -> None:
    pieces = (
        (text[: selectable_range.start], 0, False),
        (text[selectable_range.start : selected_range.start], selectable_range.start, False),
        (text[selected_range.start : selected_range.end], selected_range.start, True),
        (text[selected_range.end : selectable_range.end], selected_range.end, False),
    )
    for part_text, part_start, selected in pieces:
        _append_selectable_part(
            segments,
            text=part_text,
            part_start=part_start,
            line_y=line_y,
            segment_x=segment_x,
            base_style=segment_style,
            segment_control=segment_control,
            selected=selected,
            palette=palette,
            selection_style=selection_style,
            selection_effect=selection_effect,
        )


def selectable_text_strip(
    strip: Strip,
    *,
    line_y: int,
    x_offset: int = 0,
    selection: Selection | None = None,
    selection_style: _RichStyle | None = None,
) -> Strip:
    """Attach text offsets and apply selection styling to visible text segments.

    Textual's built-in text selection only works when rendered segments carry
    ``offset`` metadata. Widgets such as ``Input``, ``OptionList``, and
    ``RichLog`` render directly to strips, so they need this small adapter to
    participate in cross-widget selection without making their padded rows look
    selectable.
    """
    if Segment is None or _RichStyle is None:
        raise RuntimeError("Rich is not available")
    palette = current_palette()
    selection_effect = text_effects_style(selection_style)
    selected_span = selection.get_span(line_y) if selection is not None else None

    char_x = x_offset
    segments: list[Segment] = []
    for segment in strip:
        text = segment.text
        if segment.control or not text:
            segments.append(segment)
            continue

        selectable_range = _selectable_text_range(text)
        if selectable_range.empty:
            segments.append(segment)
            char_x += len(text)
            continue

        selected_range = _selected_text_range(
            selectable_range=selectable_range,
            selected_span=selected_span,
            segment_x=char_x,
        )
        if selected_range.empty:
            _append_unselected_selectable_text(
                segments,
                text=text,
                selectable_range=selectable_range,
                line_y=line_y,
                segment_x=char_x,
                segment_style=segment.style,
                segment_control=segment.control,
                palette=palette,
                selection_style=selection_style,
                selection_effect=selection_effect,
            )
        else:
            _append_selected_selectable_text(
                segments,
                text=text,
                selectable_range=selectable_range,
                selected_range=selected_range,
                line_y=line_y,
                segment_x=char_x,
                segment_style=segment.style,
                segment_control=segment.control,
                palette=palette,
                selection_style=selection_style,
                selection_effect=selection_effect,
            )

        trailing_text = text[selectable_range.end :]
        if trailing_text:
            segments.append(Segment(trailing_text, segment.style, segment.control))
        char_x += len(text)

    return transparent_strip(Strip(segments, strip.cell_length), strip.cell_length)


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
