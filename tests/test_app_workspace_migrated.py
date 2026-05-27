"""Tests for shared session lifecycle and terminal input helpers."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hephaion import commands
from hephaion.armory.search import (
    add_known_armory,
    get_last_armory,
    load_known_armories,
    load_recent_armory_entries,
    save_known_armories,
    set_last_armory,
)
from hephaion.armory.storage import initialize
from hephaion.chat.session import (
    ChatSession,
    create_plain_session,
    create_session,
)
from hephaion.commands import CommandResult
from hephaion.runtime import ChatConfig
from hephaion.terminal.history import InputHistory
from hephaion.terminal.input import handle_input
from hephaion.tui.session_actions import (
    create_startup_session,
    get_history_path,
    save_on_exit,
)
from hephaion.tui.startup_discovery import discover_startup_armory


@pytest.fixture
def initialized_armory(tmp_path: Path) -> Path:
    """Create a properly initialized armory that passes validate_armory_path."""
    armory_path = tmp_path / "test-armory"
    initialize(armory_path)
    # Add a material file so create_session() doesn't reject the armory
    (armory_path / "materials" / "notes.md").write_text("# Notes\nSome source content.\n")
    return armory_path


@pytest.fixture
def clean_armory_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    save_known_armories([])
    return armory_home


# ---------------------------------------------------------------------------
# discover_startup_armory
# ---------------------------------------------------------------------------


class TestDiscoverStartupArmory:
    """Tests for discover_startup_armory()."""

    def test_returns_none_when_cwd_not_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
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

    def test_falls_back_to_single_known_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory = tmp_path / "my-armory"
        initialize(armory)

        add_known_armory(armory)

        result = discover_startup_armory()
        assert result == armory

    def test_returns_none_when_multiple_known_armories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory_a = tmp_path / "armory-a"
        armory_b = tmp_path / "armory-b"
        initialize(armory_a)
        initialize(armory_b)

        add_known_armory(armory_a)
        add_known_armory(armory_b)

        result = discover_startup_armory()
        assert result is None

    def test_ignores_invalid_known_armories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory = tmp_path / "valid-armory"
        initialize(armory)
        # Create a path that exists but isn't a valid armory
        not_armory = tmp_path / "not-armory"
        not_armory.mkdir()

        save_known_armories([armory, not_armory])

        result = discover_startup_armory()
        assert result == armory

    def test_auto_discovers_single_armory_in_armories_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory = clean_armory_env / "workspace-fixture-1"
        initialize(armory)

        result = discover_startup_armory()
        assert result == armory

    def test_auto_discovers_and_registers_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory = clean_armory_env / "test-armory"
        initialize(armory)

        result = discover_startup_armory()
        assert result == armory

        known = load_known_armories()
        assert armory in known

    def test_returns_none_when_multiple_armories_in_armories_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory_a = clean_armory_env / "armory-a"
        armory_b = clean_armory_env / "armory-b"
        initialize(armory_a)
        initialize(armory_b)

        result = discover_startup_armory()
        assert result is None

    def test_last_armory_used_when_multiple_known(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory_a = clean_armory_env / "armory-a"
        armory_b = clean_armory_env / "armory-b"
        initialize(armory_a)
        initialize(armory_b)
        add_known_armory(armory_a)
        add_known_armory(armory_b)
        set_last_armory(armory_b)

        result = discover_startup_armory()
        assert result == armory_b

    def test_last_armory_ignored_when_deleted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory = clean_armory_env / "deleted"
        initialize(armory)
        set_last_armory(armory)
        shutil.rmtree(armory)

        result = discover_startup_armory()
        assert result is None


class TestLastArmoryHelpers:
    def test_set_and_get_last_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        armory = clean_armory_env / "my-armory"
        initialize(armory)
        set_last_armory(armory)
        assert get_last_armory() == armory.resolve()

    def test_get_last_armory_returns_none_when_unset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        assert get_last_armory() is None

    def test_get_last_armory_returns_none_for_missing_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        set_last_armory(tmp_path / "nonexistent")
        assert get_last_armory() is None

    def test_recent_armories_are_capped_to_last_three(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: Path
    ) -> None:
        armories = [clean_armory_env / f"armory-{index}" for index in range(4)]
        for armory in armories:
            initialize(armory)

        for armory in armories:
            set_last_armory(armory)

        recent = [entry.path for entry in load_recent_armory_entries()]
        assert recent == [armories[3].resolve(), armories[2].resolve(), armories[1].resolve()]


# ---------------------------------------------------------------------------
# get_history_path
# ---------------------------------------------------------------------------


class TestGetHistoryPath:
    """Tests for get_history_path()."""

    def test_plain_session_returns_cache_path(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        path = get_history_path(session)
        assert path == Path.home() / ".cache" / "hephaion" / "plain-history"

    def test_plain_session_uses_shared_system_prompt(self) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_plain_session(config)
        system_prompt = session.conversation.messages[0].content

        assert system_prompt.startswith("You are running inside Heph.")
        assert "## Guidelines" in system_prompt
        assert "Say nothing else" not in system_prompt

    def test_armory_session_returns_armory_history_path(self, initialized_armory: Path) -> None:
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_session(config, initialized_armory)
        path = get_history_path(session)
        assert path == initialized_armory / ".hephaion" / "history"


# ---------------------------------------------------------------------------
# create_startup_session
# ---------------------------------------------------------------------------


class TestCreateStartupSession:
    """Tests for create_startup_session()."""

    def test_creates_plain_session_when_no_armory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_armory_env: None
    ) -> None:
        monkeypatch.chdir(tmp_path)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")
        session = create_startup_session(config)
        assert isinstance(session, ChatSession)
        assert session.armory_path is None

    def test_multiple_known_armories_do_not_prompt_before_tui(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        clean_armory_env: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory_a = clean_armory_env / "armory-a"
        armory_b = clean_armory_env / "armory-b"
        initialize(armory_a)
        initialize(armory_b)
        add_known_armory(armory_a)
        add_known_armory(armory_b)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")

        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: pytest.fail("startup should not prompt before TUI"),
        )

        session = create_startup_session(config)

        captured = capsys.readouterr()
        assert session.armory_path is None
        assert "Multiple armories found" in captured.out

    def test_multiple_armories_in_home_do_not_prompt_before_tui(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        clean_armory_env: Path,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        armory_a = clean_armory_env / "armory-a"
        armory_b = clean_armory_env / "armory-b"
        initialize(armory_a)
        initialize(armory_b)
        config = ChatConfig(base_url="https://api.example.com", model="test-model")

        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: pytest.fail("startup should not prompt before TUI"),
        )

        session = create_startup_session(config)

        known = load_known_armories()
        assert session.armory_path is None
        assert armory_a.resolve() in known
        assert armory_b.resolve() in known

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
        assert "no materials" in captured.out.lower()
        assert f"Add files to: {armory_path / 'materials'}" in captured.out

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
        session.trace = mock_trace
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

    def test_help_command_output_is_printed_by_handle_input(
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
