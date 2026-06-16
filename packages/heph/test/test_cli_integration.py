from __future__ import annotations

import io
import json
import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import heph
import hephaion.rag.health as rag_health
import pytest
from ai.providers.llama_cpp import LlamaCppCandidate, LlamaCppModelRecord
from ai.runtime import ChatConfig
from heph.cli.main import _inject_default_subcommand, build_parser, run_argv
from heph.cli.main import main as cli_main
from heph.cli.main import sys as cli_sys
from hephaion.agent.dispatch import iter_agent_events
from hephaion.armory.search import remember_armory
from hephaion.armory.storage import initialize
from hephaion.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    TurnCompleteEvent,
)
from hephaion.chat.session import create_session
from hephaion.rag.health import ExtractionHealthIssue, ExtractionHealthReport
from hephaion.rag.index import load_or_build
from interfaces.tui import TuiDependencyError

from hephaion.chat import cli as chat_cli

cli_main_module = sys.modules[cli_main.__module__]


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
    assert "index" in help_text
    assert "health" in help_text
    assert "update" in help_text
    assert "sdk" in help_text
    assert "start           " not in help_text
    assert "shell           " not in help_text
    assert "Chat with an LLM" not in help_text
    assert "materials" in help_text
    assert "source" not in help_text
    assert "tui" not in help_text
    assert "parameters" not in help_text


def test_cli_version_uses_public_package_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])

    assert exc.value.code == 0
    assert f"heph {heph.__version__}" in capsys.readouterr().out


def test_update_command_is_not_treated_as_armory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    run_argv(parser, ["update"])

    out = capsys.readouterr().out
    assert "Heph update" in out
    assert "uv tool upgrade heph" in out


def test_project_root_resolves_workspace_checkout() -> None:
    root = cli_main_module._project_root()

    assert cli_main_module._is_source_checkout(root)
    assert (root / "packages" / "heph" / "src" / "heph").is_dir()
    assert (root / "packages" / "hephaion" / "src" / "hephaion").is_dir()


def test_source_runtime_reexecs_repo_venv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "Heph"
    venv_bin = root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_heph = venv_bin / "heph"
    venv_heph.write_text("#!/bin/sh\n", encoding="utf-8")
    captured: tuple[str, list[str], dict[str, str]] | None = None

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> None:
        nonlocal captured
        captured = (path, argv, env)
        raise SystemExit(42)

    monkeypatch.setattr(cli_main_module, "_project_root", lambda: root)
    monkeypatch.setattr(cli_main_module, "_is_source_checkout", lambda _root: True)
    monkeypatch.setattr(cli_main_module, "_docling_available", lambda: False)
    monkeypatch.setattr(cli_main_module.sys, "executable", "/Library/Python/bin/python3")
    monkeypatch.setattr(cli_main_module.sys, "argv", ["heph", "update"])
    monkeypatch.setattr(cli_main_module.os, "execve", fake_execve)

    with pytest.raises(SystemExit) as exc_info:
        cli_main_module._maybe_reexec_source_venv()

    assert exc_info.value.code == 42
    assert captured is not None
    assert captured[0] == str(venv_heph)
    assert captured[1] == [str(venv_heph), "update"]
    assert captured[2]["HEPHAION_NO_VENV_REEXEC"] == "1"


def test_source_runtime_warning_when_repo_venv_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "Heph"
    monkeypatch.setattr(cli_main_module, "_project_root", lambda: root)
    monkeypatch.setattr(cli_main_module, "_is_source_checkout", lambda _root: True)
    monkeypatch.setattr(cli_main_module, "_docling_available", lambda: False)
    monkeypatch.setattr(cli_main_module.sys, "executable", "/Library/Python/bin/python3")

    messages = cli_main_module._runtime_diagnostic_messages()

    assert "missing document conversion support" in messages[0]
    assert any("/Library/Python/bin/python3" in message for message in messages)


def test_runtime_warning_when_installed_docling_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(cli_main_module, "_project_root", lambda: tmp_path)
    monkeypatch.setattr(cli_main_module, "_is_source_checkout", lambda _root: False)
    monkeypatch.setattr(cli_main_module, "_docling_available", lambda: False)
    monkeypatch.setattr(cli_main_module.sys, "executable", "/opt/heph/bin/python")

    messages = cli_main_module._runtime_diagnostic_messages()

    assert "missing document conversion support" in messages[0]
    assert any("PDF, DOCX, PPTX, and XLSX" in message for message in messages)


def test_source_runtime_reexec_can_be_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def fake_execve(_path: str, _argv: list[str], _env: dict[str, str]) -> None:
        nonlocal called
        called = True

    monkeypatch.setenv("HEPHAION_NO_VENV_REEXEC", "1")
    monkeypatch.setattr(cli_main_module, "_is_source_checkout", lambda _root: True)
    monkeypatch.setattr(cli_main_module, "_docling_available", lambda: False)
    monkeypatch.setattr(cli_main_module.os, "execve", fake_execve)

    cli_main_module._maybe_reexec_source_venv()

    assert not called


def test_top_level_help_is_compact_and_points_to_interactive_help() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert " [options] [command] [path]" in help_text
    assert help_text.startswith("Usage:")
    assert "Examples:" in help_text
    assert "Essential commands:" in help_text
    assert "Options:" in help_text
    assert "heph gdp" in help_text
    assert "cp notes.pdf" in help_text
    assert ".armories" in help_text
    assert "--profile" not in help_text
    assert "tracemalloc" not in help_text
    assert "Inside Heph, type /help" in help_text
    assert "/models" in help_text
    assert "/exam" in help_text
    assert "/priority" in help_text
    assert "/model," not in help_text
    assert "/study" not in help_text
    assert "positional arguments:" not in help_text


def test_run_argv_dispatches_armory_init(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    parser = build_parser()
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    armory_path = armory_home / "integration-armory"

    run_argv(parser, ["armory", "init", str(armory_path)])

    out = capsys.readouterr().out
    assert "Created armory" in out
    assert f"Add source files to: {armory_path / 'materials'}" in out
    assert f"Then start working with your documents: heph {armory_path.name}" in out
    assert "~/.armories/" in out
    assert armory_path.is_dir()


def test_top_level_index_defaults_to_current_armory(
    armory: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = build_parser()
    initialize(armory)
    (armory / "materials" / "notes.md").write_text("Hello from the material.", encoding="utf-8")
    monkeypatch.chdir(armory)

    run_argv(parser, ["index"])

    out = capsys.readouterr().out
    assert "Reading: materials/notes.md" in out
    assert "Writing:" in out
    assert "Indexed 4 documents" in out
    assert (armory / ".hephaion" / "rag_index.json").is_file()


def test_top_level_health_defaults_to_current_armory(
    armory: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = build_parser()
    initialize(armory)
    (armory / "materials" / "notes.md").write_text("Hello from the material.", encoding="utf-8")
    monkeypatch.chdir(armory)

    run_argv(parser, ["health"])

    out = capsys.readouterr().out
    assert "Extraction health:" in out
    assert "Corpus forbidden text: 100.0%" in out
    assert "No generic extraction poison found." in out


def test_top_level_health_exits_nonzero_for_extraction_noise(
    armory: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = build_parser()
    initialize(armory)
    (armory / "materials" / "notes.md").write_text("Clean source text.", encoding="utf-8")
    monkeypatch.chdir(armory)

    def fake_scan_extraction_health(_armory_path: Path) -> ExtractionHealthReport:
        return ExtractionHealthReport(
            armory_path=str(armory),
            documents=1,
            checks=1,
            pass_rate=0.0,
            forbidden_text=("ExtractionNoise",),
            issues=(
                ExtractionHealthIssue(
                    source="materials/notes.md",
                    forbidden_text_present=("ExtractionNoise",),
                ),
            ),
        )

    monkeypatch.setattr(rag_health, "scan_extraction_health", fake_scan_extraction_health)

    with pytest.raises(SystemExit) as exc_info:
        run_argv(parser, ["health"])

    out = capsys.readouterr().out
    assert exc_info.value.code == 1
    assert "Extraction issues:" in out
    assert "materials/notes.md" in out
    assert "ExtractionNoise" in out


def test_main_without_args_uses_tui(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_tui(path: Path | None) -> None:
        nonlocal called
        called = True
        assert path is None

    monkeypatch.setattr(cli_sys, "argv", ["heph"])
    monkeypatch.setattr(cli_sys, "stdin", _FakeTTY(True))
    monkeypatch.setattr(cli_sys, "stdout", _FakeTTY(True))

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert called


def test_main_without_args_uses_tui_on_non_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_tui(path: Path | None) -> None:
        nonlocal called
        called = True
        assert path is None

    monkeypatch.setattr(cli_sys, "argv", ["heph"])
    monkeypatch.setattr(cli_sys, "stdin", _FakeTTY(False))
    monkeypatch.setattr(cli_sys, "stdout", _FakeTTY(False))

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert called


def test_tui_command_launches_tui_without_path() -> None:
    parser = build_parser()
    called = False

    def fake_tui(path: Path | None) -> None:
        nonlocal called
        called = True
        assert path is None

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        run_argv(parser, ["tui"])

    assert called


def test_local_search_prints_installable_hf_ref(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    candidate = LlamaCppCandidate(
        repo_id="Qwen/Qwen3-4B-GGUF",
        filename="Qwen3-4B-Q4_K_M.gguf",
        quant="Q4_K_M",
        downloads=100,
        likes=20,
        size_bytes=2_497_280_256,
        display_name="Qwen3 4B",
        recommended_ram_gb=8,
        summary="official Qwen release",
    )

    def fake_search(query: str, *, limit: int) -> list[LlamaCppCandidate]:
        assert query == "qwen"
        assert limit == 1
        return [candidate]

    monkeypatch.setattr("ai.providers.llama_cpp.search_gguf_models", fake_search)

    run_argv(parser, ["local", "search", "--limit", "1", "qwen"])

    out = capsys.readouterr().out
    assert "Qwen3 4B" in out
    assert "install Qwen/Qwen3-4B-GGUF:Q4_K_M" in out


def test_local_status_prints_revalidatable_model_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()
    record = LlamaCppModelRecord(
        model_id="llama-cpp/Qwen/Qwen3-4B-GGUF:Q4_K_M",
        repo_id="Qwen/Qwen3-4B-GGUF",
        quant="Q4_K_M",
        tool_capable=True,
        endpoint="http://127.0.0.1:18123/v1",
    )

    monkeypatch.setattr("ai.providers.llama_cpp.current_server_state", lambda: None)
    monkeypatch.setattr("ai.providers.llama_cpp.installed_records", lambda: [record])

    run_argv(parser, ["local", "status"])

    out = capsys.readouterr().out
    assert "Qwen3 4B" in out
    assert "MODEL llama-cpp/Qwen/Qwen3-4B-GGUF:Q4_K_M" in out


def test_tui_command_with_path_launches_tui_with_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = build_parser()
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    armory_path = armory_home / "integration-armory"
    run_argv(parser, ["armory", "init", str(armory_path)])
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        run_argv(parser, ["tui", str(armory_path)])

    assert captured_path == armory_path


def test_bare_path_dispatches_tui(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(cli_sys, "argv", ["heph", str(tmp_path)])

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert captured_path == tmp_path


def test_tui_command_dispatches_with_path() -> None:
    parser = build_parser()
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        run_argv(parser, ["tui", "notes"])

    assert captured_path == Path("notes")


def test_bare_armory_name_dispatches_remembered_armory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    armory_path = armory_home / "gdp"
    initialize(armory_path)
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    remember_armory(armory_path)
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(cli_sys, "argv", ["heph", "gdp"])

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert captured_path == armory_path.resolve()


def test_bare_armory_name_dispatches_copied_armory_home_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    armory_path = armory_home / "copied"
    initialize(armory_path)
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    monkeypatch.setattr(cli_sys, "argv", ["heph", "copied"])

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert captured_path == armory_path.resolve()


def test_tui_flag_alias_dispatches_tui(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_path: Path | None = Path("unset")

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(cli_sys, "argv", ["heph", "--tui"])

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert captured_path is None


def test_tui_flag_alias_help(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_sys, "argv", ["heph", "--tui", "help"])

    with pytest.raises(SystemExit) as exc_info:
        cli_main()

    assert exc_info.value.code == 0
    assert "usage: heph tui" in capsys.readouterr().out


def test_chat_ask_dispatches_without_tui(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    captured: tuple[str, list[str], bool] | None = None

    def fake_ask(args: Namespace) -> None:
        nonlocal captured
        captured = (
            args.path,
            args.prompt,
            args.jsonl,
        )

    monkeypatch.setattr("hephaion.chat.cli._cmd_chat_ask", fake_ask)

    run_argv(parser, ["chat", "ask", "--jsonl", "notes", "what", "is", "rag?"])

    assert captured == ("notes", ["what", "is", "rag?"], True)


def test_chat_ask_jsonl_emits_structured_turn_events(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = tmp_path / "armory"
    initialize(armory)

    def fake_resolve(_path: str) -> object:
        return object()

    def fake_events(_session: object, prompt: str):
        assert prompt == "what is the material about"
        yield NoticeEvent("Reading enabled indexed materials.", code="reading")
        yield MaterialOperationEvent(
            "sample_overview",
            "Sampling corpus overview: 2 excerpts from 2 of 2 indexed sources.",
            metadata={
                "evidence_blocks": 2,
                "sampled_sources": 2,
                "total_sources": 2,
            },
        )
        yield NoticeEvent(
            "Using 2 overview evidence excerpts.",
            code="evidence",
            metadata={
                "refs": ["materials/a.md#chunk=0", "materials/b.md#chunk=0"],
                "coverage": {
                    "evidence_blocks": 2,
                    "sampled_sources": 2,
                    "total_sources": 2,
                },
                "items": [
                    {
                        "evidence_id": "E1",
                        "ref": "materials/a.md#chunk=0",
                        "text_excerpt": "Alpha source text.",
                    },
                    {
                        "evidence_id": "E2",
                        "ref": "materials/b.md#chunk=0",
                        "text_excerpt": "Beta source text.",
                    },
                ],
            },
        )
        yield NoticeEvent("Writing a grounded corpus overview.", code="writing")
        yield AssistantDeltaEvent("Retrieved overview sample: content [E1][E2].")
        yield TurnCompleteEvent(
            full_text="Retrieved overview sample: content [E1][E2].",
            turn_index=1,
            latency_ms=12.5,
            finish_reason="stop",
            tokens_remaining=1000,
        )

    monkeypatch.setattr(chat_cli, "resolve_armory_session", fake_resolve)
    monkeypatch.setattr(chat_cli, "iter_chat_events", fake_events)

    parser = build_parser()
    run_argv(
        parser,
        [
            "chat",
            "ask",
            "--jsonl",
            str(armory),
            "what",
            "is",
            "the",
            "material",
            "about",
        ],
    )

    events = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert [event["type"] for event in events] == [
        "notice",
        "material_operation",
        "notice",
        "notice",
        "assistant_delta",
        "turn_complete",
    ]
    assert events[1]["operation"] == "sample_overview"
    assert events[1]["metadata"]["evidence_blocks"] == 2
    assert [events[index]["code"] for index in (0, 2, 3)] == [
        "reading",
        "evidence",
        "writing",
    ]
    assert events[2]["metadata"]["coverage"]["evidence_blocks"] == 2
    assert events[2]["metadata"]["items"][0]["evidence_id"] == "E1"
    assert events[4]["delta"].startswith("Retrieved overview sample")
    assert events[5]["full_text"].startswith("Retrieved overview sample")


def test_tui_command_reports_missing_dependency(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    def fake_tui(_path: Path | None) -> None:
        raise TuiDependencyError("missing textual")

    with (
        patch("interfaces.tui.run_tui_for_path", fake_tui),
        pytest.raises(SystemExit) as exc_info,
    ):
        run_argv(parser, ["tui"])

    assert exc_info.value.code == 2
    assert "missing textual" in capsys.readouterr().err


def test_golden_path_init_source_index_dry_run(tmp_path: Path) -> None:
    """Golden-path stress test: init armory -> add source -> index -> dry-run chat."""
    # Step 1: Init armory
    armory_path = tmp_path / "golden-armory"
    initialize(armory_path)
    assert (armory_path / ".hephaion" / "armory.toml").is_file()

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
    assert (armory_path / ".hephaion" / "rag_index.json").is_file()

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
    """No args at all → inject 'interfaces.tui'."""
    result = _inject_default_subcommand([], {"armory", "tui", "materials"})
    assert result == ["tui"]


def test_inject_default_subcommand_bare_path() -> None:
    """A bare path that isn't a known command → inject 'interfaces.tui' before it."""
    result = _inject_default_subcommand(
        ["/tmp/my-armory"],
        {"armory", "tui", "materials"},
    )
    assert result == ["tui", "/tmp/my-armory"]


def test_inject_default_subcommand_flags_before_path() -> None:
    """Flags before the path are skipped, 'interfaces.tui' injected before the path."""
    result = _inject_default_subcommand(
        ["--profile", "/tmp/armory"],
        {"armory", "tui", "materials"},
    )
    assert result == ["--profile", "tui", "/tmp/armory"]


def test_inject_default_subcommand_known_command_unchanged() -> None:
    """A known subcommand is left unchanged — argparse handles it."""
    result = _inject_default_subcommand(
        ["armory", "init", "/tmp/armory"],
        {"armory", "tui", "materials"},
    )
    assert result == ["armory", "init", "/tmp/armory"]


def test_inject_default_subcommand_flags_only() -> None:
    """Only flags, no positional → return unchanged (argparse will show help or error)."""
    result = _inject_default_subcommand(
        ["--version"],
        {"armory", "tui", "materials"},
    )
    assert result == ["--version"]


def test_inject_default_subcommand_relative_path() -> None:
    """Relative paths that aren't known commands get 'interfaces.tui' injected."""
    result = _inject_default_subcommand(
        ["./my-armory"],
        {"armory", "tui", "materials"},
    )
    assert result == ["tui", "./my-armory"]


# --- End-to-end path argument tests ---


def test_main_with_path_and_profile_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`heph --profile /path` should inject tui and pass path through."""
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(cli_sys, "argv", ["heph", "--profile", str(tmp_path)])

    # Stub profiling to avoid actual cProfile/pstats work
    def _noop_report(_prof: object) -> None:
        pass

    monkeypatch.setitem(cli_main.__globals__, "_report_profile", _noop_report)

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert captured_path == tmp_path


def test_bare_path_with_nonexistent_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """`heph /nonexistent/path` should still inject tui and pass path."""
    captured_path: Path | None = None

    def fake_tui(path: Path | None) -> None:
        nonlocal captured_path
        captured_path = path

    monkeypatch.setattr(cli_sys, "argv", ["heph", "/nonexistent/path"])

    with patch("interfaces.tui.run_tui_for_path", fake_tui):
        cli_main()

    assert captured_path == Path("/nonexistent/path")
