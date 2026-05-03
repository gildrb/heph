from __future__ import annotations

import argparse
import importlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_HELP_COMMANDS_HEADER = "Essential commands:"
_HELP_OPTIONS_HEADER = "Options:"
_HELP_EXAMPLES_HEADER = "Examples:"


class HephaistosArgumentParser(argparse.ArgumentParser):
    """Top-level help that stays compact while deriving commands from argparse."""

    def __init__(self, *args: object, compact_help: bool = False, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[reportUnknownArgumentType]
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
    """Lazy version string — avoids importlib.metadata scan at import time."""
    return f"%(prog)s {_package_version()}"


def _hide_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    name: str,
) -> None:
    subparsers._choices_actions = [
        action for action in subparsers._choices_actions if getattr(action, "dest", None) != name
    ]


def _cmd_tui(args: argparse.Namespace) -> None:
    """Start the Textual shell."""
    pathlib = importlib.import_module("pathlib")
    tui = importlib.import_module("hephaistos.tui")

    try:
        path = getattr(args, "path", None)
        tui.run_tui_for_path(pathlib.Path(path) if path else None)
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
        "Hephaistos is a local-first study shell with armories and materials indexing.",
        "",
        _HELP_EXAMPLES_HEADER,
        f"  {parser.prog}                         Start the interactive TUI",
        f"  {parser.prog} <path>                  Attach an armory path",
        f"  {parser.prog} armory init <path>      Create an armory",
        f"  {parser.prog} materials index <path>  Build the materials index",
        "",
        _HELP_COMMANDS_HEADER,
        *_format_rows(commands),
        "",
        _HELP_OPTIONS_HEADER,
        *_format_rows(options),
        "",
        "Inside Hephaistos, type /help for the full interactive command reference.",
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
        help="Enable CPU profiling (cProfile) for this session",
    )
    parser.add_argument(
        "--profile-memory",
        action="store_true",
        help="Enable memory profiling (tracemalloc) for this session",
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
        help="Launch the Textual shell",
    )
    tui.add_argument("path", nargs="?", help="Armory path to attach")
    tui.set_defaults(handler=_cmd_tui)

    armory_cli = importlib.import_module("hephaistos.armory.cli")
    armory_cli.register(subparsers)

    materials_cli = importlib.import_module("hephaistos.materials.cli")
    materials_cli.register(subparsers, index_handler=_cmd_materials_index)
    materials_cli.register_source_alias(subparsers, index_handler=_cmd_materials_index)

    # Chat subcommands are hidden.  We register stub handlers here that
    # lazily import the real implementation (and the heavy openai /
    # sentence_transformers chain) only when `heph chat …` is invoked.
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


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        _cmd_tui(args)
        return
    handler(args)


def _increment_session_count() -> None:
    """Bump the persisted session count (used for progressive keybind hints)."""
    settings_mod = importlib.import_module("hephaistos.parameters.settings")
    settings = settings_mod.load_raw_settings()
    count = int(settings.get("session_count", 0) or 0) + 1  # type: ignore[reportArgumentType]
    settings["session_count"] = count
    settings_mod.save_raw_settings(settings)


def main() -> None:
    analytics = importlib.import_module("hephaistos.analytics")
    observability = importlib.import_module("hephaistos.observability")

    analytics.init_analytics()
    observability.init_observability()

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
        argv = sys.argv[1:]
        argv = _normalise_tui_alias(argv)

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
        observability.shutdown_observability()


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
    prof.dump_stats(str(profile_path))  # type: ignore[reportUnknownMemberType]

    sys.stderr.write(f"\n=== CPU Profile saved to {profile_path} ===\n")
    stats = pstats.Stats(prof, stream=sys.stderr)  # type: ignore[reportUnknownArgumentType]
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)
    sys.stderr.write("\n")
