"""Session management commands: status, new, and sessions."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from ai.providers.endpoints import provider_uses_keyless_access
from ai.runtime import has_configured_access
from harness.chat import storage as chat_storage
from harness.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    save_session,
    session_has_messages,
)
from harness.chat.usage import load_usage_summaries
from interfaces.terminal import STYLE_DIM, print_error, print_info, print_success, styled

from heph.commands._base import (
    Command,
    CommandResult,
    ensure_session,
    format_duration,
)


def _session_status(session: ChatSession) -> str:
    msg_count = sum(1 for message in session.conversation.messages if message.role != "system")
    user_msgs = sum(1 for message in session.conversation.messages if message.role == "user")
    assistant_msgs = sum(
        1 for message in session.conversation.messages if message.role == "assistant"
    )
    usage_summary = session.usage.summary()
    lines = [
        "Current session:",
        f"  Armory:    {_session_armory_label(session)}",
        f"  Session:   {session.session_id}",
        f"  Title:     {session.title or styled('(untitled)', STYLE_DIM)}",
        f"  Model:     {session.config.model}",
        f"  API:       {session.config.base_url}",
        f"  Key:       {_session_key_status(session)}",
        f"  Mode:      {_session_runtime_label(session)}",
        f"  Runtime:   {format_duration(session.current_run_seconds)}",
        f"  Tools:     {_session_tool_count(session)}",
        f"  Messages:  {msg_count}",
        f"  Turns:     {user_msgs}",
        f"  Assistant: {assistant_msgs} messages",
        f"  Memory:    {_session_memory_count(session)} concepts",
        f"  API calls: {usage_summary['api_calls']}",
        (
            f"  Tokens:    {usage_summary['total_tokens']}"
            f" (prompt: {usage_summary['prompt_tokens']},"
            f" completion: {usage_summary['completion_tokens']})"
        ),
        f"  Cost:      ${usage_summary['cost_usd']:.4f}",
        f"  Dirty:     {'yes' if session.dirty else 'no'}",
    ]
    if session.armory_path is not None:
        lines.extend(_armory_stats(session.armory_path))
    return "\n".join(lines)


def _armory_stats(armory_path: Path) -> list[str]:
    usage_summaries = load_usage_summaries(armory_path)
    return [
        "",
        "Armory:",
        f"  Path:       {armory_path}",
        f"  Saved:      {len(chat_storage.list_sessions(armory_path))} sessions",
        f"  API calls:  {sum(int(item['api_calls']) for item in usage_summaries)}",
        f"  Tokens:     {sum(int(item['total_tokens']) for item in usage_summaries)}",
        f"  Cost:       ${sum(float(item['cost_usd']) for item in usage_summaries):.4f}",
    ]


def _session_armory_label(session: ChatSession) -> str:
    return str(session.armory_path) if session.armory_path else styled("none", STYLE_DIM)


def _session_key_status(session: ChatSession) -> str:
    if provider_uses_keyless_access(session.config.provider_slug, session.config.base_url):
        return "not needed (free provider)"
    if has_configured_access(session.config, refresh_oauth=False):
        return "configured"
    return styled("not set", STYLE_DIM)


def _session_runtime_label(session: ChatSession) -> str:
    return "agent (tools)" if session.armory_path else "plain chat"


def _session_tool_count(session: ChatSession) -> int:
    return 7 if session.armory_path else 0


def _session_memory_count(session: ChatSession) -> int:
    return len(session.memory.entries) if session.memory else 0


def _autosave_before_new_chat(session: ChatSession) -> None:
    if not (session.armory_path and session.dirty and session_has_messages(session)):
        return
    with suppress(chat_storage.ChatStorageError):
        save_session(session)


def _create_new_chat(session: ChatSession) -> ChatSession | None:
    _autosave_before_new_chat(session)
    try:
        if session.armory_path is None:
            new_session = create_plain_session(session.config)
        else:
            new_session = create_session(session.config, session.armory_path)
    except SessionError as exc:
        print_error(str(exc))
        return None
    print_success("New chat started.")
    return new_session


def _detach_armory(session: ChatSession) -> ChatSession | None:
    if session.armory_path is None:
        print_info("No armory attached.")
        return None
    _autosave_before_new_chat(session)
    new_session = create_plain_session(session.config)
    print_success("Armory detached.")
    return new_session


class StatusCommand(Command):
    name = "status"
    description = "Show session, usage, armory, and review info"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        return CommandResult(output=_session_status(s))


class StatsCommand(StatusCommand):
    name = "stats"
    description = "Alias for /status with session and armory statistics"

    def handle(self, session: object, args: str) -> CommandResult:
        result = super().handle(session, args)
        if result.output is not None:
            print(result.output)
        return CommandResult()


class NewCommand(Command):
    name = "new"
    description = "Start a new chat"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        new = _create_new_chat(s)
        return CommandResult(new_session=new)


class DetachCommand(Command):
    name = "detach"
    description = "Detach the current armory"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        return CommandResult(new_session=_detach_armory(s))


class ArmoryCommand(Command):
    name = "armory"
    description = "Browse, open, or create armories"

    def handle(self, session: object, args: str) -> CommandResult:
        del session
        subcmd = args.strip().lower()
        if subcmd not in {"", "menu", "manage", "open", "create", "new"}:
            print_error("Usage: /armory [open|create]")
            return CommandResult()
        print_info("Use the /armory browser in the TUI to open or create armories.")
        return CommandResult()


class SessionsCommand(Command):
    name = "sessions"
    description = "Switch between saved sessions"

    def handle(self, session: object, args: str) -> CommandResult:
        del session
        subcmd = args.strip().lower()
        if subcmd not in {"", "list", "recent", "browse", "menu", "resume", "last", "latest"}:
            print_error("Usage: /sessions [list|recent|browse|resume]")
            return CommandResult()
        print_info("Use the /sessions browser in the TUI to list or resume saved chats.")
        return CommandResult()


class TurnCommand(Command):
    name = "turn"
    description = "Branch from an earlier completed turn"

    def handle(self, session: object, args: str) -> CommandResult:
        del session
        subcmd = args.strip().lower()
        known_subcommands = {"list", "history", "browse", "menu", "resume", "last", "latest"}
        if subcmd and subcmd not in known_subcommands and not subcmd.startswith("t"):
            print_error("Usage: /turn [list|browse|T#]")
            return CommandResult()
        print_info("Use the /turn browser in the TUI to branch from an earlier reply.")
        return CommandResult()
