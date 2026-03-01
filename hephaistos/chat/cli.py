"""CLI commands for chat sessions."""

from __future__ import annotations

import argparse
import sys

from hephaistos.app.menu import MenuItem
from hephaistos.armory.storage import (
    ArmoryError,
    normalize_path,
    read_marker,
    validate,
)
from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    EngineError,
    get_reply,
)
from hephaistos.chat import storage as chat_storage


def _validate_armory(path_str: str):
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(path_str)
    validate(armory_path)
    read_marker(armory_path)
    return armory_path


def _read_source_context(armory_path) -> str:
    """Read all files from source/ and library/ to build context.

    Returns the concatenated content as a single string, or empty string
    if no files are found.
    """
    context_parts: list[str] = []
    for dirname in ("source", "library"):
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        for file_path in sorted(folder.rglob("*")):
            if not file_path.is_file():
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = file_path.relative_to(armory_path)
            context_parts.append(f"--- {rel} ---\n{text}")

    return "\n\n".join(context_parts)


def _build_system_prompt(source_context: str) -> str:
    """Build the system prompt, optionally including source file context."""
    base = "You are a helpful assistant."
    if not source_context:
        return base
    return (
        f"{base}\n\n"
        "The user has provided the following reference files. "
        "Use them to inform your responses:\n\n"
        f"{source_context}"
    )


def _run_chat_loop(
    config: ChatConfig,
    conversation: Conversation,
    armory_path,
    session_id: str,
    title: str,
) -> None:
    """Interactive chat REPL."""
    print("Chat started. Type 'quit' or 'exit' to end. Type 'save' to save.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            break
        if user_input.lower() == "save":
            path = chat_storage.save(
                armory_path, session_id, conversation, title=title
            )
            print(f"Chat saved to {path}")
            continue

        conversation.add("user", user_input)

        print("Assistant: ", end="", flush=True)
        try:
            reply = get_reply(config, conversation)
        except EngineError as exc:
            print(f"\nerror: {exc}", file=sys.stderr)
            # Remove the failed user message so the conversation stays clean
            conversation.messages.pop()
            continue

        conversation.add("assistant", reply)

    # Auto-save on exit
    if len(conversation.messages) > 1:  # more than just the system prompt
        if not title:
            # Use first user message as title
            for msg in conversation.messages:
                if msg.role == "user":
                    title = msg.content[:60]
                    break
        path = chat_storage.save(
            armory_path, session_id, conversation, title=title
        )
        print(f"Chat auto-saved to {path}")


def _cmd_chat_start(args: argparse.Namespace) -> None:
    """Start a new chat session."""
    try:
        armory_path = _validate_armory(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    config = ChatConfig.from_env()
    session_id = chat_storage.new_session_id()

    source_context = _read_source_context(armory_path)
    system_prompt = _build_system_prompt(source_context)

    conversation = Conversation()
    conversation.add("system", system_prompt)

    if source_context:
        file_count = source_context.count("--- ")
        print(f"Loaded {file_count} source file(s) as context.")

    print(f"Session: {session_id}")
    print(f"Model:   {config.model}")
    print(f"API:     {config.base_url}\n")

    _run_chat_loop(config, conversation, armory_path, session_id, title="")


def _cmd_chat_resume(args: argparse.Namespace) -> None:
    """Resume an existing chat session."""
    try:
        armory_path = _validate_armory(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    try:
        conversation, title = chat_storage.load(armory_path, args.session_id)
    except chat_storage.ChatStorageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    config = ChatConfig.from_env()

    msg_count = sum(1 for m in conversation.messages if m.role != "system")
    print(f"Resumed session: {args.session_id}")
    if title:
        print(f"Title: {title}")
    print(f"History: {msg_count} message(s)")
    print(f"Model:   {config.model}")
    print(f"API:     {config.base_url}\n")

    _run_chat_loop(
        config, conversation, armory_path, args.session_id, title=title
    )


def _cmd_chat_list(args: argparse.Namespace) -> None:
    """List all chat sessions in the armory."""
    try:
        armory_path = _validate_armory(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    sessions = chat_storage.list_sessions(armory_path)
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
    chat = subparsers.add_parser("chat", help="Chat with an LLM.")
    chat_sub = chat.add_subparsers(dest="chat_command", required=True)

    start = chat_sub.add_parser(
        "start", help="Start a new chat session in an armory."
    )
    start.add_argument("path", help="Path to the armory folder.")
    start.set_defaults(handler=_cmd_chat_start)

    resume = chat_sub.add_parser(
        "resume", help="Resume an existing chat session."
    )
    resume.add_argument("path", help="Path to the armory folder.")
    resume.add_argument("session_id", help="Session ID to resume.")
    resume.set_defaults(handler=_cmd_chat_resume)

    list_cmd = chat_sub.add_parser(
        "list", help="List chat sessions in an armory."
    )
    list_cmd.add_argument("path", help="Path to the armory folder.")
    list_cmd.set_defaults(handler=_cmd_chat_list)


MENU_ITEMS: list[MenuItem] = [
    MenuItem(
        label="Chat Start",
        description="Start a new chat session",
        prompts={"path": "Armory path [./armory]: "},
        defaults={"path": "./armory"},
        argv=["chat", "start"],
    ),
    MenuItem(
        label="Chat List",
        description="List chat sessions",
        prompts={"path": "Armory path [./armory]: "},
        defaults={"path": "./armory"},
        argv=["chat", "list"],
    ),
    MenuItem(
        label="Chat Resume",
        description="Resume an existing chat session",
        prompts={
            "path": "Armory path [./armory]: ",
            "session_id": "Session ID: ",
        },
        defaults={"path": "./armory"},
        argv=["chat", "resume"],
    ),
]

