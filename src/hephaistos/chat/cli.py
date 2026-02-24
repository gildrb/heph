"""CLI commands for chat sessions."""

from __future__ import annotations

import argparse

from hephaistos.chat.service import create_chat, resume_chat


def _cmd_chat_new(args: argparse.Namespace) -> None:
    print(create_chat(args.title))


def _cmd_chat_resume(args: argparse.Namespace) -> None:
    print(resume_chat(args.chat_id))


def register(subparsers) -> None:
    chat = subparsers.add_parser("chat", help="Start or resume chats.")
    chat_sub = chat.add_subparsers(dest="chat_command", required=True)

    new = chat_sub.add_parser("new", help="Start a new chat session.")
    new.add_argument("--title", help="Optional chat title.", default=None)
    new.set_defaults(handler=_cmd_chat_new)

    resume = chat_sub.add_parser("resume", help="Resume an existing chat session.")
    resume.add_argument("chat_id", help="Chat identifier.")
    resume.set_defaults(handler=_cmd_chat_resume)

