from __future__ import annotations

import contextlib
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar

import harness.chat.storage as chat_storage
from harness.chat.session import (
    SessionError,
    fork_session_at_turn,
    list_armory_sessions,
    resume_session,
    save_session,
)
from harness.chat.titles import sanitize_title_text
from harness.chat.turn_history import TurnSnapshot

from interfaces.tui.cell_text import cell_width as _cell_width
from interfaces.tui.cell_text import pad_cell_right as _pad_cell_right
from interfaces.tui.display_text import label_value_line, menu_label_value
from interfaces.tui.inline_menu import (
    _session_option_description,
    _turn_option_description,
)
from interfaces.tui.session_state import TuiRuntimeState

try:
    from textual.widgets import RichLog
except ImportError:
    RichLog = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from harness.chat.session import ChatSession

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")

_SESSION_LIST_COMMANDS = {"list", "recent"}
_SESSION_BROWSE_COMMANDS = {"", "browse", "menu"}
_SESSION_LATEST_COMMANDS = {"resume", "last", "latest"}
_TURN_LIST_COMMANDS = {"list", "history"}
_TURN_BROWSE_COMMANDS = {"", "browse", "menu"}
_TURN_LATEST_COMMANDS = {"resume", "last", "latest"}
_SESSION_LIST_FIELD_GAP = "  "
_TURN_LIST_PREVIEW_LIMIT = 64


class _SessionFlowHost(Protocol):
    session: ChatSession
    state: TuiRuntimeState

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def call_from_thread(
        self,
        callback: Callable[_P, object],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> object: ...

    def _append_notice(self, text: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _append_plain(self, text: str) -> None: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _sync_busy_to_current_session(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _open_inline_menu(
        self,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
        prompts: dict[str, str] | None = None,
        selected_label: str | None = None,
    ) -> None: ...

    def _close_inline_flow(self, notice: str = "") -> None: ...

    def _perform_session_resume(self, session_id: str) -> None: ...

    def _perform_turn_branch(self, turn_id: str) -> None: ...

    def _replace_transcript_with_resumed_session(self, resumed: ChatSession) -> None: ...

    def _session_records(self) -> list[chat_storage.SessionRecord] | None: ...

    def _handle_known_sessions_subcommand(
        self,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool: ...

    def _resume_matching_session(
        self,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool: ...

    def _handle_known_turn_subcommand(
        self,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool: ...

    def _branch_matching_turn(
        self,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool: ...

    def _show_session_records(self, sessions: list[chat_storage.SessionRecord]) -> None: ...

    def _open_session_menu(self, sessions: list[chat_storage.SessionRecord]) -> None: ...

    def _show_turn_records(self, snapshots: list[TurnSnapshot]) -> None: ...

    def _open_turn_menu(self, snapshots: list[TurnSnapshot]) -> None: ...


class TuiSessionFlowMixin:
    def _handle_sessions_command(self: _SessionFlowHost, value: str) -> None:
        _, _, args = value.partition(" ")
        subcommand = args.strip().lower()
        sessions = self._session_records()
        if sessions is None:
            return
        if not sessions:
            self._append_notice("No saved chats found.")
            return
        if self._handle_known_sessions_subcommand(sessions, subcommand):
            return
        if self._resume_matching_session(sessions, subcommand):
            return
        self._append_error("Usage: /sessions [list|recent|browse|resume]")

    def _handle_turn_command(self: _SessionFlowHost, value: str) -> None:
        _, _, args = value.partition(" ")
        subcommand = args.strip().upper()
        snapshots = list(self.session.turn_history)
        if not snapshots:
            self._append_notice("No completed turns in this chat yet.")
            return
        if self._handle_known_turn_subcommand(snapshots, subcommand.lower()):
            return
        if self._branch_matching_turn(snapshots, subcommand):
            return
        self._append_error("Usage: /turn [list|browse|T#]")

    def _handle_known_sessions_subcommand(
        self: _SessionFlowHost,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool:
        actions: dict[str, Callable[[], None]] = {}
        for commands, action in (
            (_SESSION_LIST_COMMANDS, lambda: self._show_session_records(sessions)),
            (_SESSION_BROWSE_COMMANDS, lambda: self._open_session_menu(sessions)),
            (
                _SESSION_LATEST_COMMANDS,
                lambda: self._perform_session_resume(sessions[0]["session_id"]),
            ),
        ):
            for command in commands:
                actions[command] = action
        action = actions.get(subcommand)
        if action is None:
            return False
        action()
        return True

    def _handle_known_turn_subcommand(
        self: _SessionFlowHost,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool:
        actions: dict[str, Callable[[], None]] = {}
        for commands, action in (
            (_TURN_LIST_COMMANDS, lambda: self._show_turn_records(snapshots)),
            (_TURN_BROWSE_COMMANDS, lambda: self._open_turn_menu(snapshots)),
            (_TURN_LATEST_COMMANDS, lambda: self._perform_turn_branch(snapshots[-1].turn_id)),
        ):
            for command in commands:
                actions[command] = action
        action = actions.get(subcommand)
        if action is None:
            return False
        action()
        return True

    def _session_records(self: _SessionFlowHost) -> list[chat_storage.SessionRecord] | None:
        if self.session.armory_path is None:
            self._append_notice("No armory attached. Use /armory to open one.")
            return None
        return sorted(
            list_armory_sessions(self.session.armory_path),
            key=lambda entry: entry.get("updated_at", ""),
            reverse=True,
        )

    def _show_session_records(
        self: _SessionFlowHost,
        sessions: list[chat_storage.SessionRecord],
    ) -> None:
        self._append_plain(_session_records_text(sessions, armory=self.session.armory_path))

    def _open_session_menu(
        self: _SessionFlowHost,
        sessions: list[chat_storage.SessionRecord],
    ) -> None:
        self._open_inline_menu(
            name="sessions",
            step="menu",
            title=f"Sessions  {menu_label_value('action', 'resume')}",
            options=[
                (
                    entry["session_id"],
                    _session_option_description(entry),
                )
                for entry in sessions
            ],
        )

    def _show_turn_records(self: _SessionFlowHost, snapshots: list[TurnSnapshot]) -> None:
        self._append_plain(_turn_records_text(snapshots))

    def _open_turn_menu(
        self: _SessionFlowHost,
        snapshots: list[TurnSnapshot],
    ) -> None:
        self._open_inline_menu(
            name="turn",
            step="menu",
            title=f"Turn  {menu_label_value('action', 'branch')}",
            options=[
                (
                    snapshot.turn_id,
                    _turn_option_description(snapshot),
                )
                for snapshot in snapshots
            ],
        )

    def _resume_matching_session(
        self: _SessionFlowHost,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool:
        matches = [entry for entry in sessions if entry["session_id"].startswith(subcommand)]
        if len(matches) != 1:
            return False
        self._perform_session_resume(matches[0]["session_id"])
        return True

    def _branch_matching_turn(
        self: _SessionFlowHost,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool:
        matches = [snapshot for snapshot in snapshots if snapshot.turn_id.startswith(subcommand)]
        if len(matches) != 1:
            return False
        self._perform_turn_branch(matches[0].turn_id)
        return True

    def _perform_session_resume(self: _SessionFlowHost, session_id: str) -> None:
        if self.session.armory_path is None:
            self._close_inline_flow("No armory attached. Use /armory to open one.")
            return
        if self.session.dirty:
            with contextlib.suppress(chat_storage.ChatStorageError):
                save_session(self.session)
        try:
            resumed = resume_session(self.session.config, self.session.armory_path, session_id)
        except chat_storage.ChatStorageError as exc:
            self._close_inline_flow(f"error: {exc}")
            return
        self.session = resumed
        self._replace_transcript_with_resumed_session(resumed)
        self._close_inline_flow(f"resumed session {resumed.session_id}")
        self._sync_busy_to_current_session()
        self._update_info_panel()

    def _perform_turn_branch(self: _SessionFlowHost, turn_id: str) -> None:
        try:
            branched = fork_session_at_turn(self.session, turn_id)
        except SessionError as exc:
            self._close_inline_flow(f"error: {exc}")
            return
        self.session = branched
        self._replace_transcript_with_resumed_session(branched)
        self._close_inline_flow(
            f"branched from {turn_id.upper()} into session {branched.session_id}"
        )
        self._sync_busy_to_current_session()
        self._update_info_panel()

    def _replace_transcript_with_resumed_session(
        self: _SessionFlowHost,
        resumed: ChatSession,
    ) -> None:
        self.state.transcript.clear()
        self.query_one("#transcript", RichLog).clear()
        for message in resumed.conversation.messages:
            if message.role == "user":
                self._append_entry(message.content, "user")
            elif message.role == "assistant":
                self._append_entry(message.content, "markdown")


def _session_records_text(
    sessions: list[chat_storage.SessionRecord],
    *,
    armory: object,
) -> str:
    rows = [
        (
            label_value_line("session", entry["session_id"]),
            label_value_line("title", _session_record_title(entry)),
            label_value_line("updated", entry["updated_at"]),
        )
        for entry in sessions
    ]
    widths = _field_widths(rows)
    lines = [
        f"{label_value_line('sessions', len(sessions))}  {label_value_line('armory', armory)}"
    ]
    lines.extend(_aligned_record_row(row, widths) for row in rows)
    return "\n".join(lines)


def _turn_records_text(snapshots: list[TurnSnapshot]) -> str:
    rows = [
        (
            label_value_line("turn", snapshot.turn_id),
            label_value_line("question", _turn_record_question(snapshot)),
            _turn_record_evidence(snapshot),
        )
        for snapshot in snapshots
    ]
    widths = _field_widths(rows)
    lines = [label_value_line("turns", len(snapshots))]
    lines.extend(_aligned_record_row(row, widths) for row in rows)
    return "\n".join(lines)


def _session_record_title(entry: chat_storage.SessionRecord) -> str:
    title = sanitize_title_text(entry["title"], max_chars=max(1, len(entry["title"])))
    return title or "(untitled)"


def _turn_record_question(snapshot: TurnSnapshot) -> str:
    preview = " ".join(snapshot.user_input.split())
    if len(preview) > _TURN_LIST_PREVIEW_LIMIT:
        return f"{preview[: _TURN_LIST_PREVIEW_LIMIT - 3]}..."
    return preview


def _turn_record_evidence(snapshot: TurnSnapshot) -> str:
    evidence_count = len(snapshot.evidence.items) if snapshot.evidence is not None else 0
    return label_value_line("evidence", evidence_count or "none")


def _field_widths(rows: Sequence[Sequence[str]]) -> tuple[int, ...]:
    if not rows:
        return ()
    return tuple(max(_cell_width(row[index]) for row in rows) for index in range(len(rows[0])))


def _aligned_record_row(row: Sequence[str], widths: Sequence[int]) -> str:
    fields = [
        _pad_cell_right(field, widths[index]) if index + 1 < len(row) else field
        for index, field in enumerate(row)
    ]
    return f"  {_SESSION_LIST_FIELD_GAP.join(fields)}"
