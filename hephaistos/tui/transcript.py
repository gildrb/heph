from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Protocol, TypeVar

from hephaistos.terminal import current_palette
from hephaistos.tui.flow_state import InlineFlow
from hephaistos.tui.rich_transcript import (
    enrich_reply,
    evidence_citation_spans,
    is_evidence_sources_line,
    normalize_math_output,
)
from hephaistos.tui.session_state import TuiRuntimeState, TuiTranscriptEntry

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
    from rich.console import Console, ConsoleOptions, RenderableType, RenderResult

    from hephaistos.chat.session import ChatSession

_TRANSCRIPT_ENTRY_GAP = ""
_TRANSCRIPT_HORIZONTAL_PADDING = 0
_TRANSCRIPT_TAIL_TOLERANCE = 1
_REPLY_TRANSCRIPT_HORIZONTAL_PADDING = 2
_USER_TRANSCRIPT_HORIZONTAL_PADDING = 2
_USER_TRANSCRIPT_VERTICAL_PADDING = 1

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
    _sidebar_selected_index: int | None
    _inline_flow: InlineFlow
    _transcript_reflow_pending: bool

    @property
    def abort_event(self) -> _Clearable: ...

    @property
    def completion_candidates(self) -> Sequence[object]: ...

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def set_timer(self, delay: float, callback: Callable[[], object]) -> object: ...

    def _refresh_completion_position(self) -> None: ...

    def _run_scheduled_transcript_reflow(self) -> None: ...

    def _reflow_transcript_entries(self) -> None: ...

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

    def _write_user_transcript_lines(self, log: RichLog, text: str) -> None: ...

    def _write_startup_card_lines(self, log: RichLog, text: str) -> None: ...

    def _write_padded_panel_lines(
        self,
        log: RichLog,
        text: str,
        *,
        style: _RichStyle,
    ) -> None: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _append_activity(self, text: str) -> None: ...

    def _start_thinking_animation(self) -> None: ...

    def _stop_thinking_animation(self) -> None: ...

    def _refresh_status(self, state: str = "ready") -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _update_armory_preview(self) -> None: ...

    def _update_materials_sidebar(self) -> None: ...

    def _tui_session_seconds(self) -> int: ...


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
        self._markdown = Markdown(markup)
        self._metadata_style = metadata_style

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        line_start = True
        in_sources_footer = False
        for segment in console.render(self._markdown, options):
            if segment.control:
                yield segment
                continue
            text = segment.text
            if line_start and not in_sources_footer and is_evidence_sources_line(text):
                in_sources_footer = True
            if in_sources_footer:
                yield Segment(
                    text,
                    _combined_segment_style(segment.style, self._metadata_style),
                    segment.control,
                )
            else:
                yield from self._style_citation_segments(segment)
            line_start = text.endswith("\n") if "\n" in text else False

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


def _evidence_metadata_style() -> _RichStyle:
    return _RichStyle.parse(f"dim {current_palette().text_muted}")


def _markdown_renderable(entry: TuiTranscriptEntry) -> RenderableType:
    if entry.evidence and entry.evidence.items:
        return _EvidenceMarkdown(entry.content, _evidence_metadata_style())
    return Markdown(entry.content)


def _reply_renderable(entry: TuiTranscriptEntry) -> RenderableType:
    renderable = _markdown_renderable(entry)
    if Padding is None:
        return renderable
    return Padding(renderable, (0, _REPLY_TRANSCRIPT_HORIZONTAL_PADDING))


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
            return
        self._transcript_reflow_pending = True
        self.set_timer(0.01, self._run_scheduled_transcript_reflow)

    def _run_scheduled_transcript_reflow(self: _TranscriptHost) -> None:
        self._transcript_reflow_pending = False
        self._reflow_transcript_entries()

    def _reflow_transcript_entries(self: _TranscriptHost) -> None:
        try:
            log = self.query_one("#transcript", RichLog)
        except NoMatches:
            return
        if log.has_class("hidden-for-armory"):
            return
        if log.size.width <= _TRANSCRIPT_HORIZONTAL_PADDING:
            return
        log.clear()
        for index, entry in enumerate(self.state.transcript):
            if index > 0:
                self._write_transcript_gap()
            self._write_transcript_entry(entry)

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
            if _RichText is None:
                renderable = line
            elif ansi:
                renderable = _RichText.from_ansi(line)
                if style is not None:
                    renderable.stylize(style)
            elif style is not None:
                renderable = _RichText.styled(line, style)
            else:
                renderable = line
            self._write_transcript_renderable(log, renderable)

    def _write_user_transcript_lines(self: _TranscriptHost, log: RichLog, text: str) -> None:
        p = current_palette()
        style = _RichStyle(color=p.text_primary, bgcolor=p.bg_raised, bold=True)
        self._write_padded_panel_lines(log, text, style=style)

    def _write_startup_card_lines(self: _TranscriptHost, log: RichLog, text: str) -> None:
        p = current_palette()
        self._write_transcript_lines(log, text, style=_RichStyle(color=p.text_muted))

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
        width = max(1, log.size.width - _TRANSCRIPT_HORIZONTAL_PADDING)
        content_width = max(1, width - (_USER_TRANSCRIPT_HORIZONTAL_PADDING * 2))
        console = self.console
        blank = _RichText.styled(" " * width, style)
        for _ in range(_USER_TRANSCRIPT_VERTICAL_PADDING):
            self._write_transcript_renderable(log, blank.copy())
        for line in text.splitlines() or [""]:
            renderable = _RichText.styled(line, style)
            wrapped = renderable.wrap(console, width=content_width) or [
                _RichText.styled("", style)
            ]
            for wrapped_line in wrapped:
                if wrapped_line.cell_len < content_width:
                    style_start = len(wrapped_line.plain)
                    wrapped_line.pad_right(content_width - wrapped_line.cell_len)
                    wrapped_line.stylize(style, style_start, len(wrapped_line.plain))
                panel_line = _RichText.styled(" " * _USER_TRANSCRIPT_HORIZONTAL_PADDING, style)
                panel_line.append_text(wrapped_line)
                panel_line.append(" " * _USER_TRANSCRIPT_HORIZONTAL_PADDING, style=style)
                self._write_transcript_renderable(log, panel_line)
        for _ in range(_USER_TRANSCRIPT_VERTICAL_PADDING):
            self._write_transcript_renderable(log, blank.copy())

    def _write_transcript_entry(self: _TranscriptHost, entry: TuiTranscriptEntry) -> None:
        log = self.query_one("#transcript", RichLog)
        if entry.kind == "markdown":
            self._write_transcript_renderable(log, _reply_renderable(entry))
        elif entry.kind == "user":
            self._write_user_transcript_lines(log, entry.content)
        elif entry.kind == "startup":
            self._write_startup_card_lines(log, entry.content)
        elif entry.kind == "ansi":
            if _RichText is None:
                self._write_transcript_lines(log, entry.content)
                return
            self._write_transcript_lines(log, entry.content, ansi=True)
        elif entry.kind in {"notice", "activity"}:
            if _RichText is None:
                self._write_transcript_lines(log, entry.content)
                return
            p = current_palette()
            self._write_transcript_lines(
                log,
                entry.content,
                style=_RichStyle(color=p.text_muted),
                ansi=True,
            )
        else:
            self._write_transcript_lines(log, entry.content)

    def _write_transcript_gap(self: _TranscriptHost) -> None:
        log = self.query_one("#transcript", RichLog)
        self._write_transcript_renderable(log, _TRANSCRIPT_ENTRY_GAP)

    def _append_entry(self: _TranscriptHost, content: str, kind: str = "plain") -> None:
        if self.state.transcript:
            self._write_transcript_gap()
        entry_content = normalize_math_output(content) if kind == "markdown" else content
        entry = TuiTranscriptEntry(entry_content, kind)
        self.state.transcript.append(entry)
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
        self._write_transcript_entry(entry)

    def _append_notice(self: _TranscriptHost, text: str) -> None:
        self._append_entry(text, "notice")

    def _append_activity(self: _TranscriptHost, text: str) -> None:
        self._append_entry(text, "activity")

    def _append_error(self: _TranscriptHost, text: str) -> None:
        p = current_palette()
        error_style = p.status_error_text
        self._append_entry(f"[bold {error_style}]error:[/bold {error_style}] {text}", "error")

    def _finish_turn(self: _TranscriptHost) -> None:
        self.busy = False
        self.abort_event.clear()
        self._thinking_label = "thinking"
        self._stop_thinking_animation()
        self._refresh_status("ready")
        self._refresh_footer_hints()
        self._focused_msg_index = None
        self._update_info_panel()

    def _refresh_status(self: _TranscriptHost, state: str = "ready") -> None:
        status = self.query_one("#status", Static)
        tui_module = sys.modules["hephaistos.tui"]
        status.update(tui_module._status_text(self.session, state))

    def _refresh_footer_hints(self: _TranscriptHost) -> None:
        self._refresh_completion_position()
        hints = self.query_one("#footer-hints", Static)
        if self.busy:
            tui_module = sys.modules["hephaistos.tui"]
            hints.update(tui_module._footer_hints_text(self.session, busy=True))
            return
        if self._armory_inline_active:
            hints.update(
                sys.modules["hephaistos.tui"]._armory_footer_hints_text(
                    creating=self._armory_creating,
                    filtering=bool(self._armory_filter),
                )
            )
            return
        tui_module = sys.modules["hephaistos.tui"]
        hints.update(tui_module._footer_hints_text(self.session, busy=self.busy))

    def _focus_message(self: _TranscriptHost, direction: int) -> None:
        """Navigate transcript focus for the info panel. direction: -1=up, +1=down."""
        entries = [e for e in self.state.transcript if e.kind in ("user", "markdown", "plain")]
        if not entries:
            return
        if self._focused_msg_index is None:
            self._focused_msg_index = len(entries) - 1 if direction < 0 else 0
        else:
            self._focused_msg_index = max(
                0, min(len(entries) - 1, self._focused_msg_index + direction)
            )
        entry = entries[self._focused_msg_index]
        panel = self.query_one("#info-panel", Static)
        tui_module = sys.modules["hephaistos.tui"]
        panel.update(tui_module._info_panel_message_text(entry, self.session))

    def _update_info_panel(self: _TranscriptHost) -> None:
        """Refresh the info panel to reflect current state."""
        try:
            panel = self.query_one("#info-panel", Static)
        except NoMatches:
            return
        if self._armory_inline_active:
            self._update_armory_preview()
            return
        if self._materials_inline_active:
            self._update_materials_sidebar()
            return
        if self._focused_msg_index is not None:
            entries = [e for e in self.state.transcript if e.kind in ("user", "markdown", "plain")]
            if self._focused_msg_index < len(entries):
                panel.update(
                    sys.modules["hephaistos.tui"]._info_panel_message_text(
                        entries[self._focused_msg_index],
                        self.session,
                    )
                )
                return
        tui_module = sys.modules["hephaistos.tui"]
        exam_session = self.session.study_state.exam_session
        if exam_session is not None:
            panel.update(
                tui_module._info_panel_exam_session_text(
                    exam_session,
                    self.session,
                    selected_index=self._sidebar_selected_index,
                )
            )
            return
        milestone_tracker = self.session.study_state.milestone_tracker
        if milestone_tracker is not None and milestone_tracker.milestones:
            panel.update(
                tui_module._info_panel_milestones_text(
                    milestone_tracker.milestones,
                    self.session,
                    selected_index=self._sidebar_selected_index,
                )
            )
            return
        panel.update(
            tui_module._info_panel_default_text(
                self.session,
                session_seconds=self._tui_session_seconds(),
            )
        )
