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


def test_matches_filter() -> None:
    opt = MenuOption("Claude Opus", "Fast reasoning model")
    assert menu._matches_filter(opt, "claude")
    assert menu._matches_filter(opt, "OPUS")
    assert menu._matches_filter(opt, "fast")
    assert not menu._matches_filter(opt, "gemini")


def test_matches_filter_empty() -> None:
    opt = MenuOption("Test", "Desc")
    assert menu._matches_filter(opt, "")
    assert menu._matches_filter(opt, "test")
