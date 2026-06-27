from __future__ import annotations

import interfaces.terminal as menu
import pytest
from interfaces.terminal import MenuOption


def test_select_option_uses_prompt_fallback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "2")

    selected = menu.select_option(
        "Armory",
        [
            MenuOption("Open existing armory", "Attach a workspace."),
            MenuOption("Create new armory", "Initialize a workspace."),
        ],
    )

    out = capsys.readouterr().out
    assert selected == 1
    assert "MENU armory" in out
    assert "1." in out
    assert "2." in out
    assert "q." in out
    assert "CANCEL" in out
    assert "Open existing armory" in out
    assert "Create new armory" in out
    assert " cancel" not in out


def test_select_option_prints_current_state_marker(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "q")

    selected = menu.select_option(
        "Model",
        [
            MenuOption("gpt-5.5", is_current=True),
            MenuOption("local", "installed"),
        ],
    )

    out = capsys.readouterr().out
    assert selected is None
    assert "STATE current" in out


def test_select_option_reports_invalid_choice_as_label_value_state(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    choices = iter(("wat", "q"))
    prompts: list[str] = []

    def read_choice(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(choices)

    monkeypatch.setattr("interfaces.terminal.direct_input", read_choice)

    selected = menu.select_option("Model", [MenuOption("gpt-5.5")])

    out = capsys.readouterr().out
    assert selected is None
    assert "STATE unknown option" in out
    assert prompts == ["\n  SELECT > ", "\n  SELECT > "]


def test_select_option_returns_none_for_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "q")

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
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "1")

    result = menu.confirm("Proceed?")
    assert result is True


def test_confirm_no(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "2")

    result = menu.confirm("Proceed?")
    assert result is False


def test_confirm_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "q")

    result = menu.confirm("Proceed?")
    assert result is False


def test_menu_option_dataclass() -> None:
    """Verify MenuOption fields work correctly."""
    opt = MenuOption(label="Open", description="Open a file", is_current=True)
    assert opt.label == "Open"
    assert opt.description == "Open a file"
    assert opt.is_current is True

    # Frozen - cannot reassign
    try:
        opt.label = "Changed"  # ty:ignore[invalid-assignment]
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
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "/exit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_slash_quit_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "/quit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_slash_q_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "/q")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_exit_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bare 'exit' still works (pre-existing behavior)."""
    monkeypatch.setattr("interfaces.terminal.direct_input", lambda _prompt="": "exit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_keyboard_interrupt_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("interfaces.terminal.direct_input", _raise)

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_eof_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("interfaces.terminal.direct_input", _raise)

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None
