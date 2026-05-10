# ty: ignore
from __future__ import annotations

import sys

from hephaistos.terminal import current_palette
from hephaistos.tui.rich_transcript import enrich_reply

try:
    from rich.markdown import Markdown
    from rich.style import Style as _RichStyle
    from rich.text import Text as _RichText
    from textual.css.query import NoMatches
    from textual.widgets import OptionList, RichLog, Static
except ImportError:
    Markdown = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    _RichStyle = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    _RichText = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    NoMatches = Exception  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    OptionList = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    RichLog = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    Static = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

_TRANSCRIPT_ENTRY_GAP = ""
_TRANSCRIPT_HORIZONTAL_PADDING = 0
_USER_TRANSCRIPT_HORIZONTAL_PADDING = 2
_USER_TRANSCRIPT_VERTICAL_PADDING = 1


class TuiTranscriptMixin:
    def _refresh_completion_position(self) -> None:
        position = self.query_one("#completion-position", Static)
        suggestions = self.query_one("#suggestions", OptionList)
        option_count = len(self.completion_candidates) or len(self._inline_flow.options)
        highlighted = suggestions.highlighted
        if suggestions.has_class("visible") and option_count > 0 and highlighted is not None:
            palette = current_palette()
            position.update(_RichText(f"  ({highlighted + 1}/{option_count})", style=palette.dim))
            position.add_class("visible")
            return
        position.update("")
        position.remove_class("visible")

    def _schedule_transcript_reflow(self) -> None:
        if self._transcript_reflow_pending:
            return
        self._transcript_reflow_pending = True
        self.set_timer(0.01, self._run_scheduled_transcript_reflow)

    def _run_scheduled_transcript_reflow(self) -> None:
        self._transcript_reflow_pending = False
        self._reflow_transcript_entries()

    def _reflow_transcript_entries(self) -> None:
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

    def _write_transcript_renderable(self, log: RichLog, renderable: object) -> None:
        if log.size.width <= _TRANSCRIPT_HORIZONTAL_PADDING:
            log.write(renderable)
            self._scroll_transcript_to_end(log)
            return
        width = max(1, log.size.width - _TRANSCRIPT_HORIZONTAL_PADDING)
        log.write(renderable, width=width)
        self._scroll_transcript_to_end(log)

    @staticmethod
    def _scroll_transcript_to_end(log: RichLog) -> None:
        scroll_end = getattr(log, "scroll_end", None)
        if callable(scroll_end):
            scroll_end(animate=False)

    def _write_transcript_lines(
        self,
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

    def _write_user_transcript_lines(self, log: RichLog, text: str) -> None:
        p = current_palette()
        style = _RichStyle(color=p.ember, bgcolor=p.panel, bold=True)
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

    def _write_transcript_entry(self, entry: object) -> None:
        log = self.query_one("#transcript", RichLog)
        if entry.kind == "markdown":
            self._write_transcript_renderable(log, Markdown(entry.content))
        elif entry.kind == "user":
            self._write_user_transcript_lines(log, entry.content)
        elif entry.kind == "ansi":
            if _RichText is None:
                self._write_transcript_lines(log, entry.content)
                return
            self._write_transcript_lines(log, entry.content, ansi=True)
        elif entry.kind == "notice":
            if _RichText is None:
                self._write_transcript_lines(log, entry.content)
                return
            p = current_palette()
            self._write_transcript_lines(
                log,
                entry.content,
                style=_RichStyle(color=p.dim),
                ansi=True,
            )
        else:
            self._write_transcript_lines(log, entry.content)

    def _write_transcript_gap(self) -> None:
        log = self.query_one("#transcript", RichLog)
        self._write_transcript_renderable(log, _TRANSCRIPT_ENTRY_GAP)

    def _append_entry(self, content: str, kind: str = "plain") -> None:
        if self.state.transcript:
            self._write_transcript_gap()
        tui_module = sys.modules["hephaistos.tui"]
        entry = tui_module._TuiTranscriptEntry(content, kind)
        self.state.transcript.append(entry)
        self._write_transcript_entry(entry)

    def _append_plain(self, text: str) -> None:
        self._append_entry(text)

    def _append_user(self, text: str, *, mark_working: bool = True) -> None:
        self._append_entry(text, kind="user")
        if mark_working:
            self._start_thinking_animation()

    def _append_assistant_reply(self, text: str) -> None:
        evidence = self.session.last_turn_evidence
        enriched = enrich_reply(text, evidence)
        tui_module = sys.modules["hephaistos.tui"]
        entry = tui_module._TuiTranscriptEntry(
            enriched.markdown_text,
            "markdown",
            enriched.evidence,
        )
        if self.state.transcript:
            self._write_transcript_gap()
        self.state.transcript.append(entry)
        self._write_transcript_entry(entry)

    def _append_notice(self, text: str) -> None:
        self._append_entry(text, "notice")

    def _append_error(self, text: str) -> None:
        p = current_palette()
        self._append_entry(f"[bold {p.error}]error:[/bold {p.error}] {text}")

    def _finish_turn(self) -> None:
        self.busy = False
        self.abort_event.clear()
        self._stop_thinking_animation()
        self._refresh_status("ready")
        self._refresh_footer_hints()
        self._focused_msg_index = None
        self._update_info_panel()

    def _refresh_status(self, state: str = "ready") -> None:
        status = self.query_one("#status", Static)
        tui_module = sys.modules["hephaistos.tui"]
        status.update(tui_module._status_text(self.session, state))

    def _refresh_footer_hints(self) -> None:
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

    def _focus_message(self, direction: int) -> None:
        """Navigate transcript focus for the info panel. direction: -1=up, +1=down."""
        entries = [
            e
            for e in self.state.transcript
            if e.kind in ("user", "markdown", "plain")
            and not e.content.startswith("[dim")
            and not e.content.startswith("[#808080]")
            and not e.content.startswith("[bold #CC3333]")
        ]
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

    def _update_info_panel(self) -> None:
        """Refresh the info panel to reflect current state."""
        try:
            panel = self.query_one("#info-panel", Static)
        except NoMatches:
            return
        if self._focused_msg_index is not None:
            entries = [
                e
                for e in self.state.transcript
                if e.kind in ("user", "markdown", "plain")
                and not e.content.startswith("[dim")
                and not e.content.startswith("[#808080]")
                and not e.content.startswith("[bold #CC3333]")
            ]
            if self._focused_msg_index < len(entries):
                panel.update(
                    sys.modules["hephaistos.tui"]._info_panel_message_text(
                        entries[self._focused_msg_index],
                        self.session,
                    )
                )
                return
        tui_module = sys.modules["hephaistos.tui"]
        panel.update(
            tui_module._info_panel_default_text(
                self.session,
                session_seconds=self._tui_session_seconds(),
            )
        )
