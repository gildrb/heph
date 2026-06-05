from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar

import hephaion.chat.storage as chat_storage
from hephaion.chat.session import (
    SessionError,
    fork_session_at_turn,
    list_armory_sessions,
    resume_session,
    save_session,
)
from hephaion.chat.turn_history import TurnSnapshot

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
    from hephaion.chat.session import ChatSession

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")

_SESSION_LIST_COMMANDS = {"list", "recent"}
_SESSION_BROWSE_COMMANDS = {"", "browse", "menu"}
_SESSION_LATEST_COMMANDS = {"resume", "last", "latest"}
_TURN_LIST_COMMANDS = {"list", "history"}
_TURN_BROWSE_COMMANDS = {"", "browse", "menu"}
_TURN_LATEST_COMMANDS = {"resume", "last", "latest"}


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
        lines = [f"Saved sessions for {self.session.armory_path}:"]
        for entry in sessions:
            title = entry["title"] or "(untitled)"
            lines.append(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")
        self._append_plain("\n".join(lines))

    def _open_session_menu(
        self: _SessionFlowHost,
        sessions: list[chat_storage.SessionRecord],
    ) -> None:
        self._open_inline_menu(
            name="sessions",
            step="menu",
            title="Sessions  choose a chat to resume",
            options=[
                (
                    entry["session_id"],
                    _session_option_description(entry),
                )
                for entry in sessions
            ],
        )

    def _show_turn_records(self: _SessionFlowHost, snapshots: list[TurnSnapshot]) -> None:
        lines = ["Completed turns in this chat:"]
        lines.extend(
            f"  {snapshot.turn_id}  {_turn_option_description(snapshot)}" for snapshot in snapshots
        )
        self._append_plain("\n".join(lines))

    def _open_turn_menu(
        self: _SessionFlowHost,
        snapshots: list[TurnSnapshot],
    ) -> None:
        self._open_inline_menu(
            name="turn",
            step="menu",
            title="Turn  choose a message to branch from",
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
