from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_HELP_COMMANDS_HEADER = "Essential commands:"
_HELP_OPTIONS_HEADER = "Options:"
_HELP_EXAMPLES_HEADER = "Examples:"


class HephaistosArgumentParser(argparse.ArgumentParser):
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
        return metadata.version("hephaistos")
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
    if candidate.exists() or any(separator in path for separator in ("/", "\\")):
        return candidate

    search_index = importlib.import_module("hephaistos.armory.search")
    entries = search_index.load_known_armory_entries()
    matches = [
        entry.path for entry in entries if entry.valid and entry.path.name.lower() == path.lower()
    ]
    if len(matches) == 1:
        return matches[0]
    prefix_matches = [
        entry.path
        for entry in entries
        if entry.valid and entry.path.name.lower().startswith(path.lower())
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    if len(matches) > 1 or len(prefix_matches) > 1:
        print(f"error: armory shortcut '{path}' is ambiguous", file=sys.stderr)
        raise SystemExit(2)
    return candidate


def _cmd_tui(args: argparse.Namespace) -> None:
    tui = importlib.import_module("hephaistos.tui")

    try:
        path = getattr(args, "path", None)
        tui.run_tui_for_path(_resolve_armory_argument(path))
    except tui.TuiDependencyError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


def _cmd_materials_index(args: argparse.Namespace) -> None:
    rag_index = importlib.import_module("hephaistos.rag.index")
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
    rag_health = importlib.import_module("hephaistos.rag.health")
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


def _validated_armory_path(path: str) -> Path:
    armory_storage = importlib.import_module("hephaistos.armory.storage")
    try:
        armory_path = armory_storage.normalize_path(path)
        armory_storage.validate(armory_path)
    except (armory_storage.ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    return armory_path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_source_checkout(root: Path) -> bool:
    return (root / "pyproject.toml").is_file() and (root / "hephaistos").is_dir()


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
            "  update or reinstall Hephaistos so PDF, DOCX, PPTX, and XLSX materials can be "
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
    if os.environ.get("HEPHAISTOS_NO_VENV_REEXEC") == "1":
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
    env["HEPHAISTOS_NO_VENV_REEXEC"] = "1"
    os.execve(str(venv_heph), [str(venv_heph), *sys.argv[1:]], env)


def _cmd_update(_args: argparse.Namespace) -> None:
    root = _project_root()
    executable = Path(sys.executable).resolve()
    print("Hephaistos update")
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
        "Hephaistos opens an armory and starts an interactive AI session.",
        _HELP_EXAMPLES_HEADER,
        f"  {parser.prog}                         Open your current armory or plain chat",
        f"  {parser.prog} gdp                     Open the known armory named gdp",
        f"  {parser.prog} ./gdp                   Open an armory by path",
        f"  {parser.prog} armory algorithms      Create ~/.armories/algorithms",
        "  cp notes.pdf ~/.armories/algorithms/materials/",
        f"  {parser.prog} algorithms              Start learning",
        "",
        _HELP_COMMANDS_HEADER,
        *_format_rows(commands),
        "",
        _HELP_OPTIONS_HEADER,
        *_format_rows(options),
        "",
        "Tip: name armories after modules, e.g. gdp or swt, then open them with `heph gdp`.",
        "Inside Hephaistos, type /help for commands like /status, /models, /exam, and /priority.",
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


def _confirm_move_armory_home(current_home: Path, target_home: Path) -> bool:
    print("Your armories are currently stored here:")
    print(f"  {current_home}")
    print("You asked to use this location instead:")
    print(f"  {target_home}")
    try:
        answer = input("Move the entire .armories folder there? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("y", "yes")


def _move_armory_home(current_home: Path, target_home: Path) -> None:
    if target_home.exists():
        print(f"error: target .armories folder already exists: {target_home}", file=sys.stderr)
        raise SystemExit(2)
    target_home.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(current_home), str(target_home))
    search_index = importlib.import_module("hephaistos.armory.search")
    moved_paths = [
        target_home / path.relative_to(current_home) for path in search_index.load_known_armories()
    ]
    search_index.save_known_armories(moved_paths)
    print(f"Moved .armories folder to {target_home}")


def _validate_armory_home(target_home: Path) -> Path:
    search_index = importlib.import_module("hephaistos.armory.search")
    known_homes: list[Path] = []
    for entry in search_index.load_known_armory_entries():
        if not entry.valid or entry.path.parent.name != ".armories":
            continue
        home = entry.path.parent
        if home not in known_homes:
            known_homes.append(home)
    if not known_homes or target_home in known_homes:
        return target_home
    current_home = known_homes[0]
    if _confirm_move_armory_home(current_home, target_home):
        _move_armory_home(current_home, target_home)
        return target_home
    print("Cancelled. To keep using your existing .armories folder, rerun without the path.")
    raise SystemExit(2)


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
            "set HEPHAISTOS_ARMORY_HOME or use `heph armory init <name>`.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    armory_cli = importlib.import_module("hephaistos.armory.cli")
    target = armory_cli.armory_shortcut_path(argv[1])
    target_home = _validate_armory_home(target.parent)
    return ["armory", "init", str(target_home / target.name)]


def build_parser() -> argparse.ArgumentParser:
    pathlib = importlib.import_module("pathlib")
    prog = pathlib.Path(sys.argv[0]).name or "hephaistos"
    parser = HephaistosArgumentParser(
        prog=prog,
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

    # Hidden backwards-compatible alias: `heph start [path]`
    start = subparsers.add_parser(
        "start",
        help=argparse.SUPPRESS,
    )
    start.add_argument("path", nargs="?", help=argparse.SUPPRESS)
    start.set_defaults(handler=_cmd_tui)

    tui = subparsers.add_parser(
        "tui",
        help=argparse.SUPPRESS,
    )
    tui.add_argument("path", nargs="?", help="Armory path or known armory name to open")
    tui.set_defaults(handler=_cmd_tui)

    armory_cli = importlib.import_module("hephaistos.armory.cli")
    armory_cli.register(subparsers, post_init=_remember_initialized_armory)

    materials_cli = importlib.import_module("hephaistos.materials.cli")
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
        help="Show how to update the active Hephaistos install.",
    )
    update.set_defaults(handler=_cmd_update)

    # Chat subcommands are hidden.  We register stub handlers here that
    # lazily import the real implementation (and the heavy openai /
    # sentence_transformers chain) only when `heph chat ...` is invoked.
    chat = subparsers.add_parser(
        "chat",
        help=argparse.SUPPRESS,
        description="Chat with an LLM.",
    )
    chat_sub = chat.add_subparsers(dest="chat_command", required=True)

    def _chat_handler(
        chat_cmd: str,
    ) -> Callable[[argparse.Namespace], None]:
        def _handler(args: argparse.Namespace) -> None:
            chat_cli = importlib.import_module("hephaistos.chat.cli")
            if chat_cmd == "ask":
                chat_cli._cmd_chat_ask(args)
                return
            if chat_cmd == "list":
                chat_cli._cmd_chat_list(args)
                return
            tui_mod = importlib.import_module("hephaistos.tui")
            if chat_cmd == "start":
                chat_cli._cmd_chat_start(args, run_tui=tui_mod.run_tui)
            elif chat_cmd == "resume":
                chat_cli._cmd_chat_resume(args, run_tui=tui_mod.run_tui)

        return _handler

    start = chat_sub.add_parser("start", help="Start a new chat session in an armory.")
    start.add_argument("path", help="Path to the armory folder.")
    start.set_defaults(handler=_chat_handler("start"))

    ask = chat_sub.add_parser("ask", help="Ask one question without opening the TUI.")
    ask.add_argument(
        "--jsonl",
        action="store_true",
        help="Emit structured turn events as JSON Lines instead of rendered text.",
    )
    ask.add_argument("path", help="Path to the armory folder.")
    ask.add_argument("prompt", nargs="+", help="Question or instruction to send.")
    ask.set_defaults(handler=_chat_handler("ask"))

    resume = chat_sub.add_parser("resume", help="Resume an existing chat session.")
    resume.add_argument("path", help="Path to the armory folder.")
    resume.add_argument("session_id", help="Session ID to resume.")
    resume.set_defaults(handler=_chat_handler("resume"))

    list_cmd = chat_sub.add_parser("list", help="List chat sessions in an armory.")
    list_cmd.add_argument("path", help="Path to the armory folder.")
    list_cmd.set_defaults(handler=_chat_handler("list"))

    register_config_commands = importlib.import_module("hephaistos.parameters.cli").register
    register_config_commands(subparsers)
    _hide_subparser(subparsers, "start")
    _hide_subparser(subparsers, "chat")

    return parser


def _remember_initialized_armory(path: Path) -> None:
    search_index = importlib.import_module("hephaistos.armory.search")
    search_index.add_known_armory(path)


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

    analytics = importlib.import_module("hephaistos.diagnostics.events")
    diagnostics = importlib.import_module("hephaistos.diagnostics.crashes")

    analytics.init_analytics()
    diagnostics.init_diagnostics()
    for message in _runtime_diagnostic_messages():
        print(message, file=sys.stderr)

    # Track session count for progressive keybind hints.
    settings_mod = importlib.import_module("hephaistos.parameters.settings")
    settings = settings_mod.load_raw_settings()
    count = int(settings.get("session_count", 0) or 0) + 1  # ty:ignore[invalid-argument-type]
    settings["session_count"] = count
    settings_mod.save_raw_settings(settings)

    # Detect profile flags before argparse (so profiling covers argparse itself)
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
        parser = build_parser()
        argv = _normalise_argv(sys.argv[1:])

        # If the first non-flag arg isn't a known subcommand (e.g. a path),
        # transparently inject the default interface subcommand so `heph /my/armory` just works.
        known_commands: set[str] = set()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                known_commands = set(action.choices.keys())
                break
        argv = _inject_default_subcommand(argv, known_commands)

        run_argv(parser, argv)
    finally:
        if _profile_memory:
            tracemalloc = importlib.import_module("tracemalloc")
            snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
            top = snapshot.statistics("lineno")[:20]
            sys.stderr.write("\n=== Memory Profile (top 20) ===\n")
            for stat in top:
                sys.stderr.write(f"  {stat}\n")
            sys.stderr.write("\n")
        if _profile and _prof is not None:
            _prof.disable()
            _report_profile(_prof)
        analytics.shutdown_analytics()
        diagnostics.shutdown_diagnostics()


def _report_profile(prof: object) -> None:
    """Save cProfile results and print summary."""
    datetime_mod = importlib.import_module("datetime")
    pathlib = importlib.import_module("pathlib")
    pstats = importlib.import_module("pstats")

    ts = datetime_mod.datetime.now(datetime_mod.UTC).strftime("%Y%m%dT%H%M%SZ")
    profile_dir = pathlib.Path.home() / ".cache" / "hephaistos" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / f"{ts}.prof"
    prof.dump_stats(str(profile_path))  # ty:ignore[unresolved-attribute]

    sys.stderr.write(f"\n=== CPU Profile saved to {profile_path} ===\n")
    stats = pstats.Stats(prof, stream=sys.stderr)  # ty:ignore[invalid-argument-type]
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)
    sys.stderr.write("\n")
