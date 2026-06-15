from __future__ import annotations

import argparse
import importlib
import os
import sys
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

_HELP_COMMANDS_HEADER = "Essential commands:"
_HELP_OPTIONS_HEADER = "Options:"
_HELP_EXAMPLES_HEADER = "Examples:"


class HephArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: object, compact_help: bool = False, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # ty:ignore[invalid-argument-type]
        self._compact_help = compact_help

    def format_help(self) -> str:
        if not self._compact_help:
            return super().format_help()
        return _format_compact_help(self)


def _package_version() -> str:
    metadata = importlib.import_module("importlib.metadata")
    try:
        return metadata.version("heph")
    except Exception:
        return "0.1.0"


def _hide_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
) -> None:
    subparsers._choices_actions = [
        action for action in subparsers._choices_actions if getattr(action, "dest", None) != name
    ]


def _resolve_armory_argument(path: str | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    if _is_explicit_armory_path(path, candidate):
        return candidate

    matches, prefix_matches = _available_armory_shortcut_matches(path)
    if match := _single_shortcut_match(matches):
        return match
    if match := _single_shortcut_match(prefix_matches):
        return match
    if len(matches) > 1 or len(prefix_matches) > 1:
        _raise_ambiguous_armory_shortcut(path)
    return candidate


def _is_explicit_armory_path(raw_path: str, candidate: Path) -> bool:
    return candidate.exists() or any(separator in raw_path for separator in ("/", "\\"))


def _available_armory_shortcut_matches(shortcut: str) -> tuple[list[Path], list[Path]]:
    search_index = importlib.import_module("hephaion.armory.search")
    entries = search_index.load_available_armory_entries()
    shortcut_lower = shortcut.lower()
    valid_paths = [entry.path for entry in entries if entry.valid]
    matches = [path for path in valid_paths if path.name.lower() == shortcut_lower]
    prefix_matches = [path for path in valid_paths if path.name.lower().startswith(shortcut_lower)]
    return matches, prefix_matches


def _single_shortcut_match(matches: list[Path]) -> Path | None:
    return matches[0] if len(matches) == 1 else None


def _raise_ambiguous_armory_shortcut(shortcut: str) -> None:
    print(f"error: armory shortcut '{shortcut}' is ambiguous", file=sys.stderr)
    raise SystemExit(2)


def _cmd_tui(args: argparse.Namespace) -> None:
    tui = importlib.import_module("interfaces.tui")
    commands = importlib.import_module("heph.commands")
    tui.set_command_registry_fn(commands.get_registry)

    try:
        path = getattr(args, "path", None)
        tui.run_tui_for_path(_resolve_armory_argument(path))
    except tui.TuiDependencyError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


def _cmd_materials_index(args: argparse.Namespace) -> None:
    rag_index = importlib.import_module("hephaion.rag.index")
    armory_path = _validated_armory_path(args.path)

    def progress(action: str, detail: str) -> None:
        labels = {
            "reading": "Reading",
            "indexed": "Indexed",
            "skipped": "Skipped",
            "writing": "Writing",
        }
        print(f"{labels.get(action, action.title())}: {detail}")

    index = rag_index.build_index(armory_path, progress=progress)
    print(f"Indexed {len(index.documents)} documents ({index.chunk_count} chunks)")


def _cmd_health(args: argparse.Namespace) -> None:
    rag_health = importlib.import_module("hephaion.rag.health")
    armory_path = _validated_armory_path(args.path)

    report = rag_health.scan_extraction_health(armory_path)
    print(f"Extraction health: {report.documents} indexed document(s)")
    print(f"Corpus forbidden text: {report.pass_rate:.1%}")
    if report.issues:
        print("Extraction issues:")
        for issue in report.issues[:10]:
            print(f"- {issue.source}: {', '.join(issue.forbidden_text_present)}")
        if len(report.issues) > 10:
            print(f"- ... {len(report.issues) - 10} more")
        raise SystemExit(1)
    print("No generic extraction poison found.")


def _cmd_chat_ask(args: argparse.Namespace) -> None:
    chat_cli = importlib.import_module("hephaion.chat.cli")
    chat_cli._cmd_chat_ask(args)


def _cmd_sdk_serve(args: argparse.Namespace) -> None:
    if args.no_session and args.session_id is not None:
        print("error: --session-id cannot be used with --no-session", file=sys.stderr)
        raise SystemExit(2)
    sdk_factory = importlib.import_module("heph.sdk.factory")
    sdk_stdio = importlib.import_module("heph.sdk.stdio")
    options = sdk_factory.HephSdkOptions(
        armory_path=args.armory_path,
        create_armory=args.create_armory,
        session_id=args.session_id,
        start_session=not args.no_session,
        base_url=args.base_url,
        model=args.model,
        max_tokens=args.max_tokens,
        rag_context_budget=args.rag_context_budget,
        reasoning_level=args.reasoning_level,
        thinking_visibility=args.thinking_visibility,
        temperature=args.temperature,
    )
    sdk_stdio.serve_stdio(options)


def _cmd_sdk_capabilities(args: argparse.Namespace) -> None:
    json = importlib.import_module("json")
    sdk_capabilities = importlib.import_module("heph.sdk.capabilities")
    payload = sdk_capabilities.get_sdk_capabilities().to_dict()
    indent = 2 if args.pretty else None
    separators = None if args.pretty else (",", ":")
    _write_stdout(json.dumps(payload, ensure_ascii=False, indent=indent, separators=separators))


def _write_stdout(text: str) -> None:
    try:
        sys.stdout.write(text)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        _exit_cleanly_after_broken_pipe()


def _exit_cleanly_after_broken_pipe() -> None:
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
    except OSError:
        raise SystemExit(0) from None
    try:
        with suppress(AttributeError, OSError, ValueError):
            os.dup2(devnull_fd, sys.stdout.fileno())
    finally:
        os.close(devnull_fd)
    raise SystemExit(0) from None


def _validated_armory_path(path: str) -> Path:
    armory_storage = importlib.import_module("hephaion.armory.storage")
    try:
        armory_path = armory_storage.normalize_path(path)
        armory_storage.validate(armory_path)
    except (armory_storage.ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    return armory_path


def _project_root() -> Path:
    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        if _is_source_checkout(parent):
            return parent
    return module_path.parents[2]


def _is_source_checkout(root: Path) -> bool:
    return (
        (root / "pyproject.toml").is_file()
        and (root / "packages" / "heph" / "src" / "heph").is_dir()
        and (root / "packages" / "hephaion" / "src" / "hephaion").is_dir()
    )


def _docling_available() -> bool:
    importlib_util = importlib.import_module("importlib.util")
    return importlib_util.find_spec("docling") is not None


def _runtime_diagnostic_messages() -> list[str]:
    root = _project_root()
    if _docling_available():
        return []

    executable = Path(sys.executable).resolve()
    if not _is_source_checkout(root):
        return [
            "warning: this `heph` executable is missing document conversion support.",
            f"  active Python: {executable}",
            "  install the optional docling extra so PDF, DOCX, PPTX, and XLSX materials can be "
            "indexed.",
        ]

    expected_venv = root / ".venv"
    if executable.is_relative_to(expected_venv):
        return []

    return [
        "warning: this `heph` executable is importing the source checkout but is missing "
        "document conversion support.",
        f"  active Python: {executable}",
        f"  source checkout: {root}",
        "  run from the checkout with `uv run heph`, or update this executable with "
        "`uv tool upgrade heph`.",
    ]


def _maybe_reexec_source_venv() -> None:
    if os.environ.get("HEPHAION_NO_VENV_REEXEC") == "1":
        return
    root = _project_root()
    if not _is_source_checkout(root) or _docling_available():
        return
    executable = Path(sys.executable).resolve()
    expected_venv = root / ".venv"
    if executable.is_relative_to(expected_venv):
        return
    binary = ("Scripts", "heph.exe") if sys.platform == "win32" else ("bin", "heph")
    venv_heph = root / ".venv" / binary[0] / binary[1]
    if not venv_heph.is_file():
        return
    env = os.environ.copy()
    env["HEPHAION_NO_VENV_REEXEC"] = "1"
    os.execve(str(venv_heph), [str(venv_heph), *sys.argv[1:]], env)


def _cmd_update(_args: argparse.Namespace) -> None:
    root = _project_root()
    executable = Path(sys.executable).resolve()
    print("Heph update")
    print(f"  executable: {executable}")
    print(f"  package: {Path(__file__).resolve()}")
    if _is_source_checkout(root):
        print()
        print("This executable is importing a source checkout:")
        print(f"  {root}")
        print()
        print("For this checkout, run:")
        print(f"  cd {root}")
        print("  uv sync")
        print("  uv run heph")
        print()
        print("For a global uv tool install, run:")
        print("  uv tool upgrade heph")
        return

    uv_tool_markers = (".local/share/uv/tools/heph", "/uv/tools/heph/")
    if any(marker in str(executable) for marker in uv_tool_markers):
        print()
        print("Upgrade this uv tool install with:")
        print("  uv tool upgrade heph")
        return

    print()
    print("Could not detect the installer for this executable.")
    print("If you installed with uv, run:")
    print("  uv tool upgrade heph")


def _cmd_local(args: argparse.Namespace) -> None:
    command = args.local_command
    if command == "search":
        _cmd_local_search(args)
        return
    if command == "install":
        _cmd_local_install(args)
        return
    if command == "status":
        _cmd_local_status()
        return
    if command == "revalidate":
        _cmd_local_revalidate(args)
        return
    if command == "stop":
        _cmd_local_stop()


def _cmd_local_search(args: argparse.Namespace) -> None:
    llama_cpp = importlib.import_module("ai.providers.llama_cpp")
    query = " ".join(args.query).strip()
    candidates = llama_cpp.search_gguf_models(query, limit=args.limit)
    if not candidates:
        print("No curated local models matched that search.")
        return
    for index, candidate in enumerate(candidates, start=1):
        details = _local_candidate_details(candidate)
        target = _local_candidate_install_target(candidate)
        if target:
            details = f"install {target}; {details}" if details else f"install {target}"
        suffix = f"  {details}" if details else ""
        print(f"{index}. {candidate.label}{suffix}")


def _cmd_local_install(args: argparse.Namespace) -> None:
    if not args.target:
        print(
            "error: local install requires a Hugging Face repo or local .gguf path",
            file=sys.stderr,
        )
        raise SystemExit(2)
    local_llm = importlib.import_module("heph.local_llm")
    candidate = None
    if not _local_target_is_file(args.target):
        candidate = local_llm.find_hf_candidate(args.target)
        if candidate is None:
            print("error: no curated local model matched that target", file=sys.stderr)
            raise SystemExit(1)
    if not args.yes and not _confirm_cli_local_load(args.target, candidate):
        print("Cancelled.")
        return
    try:
        result = local_llm.install_local_target(args.target, model_id=args.model_id or "")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    if not result.capability.passed:
        reason = result.capability.reason or "model did not return a valid tool call"
        print(
            f"Installed but not activated because the tool-call probe failed: {reason}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    local_llm.activate_local_record(result.record)
    print(f"Activated local model: {result.record.model_id}")


def _cmd_local_status() -> None:
    llama_cpp = importlib.import_module("ai.providers.llama_cpp")
    print("Local llama.cpp")
    print(f"  cache: {llama_cpp.llama_cpp_cache_dir()}")
    print(f"  models: {llama_cpp.llama_cpp_model_cache_dir()}")
    server = llama_cpp.current_server_state()
    if server is None:
        print("  server: stopped")
    else:
        print(f"  server: running on {server.endpoint}")
        print(f"  active model: {server.model_id}")
    records = llama_cpp.installed_records()
    if not records:
        print("  installed: none")
        return
    print("  installed:")
    for record in records:
        status = "tool-capable" if record.tool_capable else "not selectable"
        candidate = llama_cpp.catalog_candidate_for_model_id(record.model_id)
        label = candidate.label if candidate is not None else record.model_id
        resource = _local_candidate_details(candidate) if candidate is not None else ""
        details = [status, f"MODEL {record.model_id}"]
        if resource:
            details.append(resource)
        print(f"  - {label} ({'; '.join(details)})")


def _cmd_local_revalidate(args: argparse.Namespace) -> None:
    llama_cpp = importlib.import_module("ai.providers.llama_cpp")
    local_llm = importlib.import_module("heph.local_llm")
    capability = llama_cpp.revalidate_model(args.model_id)
    record = llama_cpp.model_record(args.model_id)
    if record is None:
        print(f"error: {capability.reason or 'model is not installed'}", file=sys.stderr)
        raise SystemExit(1)
    if not capability.passed:
        reason = capability.reason or "model did not return a valid tool call"
        print(f"error: tool-call probe failed: {reason}", file=sys.stderr)
        raise SystemExit(1)
    local_llm.activate_local_record(record)
    print(f"Revalidated and activated local model: {args.model_id}")


def _cmd_local_stop() -> None:
    llama_cpp = importlib.import_module("ai.providers.llama_cpp")
    if llama_cpp.stop_llama_server():
        print("Stopped llama.cpp.")
        return
    print("No managed llama.cpp server was running.")


def _local_candidate_details(candidate: object) -> str:
    details: list[str] = []
    quant = getattr(candidate, "quant", "")
    if isinstance(quant, str) and quant:
        details.append(quant)
    size_bytes = getattr(candidate, "size_bytes", 0)
    if isinstance(size_bytes, int):
        size = _format_local_size(size_bytes)
        if size:
            details.append(f"{size} download")
    recommended_ram_gb = getattr(candidate, "recommended_ram_gb", 0)
    if isinstance(recommended_ram_gb, int) and recommended_ram_gb:
        details.append(f"needs {recommended_ram_gb} GB RAM")
    return ", ".join(details)


def _local_candidate_install_target(candidate: object) -> str:
    hf_ref = getattr(candidate, "hf_ref", "")
    if isinstance(hf_ref, str) and hf_ref:
        return hf_ref
    repo_id = getattr(candidate, "repo_id", "")
    return repo_id if isinstance(repo_id, str) else ""


def _local_target_is_file(target: str) -> bool:
    path = Path(target).expanduser()
    return path.is_file() or target.lower().endswith(".gguf")


def _confirm_cli_local_load(target: str, candidate: object | None) -> bool:
    terminal = importlib.import_module("interfaces.terminal")
    if candidate is not None:
        label = getattr(candidate, "label", target)
        details = _local_candidate_details(candidate)
        return bool(terminal.confirm(f"Load {label}? {details}.", default=False))

    path = Path(target).expanduser()
    size = _format_local_size(path.stat().st_size) if path.is_file() else "unknown size"
    return bool(
        terminal.confirm(
            f"Load local GGUF {path.name}? {size} download; RAM depends on the file.",
            default=False,
        )
    )


def _format_local_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return ""
    size_gb = size_bytes / 1024**3
    if size_gb < 0.05:
        return "<0.1 GB"
    return f"{size_gb:.1f} GB"


def _format_rows(rows: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return []
    width = max(len(name) for name, _description in rows)
    return [f"  {name.ljust(width)}  {description}".rstrip() for name, description in rows]


def _format_compact_help(parser: argparse.ArgumentParser) -> str:
    commands: list[tuple[str, str]] = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            commands = [
                (choice.dest, choice.help or "")
                for choice in action._choices_actions
                if choice.help is not argparse.SUPPRESS
            ]
            break
    options = [
        (", ".join(action.option_strings), action.help or "")
        for action in parser._actions
        if action.option_strings and action.help is not argparse.SUPPRESS
    ]
    lines = [
        f"Usage: {parser.prog} [options] [command] [path]",
        "",
        "Open Heph, the agent inside the Hephaion harness.",
        _HELP_EXAMPLES_HEADER,
        f"  {parser.prog}                         Open your current armory or plain chat",
        f"  {parser.prog} gdp                     Open ~/.armories/gdp",
        f"  {parser.prog} course-notes            Open ~/.armories/course-notes",
        f"  {parser.prog} ./course-notes          Open an armory by path",
        f"  {parser.prog} armory course-notes    Create ~/.armories/course-notes",
        "  cp notes.pdf ~/.armories/course-notes/materials/",
        f"  {parser.prog} course-notes           Start working",
        "",
        _HELP_COMMANDS_HEADER,
        *_format_rows(commands),
        "",
        _HELP_OPTIONS_HEADER,
        *_format_rows(options),
        "",
        "Tip: name armories after your materials, then open them with `heph course-notes`.",
        "Inside Heph, type /help for commands like /status, /models, /exam, and /priority.",
    ]
    return "\n".join(lines) + "\n"


def _inject_default_subcommand(argv: list[str], known_commands: set[str]) -> list[str]:
    # No args at all → inject the TUI.
    if not argv:
        return ["tui"]
    for i, arg in enumerate(argv):
        if not arg.startswith("-"):
            if arg not in known_commands:
                return [*argv[:i], "tui", *argv[i:]]
            break
    return argv


def _normalise_armory_shortcut(argv: list[str]) -> list[str]:
    if (
        len(argv) < 2
        or argv[0] != "armory"
        or argv[1] in ("init", "open", "-h", "--help", "help")
        or argv[1].startswith("-")
        or len(argv) > 3
    ):
        return argv
    if len(argv) == 3:
        print(
            "error: armory parent paths are no longer supported; "
            "set HEPHAION_ARMORY_HOME or use `heph armory init <name>`.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    armory_cli = importlib.import_module("hephaion.armory.cli")
    target = armory_cli.armory_shortcut_path(argv[1])
    return ["armory", "init", str(target)]


def build_parser() -> argparse.ArgumentParser:
    parser = HephArgumentParser(
        prog="heph",
        description="TUI-first document CLI.",
        compact_help=True,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_package_version()}",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--profile-memory",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="command",
        parser_class=argparse.ArgumentParser,
    )

    tui = subparsers.add_parser(
        "tui",
        help=argparse.SUPPRESS,
    )
    tui.add_argument("path", nargs="?", help="Armory name or explicit path to open")
    tui.set_defaults(handler=_cmd_tui)

    armory_cli = importlib.import_module("hephaion.armory.cli")
    armory_cli.register(subparsers, post_init=_remember_initialized_armory)

    materials_cli = importlib.import_module("hephaion.materials.cli")
    materials_cli.register(subparsers, index_handler=_cmd_materials_index)

    index = subparsers.add_parser(
        "index",
        help="Build or refresh the materials index.",
    )
    index.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the armory folder. Defaults to the current directory.",
    )
    index.set_defaults(handler=_cmd_materials_index)

    health = subparsers.add_parser(
        "health",
        help="Check indexed materials for generic extraction problems.",
    )
    health.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the armory folder. Defaults to the current directory.",
    )
    health.set_defaults(handler=_cmd_health)

    update = subparsers.add_parser(
        "update",
        help="Show how to update the active Heph install.",
    )
    update.set_defaults(handler=_cmd_update)

    local = subparsers.add_parser(
        "local",
        help="Manage private local llama.cpp models.",
    )
    local_sub = local.add_subparsers(dest="local_command", required=True)
    local_search = local_sub.add_parser(
        "search",
        help="Browse curated GGUF models.",
    )
    local_search.add_argument(
        "query",
        nargs="*",
        help="Catalog terms or a Hugging Face owner/repo.",
    )
    local_search.add_argument("--limit", type=int, default=20, help="Maximum results to show.")
    local_search.set_defaults(handler=_cmd_local)

    local_install = local_sub.add_parser(
        "install",
        help="Install a curated GGUF model or local .gguf path.",
    )
    local_install.add_argument(
        "target",
        nargs="?",
        help="Curated Hugging Face repo[:quant] or .gguf path.",
    )
    local_install.add_argument(
        "--model-id",
        default="",
        help="Model id alias for a local .gguf path.",
    )
    local_install.add_argument(
        "--yes",
        action="store_true",
        help="Skip the local model load confirmation.",
    )
    local_install.set_defaults(handler=_cmd_local)

    local_status = local_sub.add_parser("status", help="Show local llama.cpp status.")
    local_status.set_defaults(handler=_cmd_local)

    local_revalidate = local_sub.add_parser(
        "revalidate",
        help="Run the tool-call probe for an installed local model.",
    )
    local_revalidate.add_argument("model_id", help="Installed local model id.")
    local_revalidate.set_defaults(handler=_cmd_local)

    local_stop = local_sub.add_parser("stop", help="Stop the managed llama.cpp server.")
    local_stop.set_defaults(handler=_cmd_local)

    sdk = subparsers.add_parser(
        "sdk",
        help="Run SDK services for native clients.",
    )
    sdk_sub = sdk.add_subparsers(dest="sdk_command", required=True)
    sdk_serve = sdk_sub.add_parser(
        "serve",
        help="Run the SDK JSONL stdio service.",
    )
    sdk_serve.add_argument(
        "--armory",
        dest="armory_path",
        help="Armory path to open before serving. Defaults to plain chat.",
    )
    sdk_serve.add_argument(
        "--create-armory",
        action="store_true",
        help="Create --armory before serving.",
    )
    sdk_serve.add_argument(
        "--session-id",
        help="Resume a saved session before serving.",
    )
    sdk_serve.add_argument(
        "--no-session",
        action="store_true",
        help="Start without an active session.",
    )
    sdk_serve.add_argument("--base-url", help="Override the provider API base URL.")
    sdk_serve.add_argument("--model", help="Override the active model.")
    sdk_serve.add_argument("--max-tokens", type=int, help="Override max output tokens.")
    sdk_serve.add_argument(
        "--rag-context-budget",
        type=int,
        help="Override the retrieval context token budget.",
    )
    sdk_serve.add_argument("--reasoning-level", help="Override the reasoning level.")
    sdk_serve.add_argument(
        "--thinking-visibility",
        help="Override model thinking visibility.",
    )
    sdk_serve.add_argument("--temperature", type=float, help="Override generation temperature.")
    sdk_serve.set_defaults(handler=_cmd_sdk_serve)

    sdk_capabilities = sdk_sub.add_parser(
        "capabilities",
        help="Print the SDK capability contract as JSON.",
    )
    sdk_capabilities.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the capability JSON.",
    )
    sdk_capabilities.set_defaults(handler=_cmd_sdk_capabilities)

    # Chat automation is hidden from the main help, but kept for scripts and
    # harness audits that need a structured non-interactive turn stream.
    chat = subparsers.add_parser(
        "chat",
        help=argparse.SUPPRESS,
        description="Chat with an LLM.",
    )
    chat_sub = chat.add_subparsers(dest="chat_command", required=True)

    ask = chat_sub.add_parser("ask", help="Ask one question without opening the TUI.")
    ask.add_argument(
        "--jsonl",
        action="store_true",
        help="Emit structured turn events as JSON Lines instead of rendered text.",
    )
    ask.add_argument("path", help="Path to the armory folder.")
    ask.add_argument("prompt", nargs="+", help="Question or instruction to send.")
    ask.set_defaults(handler=_cmd_chat_ask)

    register_config_commands = importlib.import_module("hephaion.parameters.cli").register
    register_config_commands(subparsers)
    register_learning_commands = importlib.import_module("hephaion.learning.cli").register
    register_learning_commands(subparsers)
    _hide_subparser(subparsers, "chat")

    return parser


def _remember_initialized_armory(path: Path) -> None:
    search_index = importlib.import_module("hephaion.armory.search")
    search_index.remember_armory(path)


def _normalise_argv(argv: list[str]) -> list[str]:
    if not argv or argv[0] not in ("--tui", "-tui"):
        return _normalise_armory_shortcut(argv)
    rest = argv[1:]
    if rest and rest[0] in ("help", "-h", "--help"):
        return _normalise_armory_shortcut(["tui", "--help", *rest[1:]])
    return _normalise_armory_shortcut(["tui", *rest])


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(_normalise_argv(argv))
    handler = getattr(args, "handler", None)
    if handler is None:
        _cmd_tui(args)
        return
    handler(args)


def main() -> None:
    _maybe_reexec_source_venv()
    shutdown_analytics, shutdown_diagnostics = _init_diagnostics()
    _increment_session_count()

    _profile = "--profile" in sys.argv[1:]
    _profile_memory = "--profile-memory" in sys.argv[1:]
    _prof = None
    if _profile:
        _cprofile = importlib.import_module("cProfile")
        _prof = _cprofile.Profile()
        _prof.enable()

    if _profile_memory:
        tracemalloc = importlib.import_module("tracemalloc")
        tracemalloc.start()

    try:
        _run_main_argv(sys.argv[1:])
    finally:
        if _profile_memory:
            _report_memory_profile()
        if _profile and _prof is not None:
            _prof.disable()
            _report_profile(_prof)
        shutdown_analytics()
        shutdown_diagnostics()


def _init_diagnostics() -> tuple[Callable[[], None], Callable[[], None]]:
    analytics = importlib.import_module("hephaion.diagnostics.events")
    diagnostics = importlib.import_module("hephaion.diagnostics.crashes")
    analytics.init_analytics()
    diagnostics.init_diagnostics()
    for message in _runtime_diagnostic_messages():
        print(message, file=sys.stderr)
    return analytics.shutdown_analytics, diagnostics.shutdown_diagnostics


def _increment_session_count() -> None:
    settings_mod = importlib.import_module("hephaion.parameters.settings")
    settings = settings_mod.load_raw_settings()
    count = int(settings.get("session_count", 0) or 0) + 1  # ty:ignore[invalid-argument-type]
    settings["session_count"] = count
    settings_mod.save_raw_settings(settings)


def _run_main_argv(raw_argv: list[str]) -> None:
    parser = build_parser()
    argv = _normalise_argv(raw_argv)
    argv = _inject_default_subcommand(argv, _known_parser_commands(parser))
    run_argv(parser, argv)


def _known_parser_commands(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices.keys())
    return set()


def _report_memory_profile() -> None:
    tracemalloc = importlib.import_module("tracemalloc")
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()
    top = snapshot.statistics("lineno")[:20]
    sys.stderr.write("\n=== Memory Profile (top 20) ===\n")
    for stat in top:
        sys.stderr.write(f"  {stat}\n")
    sys.stderr.write("\n")


def _report_profile(prof: object) -> None:
    """Save cProfile results and print summary."""
    datetime_mod = importlib.import_module("datetime")
    pathlib = importlib.import_module("pathlib")
    pstats = importlib.import_module("pstats")

    ts = datetime_mod.datetime.now(datetime_mod.UTC).strftime("%Y%m%dT%H%M%SZ")
    profile_dir = pathlib.Path.home() / ".cache" / "hephaion" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / f"{ts}.prof"
    prof.dump_stats(str(profile_path))  # ty:ignore[unresolved-attribute]

    sys.stderr.write(f"\n=== CPU Profile saved to {profile_path} ===\n")
    stats = pstats.Stats(prof, stream=sys.stderr)  # ty:ignore[invalid-argument-type]
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)
    sys.stderr.write("\n")
