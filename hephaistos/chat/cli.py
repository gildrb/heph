"""CLI commands for chat sessions."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from hephaistos.armory.search import set_last_armory
from hephaistos.armory.storage import ArmoryError
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.automation import event_to_json_object, iter_chat_events
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_session,
    list_armory_sessions,
    resume_session,
    send_user_message,
    validate_armory_path,
)
from hephaistos.parameters.cli import load_config


def _validated_armory_path(path: str) -> Path:
    try:
        return validate_armory_path(path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def resolve_armory_session(path: str) -> ChatSession:
    armory_path = _validated_armory_path(path)
    try:
        session = create_session(load_config(armory_path), armory_path)
        set_last_armory(armory_path)
        return session
    except SessionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _cmd_chat_start(args: argparse.Namespace, *, run_tui: Callable[..., None]) -> None:
    session = resolve_armory_session(args.path)
    run_tui(session)


def _cmd_chat_resume(args: argparse.Namespace, *, run_tui: Callable[..., None]) -> None:
    armory_path = _validated_armory_path(args.path)
    try:
        session = resume_session(load_config(armory_path), armory_path, args.session_id)
    except chat_storage.ChatStorageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    run_tui(session)


def _cmd_chat_ask(args: argparse.Namespace) -> None:
    session = resolve_armory_session(args.path)
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        print("error: prompt is required", file=sys.stderr)
        raise SystemExit(2)
    if args.jsonl:
        for event in iter_chat_events(session, prompt):
            print(json.dumps(event_to_json_object(event), ensure_ascii=False))
        return
    send_user_message(session, prompt)


def _cmd_chat_list(args: argparse.Namespace) -> None:
    armory_path = _validated_armory_path(args.path)
    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print("No chat sessions found.")
        return

    for session in sessions:
        title = session["title"] or "(untitled)"
        print(f"  {session['session_id']}  {title}  ({session['updated_at']})")
