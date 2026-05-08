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
    """Top-level help that stays compact while deriving commands from argparse."""

    def __init__(self, *args: object, compact_help: bool = False, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[reportUnknownArgumentType]  # ty:ignore[invalid-argument-type]
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


def _version_string() -> str:
    """Lazy version string - avoids importlib.metadata scan at import time."""
    return f"%(prog)s {_package_version()}"


def _hide_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    name: str,
) -> None:
    subparsers._choices_actions = [
        action for action in subparsers._choices_actions if getattr(action, "dest", None) != name
    ]


def _resolve_armory_argument(path: str | None) -> Path | None:
    """Resolve a path or known armory shortcut for TUI startup."""
    if not path:
        return None
    candidate = Path(path)
    if candidate.exists() or any(separator in path for separator in ("/", "\\")):
        return candidate

    search_index = importlib.import_module("hephaistos.armory.search")
    matches = [
        entry.path
        for entry in search_index.load_known_armory_entries()
        if entry.valid and entry.path.name.lower() == path.lower()
    ]
    if len(matches) == 1:
        return matches[0]
    prefix_matches = [
        entry.path
        for entry in search_index.load_known_armory_entries()
        if entry.valid and entry.path.name.lower().startswith(path.lower())
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    if len(matches) > 1 or len(prefix_matches) > 1:
        print(f"error: armory shortcut '{path}' is ambiguous", file=sys.stderr)
        raise SystemExit(2)
    return candidate


def _cmd_tui(args: argparse.Namespace) -> None:
    """Start the Textual shell."""
    tui = importlib.import_module("hephaistos.tui")

    try:
        path = getattr(args, "path", None)
        tui.run_tui_for_path(_resolve_armory_argument(path))
    except tui.TuiDependencyError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


def _cmd_materials_index(args: argparse.Namespace) -> None:
    """Build or refresh the RAG index for study materials."""
    rag_index = importlib.import_module("hephaistos.rag.index")
    armory_storage = importlib.import_module("hephaistos.armory.storage")
    try:
        armory_path = armory_storage.normalize_path(args.path)
        armory_storage.validate(armory_path)
    except (armory_storage.ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    index = rag_index.build_index(armory_path)
    print(f"Indexed {len(index.documents)} documents ({index.chunk_count} chunks)")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_source_checkout(root: Path) -> bool:
    return (root / "pyproject.toml").is_file() and (root / "hephaistos").is_dir()


def _path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _docling_available() -> bool:
    importlib_util = importlib.import_module("importlib.util")
    return importlib_util.find_spec("docling") is not None


def _runtime_diagnostic_messages() -> list[str]:
    """Return startup warnings for split source/runtime installs."""
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
    if _path_is_relative_to(executable, expected_venv):
        return []

    return [
        "warning: this `heph` executable is importing the source checkout but is missing "
        "document conversion support.",
        f"  active Python: {executable}",
        f"  source checkout: {root}",
        "  run from the checkout with `uv run heph`, or update this executable with "
        "`uv tool upgrade hephaistos`.",
    ]


def _source_venv_heph(root: Path) -> Path | None:
    if sys.platform == "win32":
        candidate = root / ".venv" / "Scripts" / "heph.exe"
    else:
        candidate = root / ".venv" / "bin" / "heph"
    if candidate.is_file():
        return candidate
    return None


def _maybe_reexec_source_venv() -> None:
    """Avoid mixing a source checkout with a different Python environment."""
    if os.environ.get("HEPHAISTOS_NO_VENV_REEXEC") == "1":
        return
    root = _project_root()
    if not _is_source_checkout(root) or _docling_available():
        return
    executable = Path(sys.executable).resolve()
    expected_venv = root / ".venv"
    if _path_is_relative_to(executable, expected_venv):
        return
    venv_heph = _source_venv_heph(root)
    if venv_heph is None:
        return
    env = os.environ.copy()
    env["HEPHAISTOS_NO_VENV_REEXEC"] = "1"
    os.execve(str(venv_heph), [str(venv_heph), *sys.argv[1:]], env)


def _emit_runtime_diagnostics() -> None:
    for message in _runtime_diagnostic_messages():
        print(message, file=sys.stderr)


def _cmd_update(_args: argparse.Namespace) -> None:
    """Explain how to update the active Hephaistos installation."""
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
        print("  uv tool upgrade hephaistos")
        return

    executable_text = str(executable)
    if ".local/share/uv/tools/hephaistos" in executable_text or "/uv/tools/hephaistos/" in (
        executable_text
    ):
        print()
        print("Upgrade this uv tool install with:")
        print("  uv tool upgrade hephaistos")
        return

    print()
    print("Could not detect the installer for this executable.")
    print("If you installed with uv, run:")
    print("  uv tool upgrade hephaistos")


def _get_subcommand_names(parser: argparse.ArgumentParser) -> set[str]:
    """Return the set of registered subcommand names."""
    for action in parser._actions:  # type: ignore[reportPrivateUsage]
        if isinstance(action, argparse._SubParsersAction):  # type: ignore[reportPrivateUsage]
            return set(action.choices.keys())  # type: ignore[reportUnknownMemberType,reportUnknownArgumentType]
    return set()


def _get_visible_subcommands(parser: argparse.ArgumentParser) -> list[tuple[str, str]]:
    for action in parser._actions:  # type: ignore[reportPrivateUsage]
        if isinstance(action, argparse._SubParsersAction):  # type: ignore[reportPrivateUsage]
            return [
                (choice.dest, choice.help or "")
                for choice in action._choices_actions  # type: ignore[reportPrivateUsage]
                if choice.help is not argparse.SUPPRESS
            ]
    return []


def _get_visible_options(parser: argparse.ArgumentParser) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    for action in parser._actions:  # type: ignore[reportPrivateUsage]
        if not action.option_strings or action.help is argparse.SUPPRESS:
            continue
        option = ", ".join(action.option_strings)
        help_text = action.help or ""
        options.append((option, help_text))
    return options


def _format_rows(rows: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return []
    width = max(len(name) for name, _description in rows)
    return [f"  {name.ljust(width)}  {description}".rstrip() for name, description in rows]


def _format_compact_help(parser: argparse.ArgumentParser) -> str:
    commands = _get_visible_subcommands(parser)
    options = _get_visible_options(parser)
    lines = [
        f"Usage: {parser.prog} [options] [command] [path]",
        "",
        "Hephaistos opens a study armory and starts an interactive AI study session.",
        _HELP_EXAMPLES_HEADER,
        f"  {parser.prog}                         Open your current armory or plain chat",
        f"  {parser.prog} gdp                     Open the known armory named gdp",
        f"  {parser.prog} ./gdp                   Open an armory by path",
        f"  {parser.prog} armory mfi-1           Create ~/.armories/mfi-1",
        "  cp notes.pdf ~/.armories/mfi-1/materials/",
        f"  {parser.prog} mfi-1                   Start studying",
        "",
        _HELP_COMMANDS_HEADER,
        *_format_rows(commands),
        "",
        _HELP_OPTIONS_HEADER,
        *_format_rows(options),
        "",
        "Tip: name armories after modules, e.g. gdp or swt, then open them with `heph gdp`.",
        "Inside Hephaistos, type /help for chat commands like /status, /model, and /study.",
    ]
    return "\n".join(lines) + "\n"


def _inject_default_subcommand(argv: list[str], known_commands: set[str]) -> list[str]:
    """Prepend the default subcommand when no explicit subcommand is given."""
    # No args at all → inject the TUI.
    if not argv:
        return ["tui"]
    for i, arg in enumerate(argv):
        if not arg.startswith("-"):
            if arg not in known_commands:
                return [*argv[:i], "tui", *argv[i:]]
            break
    return argv


def _known_armory_homes() -> list[Path]:
    search_index = importlib.import_module("hephaistos.armory.search")
    homes: list[Path] = []
    for entry in search_index.load_known_armory_entries():
        if not entry.valid or entry.path.parent.name != ".armories":
            continue
        home = entry.path.parent
        if home not in homes:
            homes.append(home)
    return homes


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
    known_homes = _known_armory_homes()
    if not known_homes or target_home in known_homes:
        return target_home
    current_home = known_homes[0]
    if _confirm_move_armory_home(current_home, target_home):
        _move_armory_home(current_home, target_home)
        return target_home
    print("Cancelled. To keep using your existing .armories folder, rerun without the path.")
    raise SystemExit(2)


def _normalise_armory_shortcut(argv: list[str]) -> list[str]:
    """Accept `heph armory <name>` as create-armory shorthand."""
    if len(argv) < 2 or argv[0] != "armory":
        return argv
    subcommand = argv[1]
    if subcommand in ("init", "open", "-h", "--help", "help"):
        return argv
    if subcommand.startswith("-"):
        return argv
    if len(argv) > 3:
        return argv
    if len(argv) == 3:
        print(
            "error: armory parent paths are no longer supported; "
            "set HEPHAISTOS_ARMORY_HOME or use `heph armory init <name>`.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    armory_cli = importlib.import_module("hephaistos.armory.cli")
    target = armory_cli.armory_shortcut_path(subcommand)
    target_home = _validate_armory_home(target.parent)
    return ["armory", "init", str(target_home / target.name)]


def _normalise_tui_alias(argv: list[str]) -> list[str]:
    """Accept common flag-shaped TUI aliases as shorthand for ``tui``."""
    if not argv:
        return argv
    if argv[0] not in ("--tui", "-tui"):
        return argv
    rest = argv[1:]
    if rest and rest[0] in ("help", "-h", "--help"):
        return ["tui", "--help", *rest[1:]]
    return ["tui", *rest]


def build_parser() -> argparse.ArgumentParser:
    pathlib = importlib.import_module("pathlib")
    prog = pathlib.Path(sys.argv[0]).name or "hephaistos"
    parser = HephaistosArgumentParser(
        prog=prog,
        description="TUI-first study CLI.",
        compact_help=True,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_version_string(),
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
    materials_cli.register_source_alias(subparsers, index_handler=_cmd_materials_index)

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
        """Return a stub handler that lazily loads chat.cli and dispatches."""

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
    return _normalise_armory_shortcut(_normalise_tui_alias(argv))


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(_normalise_argv(argv))
    handler = getattr(args, "handler", None)
    if handler is None:
        _cmd_tui(args)
        return
    handler(args)


def _increment_session_count() -> None:
    """Bump the persisted session count (used for progressive keybind hints)."""
    settings_mod = importlib.import_module("hephaistos.parameters.settings")
    settings = settings_mod.load_raw_settings()
    count = int(settings.get("session_count", 0) or 0) + 1  # type: ignore[reportArgumentType]  # ty:ignore[invalid-argument-type]
    settings["session_count"] = count
    settings_mod.save_raw_settings(settings)


def main() -> None:
    _maybe_reexec_source_venv()

    analytics = importlib.import_module("hephaistos.diagnostics.events")
    diagnostics = importlib.import_module("hephaistos.diagnostics.crashes")

    analytics.init_analytics()
    diagnostics.init_diagnostics()
    _emit_runtime_diagnostics()

    # Track session count for progressive keybind hints.
    _increment_session_count()

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
        known_commands = _get_subcommand_names(parser)
        argv = _inject_default_subcommand(argv, known_commands)

        run_argv(parser, argv)
    finally:
        if _profile_memory:
            _report_memory()
        if _profile and _prof is not None:
            _prof.disable()
            _report_profile(_prof)
        analytics.shutdown_analytics()
        diagnostics.shutdown_diagnostics()


def _report_memory() -> None:
    """Print top memory allocations from tracemalloc."""
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
    profile_dir = pathlib.Path.home() / ".cache" / "hephaistos" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / f"{ts}.prof"
    prof.dump_stats(str(profile_path))  # type: ignore[reportUnknownMemberType]  # ty:ignore[unresolved-attribute]

    sys.stderr.write(f"\n=== CPU Profile saved to {profile_path} ===\n")
    stats = pstats.Stats(prof, stream=sys.stderr)  # type: ignore[reportUnknownArgumentType]  # ty:ignore[invalid-argument-type]
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)
    sys.stderr.write("\n")
