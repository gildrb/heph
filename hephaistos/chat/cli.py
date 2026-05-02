"""CLI commands for chat sessions."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import cast

from hephaistos.armory.storage import ArmoryError
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.automation import event_to_json_object, iter_chat_events
from hephaistos.chat.events import AssistantDeltaEvent, NoticeEvent, ToolCallEvent, ToolResultEvent
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_session,
    list_armory_sessions,
    resume_session,
    save_session,
    validate_armory_path,
)
from hephaistos.parameters.cli import load_config


def resolve_armory_session(path: str) -> ChatSession:
    """Validate armory path and create a session, with CLI error handling."""
    try:
        armory_path = validate_armory_path(path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    try:
        return create_session(load_config(armory_path), armory_path)
    except SessionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _cmd_chat_start(args: argparse.Namespace, *, run_tui: Callable[..., None]) -> None:
    """Start a new chat session."""
    session = resolve_armory_session(args.path)
    run_tui(session)


def _cmd_chat_resume(args: argparse.Namespace, *, run_tui: Callable[..., None]) -> None:
    """Resume an existing chat session."""
    try:
        armory_path = validate_armory_path(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    try:
        session = resume_session(load_config(armory_path), armory_path, args.session_id)
    except chat_storage.ChatStorageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    run_tui(session)


def _prompt_from_args(args: argparse.Namespace) -> str:
    prompt_parts = cast("list[str] | None", getattr(args, "prompt", None))
    if prompt_parts:
        return " ".join(prompt_parts).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    print("error: provide a prompt argument or pipe prompt text on stdin", file=sys.stderr)
    raise SystemExit(2)


def _cmd_chat_ask(args: argparse.Namespace) -> None:
    """Run one non-interactive chat turn for automation."""
    session_id = getattr(args, "session_id", None)
    if isinstance(session_id, str) and session_id:
        try:
            armory_path = validate_armory_path(args.path)
        except ArmoryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        try:
            session = resume_session(load_config(armory_path), armory_path, session_id)
        except (chat_storage.ChatStorageError, SessionError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
    else:
        session = resolve_armory_session(args.path)

    prompt = _prompt_from_args(args)
    if not prompt:
        print("error: prompt cannot be empty", file=sys.stderr)
        raise SystemExit(2)

    try:
        json_output = bool(getattr(args, "json", False))
        for event in iter_chat_events(session, prompt):
            if json_output:
                print(json.dumps(event_to_json_object(event), sort_keys=True))
            elif isinstance(event, AssistantDeltaEvent):
                sys.stdout.write(event.delta)
                sys.stdout.flush()
            elif isinstance(event, ToolCallEvent | ToolResultEvent | NoticeEvent):
                print(event_to_json_object(event), file=sys.stderr)
        if not json_output:
            print()
        if bool(getattr(args, "save", False)):
            path = save_session(session)
            if json_output:
                print(json.dumps({"type": "session_saved", "path": str(path)}, sort_keys=True))
            else:
                print(f"Saved chat to {path}", file=sys.stderr)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _cmd_chat_list(args: argparse.Namespace) -> None:
    """List all chat sessions in the armory."""
    try:
        armory_path = validate_armory_path(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print("No chat sessions found.")
        return

    for session in sessions:
        title = session["title"] or "(untitled)"
        print(f"  {session['session_id']}  {title}  ({session['updated_at']})")


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    *,
    run_tui: Callable[..., None],
) -> None:
    """Register chat subcommands."""
    chat = subparsers.add_parser(
        "chat",
        help="Run chat automation commands",
        description="Chat with an LLM.",
    )
    chat_sub = chat.add_subparsers(dest="chat_command", required=True)

    start = chat_sub.add_parser(
        "start",
        help="Start a new chat session in an armory.",
    )
    start.add_argument("path", help="Path to the armory folder.")
    start.set_defaults(handler=lambda a: _cmd_chat_start(a, run_tui=run_tui))  # type: ignore[arg-type]

    resume = chat_sub.add_parser(
        "resume",
        help="Resume an existing chat session.",
    )
    resume.add_argument("path", help="Path to the armory folder.")
    resume.add_argument("session_id", help="Session ID to resume.")
    resume.set_defaults(handler=lambda a: _cmd_chat_resume(a, run_tui=run_tui))  # type: ignore[arg-type]

    ask = chat_sub.add_parser(
        "ask",
        help="Run one non-interactive chat turn.",
    )
    ask.add_argument("path", help="Path to the armory folder.")
    ask.add_argument("prompt", nargs="*", help="Prompt text. Reads stdin when omitted.")
    ask.add_argument("--resume", dest="session_id", help="Session ID to continue before asking.")
    ask.add_argument("--save", action="store_true", help="Persist the resulting chat session.")
    ask.add_argument("--json", action="store_true", help="Emit structured JSONL events.")
    ask.set_defaults(handler=_cmd_chat_ask)

    list_cmd = chat_sub.add_parser(
        "list",
        help="List chat sessions in an armory.",
    )
    list_cmd.add_argument("path", help="Path to the armory folder.")
    list_cmd.set_defaults(handler=_cmd_chat_list)
