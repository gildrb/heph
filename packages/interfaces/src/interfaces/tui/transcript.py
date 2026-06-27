from __future__ import annotations

import sys
import textwrap
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Protocol, TypeVar

from interfaces.terminal import current_palette
from interfaces.tui.display_text import status_render_width
from interfaces.tui.flow_state import InlineFlow
from interfaces.tui.keymap import RuntimeKeymap
from interfaces.tui.render_state import DirtyRegion
from interfaces.tui.rich_transcript import (
    enrich_reply,
    evidence_citation_spans,
    is_evidence_sources_line,
    normalize_math_output,
)
from interfaces.tui.session_state import TuiRuntimeState, TuiTranscriptEntry

try:
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.segment import Segment
    from rich.style import Style as _RichStyle
    from rich.text import Text as _RichText
    from textual.css.query import NoMatches
    from textual.widgets import OptionList, RichLog, Static
except ImportError:
    Markdown = None  # ty:ignore[invalid-assignment]
    Padding = None  # ty:ignore[invalid-assignment]
    Segment = None  # ty:ignore[invalid-assignment]
    _RichStyle = None  # ty:ignore[invalid-assignment]
    _RichText = None  # ty:ignore[invalid-assignment]
    NoMatches = Exception  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from harness.chat.session import ChatSession
    from rich.console import Console, ConsoleOptions, RenderableType, RenderResult

_TRANSCRIPT_ENTRY_GAP = ""
_TRANSCRIPT_HORIZONTAL_PADDING = 0
_TRANSCRIPT_TAIL_TOLERANCE = 1
_REPLY_TRANSCRIPT_HORIZONTAL_PADDING = 2
_USER_TRANSCRIPT_HORIZONTAL_PADDING = 2
_USER_TRANSCRIPT_VERTICAL_PADDING = 1
_TRANSCRIPT_REFLOW_DELAY_SECONDS = 0.01

_WidgetT = TypeVar("_WidgetT")


class _Clearable(Protocol):
    def clear(self) -> None: ...


class _TranscriptHost(Protocol):
    busy: bool
    _thinking_label: str
    console: Console
    session: ChatSession
    state: TuiRuntimeState
    _armory_creating: bool
    _armory_filter: str
    _armory_inline_active: bool
    _materials_inline_active: bool
    _focused_msg_index: int | None
    _inline_flow: InlineFlow
    _keymap: RuntimeKeymap
    _transcript_reflow_pending: bool
    _transcript_reflow_requested_while_pending: bool
    _transcript_render_width: int | None
    _side_panel_progress: str

    @property
    def abort_event(self) -> _Clearable: ...

    @property
    def completion_candidates(self) -> Sequence[object]: ...

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def set_timer(self, delay: float, callback: Callable[[], object]) -> object: ...

    def _refresh_completion_position(self) -> None: ...

    def _schedule_transcript_reflow(self) -> None: ...

    def _run_scheduled_transcript_reflow(self) -> None: ...

    def _reflow_transcript_entries(self) -> None: ...

    def _reflowable_transcript_log(self) -> RichLog | None: ...

    def _write_transcript_gap(self) -> None: ...

    def _write_transcript_entry(self, entry: TuiTranscriptEntry) -> None: ...

    def _write_transcript_renderable(self, log: RichLog, renderable: object) -> None: ...

    def _scroll_transcript_to_end(self, log: RichLog) -> None: ...

    def _transcript_should_follow_tail(self, log: RichLog) -> bool: ...

    def _write_transcript_lines(
        self,
        log: RichLog,
        text: str,
        *,
        style: _RichStyle | None = None,
        ansi: bool = False,
    ) -> None: ...

    def _write_padded_panel_lines(
        self,
        log: RichLog,
        text: str,
        *,
        style: _RichStyle,
    ) -> None: ...

    def _write_panel_vertical_padding(self, log: RichLog, blank: object) -> None: ...

    def _write_wrapped_panel_line(
        self,
        log: RichLog,
        line: str,
        content_width: int,
        style: _RichStyle,
    ) -> None: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _replace_last_notice(self, text: str) -> None: ...

    def _append_activity(self, text: str) -> None: ...

    def _start_thinking_animation(self) -> None: ...

    def _stop_thinking_animation(self) -> None: ...

    def _refresh_status(self) -> None: ...

    def _status_title(self) -> str: ...

    def _refresh_footer_hints(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _update_focused_info_panel(self) -> bool: ...

    def _update_armory_preview(self) -> None: ...

    def _update_materials_sidebar(self) -> None: ...

    def _materials_footer_text(self) -> str: ...

    def _update_static_region(
        self,
        selector: str,
        widget_type: type[Static],
        region: DirtyRegion,
        renderable: object,
    ) -> None: ...


def _combined_segment_style(
    base_style: _RichStyle | None,
    metadata_style: _RichStyle,
) -> _RichStyle:
    if base_style is None:
        return metadata_style
    return base_style + metadata_style


class _EvidenceMarkdown:
    """Markdown renderable with dimmed evidence metadata."""

    def __init__(self, markup: str, metadata_style: _RichStyle) -> None:
        self._markdown = _TranscriptMarkdown(markup)
        self._metadata_style = metadata_style

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        line_start = True
        in_sources_footer = False
        for segment in console.render(self._markdown, options):
            if self._starts_sources_footer(segment, line_start, in_sources_footer):
                in_sources_footer = True
            yield from self._styled_segments(segment, in_sources_footer)
            line_start = _next_line_starts(segment.text)

    @staticmethod
    def _starts_sources_footer(
        segment: Segment,
        line_start: bool,
        in_sources_footer: bool,
    ) -> bool:
        return line_start and not in_sources_footer and is_evidence_sources_line(segment.text)

    def _styled_segments(self, segment: Segment, in_sources_footer: bool) -> RenderResult:
        if in_sources_footer:
            yield self._metadata_segment(segment)
            return
        yield from self._style_citation_segments(segment)

    def _metadata_segment(self, segment: Segment) -> Segment:
        return Segment(
            segment.text,
            _combined_segment_style(segment.style, self._metadata_style),
            segment.control,
        )

    def _style_citation_segments(self, segment: Segment) -> RenderResult:
        text = segment.text
        last_end = 0
        for start, end in evidence_citation_spans(text):
            if start > last_end:
                yield Segment(text[last_end:start], segment.style, segment.control)
            yield Segment(
                text[start:end],
                _combined_segment_style(segment.style, self._metadata_style),
                segment.control,
            )
            last_end = end
        if last_end < len(text):
            yield Segment(text[last_end:], segment.style, segment.control)


class _TranscriptMarkdown:
    """Markdown renderable with transcript-safe list marker styling."""

    def __init__(self, markup: str) -> None:
        self._markdown = Markdown(markup)

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        for segment in console.render(self._markdown, options):
            if segment.control:
                yield segment
                continue
            yield _plain_markdown_list_marker_segment(segment)


def _plain_markdown_list_marker_segment(segment: Segment) -> Segment:
    text = segment.text
    marker = text.strip()
    if not marker.isdecimal():
        return segment
    if not text.startswith(" ") or not text.endswith(" "):
        return segment
    return Segment(text, None, segment.control)


def _next_line_starts(text: str) -> bool:
    return text.endswith("\n") if "\n" in text else False


def _evidence_metadata_style() -> _RichStyle:
    return _RichStyle.parse(f"dim {current_palette().text_muted}")


def _reply_renderable(entry: TuiTranscriptEntry) -> RenderableType:
    if entry.evidence and entry.evidence.items:
        renderable = _EvidenceMarkdown(entry.content, _evidence_metadata_style())
    else:
        renderable = _TranscriptMarkdown(entry.content)
    if Padding is None:
        return renderable
    return Padding(renderable, (0, _REPLY_TRANSCRIPT_HORIZONTAL_PADDING))


def _transcript_line_renderable(
    line: str,
    *,
    style: _RichStyle | None = None,
    ansi: bool = False,
) -> object:
    if _RichText is None:
        return line
    if ansi:
        renderable = _RichText.from_ansi(line)
        if style is not None:
            renderable.stylize(style)
        return renderable
    if style is not None:
        return _RichText.styled(line, style)
    return line


def _continuation_indent(line: str) -> str:
    leading_width = len(line) - len(line.lstrip(" "))
    remaining = line[leading_width:]
    return " " * (leading_width + _list_marker_width(remaining))


def _list_marker_width(text: str) -> int:
    if text.startswith(("- ", "* ", "+ ", "• ")):
        return 2
    marker, separator, _rest = text.partition(" ")
    if separator and marker.endswith((".", ")")) and marker[:-1].isdecimal():
        return len(marker) + len(separator)
    return 0


def _wrap_transcript_plain_line(line: str, width: int) -> list[str]:
    if not line:
        return [""]
    wrapper = textwrap.TextWrapper(
        width=max(1, width),
        subsequent_indent=_continuation_indent(line),
        replace_whitespace=False,
        drop_whitespace=True,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapper.wrap(line) or [line]


def _clip_transcript_plain_line(line: str, width: int) -> str:
    if len(line) <= width:
        return line
    if width <= 3:
        return "." * width
    return f"{line[: width - 3].rstrip()}..."


def _transcript_line_renderables(
    line: str,
    *,
    width: int,
    style: _RichStyle | None = None,
    ansi: bool = False,
) -> list[object]:
    if ansi:
        return [_transcript_line_renderable(line, style=style, ansi=ansi)]
    return [
        _transcript_line_renderable(wrapped_line, style=style)
        for wrapped_line in _wrap_transcript_plain_line(line, width)
    ]


def _transcript_activity_renderable(
    line: str,
    *,
    width: int,
    style: _RichStyle,
) -> object:
    return _transcript_line_renderable(
        _clip_transcript_plain_line(line, width),
        style=style,
    )


def _panel_width(log: RichLog) -> int:
    return max(1, log.size.width - _TRANSCRIPT_HORIZONTAL_PADDING)


def _panel_content_width(log: RichLog) -> int:
    return max(1, _panel_width(log) - (_USER_TRANSCRIPT_HORIZONTAL_PADDING * 2))


def _panel_blank_line(log: RichLog, style: _RichStyle) -> _RichText:
    return _RichText.styled(" " * _panel_width(log), style)


def _wrap_panel_line(
    console: Console,
    line: str,
    width: int,
    style: _RichStyle,
) -> list[_RichText]:
    renderable = _RichText.styled(line, style)
    wrapped = list(renderable.wrap(console, width=width))
    return wrapped or [_RichText.styled("", style)]


def _pad_panel_content_line(line: _RichText, width: int, style: _RichStyle) -> None:
    if line.cell_len >= width:
        return
    style_start = len(line.plain)
    line.pad_right(width - line.cell_len)
    line.stylize(style, style_start, len(line.plain))


def _panel_line(wrapped_line: _RichText, width: int, style: _RichStyle) -> _RichText:
    _pad_panel_content_line(wrapped_line, width, style)
    panel_line = _RichText.styled(" " * _USER_TRANSCRIPT_HORIZONTAL_PADDING, style)
    panel_line.append_text(wrapped_line)
    panel_line.append(" " * _USER_TRANSCRIPT_HORIZONTAL_PADDING, style=style)
    return panel_line


def _focusable_transcript_entries(
    entries: Sequence[TuiTranscriptEntry],
) -> list[TuiTranscriptEntry]:
    return [entry for entry in entries if entry.kind in ("user", "markdown", "plain")]


type _EntryWriter = Callable[[_TranscriptHost, RichLog, TuiTranscriptEntry], None]


def _write_markdown_entry(
    host: _TranscriptHost,
    log: RichLog,
    entry: TuiTranscriptEntry,
) -> None:
    host._write_transcript_renderable(log, _reply_renderable(entry))


def _write_user_entry(host: _TranscriptHost, log: RichLog, entry: TuiTranscriptEntry) -> None:
    palette = current_palette()
    host._write_padded_panel_lines(
        log,
        entry.content,
        style=_RichStyle(color=palette.text_primary, bgcolor=palette.bg_raised, bold=True),
    )


def _write_startup_entry(host: _TranscriptHost, log: RichLog, entry: TuiTranscriptEntry) -> None:
    palette = current_palette()
    host._write_transcript_lines(
        log,
        entry.content,
        style=_RichStyle(color=palette.text_muted),
    )


def _write_ansi_entry(host: _TranscriptHost, log: RichLog, entry: TuiTranscriptEntry) -> None:
    host._write_transcript_lines(log, entry.content, ansi=_RichText is not None)


def _write_muted_ansi_entry(
    host: _TranscriptHost,
    log: RichLog,
    entry: TuiTranscriptEntry,
) -> None:
    if _RichText is None:
        host._write_transcript_lines(log, entry.content)
        return
    palette = current_palette()
    host._write_transcript_lines(
        log,
        entry.content,
        style=_RichStyle(color=palette.text_muted),
        ansi=True,
    )


def _write_activity_entry(host: _TranscriptHost, log: RichLog, entry: TuiTranscriptEntry) -> None:
    palette = current_palette()
    style = _RichStyle(color=palette.text_muted)
    for line in entry.content.splitlines() or [""]:
        renderable = _transcript_activity_renderable(
            line,
            width=max(1, log.size.width - _TRANSCRIPT_HORIZONTAL_PADDING),
            style=style,
        )
        host._write_transcript_renderable(log, renderable)


def _write_plain_entry(host: _TranscriptHost, log: RichLog, entry: TuiTranscriptEntry) -> None:
    host._write_transcript_lines(log, entry.content)


_ENTRY_WRITERS: dict[str, _EntryWriter] = {
    "markdown": _write_markdown_entry,
    "user": _write_user_entry,
    "startup": _write_startup_entry,
    "ansi": _write_ansi_entry,
    "notice": _write_muted_ansi_entry,
    "activity": _write_activity_entry,
}


class TuiTranscriptMixin:
    def _refresh_completion_position(self: _TranscriptHost) -> None:
        position = self.query_one("#completion-position", Static)
        suggestions = self.query_one("#suggestions", OptionList)
        option_count = len(self.completion_candidates) or len(self._inline_flow.options)
        highlighted = suggestions.highlighted
        if suggestions.has_class("visible") and option_count > 0 and highlighted is not None:
            palette = current_palette()
            position_text = f"  ({highlighted + 1}/{option_count})"
            position.update(_RichText(position_text, style=palette.text_muted))
            position.add_class("visible")
            return
        position.update("")
        position.remove_class("visible")

    def _schedule_transcript_reflow(self: _TranscriptHost) -> None:
        if self._transcript_reflow_pending:
            self._transcript_reflow_requested_while_pending = True
            return
        log = self._reflowable_transcript_log()
        if log is not None and self._transcript_render_width == log.size.width:
            return
        self._transcript_reflow_pending = True
        self.set_timer(_TRANSCRIPT_REFLOW_DELAY_SECONDS, self._run_scheduled_transcript_reflow)

    def _run_scheduled_transcript_reflow(self: _TranscriptHost) -> None:
        self._transcript_reflow_pending = False
        self._reflow_transcript_entries()
        if self._transcript_reflow_requested_while_pending:
            self._transcript_reflow_requested_while_pending = False
            self._transcript_render_width = None
            self._schedule_transcript_reflow()

    def _reflow_transcript_entries(self: _TranscriptHost) -> None:
        log = self._reflowable_transcript_log()
        if log is None:
            return
        self._transcript_render_width = log.size.width
        log.clear()
        for index, entry in enumerate(self.state.transcript):
            if index > 0:
                self._write_transcript_gap()
            self._write_transcript_entry(entry)

    def _reflowable_transcript_log(self: _TranscriptHost) -> RichLog | None:
        try:
            log = self.query_one("#transcript", RichLog)
        except NoMatches:
            return None
        if log.has_class("hidden-for-armory"):
            return None
        if log.size.width <= _TRANSCRIPT_HORIZONTAL_PADDING:
            return None
        return log

    def _write_transcript_renderable(
        self: _TranscriptHost, log: RichLog, renderable: object
    ) -> None:
        follow_tail = self._transcript_should_follow_tail(log)
        previous_scroll_y = log.scroll_y
        previous_auto_scroll = log.auto_scroll
        if not follow_tail:
            log.auto_scroll = False
        try:
            if log.size.width <= _TRANSCRIPT_HORIZONTAL_PADDING:
                log.write(renderable)
            else:
                width = max(1, log.size.width - _TRANSCRIPT_HORIZONTAL_PADDING)
                log.write(renderable, width=width)
        finally:
            if not follow_tail:
                log.auto_scroll = previous_auto_scroll
                log.scroll_y = previous_scroll_y
        if follow_tail:
            self._scroll_transcript_to_end(log)

    @staticmethod
    def _transcript_should_follow_tail(log: RichLog) -> bool:
        return log.scroll_y >= log.max_scroll_y - _TRANSCRIPT_TAIL_TOLERANCE

    @staticmethod
    def _scroll_transcript_to_end(log: RichLog) -> None:
        scroll_end = getattr(log, "scroll_end", None)
        if callable(scroll_end):
            scroll_end(animate=False)

    def _write_transcript_lines(
        self: _TranscriptHost,
        log: RichLog,
        text: str,
        *,
        style: _RichStyle | None = None,
        ansi: bool = False,
    ) -> None:
        lines = text.splitlines() or [""]
        for line in lines:
            width = max(1, log.size.width - _TRANSCRIPT_HORIZONTAL_PADDING)
            renderables = _transcript_line_renderables(
                line,
                width=width,
                style=style,
                ansi=ansi,
            )
            for renderable in renderables:
                self._write_transcript_renderable(log, renderable)

    def _write_padded_panel_lines(
        self: _TranscriptHost,
        log: RichLog,
        text: str,
        *,
        style: _RichStyle,
    ) -> None:
        if _RichText is None or log.size.width <= _TRANSCRIPT_HORIZONTAL_PADDING:
            self._write_transcript_lines(log, text, style=style)
            return
        content_width = _panel_content_width(log)
        blank = _panel_blank_line(log, style)
        self._write_panel_vertical_padding(log, blank)
        for line in text.splitlines() or [""]:
            self._write_wrapped_panel_line(log, line, content_width, style)
        self._write_panel_vertical_padding(log, blank)

    def _write_panel_vertical_padding(self: _TranscriptHost, log: RichLog, blank: object) -> None:
        for _ in range(_USER_TRANSCRIPT_VERTICAL_PADDING):
            copy = getattr(blank, "copy", None)
            self._write_transcript_renderable(log, copy() if callable(copy) else blank)

    def _write_wrapped_panel_line(
        self: _TranscriptHost,
        log: RichLog,
        line: str,
        content_width: int,
        style: _RichStyle,
    ) -> None:
        for wrapped_line in _wrap_panel_line(self.console, line, content_width, style):
            self._write_transcript_renderable(log, _panel_line(wrapped_line, content_width, style))

    def _write_transcript_entry(self: _TranscriptHost, entry: TuiTranscriptEntry) -> None:
        log = self.query_one("#transcript", RichLog)
        writer = _ENTRY_WRITERS.get(entry.kind, _write_plain_entry)
        writer(self, log, entry)

    def _write_transcript_gap(self: _TranscriptHost) -> None:
        log = self.query_one("#transcript", RichLog)
        self._write_transcript_renderable(log, _TRANSCRIPT_ENTRY_GAP)

    def _append_entry(self: _TranscriptHost, content: str, kind: str = "plain") -> None:
        if self.state.transcript:
            self._write_transcript_gap()
        entry_content = normalize_math_output(content) if kind == "markdown" else content
        entry = TuiTranscriptEntry(entry_content, kind)
        self.state.transcript.append(entry)
        self._transcript_render_width = self.query_one("#transcript", RichLog).size.width
        self._write_transcript_entry(entry)

    def _append_plain(self: _TranscriptHost, text: str) -> None:
        self._append_entry(text)

    def _append_user(self: _TranscriptHost, text: str, *, mark_working: bool = True) -> None:
        self._append_entry(text, kind="user")
        if mark_working:
            self._start_thinking_animation()

    def _append_assistant_reply(self: _TranscriptHost, text: str) -> None:
        evidence = self.session.last_turn_evidence
        enriched = enrich_reply(text, evidence)
        entry = TuiTranscriptEntry(
            enriched.markdown_text,
            "markdown",
            enriched.evidence,
        )
        if self.state.transcript:
            self._write_transcript_gap()
        self.state.transcript.append(entry)
        self._transcript_render_width = self.query_one("#transcript", RichLog).size.width
        self._write_transcript_entry(entry)

    def _append_notice(self: _TranscriptHost, text: str) -> None:
        self._append_entry(text, "notice")

    def _replace_last_notice(self: _TranscriptHost, text: str) -> None:
        if not self.state.transcript or self.state.transcript[-1].kind != "notice":
            self._append_entry(text, "notice")
            return
        self.state.transcript[-1] = TuiTranscriptEntry(text, "notice")
        self._reflow_transcript_entries()

    def _append_activity(self: _TranscriptHost, text: str) -> None:
        log = self.query_one("#transcript", RichLog)
        entry = TuiTranscriptEntry(text, "activity")
        if self.state.transcript and self.state.transcript[-1].kind == "activity":
            previous = self.state.transcript[-1]
            self.state.transcript[-1] = TuiTranscriptEntry(
                f"{previous.content}\n{text}",
                "activity",
            )
            self._transcript_render_width = log.size.width
            self._write_transcript_entry(entry)
            return
        self._append_entry(text, "activity")

    def _append_error(self: _TranscriptHost, text: str) -> None:
        p = current_palette()
        error_style = p.status_error_text
        self._append_entry(f"[bold {error_style}]error:[/bold {error_style}] {text}", "error")

    def _finish_turn(self: _TranscriptHost) -> None:
        self.busy = False
        self.abort_event.clear()
        self._thinking_label = "thinking"
        self._side_panel_progress = ""
        self._stop_thinking_animation()
        self._refresh_status()
        self._refresh_footer_hints()
        self._focused_msg_index = None
        self._update_info_panel()

    def _refresh_status(self: _TranscriptHost) -> None:
        tui_module = sys.modules["interfaces.tui"]
        status = self.query_one("#status", Static)
        status_width = status_render_width(status.size.width)
        self._update_static_region(
            "#status",
            Static,
            DirtyRegion.STATUS,
            tui_module._status_text(
                self.session,
                title=self._status_title(),
                width=status_width,
            ),
        )

    def _refresh_footer_hints(self: _TranscriptHost) -> None:
        self._refresh_completion_position()
        tui_module = sys.modules["interfaces.tui"]
        if self._armory_inline_active:
            self._update_static_region(
                "#footer-hints",
                Static,
                DirtyRegion.FOOTER,
                tui_module._armory_footer_hints_text(
                    creating=self._armory_creating,
                    filtering=bool(self._armory_filter),
                ),
            )
            return
        if self._materials_inline_active:
            self._update_static_region(
                "#footer-hints",
                Static,
                DirtyRegion.FOOTER,
                self._materials_footer_text(),
            )
            return
        self._update_static_region(
            "#footer-hints",
            Static,
            DirtyRegion.FOOTER,
            tui_module._footer_hints_text(self.session, busy=self.busy, keymap=self._keymap),
        )

    def _focus_message(self: _TranscriptHost, direction: int) -> None:
        """Navigate transcript focus for the info panel. direction: -1=up, +1=down."""
        entries = _focusable_transcript_entries(self.state.transcript)
        if not entries:
            return
        if self._focused_msg_index is None:
            self._focused_msg_index = len(entries) - 1 if direction < 0 else 0
        else:
            self._focused_msg_index = max(
                0, min(len(entries) - 1, self._focused_msg_index + direction)
            )
        entry = entries[self._focused_msg_index]
        tui_module = sys.modules["interfaces.tui"]
        self._update_static_region(
            "#info-panel",
            Static,
            DirtyRegion.SIDE_PANEL,
            tui_module._info_panel_message_text(entry, self.session),
        )

    def _update_info_panel(self: _TranscriptHost) -> None:
        """Refresh the info panel to reflect current state."""
        try:
            self.query_one("#info-panel", Static)
        except NoMatches:
            return
        if self._armory_inline_active:
            self._update_armory_preview()
            return
        if self._materials_inline_active:
            self._update_materials_sidebar()
            return
        if self._update_focused_info_panel():
            return
        tui_module = sys.modules["interfaces.tui"]
        self._update_static_region(
            "#info-panel",
            Static,
            DirtyRegion.SIDE_PANEL,
            tui_module._info_panel_default_text(
                self.session,
                busy=self.busy,
                progress=self._side_panel_progress,
            ),
        )

    def _update_focused_info_panel(self: _TranscriptHost) -> bool:
        if self._focused_msg_index is None:
            return False
        entries = _focusable_transcript_entries(self.state.transcript)
        if self._focused_msg_index >= len(entries):
            return False
        self._update_static_region(
            "#info-panel",
            Static,
            DirtyRegion.SIDE_PANEL,
            sys.modules["interfaces.tui"]._info_panel_message_text(
                entries[self._focused_msg_index],
                self.session,
            ),
        )
        return True
