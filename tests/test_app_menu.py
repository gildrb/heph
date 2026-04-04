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
