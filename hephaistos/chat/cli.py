"""CLI commands for chat sessions."""

from __future__ import annotations

import argparse
import sys

from hephaistos.app.shell import run_chat_shell
from hephaistos.armory.storage import ArmoryError
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import (
    create_session,
    list_armory_sessions,
    resume_session,
    validate_armory_path,
)
from hephaistos.parameters.cli import load_config


def _cmd_chat_start(args: argparse.Namespace) -> None:
    """Start a new chat session."""
    try:
        armory_path = validate_armory_path(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    run_chat_shell(create_session(load_config(armory_path), armory_path))


def _cmd_chat_resume(args: argparse.Namespace) -> None:
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

    run_chat_shell(session)


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
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register chat subcommands."""
    chat = subparsers.add_parser(
        "chat",
        help=argparse.SUPPRESS,
        description="Chat with an LLM.",
    )
    chat_sub = chat.add_subparsers(dest="chat_command", required=True)

    start = chat_sub.add_parser(
        "start",
        help="Start a new chat session in an armory.",
    )
    start.add_argument("path", help="Path to the armory folder.")
    start.set_defaults(handler=_cmd_chat_start)

    resume = chat_sub.add_parser(
        "resume",
        help="Resume an existing chat session.",
    )
    resume.add_argument("path", help="Path to the armory folder.")
    resume.add_argument("session_id", help="Session ID to resume.")
    resume.set_defaults(handler=_cmd_chat_resume)

    list_cmd = chat_sub.add_parser(
        "list",
        help="List chat sessions in an armory.",
    )
    list_cmd.add_argument("path", help="Path to the armory folder.")
    list_cmd.set_defaults(handler=_cmd_chat_list)
