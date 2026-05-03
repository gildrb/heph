# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportPrivateUsage=false
# pyright: reportUnknownVariableType=false, reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportAttributeAccessIssue=false, reportOptionalCall=false
from __future__ import annotations

import sys

from hephaistos.app.palette import current_palette
from hephaistos.app.rich_transcript import enrich_reply

try:
    from rich.markdown import Markdown
    from rich.text import Text as _RichText
    from textual.widgets import RichLog, Static
except ImportError:
    Markdown = None  # type: ignore[assignment]
    _RichText = None  # type: ignore[assignment]
    RichLog = None  # type: ignore[assignment]
    Static = None  # type: ignore[assignment]

_TRANSCRIPT_ENTRY_GAP = ""


class TuiTranscriptMixin:
    def _write_transcript_entry(self, entry: object) -> None:
        log = self.query_one("#transcript", RichLog)
        if entry.kind == "markdown":
            log.write(Markdown(entry.content))
        elif entry.kind == "ansi":
            if _RichText is None:
                log.write(entry.content)
                return
            log.write(_RichText.from_ansi(entry.content))
        else:
            log.write(entry.content)

    def _write_transcript_gap(self) -> None:
        self.query_one("#transcript", RichLog).write(_TRANSCRIPT_ENTRY_GAP)

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
        p = current_palette()
        self._append_entry(f"[bold {p.text}]You:[/bold {p.text}] {text}")
        if mark_working:
            self._start_thinking_animation()

    def _append_assistant_reply(self, text: str) -> None:
        evidence = self.session.last_turn_evidence
        enriched = enrich_reply(text, evidence)
        tui_module = sys.modules["hephaistos.tui"]
        entry = tui_module._TuiTranscriptEntry(enriched.markdown_text, "markdown")
        if self.state.transcript:
            self._write_transcript_gap()
        self.state.transcript.append(entry)
        log = self.query_one("#transcript", RichLog)
        log.write(Markdown(enriched.markdown_text))

    def _append_notice(self, text: str) -> None:
        p = current_palette()
        self._append_entry(f"[{p.dim}]{text}[/{p.dim}]")

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
        hints = self.query_one("#footer-hints", Static)
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
            if e.kind in ("markdown", "plain")
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
        panel = self.query_one("#info-panel", Static)
        if self._focused_msg_index is not None:
            entries = [
                e
                for e in self.state.transcript
                if e.kind in ("markdown", "plain")
                and not e.content.startswith("[dim")
                and not e.content.startswith("[#808080]")
                and not e.content.startswith("[bold #CC3333]")
            ]
            if self._focused_msg_index < len(entries):
                panel.update(
                    sys.modules["hephaistos.tui"]._info_panel_message_text(
                        entries[self._focused_msg_index], self.session
                    )
                )
                return
        tui_module = sys.modules["hephaistos.tui"]
        panel.update(tui_module._info_panel_default_text(self.session))
