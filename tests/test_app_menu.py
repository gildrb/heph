from __future__ import annotations

from hephaistos.app import menu
from hephaistos.app.menu import MenuOption


def test_select_option_uses_prompt_fallback(monkeypatch, capsys) -> None:
    monkeypatch.setattr(menu.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(menu.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")

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


def test_select_option_returns_none_for_cancel(monkeypatch) -> None:
    monkeypatch.setattr(menu.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(menu.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")

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


def test_confirm_yes(monkeypatch) -> None:
    monkeypatch.setattr(menu.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(menu.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

    result = menu.confirm("Proceed?")
    assert result is True


def test_confirm_no(monkeypatch) -> None:
    monkeypatch.setattr(menu.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(menu.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")

    result = menu.confirm("Proceed?")
    assert result is False


def test_confirm_cancel(monkeypatch) -> None:
    monkeypatch.setattr(menu.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(menu.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")

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
