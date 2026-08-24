from __future__ import annotations

import argparse
import importlib
import os
import sys
from contextlib import suppress
from pathlib import Path

from heph import __version__

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
    return __version__


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
    search_index = importlib.import_module("harness.armory.search")
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
    rag_index = importlib.import_module("harness.rag.index")
    rag_config = importlib.import_module("harness.rag.config")
    parameters = importlib.import_module("harness.parameters.cli")
    armory_path = _validated_armory_path(args.path)

    def progress(action: str, detail: str) -> None:
        labels = {
            "reading": "Reading",
            "indexed": "Indexed",
            "skipped": "Skipped",
            "writing": "Writing",
            "warning": "Warning",
            "embedding_notice": "Embeddings",
            "embedding_warning": "Embedding warning",
            "embedded": "Embedded",
        }
        print(f"{labels.get(action, action.title())}: {detail}")

    config = parameters.load_config(armory_path)
    index = rag_index.build_index(
        armory_path,
        progress=progress,
        embedding_config=config,
        embed_model=rag_config.configured_embedding_model(),
    )
    print(f"Indexed {len(index.documents)} documents ({index.chunk_count} chunks)")


def _cmd_health(args: argparse.Namespace) -> None:
    rag_health = importlib.import_module("harness.rag.health")
    optional_backends = importlib.import_module("harness.rag.optional_backends")
    rag_config = importlib.import_module("harness.rag.config")
    parameters = importlib.import_module("harness.parameters.cli")
    armory_path = _validated_armory_path(args.path)

    print("Capabilities:")
    for capability in optional_backends.capabilities():
        status = "available" if capability.available else "unavailable"
        print(f"- {capability.name}: {status} ({capability.enables})")
        if not capability.available:
            print(f"  Without it: {capability.fallback}")
    config = parameters.load_config(armory_path)
    embedding_model = rag_config.configured_embedding_model()
    if embedding_model and config.base_url:
        print(f"- embeddings: configured ({config.base_url.rstrip('/')}, model={embedding_model})")
    else:
        print("- embeddings: unavailable (set HARNESS_EMBED_MODEL and configure a provider)")

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
    chat_cli = importlib.import_module("harness.chat.cli")
    chat_cli._cmd_chat_ask(args)


def _cmd_trust(args: argparse.Namespace) -> None:
    trust = importlib.import_module("heph.trust")
    armory_path = _validated_armory_path(args.path) if args.path else None
    _write_stdout(trust.format_trust_report(armory_path))


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
    armory_storage = importlib.import_module("harness.armory.storage")
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
        and (root / "packages" / "harness" / "src" / "harness").is_dir()
    )


def _document_conversion_available() -> bool:
    importlib_util = importlib.import_module("importlib.util")
    return all(
        importlib_util.find_spec(module_name) is not None
        for module_name in ("defusedxml", "pypdfium2")
    )


def _runtime_diagnostic_messages() -> list[str]:
    root = _project_root()
    if _document_conversion_available():
        return []

    executable = Path(sys.executable).resolve()
    if not _is_source_checkout(root):
        return [
            "warning: this `heph` executable is missing native document extraction support.",
            f"  active Python: {executable}",
            "  repair this install with `uv tool install --force heph@latest`.",
        ]

    expected_venv = root / ".venv"
    if executable.is_relative_to(expected_venv):
        return []

    return [
        "warning: this `heph` executable is importing the source checkout but is missing "
        "native document extraction support.",
        f"  active Python: {executable}",
        f"  source checkout: {root}",
        "  run from the checkout with `uv run heph`, or update this executable with "
        "`uv tool upgrade heph`.",
    ]


def _maybe_reexec_source_venv() -> None:
    if os.environ.get("HARNESS_NO_VENV_REEXEC") == "1":
        return
    root = _project_root()
    if not _is_source_checkout(root) or _document_conversion_available():
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
    env["HARNESS_NO_VENV_REEXEC"] = "1"
    os.execve(str(venv_heph), [str(venv_heph), *sys.argv[1:]], env)


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
        "Open Heph, the model plus local harness for grounded work.",
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
        "Inside Heph, type /help for commands like /status, /models, /evidence, and /armory.",
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
            "set HARNESS_ARMORY_HOME or use `heph armory init <name>`.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    armory_cli = importlib.import_module("harness.armory.cli")
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

    armory_cli = importlib.import_module("harness.armory.cli")
    armory_cli.register(subparsers, post_init=_remember_initialized_armory)

    materials_cli = importlib.import_module("harness.materials.cli")
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

    trust = subparsers.add_parser(
        "trust",
        help="Show local data and shell trust.",
    )
    trust.add_argument(
        "path",
        nargs="?",
        help="Optional armory path used to print exact state paths.",
    )
    trust.set_defaults(handler=_cmd_trust)

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

    register_config_commands = importlib.import_module("harness.parameters.cli").register
    register_config_commands(subparsers)
    _hide_subparser(subparsers, "chat")

    return parser


def _remember_initialized_armory(path: Path) -> None:
    search_index = importlib.import_module("harness.armory.search")
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
    for message in _runtime_diagnostic_messages():
        print(message, file=sys.stderr)
    _run_main_argv(sys.argv[1:])


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
