from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.app import menu
from hephaistos.app.menu import MenuOption


def test_select_option_uses_prompt_fallback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "2")

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


def test_select_option_returns_none_for_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "q")

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
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "1")

    result = menu.confirm("Proceed?")
    assert result is True


def test_confirm_no(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "2")

    result = menu.confirm("Proceed?")
    assert result is False


def test_confirm_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "q")

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
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "/exit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_slash_quit_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "/quit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_slash_q_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "/q")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_exit_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bare 'exit' still works (pre-existing behavior)."""
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "exit")

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_keyboard_interrupt_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("hephaistos.terminal.direct_input", _raise)

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


def test_select_option_eof_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("hephaistos.terminal.direct_input", _raise)

    selected = menu.select_option(
        "Armory",
        [MenuOption("Open existing armory", "Attach a workspace.")],
    )
    assert selected is None


# ---------------------------------------------------------------------------
# Directory browser
# ---------------------------------------------------------------------------


def test_browse_directory_choose_current(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = iter(["c"])

    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": next(calls))

    result = menu.browse_directory("Test Browser", tmp_path)
    assert result == tmp_path


def test_browse_directory_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": "q")

    result = menu.browse_directory("Test Browser", Path("/tmp"))
    assert result is None


def test_browse_directory_navigate_parent_and_cancel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    child = tmp_path / "subdir"
    child.mkdir()
    calls = iter(["1", "c"])
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": next(calls))

    result = menu.browse_directory("Test", child)
    assert result == tmp_path


def test_browse_directory_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _raise(_: str = "") -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("hephaistos.terminal.direct_input", _raise)

    result = menu.browse_directory("Test", tmp_path)
    assert result is None


def test_browse_directory_eof(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def _raise(_: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("hephaistos.terminal.direct_input", _raise)

    result = menu.browse_directory("Test", tmp_path)
    assert result is None


def test_browse_directory_defaults_to_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = iter(["c"])
    monkeypatch.setattr("hephaistos.terminal.direct_input", lambda _prompt="": next(calls))
    monkeypatch.setattr("hephaistos.app.menu.browse_directory", menu.browse_directory)

    result = menu.browse_directory("Test")
    assert result == Path.home()
