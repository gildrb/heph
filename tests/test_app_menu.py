from __future__ import annotations

import pytest
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from hephaistos.app import menu
from hephaistos.app.keybindings import DEFAULT_MENU_KEYBINDINGS
from hephaistos.app.menu import MenuOption


def _select_interactively(keys: str, options: list[MenuOption]) -> int | None:
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(keys)
        return menu._select_with_prompt_toolkit(  # type: ignore[reportPrivateUsage]
            "Armory",
            options,
            DEFAULT_MENU_KEYBINDINGS,
            input_obj=pipe_input,
            output_obj=DummyOutput(),
        )


def test_select_option_uses_prompt_fallback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "2")

    selected = menu.select_option(
        "Armory",
        [
            MenuOption("Open existing armory", "Attach a workspace."),
            MenuOption("Create new armory", "Initialize a workspace."),
        ],
    )

    out = capsys.readouterr().out
    assert selected == 1
    assert "Open existing armory" in out
    assert "Create new armory" in out


def test_prompt_toolkit_menu_uses_down_arrow_to_select_next_option() -> None:
    selected = _select_interactively(
        "\x1b[B\r",
        [
            MenuOption("Open existing armory", "Attach a workspace."),
            MenuOption("Create new armory", "Initialize a workspace."),
        ],
    )

    assert selected == 1


def test_prompt_toolkit_menu_uses_up_arrow_to_wrap_to_last_option() -> None:
    selected = _select_interactively(
        "\x1b[A\r",
        [
            MenuOption("Open existing armory", "Attach a workspace."),
            MenuOption("Create new armory", "Initialize a workspace."),
        ],
    )

    assert selected == 1


def test_prompt_toolkit_menu_starts_on_current_option() -> None:
    selected = _select_interactively(
        "\r",
        [
            MenuOption("Open existing armory", "Attach a workspace."),
            MenuOption("Create new armory", "Initialize a workspace.", is_current=True),
        ],
    )

    assert selected == 1


def test_prompt_toolkit_menu_q_cancels() -> None:
    selected = _select_interactively(
        "q",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )

    assert selected is None


def test_select_option_returns_none_for_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "q")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )

    assert selected is None


def test_menu_option_default_description() -> None:
    opt = MenuOption("test")
    assert opt.label == "test"
    assert opt.description == ""
    assert opt.is_current is False


def test_menu_option_with_current_marker() -> None:
    opt = MenuOption("test", "desc", is_current=True)
    assert opt.is_current is True


def test_select_option_empty_list() -> None:
    result = menu.select_option("Empty", [])
    assert result is None


def test_confirm_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "1")

    result = menu.confirm("Proceed?")
    assert result is True


def test_confirm_no(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "2")

    result = menu.confirm("Proceed?")
    assert result is False


def test_confirm_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "q")

    result = menu.confirm("Proceed?")
    assert result is False


def test_menu_option_dataclass() -> None:
    """Verify MenuOption fields work correctly."""
    opt = MenuOption(label="Open", description="Open a file", is_current=True)
    assert opt.label == "Open"
    assert opt.description == "Open a file"
    assert opt.is_current is True

    # Frozen — cannot reassign
    try:
        opt.label = "Changed"  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except AttributeError:
        pass

    # Defaults
    opt2 = MenuOption(label="Test")
    assert opt2.description == ""
    assert opt2.is_current is False


# ---------------------------------------------------------------------------
# Slash-prefixed exit commands
# ---------------------------------------------------------------------------


def test_select_option_slash_exit_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "/exit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_slash_quit_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "/quit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_slash_q_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "/q")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_exit_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bare 'exit' still works (pre-existing behavior)."""
    monkeypatch.setattr("hephaistos.app.menu.direct_input", lambda _prompt="": "exit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_keyboard_interrupt_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("hephaistos.app.menu.direct_input", _raise)

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_eof_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("hephaistos.app.menu.direct_input", _raise)

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None
