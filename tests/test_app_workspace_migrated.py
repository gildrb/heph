"""Tests for the 5 shared functions migrated from shell.py to workspace.py.

These functions are: _create_startup_session, _get_history_path, _handle_input,
_save_on_exit, _discover_startup_armory.

Validates VAL-STRUCT-003: Shared functions from shell.py migrated.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hephaistos.app import commands
from hephaistos.app.commands import CommandResult
from hephaistos.app.input_history import InputHistory
from hephaistos.app.workspace import (
    _create_startup_session,  # type: ignore[reportPrivateUsage]
    _discover_startup_armory,  # type: ignore[reportPrivateUsage]
    _get_history_path,  # type: ignore[reportPrivateUsage]
    _handle_input,  # type: ignore[reportPrivateUsage]
    _save_on_exit,  # type: ignore[reportPrivateUsage]
)
from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import (
    ChatSession,
    create_plain_session,
    create_session,
)


@pytest.fixture
def initialized_armory(tmp_path: Path) -> Path:
    """Create a properly initialized armory that passes validate_armory_path."""
    armory_path = tmp_path / "test-armory"
    initialize(armory_path)
    # Add a material file so create_session() doesn't reject the armory
    (armory_path / "materials" / "notes.md").write_text("# Notes\nSome study content.\n")
    return armory_path


# ---------------------------------------------------------------------------
# _discover_startup_armory
# ---------------------------------------------------------------------------


class TestDiscoverStartupArmory:
    """Tests for _discover_startup_armory()."""

    def test_returns_none_when_cwd_not_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = _discover_startup_armory()
        assert result is None

    def test_returns_path_when_cwd_is_armory(
        self, initialized_armory: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(initialized_armory)
        result = _discover_startup_armory()
        assert result == initialized_armory


# ---------------------------------------------------------------------------
# _get_history_path
# ---------------------------------------------------------------------------


class TestGetHistoryPath:
    """Tests for _get_history_path()."""

    def test_plain_session_returns_cache_path(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        path = _get_history_path(session)
        assert path == Path.home() / ".cache" / "hephaistos" / "plain-history"

    def test_armory_session_returns_armory_history_path(self, initialized_armory: Path) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_session(config, initialized_armory)
        path = _get_history_path(session)
        assert path == initialized_armory / ".hephaistos" / "history"


# ---------------------------------------------------------------------------
# _create_startup_session
# ---------------------------------------------------------------------------


class TestCreateStartupSession:
    """Tests for _create_startup_session()."""

    def test_creates_plain_session_when_no_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = _create_startup_session(config)
        assert isinstance(session, ChatSession)
        assert session.armory_path is None

    def test_creates_armory_session_when_armory_found(
        self, initialized_armory: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(initialized_armory)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = _create_startup_session(config)
        assert isinstance(session, ChatSession)
        assert session.armory_path == initialized_armory


# ---------------------------------------------------------------------------
# _save_on_exit
# ---------------------------------------------------------------------------


class TestSaveOnExit:
    """Tests for _save_on_exit()."""

    def test_no_save_when_not_dirty(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        # Plain session is not dirty and has no armory — should just close trace
        _save_on_exit(session)  # should not raise

    def test_closes_trace_even_when_not_saving(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        mock_trace = MagicMock()
        session.trace = mock_trace  # type: ignore[assignment]
        _save_on_exit(session)
        mock_trace.close.assert_called_once()


# ---------------------------------------------------------------------------
# _handle_input
# ---------------------------------------------------------------------------


class TestHandleInput:
    """Tests for _handle_input()."""

    def _make_session(self) -> ChatSession:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        return create_plain_session(config)

    def test_empty_input_continues(self) -> None:
        session = self._make_session()
        history = InputHistory()
        new_session, should_continue = _handle_input(session, "", history)
        assert should_continue is True
        assert new_session is session

    def test_whitespace_only_input_continues(self) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = _handle_input(session, "   ", history)
        assert should_continue is True

    def test_streaming_enqueues_steering(self) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = _handle_input(
            session, "steer this", history, streaming=True
        )
        assert should_continue is True
        assert "steer this" in session.steering._messages  # type: ignore[reportPrivateUsage]

    def test_shell_escape_adds_to_history(self) -> None:
        session = self._make_session()
        history = InputHistory()
        with patch("hephaistos.app.workspace._run_shell_command"):
            _new_session, should_continue = _handle_input(session, "!echo hi", history)
        assert should_continue is True
        assert "echo hi" in str(
            history._entries  # type: ignore[reportPrivateUsage]
        )

    def test_unknown_command_prints_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = _handle_input(session, "/nonexistent", history)
        assert should_continue is True
        output = capsys.readouterr().out
        assert "Unknown command" in output

    def test_exit_command_returns_false(self) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = _handle_input(session, "/exit", history)
        assert should_continue is False

    @pytest.mark.parametrize(
        "command_name",
        [cmd.name for cmd in commands.get_registry().commands],
    )
    def test_registered_command_input_invokes_handler(
        self,
        monkeypatch: pytest.MonkeyPatch,
        command_name: str,
    ) -> None:
        session = self._make_session()
        history = InputHistory()
        registry = commands.get_registry()
        command = registry.find(command_name)
        assert command is not None
        calls: list[tuple[ChatSession, str]] = []

        def fake_handle(active_session: ChatSession, args: str) -> CommandResult:
            calls.append((active_session, args))
            return CommandResult()

        monkeypatch.setattr(command, "handle", fake_handle)

        new_session, should_continue = _handle_input(
            session,
            f"/{command_name} sentinel args",
            history,
        )

        assert should_continue is True
        assert new_session is session
        assert calls == [(session, "sentinel args")]
        assert history.entries[-1] == f"/{command_name} sentinel args"

    @pytest.mark.parametrize(
        ("alias", "command_name"),
        [(alias, cmd.name) for cmd in commands.get_registry().commands for alias in cmd.aliases],
    )
    def test_registered_command_alias_invokes_handler(
        self,
        monkeypatch: pytest.MonkeyPatch,
        alias: str,
        command_name: str,
    ) -> None:
        session = self._make_session()
        history = InputHistory()
        command = commands.get_registry().find(command_name)
        assert command is not None
        calls: list[str] = []

        def fake_handle(_active_session: ChatSession, args: str) -> CommandResult:
            calls.append(args)
            return CommandResult()

        monkeypatch.setattr(command, "handle", fake_handle)

        _new_session, should_continue = _handle_input(
            session,
            f"/{alias} alias args",
            history,
        )

        assert should_continue is True
        assert calls == ["alias args"]
        assert history.entries[-1] == f"/{alias} alias args"

    def test_help_command_output_is_printed_by_input_dispatch(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = self._make_session()
        history = InputHistory()

        _new_session, should_continue = _handle_input(session, "/help", history)

        output = capsys.readouterr().out
        assert should_continue is True
        assert "Commands" in output
        assert "/help" in output
        assert "/status" in output
        assert history.entries[-1] == "/help"


# ---------------------------------------------------------------------------
# Importability checks (VAL-STRUCT-003)
# ---------------------------------------------------------------------------


class TestImportability:
    """Verify all 5 migrated functions are importable from workspace."""

    def test_all_functions_importable(self) -> None:
        """All 5 migrated functions are callable from workspace.py."""
        assert callable(_create_startup_session)
        assert callable(_get_history_path)
        assert callable(_handle_input)
        assert callable(_save_on_exit)
        assert callable(_discover_startup_armory)
