"""Tests for shared session lifecycle and shell input helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hephaistos import commands
from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import (
    ChatSession,
    create_plain_session,
    create_session,
)
from hephaistos.commands import CommandResult
from hephaistos.shell.lifecycle import (
    create_startup_session,
    discover_startup_armory,
    get_history_path,
    save_on_exit,
)
from hephaistos.terminal.history import InputHistory
from hephaistos.terminal.input import handle_input


@pytest.fixture
def initialized_armory(tmp_path: Path) -> Path:
    """Create a properly initialized armory that passes validate_armory_path."""
    armory_path = tmp_path / "test-armory"
    initialize(armory_path)
    # Add a material file so create_session() doesn't reject the armory
    (armory_path / "materials" / "notes.md").write_text("# Notes\nSome study content.\n")
    return armory_path


# ---------------------------------------------------------------------------
# discover_startup_armory
# ---------------------------------------------------------------------------


class TestDiscoverStartupArmory:
    """Tests for discover_startup_armory()."""

    def test_returns_none_when_cwd_not_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = discover_startup_armory()
        assert result is None

    def test_returns_path_when_cwd_is_armory(
        self, initialized_armory: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(initialized_armory)
        result = discover_startup_armory()
        assert result == initialized_armory


# ---------------------------------------------------------------------------
# get_history_path
# ---------------------------------------------------------------------------


class TestGetHistoryPath:
    """Tests for get_history_path()."""

    def test_plain_session_returns_cache_path(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        path = get_history_path(session)
        assert path == Path.home() / ".cache" / "hephaistos" / "plain-history"

    def test_armory_session_returns_armory_history_path(self, initialized_armory: Path) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_session(config, initialized_armory)
        path = get_history_path(session)
        assert path == initialized_armory / ".hephaistos" / "history"


# ---------------------------------------------------------------------------
# create_startup_session
# ---------------------------------------------------------------------------


class TestCreateStartupSession:
    """Tests for create_startup_session()."""

    def test_creates_plain_session_when_no_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_startup_session(config)
        assert isinstance(session, ChatSession)
        assert session.armory_path is None

    def test_onboarding_creates_armory_and_waits_for_materials(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory_path = tmp_path / "onboarded"
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        prompts: list[str] = []

        def fake_input(prompt: str) -> str:
            prompts.append(prompt)
            if len(prompts) == 1:
                return str(armory_path)
            (armory_path / "materials" / "notes.md").write_text("# Notes\nStudy content.\n")
            return ""

        monkeypatch.setattr("hephaistos.shell.lifecycle._stdio_is_interactive", lambda: True)
        monkeypatch.setattr("builtins.input", fake_input)

        session = create_startup_session(config)

        assert session.armory_path == armory_path.resolve()
        assert session.source_file_count == 1
        assert len(prompts) == 2

    def test_empty_auto_discovered_armory_falls_back_with_setup_steps(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        armory_path = tmp_path / "empty-armory"
        initialize(armory_path)
        monkeypatch.chdir(armory_path)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")

        session = create_startup_session(config)

        captured = capsys.readouterr()
        assert session.armory_path is None
        assert "no study materials" in captured.out.lower()
        assert f"Add files to: {armory_path / 'materials'}" in captured.out
        assert "~/.armories/" in captured.out
        assert "No study session started because the armory still has no materials" in captured.out

    def test_creates_armory_session_when_armory_found(
        self, initialized_armory: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(initialized_armory)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_startup_session(config)
        assert isinstance(session, ChatSession)
        assert session.armory_path == initialized_armory


# ---------------------------------------------------------------------------
# save_on_exit
# ---------------------------------------------------------------------------


class TestSaveOnExit:
    """Tests for save_on_exit()."""

    def test_no_save_when_not_dirty(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        # Plain session is not dirty and has no armory — should just close trace
        save_on_exit(session)  # should not raise

    def test_closes_trace_even_when_not_saving(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        mock_trace = MagicMock()
        session.trace = mock_trace  # type: ignore[assignment]
        save_on_exit(session)
        mock_trace.close.assert_called_once()


# ---------------------------------------------------------------------------
# handle_input
# ---------------------------------------------------------------------------


class TestHandleInput:
    """Tests for handle_input()."""

    def _make_session(self) -> ChatSession:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        return create_plain_session(config)

    def test_empty_input_continues(self) -> None:
        session = self._make_session()
        history = InputHistory()
        new_session, should_continue = handle_input(session, "", history)
        assert should_continue is True
        assert new_session is session

    def test_whitespace_only_input_continues(self) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = handle_input(session, "   ", history)
        assert should_continue is True

    def test_streaming_enqueues_steering(self) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = handle_input(
            session, "steer this", history, streaming=True
        )
        assert should_continue is True
        assert "steer this" in session.steering._messages  # type: ignore[reportPrivateUsage]

    def test_shell_escape_adds_to_history(self) -> None:
        session = self._make_session()
        history = InputHistory()
        with patch("hephaistos.terminal.input.run_shell_command"):
            _new_session, should_continue = handle_input(session, "!echo hi", history)
        assert should_continue is True
        assert "echo hi" in str(
            history._entries  # type: ignore[reportPrivateUsage]
        )

    def test_unknown_command_prints_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = handle_input(session, "/nonexistent", history)
        assert should_continue is True
        output = capsys.readouterr().out
        assert "Unknown command" in output

    def test_exit_command_returns_false(self) -> None:
        session = self._make_session()
        history = InputHistory()
        _new_session, should_continue = handle_input(session, "/exit", history)
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

        new_session, should_continue = handle_input(
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

        _new_session, should_continue = handle_input(
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

        _new_session, should_continue = handle_input(session, "/help", history)

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
    """Verify migrated functions are importable from canonical modules."""

    def test_all_functions_importable(self) -> None:
        """Migrated functions are callable from their focused modules."""
        assert callable(create_startup_session)
        assert callable(get_history_path)
        assert callable(handle_input)
        assert callable(save_on_exit)
        assert callable(discover_startup_armory)
