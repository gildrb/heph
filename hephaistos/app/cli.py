from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
import tracemalloc
from datetime import UTC, datetime
from importlib.metadata import version as _pkg_version
from pathlib import Path

from hephaistos.analytics import init_analytics, shutdown_analytics
from hephaistos.app.shell import run_chat_shell
from hephaistos.app.tui import TuiDependencyError, run_tui_for_path
from hephaistos.armory.cli import register as register_armory_commands
from hephaistos.chat.cli import register as register_chat_commands
from hephaistos.chat.cli import resolve_armory_session
from hephaistos.observability import init_observability, shutdown_observability
from hephaistos.parameters.cli import (
    register as register_config_commands,
)
from hephaistos.source.cli import register as register_source_commands

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
    try:
        return _pkg_version("hephaistos")
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


def _cmd_shell(args: argparse.Namespace) -> None:
    """Start the classic prompt-toolkit shell, optionally attached to a specific armory."""
    if args.path:
        session = resolve_armory_session(args.path)
        run_chat_shell(session)
        return
    run_chat_shell()


def _cmd_tui(args: argparse.Namespace) -> None:
    """Start the Textual shell."""
    try:
        path = getattr(args, "path", None)
        run_tui_for_path(Path(path) if path else None)
    except TuiDependencyError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


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
        "Hephaistos is a local-first study shell with armories and source indexing.",
        "",
        _HELP_EXAMPLES_HEADER,
        f"  {parser.prog}                         Start the interactive TUI",
        f"  {parser.prog} <path>                  Attach an armory path",
        f"  {parser.prog} armory init <path>      Create an armory",
        f"  {parser.prog} source index <path>     Build the source index",
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


def _inject_tui_if_path(argv: list[str], known_commands: set[str]) -> list[str]:
    """Prepend 'tui' if the first non-flag arg is not a known subcommand."""
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
    prog = Path(sys.argv[0]).name or "hephaistos"
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

    # Hidden escape hatch for the original prompt-toolkit shell.
    shell = subparsers.add_parser(
        "shell",
        help=argparse.SUPPRESS,
    )
    shell.add_argument("path", nargs="?", help=argparse.SUPPRESS)
    shell.set_defaults(handler=_cmd_shell)

    tui = subparsers.add_parser(
        "tui",
        help="Launch the Textual shell",
    )
    tui.add_argument("path", nargs="?", help="Armory path to attach")
    tui.set_defaults(handler=_cmd_tui)

    register_armory_commands(subparsers)
    register_source_commands(subparsers)
    register_chat_commands(subparsers, run_shell=run_chat_shell)
    register_config_commands(subparsers)
    _hide_subparser(subparsers, "start")
    _hide_subparser(subparsers, "shell")
    _hide_subparser(subparsers, "chat")

    return parser


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        _cmd_tui(args)
        return
    handler(args)


def main() -> None:
    init_analytics()
    init_observability()

    # Detect profile flags before argparse (so profiling covers argparse itself)
    _profile = "--profile" in sys.argv[1:]
    _profile_memory = "--profile-memory" in sys.argv[1:]

    _prof = None
    if _profile:
        _prof = cProfile.Profile()
        _prof.enable()

    if _profile_memory:
        tracemalloc.start()

    try:
        parser = build_parser()
        argv = sys.argv[1:]
        argv = _normalise_tui_alias(argv)

        # If the first non-flag arg isn't a known subcommand (e.g. a path),
        # transparently inject "tui" so `heph /my/armory` just works.
        known_commands = _get_subcommand_names(parser)
        argv = _inject_tui_if_path(argv, known_commands)

        run_argv(parser, argv)
    finally:
        if _profile_memory:
            _report_memory()
        if _profile and _prof is not None:
            _prof.disable()
            _report_profile(_prof)
        shutdown_analytics()
        shutdown_observability()


def _report_memory() -> None:
    """Print top memory allocations from tracemalloc."""
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()
    top = snapshot.statistics("lineno")[:20]
    sys.stderr.write("\n=== Memory Profile (top 20) ===\n")
    for stat in top:
        sys.stderr.write(f"  {stat}\n")
    sys.stderr.write("\n")


def _report_profile(prof: cProfile.Profile) -> None:
    """Save cProfile results and print summary."""
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    profile_dir = Path.home() / ".cache" / "hephaistos" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / f"{ts}.prof"
    prof.dump_stats(str(profile_path))

    sys.stderr.write(f"\n=== CPU Profile saved to {profile_path} ===\n")
    stats = pstats.Stats(prof, stream=sys.stderr)
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)
    sys.stderr.write("\n")
