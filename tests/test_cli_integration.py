from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

import pytest

import hephaistos.app.cli as app_cli
from hephaistos.agent.dispatch import iter_agent_events
from hephaistos.app.cli import build_parser, run_argv
from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.events import TurnCompleteEvent
from hephaistos.chat.session import create_session
from hephaistos.rag.index import load_or_build
from hephaistos.tui import TuiDependencyError


class _FakeTTY(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_parser_includes_expected_top_level_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "armory" in help_text
    assert "start           " not in help_text
    assert "shell           " not in help_text
    assert "chat" not in help_text
    assert "source" in help_text
    assert "tui" in help_text
    assert "parameters" not in help_text


def test_top_level_help_is_compact_and_points_to_interactive_help() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert " [options] [command] [path]" in help_text
    assert help_text.startswith("Usage:")
    assert "Examples:" in help_text
    assert "Essential commands:" in help_text
    assert "Options:" in help_text
    assert "Inside Hephaistos, type /help" in help_text
    assert "positional arguments:" not in help_text


def test_run_argv_dispatches_armory_init(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()
    armory_path = tmp_path / "integration-armory"

    run_argv(parser, ["armory", "init", str(armory_path)])

    out = capsys.readouterr().out
    assert "Initialized armory at" in out
    assert armory_path.is_dir()


def test_main_without_args_uses_tui(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_tui(path: Path | None) -> None:
        nonlocal called
        called = True
        assert path is None

    monkeypatch.setattr(app_cli.sys, "argv", ["heph"])
    monkeypatch.setattr(app_cli.sys, "stdin", _FakeTTY(True))
    monkeypatch.setattr(app_cli.sys, "stdout", _FakeTTY(True))

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        app_cli.main()

    assert called


def test_main_without_args_uses_tui_on_non_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_tui(path: Path | None) -> None:
        nonlocal called
        called = True
        assert path is None

    monkeypatch.setattr(app_cli.sys, "argv", ["heph"])
    monkeypatch.setattr(app_cli.sys, "stdin", _FakeTTY(False))
    monkeypatch.setattr(app_cli.sys, "stdout", _FakeTTY(False))

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        app_cli.main()

    assert called


def test_start_command_launches_tui_without_path() -> None:
    parser = build_parser()
    called = False

    def fake_tui(path: Path | None) -> None:
        nonlocal called
        called = True
        assert path is None

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        run_argv(parser, ["start"])

    assert called


def test_start_command_with_path_launches_tui_with_path(
    tmp_path: Path,
) -> None:
    parser = build_parser()
    armory_path = tmp_path / "integration-armory"
    run_argv(parser, ["armory", "init", str(armory_path)])
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        run_argv(parser, ["start", str(armory_path)])

    assert captured_path == armory_path


def test_bare_path_dispatches_tui(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(app_cli.sys, "argv", ["heph", str(tmp_path)])

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        app_cli.main()

    assert captured_path == tmp_path


def test_tui_command_dispatches_with_path() -> None:
    parser = build_parser()
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        run_argv(parser, ["tui", "notes"])

    assert captured_path == Path("notes")


def test_tui_flag_alias_dispatches_tui(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_path: Path | None = Path("unset")

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(app_cli.sys, "argv", ["heph", "--tui"])

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        app_cli.main()

    assert captured_path is None


def test_tui_flag_alias_help(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(app_cli.sys, "argv", ["heph", "--tui", "help"])

    with pytest.raises(SystemExit) as exc_info:
        app_cli.main()

    assert exc_info.value.code == 0
    assert "usage: heph tui" in capsys.readouterr().out


def test_chat_ask_dispatches_without_tui(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    captured: tuple[str, list[str]] | None = None

    def fake_ask(args: object) -> None:
        nonlocal captured
        captured = (args.path, args.prompt)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]

    monkeypatch.setattr("hephaistos.chat.cli._cmd_chat_ask", fake_ask)

    run_argv(parser, ["chat", "ask", "notes", "what", "is", "rag?"])

    assert captured == ("notes", ["what", "is", "rag?"])


def test_tui_command_reports_missing_dependency(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    def fake_tui(_path: Path | None) -> None:
        raise TuiDependencyError("missing textual")

    with (
        patch("hephaistos.tui.run_tui_for_path", fake_tui),
        pytest.raises(SystemExit) as exc_info,
    ):
        run_argv(parser, ["tui"])

    assert exc_info.value.code == 2
    assert "missing textual" in capsys.readouterr().err


def test_golden_path_init_source_index_dry_run(tmp_path: Path) -> None:
    """Golden-path smoke test: init armory -> add source -> index -> dry-run chat."""
    # Step 1: Init armory
    armory_path = tmp_path / "golden-armory"
    initialize(armory_path)
    assert (armory_path / ".hephaistos" / "armory.toml").is_file()

    # Step 2: Add material documents
    source_dir = armory_path / "materials"
    (source_dir / "basics.md").write_text(
        "# Basics\n\nPython is a programming language.\n\nVariables store values.\n",
        encoding="utf-8",
    )
    (source_dir / "advanced.md").write_text(
        "# Advanced\n\nDecorators wrap functions.\n\nGenerators yield values lazily.\n",
        encoding="utf-8",
    )

    # Step 3: Build index
    index = load_or_build(armory_path)
    assert index.chunk_count > 0
    assert (armory_path / ".hephaistos" / "rag_index.json").is_file()

    # Step 4: Create session with armory
    config = ChatConfig(base_url="https://api.example.invalid", model="test-model")
    session = create_session(config, armory_path)
    assert session.armory_path == armory_path
    assert session.source_file_count >= 2

    # Step 5: Dry-run agent loop (no LLM calls needed)
    events = list(
        iter_agent_events(
            config,
            session.conversation,
            armory_path,
            dry_run=True,
        )
    )

    assert len(events) >= 2
    assert events[0].kind == "notice"
    assert isinstance(events[-1], TurnCompleteEvent)
    assert events[-1].finish_reason == "dry_run"
    assert events[-1].tokens_remaining > 0


# --- _inject_default_subcommand tests ---


def test_inject_default_subcommand_empty_args() -> None:
    """No args at all → inject 'tui'."""
    result = app_cli._inject_default_subcommand([], {"armory", "tui", "source"})  # type: ignore[reportPrivateUsage]
    assert result == ["tui"]


def test_inject_default_subcommand_bare_path() -> None:
    """A bare path that isn't a known command → inject 'tui' before it."""
    result = app_cli._inject_default_subcommand(  # type: ignore[reportPrivateUsage]
        ["/tmp/my-armory"],
        {"armory", "tui", "source"},
    )
    assert result == ["tui", "/tmp/my-armory"]


def test_inject_default_subcommand_flags_before_path() -> None:
    """Flags before the path are skipped, 'tui' injected before the path."""
    result = app_cli._inject_default_subcommand(  # type: ignore[reportPrivateUsage]
        ["--profile", "/tmp/armory"],
        {"armory", "tui", "source"},
    )
    assert result == ["--profile", "tui", "/tmp/armory"]


def test_inject_default_subcommand_known_command_unchanged() -> None:
    """A known subcommand is left unchanged — argparse handles it."""
    result = app_cli._inject_default_subcommand(  # type: ignore[reportPrivateUsage]
        ["armory", "init", "/tmp/armory"],
        {"armory", "tui", "source"},
    )
    assert result == ["armory", "init", "/tmp/armory"]


def test_inject_default_subcommand_flags_only() -> None:
    """Only flags, no positional → return unchanged (argparse will show help or error)."""
    result = app_cli._inject_default_subcommand(  # type: ignore[reportPrivateUsage]
        ["--version"],
        {"armory", "tui", "source"},
    )
    assert result == ["--version"]


def test_inject_default_subcommand_relative_path() -> None:
    """Relative paths that aren't known commands get 'tui' injected."""
    result = app_cli._inject_default_subcommand(  # type: ignore[reportPrivateUsage]
        ["./my-armory"],
        {"armory", "tui", "source"},
    )
    assert result == ["tui", "./my-armory"]


# --- End-to-end path argument tests ---


def test_main_with_path_and_profile_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`heph --profile /path` should inject tui and pass path through."""
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(app_cli.sys, "argv", ["heph", "--profile", str(tmp_path)])

    # Stub profiling to avoid actual cProfile/pstats work
    def _noop_report(_prof: object) -> None:
        pass

    monkeypatch.setitem(app_cli.main.__globals__, "_report_profile", _noop_report)

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        app_cli.main()

    assert captured_path == tmp_path


def test_bare_path_with_nonexistent_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """`heph /nonexistent/path` should still inject tui and pass path."""
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(app_cli.sys, "argv", ["heph", "/nonexistent/path"])

    with patch("hephaistos.tui.run_tui_for_path", fake_tui):
        app_cli.main()

    assert captured_path == Path("/nonexistent/path")
