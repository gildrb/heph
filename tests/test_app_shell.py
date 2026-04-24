"""Tests for the interactive shell (using fallback mode)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

import pytest
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import FloatContainer, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.defaults import default_ui_style

from hephaistos.app import menu, palette, shell, workspace
from hephaistos.app.commands import SettingsCommand
from hephaistos.app.display import format_shell_header, print_shell_intro
from hephaistos.app.input_history import InputHistory
from hephaistos.armory.storage import initialize
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, Conversation, EngineError
from hephaistos.chat.session import SessionError, create_plain_session, create_session
from hephaistos.providers.config import _default_config  # type: ignore[reportPrivateUsage]


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
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    old_armory = _make_armory(tmp_path / "old")
    new_armory = _make_armory(tmp_path / "new")

    responses = iter(["/armory", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    monkeypatch.setattr(
        "hephaistos.app.workspace.browse_directory",
        lambda *_, **_kw: new_armory,  # type: ignore[reportUnknownLambdaType]
    )
    monkeypatch.setattr(
        workspace,
        "select_option",
        lambda *_args, **_kwargs: 0,  # type: ignore[reportUnknownLambdaType]
    )

    session = create_session(_test_config(), old_armory)
    with (
        patch.object(shell.sys.stdin, "isatty", return_value=False),
        patch.object(shell.sys.stdout, "isatty", return_value=False),
    ):
        shell._run_fallback_shell(session)  # type: ignore[reportPrivateUsage]

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


def test_fallback_shell_exits_on_quit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    responses = iter(["/quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = _make_session(tmp_path)
    shell._run_fallback_shell(session)  # type: ignore[reportPrivateUsage]

    out = capsys.readouterr().out
    assert "basic mode" in out


def test_fallback_shell_without_startup_armory_uses_plain_chat(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    prompts: list[str] = []
    responses = iter(["/exit"])

    def _input(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(responses)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", _input)

    shell._run_fallback_shell()  # type: ignore[reportPrivateUsage]

    out = capsys.readouterr().out
    assert "No armory found" not in out
    assert "basic mode" in out
    assert prompts == ["> "]


def test_create_startup_session_only_auto_opens_current_armory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    armory = _make_armory(tmp_path / "fallback")
    monkeypatch.chdir(armory)

    session = shell._create_startup_session(_test_config())  # type: ignore[reportPrivateUsage]

    assert session.armory_path == armory
    assert session.source_files == ("source/exam.md",)


def test_create_startup_session_ignores_default_armory_outside_workspace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _make_armory(tmp_path / "fallback")
    monkeypatch.chdir(tmp_path)

    session = shell._create_startup_session(_test_config())  # type: ignore[reportPrivateUsage]

    assert session.armory_path is None


def test_fallback_shell_runs_bang_command(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    responses = iter(["!echo hello", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    session = _make_session(tmp_path)
    shell._run_fallback_shell(session)  # type: ignore[reportPrivateUsage]

    out = capsys.readouterr().out
    assert "hello" in out


def test_handle_input_slash_command(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/status", history)  # type: ignore[reportPrivateUsage]
    assert cont is True
    out = capsys.readouterr().out
    assert "Session:" in out


def test_handle_input_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/exit", history)  # type: ignore[reportPrivateUsage]
    assert cont is False


def test_handle_input_shell_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "!echo test-output", history)  # type: ignore[reportPrivateUsage]
    assert cont is True
    out = capsys.readouterr().out
    assert "test-output" in out


def test_handle_input_unknown_command(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    history = InputHistory()
    session, cont = shell._handle_input(session, "/unknown", history)  # type: ignore[reportPrivateUsage]
    assert cont is True
    out = capsys.readouterr().out
    assert "Unknown command" in out


def test_handle_input_engine_error_does_not_print_assistant_placeholder(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    session = _make_session(tmp_path)
    session.config.api_key = "test-key"
    history = InputHistory()

    with patch(
        "hephaistos.app.shell.send_user_message",
        side_effect=EngineError("Provider rejected the request. Configure /api key or /login."),
    ):
        session, cont = shell._handle_input(session, "hello", history)  # type: ignore[reportPrivateUsage]

    assert cont is True
    out = capsys.readouterr().out
    assert "Provider rejected the request" in out
    assert "Assistant:" not in out


def test_bottom_toolbar_uses_cached_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    toolbar_ref = [shell._build_bottom_toolbar_status(session)]  # type: ignore[reportPrivateUsage]

    idle_toolbar = shell._get_bottom_toolbar(toolbar_ref)  # type: ignore[reportPrivateUsage]
    idle_text = "".join(fragment[1] for fragment in idle_toolbar)

    assert "/settings prefs" in idle_text
    assert "context" not in idle_text
    assert "source" not in idle_text

    runtime = shell.ShellRuntime(busy=True, steering_count=2)
    shell._refresh_bottom_toolbar(session, toolbar_ref, runtime)  # type: ignore[reportPrivateUsage]
    busy_toolbar = shell._get_bottom_toolbar(toolbar_ref)  # type: ignore[reportPrivateUsage]
    busy_text = "".join(fragment[1] for fragment in busy_toolbar)

    assert "assistant working" in busy_text
    assert "queued 2" in busy_text


def test_format_menu_pads_rows_and_marks_active_option(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("hephaistos.app.menu._terminal_columns", lambda default=80: 80)

    fragments = menu._format_menu(  # type: ignore[reportPrivateUsage]
        "Appearance",
        [
            menu.MenuOption("Forge", "Theme preset", is_current=True),
            menu.MenuOption("Light", "Theme preset"),
        ],
        selected=0,
    )
    lines = "".join(fragment[1] for fragment in fragments).splitlines()

    assert "active" in lines[1]
    assert all(len(line) == 80 for line in lines)


def test_appearance_menu_updates_theme_without_printing_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selections = iter([1, 3])
    save_calls: list[tuple[str, str]] = []
    theme_calls: list[str] = []
    success_messages: list[str] = []

    def fake_select_option(*_args: object, **_kwargs: object) -> int:
        return next(selections)

    def fake_save_setting(key: str, value: str) -> None:
        save_calls.append((key, value))

    def fake_set_theme(theme: str) -> None:
        theme_calls.append(theme)

    def fake_print_success(msg: str) -> None:
        success_messages.append(msg)

    monkeypatch.setattr(
        "hephaistos.app.commands.select_option",
        fake_select_option,
    )
    monkeypatch.setattr("hephaistos.app.commands.current_theme_name", lambda: "forge")
    monkeypatch.setattr(
        "hephaistos.app.commands.save_setting",
        fake_save_setting,
    )
    monkeypatch.setattr(
        "hephaistos.app.commands.set_theme",
        fake_set_theme,
    )
    monkeypatch.setattr(
        "hephaistos.app.commands.print_success",
        fake_print_success,
    )

    SettingsCommand()._appearance_menu()  # type: ignore[reportPrivateUsage]

    assert save_calls == [("theme", "light")]
    assert theme_calls == ["light"]
    assert success_messages == []


def test_bottom_toolbar_shows_compact_status(tmp_path: Path) -> None:
    session = _make_session(tmp_path)

    status = shell._build_bottom_toolbar_status(session)  # type: ignore[reportPrivateUsage]

    assert "alt+enter newline" in status
    assert "/help commands" in status
    assert "/settings prefs" in status
    assert "! shell" in status
    assert "·" not in status
    assert "context" not in status
    assert "source" not in status


def test_bottom_toolbar_shows_busy_hint(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    runtime = shell.ShellRuntime(busy=True, steering_count=2)

    status = shell._build_bottom_toolbar_status(session, runtime)  # type: ignore[reportPrivateUsage]

    assert "assistant working" in status
    assert "enter queues follow-up" in status
    assert "queued 2" in status
    assert "·" not in status


def test_shell_style_overrides_default_reversed_toolbar() -> None:
    palette.set_theme("forge")
    style_rules = shell.shell_style_dict()  # type: ignore[reportPrivateUsage]

    assert style_rules["composer"] == "bg:#1C1C1C fg:#E0E0E0"
    assert style_rules["prompt-mark"] == "bold #C8C8C8"
    assert "frame" not in style_rules
    assert "frame.border" not in style_rules

    merged = merge_styles([default_ui_style(), Style.from_dict(style_rules)])
    for style_name, expected_fg in (
        ("bottom-toolbar", "808080"),
        ("bottom-toolbar.text", "808080"),
        ("toolbar-location", "E0E0E0"),
        ("toolbar-accent", "E0E0E0"),
        ("toolbar-error", "CC3333"),
    ):
        attrs = merged.get_attrs_for_style_str(f"class:{style_name}")
        assert attrs.bgcolor == "1C1C1C", f"{style_name} bgcolor mismatch"
        assert attrs.color == expected_fg, f"{style_name} fg mismatch"
        assert attrs.reverse is False, f"{style_name} should have reverse disabled"


def test_complete_keybinding_starts_and_cycles_completions() -> None:
    bindings = shell._build_keybindings(shell.DEFAULT_SHELL_KEYBINDINGS)  # type: ignore[reportPrivateUsage]
    complete_binding = next(
        binding
        for binding in bindings.bindings
        if tuple(str(key) for key in binding.keys) == ("Keys.ControlI",)
    )

    class _FakeBuffer:
        def __init__(self) -> None:
            self.complete_state: object | None = None
            self.start_calls: list[bool] = []
            self.next_calls = 0

        def start_completion(self, *, select_first: bool = False) -> None:
            self.start_calls.append(select_first)

        def complete_next(self) -> None:
            self.next_calls += 1

    fake_buffer = _FakeBuffer()
    event = SimpleNamespace(current_buffer=fake_buffer)
    key_event = cast("KeyPressEvent", event)

    complete_binding.handler(key_event)

    assert fake_buffer.start_calls == [False]

    fake_buffer.complete_state = object()
    complete_binding.handler(key_event)

    assert fake_buffer.next_calls == 1


def test_shell_layout_includes_completion_menu() -> None:
    input_buffer = Buffer(name="input")

    layout = shell._build_shell_layout(  # type: ignore[reportPrivateUsage]
        input_buffer,
        get_header=lambda: FormattedText([]),
        get_chat=lambda: FormattedText([]),
        get_status=lambda: FormattedText([]),
    )

    assert isinstance(layout.container, FloatContainer)
    assert any(
        isinstance(float_item.content, CompletionsMenu) for float_item in layout.container.floats
    )


def test_shell_layout_wraps_and_grows_composer() -> None:
    input_buffer = Buffer(name="input")

    layout = shell._build_shell_layout(  # type: ignore[reportPrivateUsage]
        input_buffer,
        get_header=lambda: FormattedText([]),
        get_chat=lambda: FormattedText([]),
        get_status=lambda: FormattedText([]),
    )
    assert isinstance(layout.container, FloatContainer)
    content = layout.container.content
    assert isinstance(content, HSplit)
    composer = next(
        cast("Window", window)
        for window in content.children
        if isinstance(cast("Window", window).content, BufferControl)
    )

    assert composer.wrap_lines()
    get_height = cast("Callable[[], Dimension]", composer.height)
    height = get_height()
    assert isinstance(height, Dimension)
    assert height.min == 2
    assert height.preferred == 2
    assert height.max == 8

    input_buffer.text = "x" * 200
    grown_height = get_height()

    assert isinstance(grown_height, Dimension)
    assert grown_height.preferred > 2
    assert grown_height.max == 8


def test_slash_completer_suggests_provider_subcommands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        shell.ProviderConfig,
        "load",
        classmethod(lambda cls: _default_config()),  # type: ignore[reportPrivateUsage, reportUnknownLambdaType]
    )
    completer = shell.SlashCommandCompleter()

    completions = list(completer.get_completions(Document("/provider u"), CompleteEvent()))

    assert any(completion.text == "use " for completion in completions)

    completions = list(completer.get_completions(Document("/provider use za"), CompleteEvent()))

    assert any(completion.text == "zai " for completion in completions)


def test_slash_completer_matches_command_aliases() -> None:
    completer = shell.SlashCommandCompleter()

    completions = list(completer.get_completions(Document("/qui"), CompleteEvent()))

    assert any(completion.text == "quit " for completion in completions)


def test_shell_intro_uses_compact_header(capsys: pytest.CaptureFixture[str]) -> None:
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
    assert "/settings" in out
    assert "/armory" in out
    assert "configure api" in out
    assert "alt+enter" not in out


# ---------------------------------------------------------------------------
# Cancellation / back-navigation tests
# ---------------------------------------------------------------------------


def test_prompt_path_returns_none_on_q(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "q")
    result = workspace._prompt_path("Path", "/default")  # type: ignore[reportPrivateUsage]
    assert result is None


def test_prompt_path_returns_none_on_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "cancel")
    result = workspace._prompt_path("Path", "/default")  # type: ignore[reportPrivateUsage]
    assert result is None


def test_prompt_path_returns_none_on_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "back")
    result = workspace._prompt_path("Path", "/default")  # type: ignore[reportPrivateUsage]
    assert result is None


def test_prompt_path_returns_default_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "")
    result = workspace._prompt_path("Path", "/default")  # type: ignore[reportPrivateUsage]
    assert result == "/default"


def test_prompt_path_returns_value_when_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "/my/path")
    result = workspace._prompt_path("Path", "/default")  # type: ignore[reportPrivateUsage]
    assert result == "/my/path"


def test_prompt_path_returns_none_on_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("hephaistos.app.workspace.direct_input", _raise)
    result = workspace._prompt_path("Path", "/default")  # type: ignore[reportPrivateUsage]
    assert result is None


def test_prompt_path_returns_none_on_eof(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("hephaistos.app.workspace.direct_input", _raise)
    result = workspace._prompt_path("Path", "/default")  # type: ignore[reportPrivateUsage]
    assert result is None


def test_open_armory_cancelled_returns_session_unchanged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr(
        "hephaistos.app.workspace.browse_directory",
        lambda *_, **_kw: None,  # type: ignore[reportUnknownLambdaType]
    )
    new_session = workspace._open_armory(session)  # type: ignore[reportPrivateUsage]

    assert new_session is session
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_create_armory_cancelled_returns_session_unchanged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr(
        "hephaistos.app.workspace.browse_directory",
        lambda *_, **_kw: None,  # type: ignore[reportUnknownLambdaType]
    )
    new_session = workspace._create_armory(session)  # type: ignore[reportPrivateUsage]

    assert new_session is session
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_handle_armory_command_detaches_armory(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr(
        workspace,
        "select_option",
        lambda *_args, **_kwargs: 2,  # type: ignore[reportUnknownLambdaType]
    )
    new_session = workspace._handle_armory_command(session)  # type: ignore[reportPrivateUsage]

    assert new_session is not session
    assert new_session.armory_path is None
    assert new_session.source_file_count == 0
    out = capsys.readouterr().out
    assert "Detached armory. Plain chat mode." in out


def test_prompt_armory_for_sessions_cancelled_returns_none(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    session = _make_session(tmp_path)

    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "q")
    result = workspace._prompt_armory_for_sessions(session)  # type: ignore[reportPrivateUsage]

    assert result is None
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_resume_saved_chat_cancelled_returns_session_unchanged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    session = create_plain_session(_test_config())

    # Cancel at the path prompt
    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "q")
    new_session = workspace._resume_saved_chat(session)  # type: ignore[reportPrivateUsage]

    assert new_session is session
    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_list_saved_chats_cancelled_returns_early(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    session = create_plain_session(_test_config())

    # Cancel at the path prompt
    monkeypatch.setattr("hephaistos.app.workspace.direct_input", lambda _prompt="": "q")
    workspace._list_saved_chats(session)  # type: ignore[reportPrivateUsage]

    out = capsys.readouterr().out
    assert "Cancelled" in out


def test_list_saved_chats_uses_active_armory_without_prompt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    session = _make_session(tmp_path)
    assert session.armory_path is not None

    conv = Conversation()
    conv.add("system", "sys")
    conv.add("user", "saved question")
    chat_storage.save(session.armory_path, "saved12345678", conv, title="Saved Chat")

    def fail_prompt(_prompt: str = "") -> str:
        raise AssertionError("active armory should not prompt for a path")

    monkeypatch.setattr("hephaistos.app.workspace.direct_input", fail_prompt)

    workspace._list_saved_chats(session)  # type: ignore[reportPrivateUsage]

    out = capsys.readouterr().out
    assert "Saved chats for" in out
    assert "saved12345678" in out
    assert "Saved Chat" in out


def test_resume_saved_chat_accepts_unique_id_prefix(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    session = _make_session(tmp_path)
    assert session.armory_path is not None

    conv = Conversation()
    conv.add("system", "sys")
    conv.add("user", "saved question")
    chat_storage.save(session.armory_path, "abcdef123456", conv, title="Saved Chat")

    def fail_prompt(_prompt: str = "") -> str:
        raise AssertionError("active armory should not prompt for a path")

    monkeypatch.setattr("hephaistos.app.workspace.direct_input", fail_prompt)

    resumed = workspace._resume_saved_chat(session, "abc")  # type: ignore[reportPrivateUsage]

    out = capsys.readouterr().out
    assert resumed is not session
    assert resumed.session_id == "abcdef123456"
    assert "Resumed session abcdef123456" in out


def test_resume_saved_chat_reports_ambiguous_id_prefix(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    session = _make_session(tmp_path)
    assert session.armory_path is not None

    conv = Conversation()
    conv.add("system", "sys")
    conv.add("user", "saved question")
    chat_storage.save(session.armory_path, "abc111222333", conv, title="First")
    chat_storage.save(session.armory_path, "abc999888777", conv, title="Second")

    resumed = workspace._resume_saved_chat(session, "abc")  # type: ignore[reportPrivateUsage]

    out = capsys.readouterr().out
    assert resumed is session
    assert "Multiple saved chats match 'abc'" in out
    assert "abc111222333" in out
    assert "abc999888777" in out


def test_format_shell_header_includes_core_metadata() -> None:
    fragments = format_shell_header(
        version="0.0.0-test",
        armory_path="/home/user/armory",
        source_file_count=3,
        source_files=("source/a.md", "source/b.md", "library/c.md"),
        model="gpt-4o-mini",
        has_api_key=True,
    )

    text = "".join(frag[1] for frag in fragments)
    assert "Hephaistos" in text
    assert "v0.0.0-test" in text
    assert "/home/user/armory" in text
    assert "gpt-4o-mini" in text
    assert "configured" in text
    assert "source/a.md, source/b.md, library/c.md" in text
    assert "alt+enter" not in text
    assert "newline" not in text

    styles = {style for style, _ in fragments if style}
    assert "class:header.title" in styles
    assert ("class:header.configured", "gpt-4o-mini") in fragments
    assert "class:header.success" in styles


def test_format_shell_header_marks_missing_model_armory_and_sources() -> None:
    fragments = format_shell_header(
        version="0.0.0-test",
        armory_path="none",
        source_file_count=0,
        model="",
        has_api_key=True,
    )

    assert ("class:header.ember", "none") in fragments
    assert fragments.count(("class:header.ember", "none")) == 3


def test_format_shell_header_warns_when_api_key_missing() -> None:
    fragments = format_shell_header(
        version="0.0.0-test",
        armory_path="none",
        source_file_count=0,
        model="gpt-4o-mini",
        has_api_key=False,
    )

    text = "".join(frag[1] for frag in fragments)
    styles = {style for style, _ in fragments if style}
    assert "missing" in text
    assert "/api key <your-key>" in text
    assert "class:header.error" in styles
    assert "class:header.warning" in styles


def test_chat_writer_appends_styled_fragments() -> None:
    chat_lines: list[tuple[str, str]] = []
    calls = {"invalidate": 0}

    class FakeApp:
        def invalidate(self) -> None:
            calls["invalidate"] += 1

    writer = shell._ChatWriter(chat_lines, FakeApp())  # type: ignore[reportPrivateUsage]
    written = writer.write("hello ")
    writer.write("world")

    assert written == len("hello ")
    assert chat_lines == [
        ("class:chat-area.system", "hello "),
        ("class:chat-area.system", "world"),
    ]
    assert calls["invalidate"] == 2


def test_capture_to_chat_redirects_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    chat_lines: list[tuple[str, str]] = []

    class FakeApp:
        def invalidate(self) -> None:
            return

    with shell._capture_to_chat(chat_lines, FakeApp()):  # type: ignore[reportPrivateUsage]
        print("captured-line")

    joined = "".join(text for _, text in chat_lines)
    assert "captured-line" in joined


def test_run_shell_command_captured_routes_stdout_and_stderr() -> None:
    chat_lines: list[tuple[str, str]] = []

    class FakeApp:
        def invalidate(self) -> None:
            return

    shell._run_shell_command_captured(  # type: ignore[reportPrivateUsage]
        "printf hello; printf err 1>&2",
        chat_lines,
        FakeApp(),
    )

    styles = [style for style, _ in chat_lines]
    texts = [text for _, text in chat_lines]
    assert any(style == "class:chat-area.system" for style in styles)
    assert any("hello" in text for text in texts)
    assert any("err" in text for text in texts)
