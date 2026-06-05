"""CLI commands for chat sessions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from armory.search import set_last_armory
from armory.storage import ArmoryError
from parameters.cli import load_config

from chat.automation import event_to_json_object, iter_chat_events
from chat.session import (
    ChatSession,
    SessionError,
    create_session,
    send_user_message,
    validate_armory_path,
)


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
