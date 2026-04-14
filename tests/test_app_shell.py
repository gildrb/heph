"""Tests for the interactive shell (using fallback mode)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from hephaistos.app import shell
from hephaistos.app.display import print_shell_intro
from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig, EngineError
from hephaistos.chat.session import SessionError, create_session
from hephaistos.providers.config import _default_config


def _test_config() -> ChatConfig:
    """Create a ChatConfig with explicit endpoint/model for tests."""
    return ChatConfig(
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
    )


def _make_armory(tmp_path: Path) -> Path:
    """Create a valid armory with one source file."""
    armory_path = tmp_path / "test-armory"
    initialize(armory_path)
    (armory_path / "source").mkdir(exist_ok=True)
    (armory_path / "source" / "exam.md").write_text(
        "# Past Exam\n## Q1\nWhat is 2+2?\n\nAnswer: 4\n"
    )
    return armory_path


def _make_session(tmp_path: Path):
    """Create a session attached to a valid armory."""
    armory_path = _make_armory(tmp_path)
    return create_session(_test_config(), armory_path)


def test_run_chat_shell_armory_command_opens_existing_armory(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    old_armory = _make_armory(tmp_path / "old")
    new_armory = _make_armory(tmp_path / "new")

    responses = iter(["/armory", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": str(new_armory))
    monkeypatch.setattr(shell, "select_option", lambda *_args, **_kwargs: 0)

    session = create_session(_test_config(), old_armory)
    with (
        patch.object(shell.sys.stdin, "isatty", return_value=False),
        patch.object(shell.sys.stdout, "isatty", return_value=False),
    ):
        shell._run_fallback_shell(session)

    out = capsys.readouterr().out
    assert f"Using armory {new_armory.resolve()}" in out


def test_create_session_without_armory_raises(tmp_path: Path) -> None:
    with pytest.raises(SessionError, match="armory is required"):
        create_session(_test_config(), None)  # type: ignore[arg-type]


def test_create_session_empty_armory_raises(tmp_path: Path) -> None:
    armory_path = tmp_path / "empty-armory"
    initialize(armory_path)
    # No source files
    with pytest.raises(SessionError, match="no source documents"):
        create_session(_test_config(), armory_path)


def test_fallback_shell_exits_on_quit(monkeypatch, capsys, tmp_path: Path) -> None:
    responses = iter(["/quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = _make_session(tmp_path)
    shell._run_fallback_shell(session)

    out = capsys.readouterr().out
    assert "basic mode" in out


def test_fallback_shell_without_startup_armory_uses_plain_chat(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    prompts: list[str] = []
    responses = iter(["/exit"])

    def _input(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(responses)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", _input)

    shell._run_fallback_shell()

    out = capsys.readouterr().out
    assert "No armory found" not in out
    assert "basic mode" in out
    assert prompts == ["> "]


def test_fallback_shell_runs_bang_command(monkeypatch, capsys, tmp_path: Path) -> None:
    responses = iter(["!echo hello", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = _make_session(tmp_path)
    shell._run_fallback_shell(session)

    out = capsys.readouterr().out
    assert "hello" in out


def test_handle_input_slash_command(monkeypatch, capsys, tmp_path: Path) -> None:
    from hephaistos.app.input_history import InputHistory

    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/status", history)
    assert cont is True
    out = capsys.readouterr().out
    assert "Session:" in out


def test_handle_input_exit(monkeypatch, tmp_path: Path) -> None:
    from hephaistos.app.input_history import InputHistory

    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/exit", history)
    assert cont is False


def test_handle_input_shell_mode(monkeypatch, capsys, tmp_path: Path) -> None:
    from hephaistos.app.input_history import InputHistory

    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "!echo test-output", history)
    assert cont is True
    out = capsys.readouterr().out
    assert "test-output" in out


def test_handle_input_unknown_command(capsys, tmp_path: Path) -> None:
    from hephaistos.app.input_history import InputHistory

    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/unknown", history)
    assert cont is True
    out = capsys.readouterr().out
    assert "Unknown command" in out


def test_handle_input_engine_error_does_not_print_assistant_placeholder(
    capsys,
    tmp_path: Path,
) -> None:
    from hephaistos.app.input_history import InputHistory

    session = _make_session(tmp_path)
    session.config.api_key = "test-key"
    history = InputHistory()

    with patch(
        "hephaistos.app.shell.send_user_message",
        side_effect=EngineError("Provider rejected the request. Configure /api key or /login."),
    ):
        session, cont = shell._handle_input(session, "hello", history)

    assert cont is True
    out = capsys.readouterr().out
    assert "Provider rejected the request" in out
    assert "Assistant:" not in out


def test_bottom_toolbar_uses_cached_status(monkeypatch, tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    calls = 0

    def fake_context_left(_session) -> int:
        nonlocal calls
        calls += 1
        return 73

    monkeypatch.setattr(shell, "_context_left", fake_context_left)

    toolbar_ref = [shell._build_bottom_toolbar_status(session)]

    shell._get_bottom_toolbar(toolbar_ref)
    shell._get_bottom_toolbar(toolbar_ref)

    assert calls == 1

    shell._refresh_bottom_toolbar(session, toolbar_ref)

    assert calls == 2


def test_prompt_message_uses_visible_composer_prefix() -> None:
    assert list(shell._get_prompt_message()()) == [("class:prompt-mark", "> ")]


def test_prompt_message_switches_to_follow_up_prefix_when_busy() -> None:
    runtime = shell.ShellRuntime(busy=True)

    assert list(shell._get_prompt_message(runtime)()) == [("class:prompt-mark", "+ ")]


def test_dynamic_composer_accepts_pipe_input() -> None:
    with create_pipe_input() as pipe_input:
        session = PromptSession(
            message=shell._get_prompt_message(),
            style=shell._PT_STYLE,
            history=InMemoryHistory(),
            completer=shell.SlashCommandCompleter(),
            key_bindings=shell._build_keybindings(shell.DEFAULT_SHELL_KEYBINDINGS),
            bottom_toolbar=lambda: shell._get_bottom_toolbar(["~ · plain chat"]),
            multiline=True,
            complete_while_typing=True,
            show_frame=False,
            input=pipe_input,
            output=DummyOutput(),
        )
        pipe_input.send_text("hello\r")

        assert session.prompt() == "hello"


def test_bottom_toolbar_shows_multiline_status(tmp_path: Path) -> None:
    session = _make_session(tmp_path)

    status = shell._build_bottom_toolbar_status(session)

    assert session.armory_path is not None
    assert shell._display_path(session.armory_path) in status
    assert "armory attached" in status
    assert "model" in status
    assert "context" in status
    assert "api " in status
    assert "source 1 file" in status
    assert "enter send" in status


def test_bottom_toolbar_shows_busy_hint(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    runtime = shell.ShellRuntime(busy=True, steering_count=2)

    status = shell._build_bottom_toolbar_status(session, runtime)

    assert "assistant working" in status
    assert "enter queues follow-up" in status
    assert "queued 2" in status


def test_shell_style_overrides_default_reversed_toolbar() -> None:
    style_rules = dict(shell._PT_STYLE.style_rules)

    assert style_rules["bottom-toolbar"] == "noreverse fg:#808080"
    assert style_rules["bottom-toolbar.text"] == "noreverse fg:#808080"
    assert style_rules["composer"] == "bg:#1C1C1C fg:#E0E0E0"
    assert style_rules["prompt-mark"] == "bold #C8C8C8"
    assert "frame" not in style_rules
    assert "frame.border" not in style_rules


def test_slash_completer_suggests_provider_subcommands(monkeypatch) -> None:
    monkeypatch.setattr(shell.ProviderConfig, "load", classmethod(lambda cls: _default_config()))
    completer = shell.SlashCommandCompleter()

    completions = list(completer.get_completions(Document("/provider u"), CompleteEvent()))

    assert any(completion.text == "use " for completion in completions)

    completions = list(completer.get_completions(Document("/provider use za"), CompleteEvent()))

    assert any(completion.text == "zai " for completion in completions)


def test_slash_completer_matches_command_aliases() -> None:
    completer = shell.SlashCommandCompleter()

    completions = list(completer.get_completions(Document("/qui"), CompleteEvent()))

    assert any(completion.text == "quit " for completion in completions)


def test_shell_intro_uses_compact_header(capsys) -> None:
    print_shell_intro(
        version="0.1.0",
        armory_path="none",
        source_file_count=0,
        model="glm-5v-turbo",
        has_api_key=False,
    )

    out = capsys.readouterr().out
    assert "Hephaistos" in out
    assert "__  __" not in out
    assert "/help" in out
    assert "/armory" in out
    assert "configure api" in out


# ---------------------------------------------------------------------------
# Cancellation / back-navigation tests
# ---------------------------------------------------------------------------


def test_prompt_path_returns_none_on_q(monkeypatch) -> None:
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "q")
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_prompt_path_returns_none_on_cancel(monkeypatch) -> None:
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "cancel")
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_prompt_path_returns_none_on_back(monkeypatch) -> None:
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "back")
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_prompt_path_returns_default_on_empty(monkeypatch) -> None:
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "")
    result = shell._prompt_path("Path", "/default")
    assert result == "/default"


def test_prompt_path_returns_value_when_provided(monkeypatch) -> None:
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "/my/path")
    result = shell._prompt_path("Path", "/default")
    assert result == "/my/path"


def test_prompt_path_returns_none_on_keyboard_interrupt(monkeypatch) -> None:
    def _raise(_: str = "") -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("hephaistos.app.shell.direct_input", _raise)
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_prompt_path_returns_none_on_eof(monkeypatch) -> None:
    def _raise(_: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("hephaistos.app.shell.direct_input", _raise)
    result = shell._prompt_path("Path", "/default")
    assert result is None


def test_open_armory_cancelled_returns_session_unchanged(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "q")
    new_session = shell._open_armory(session)

    assert new_session is session
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_create_armory_cancelled_returns_session_unchanged(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "q")
    new_session = shell._create_armory(session)

    assert new_session is session
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_handle_armory_command_detaches_armory(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr(shell, "select_option", lambda *_args, **_kwargs: 2)
    new_session = shell._handle_armory_command(session)

    assert new_session is not session
    assert new_session.armory_path is None
    assert new_session.source_file_count == 0
    out = capsys.readouterr().out
    assert "Detached armory. Plain chat mode." in out


def test_prompt_armory_for_sessions_cancelled_returns_none(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "q")
    result = shell._prompt_armory_for_sessions(session)

    assert result is None
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_resume_saved_chat_cancelled_returns_session_unchanged(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    # Cancel at the path prompt
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "q")
    new_session = shell._resume_saved_chat(session)

    assert new_session is session


def test_list_saved_chats_cancelled_returns_early(monkeypatch, capsys, tmp_path: Path) -> None:
    session = _make_session(tmp_path)

    # Cancel at the path prompt
    monkeypatch.setattr("hephaistos.app.shell.direct_input", lambda _prompt="": "q")
    shell._list_saved_chats(session)

    out = capsys.readouterr().out
    assert "Cancelled" in out
