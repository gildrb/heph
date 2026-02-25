from __future__ import annotations

from pathlib import Path

from hephaistos.app.cli import build_parser, run_argv


def test_parser_includes_expected_top_level_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "armory" in help_text
    assert "source" not in help_text
    assert "chat" not in help_text
    assert "parameters" not in help_text


def test_run_argv_dispatches_armory_init(tmp_path: Path, capsys) -> None:
    parser = build_parser()
    armory_path = tmp_path / "integration-armory"

    run_argv(parser, ["armory", "init", str(armory_path)])

    out = capsys.readouterr().out
    assert "Initialized armory at" in out
    assert armory_path.is_dir()
