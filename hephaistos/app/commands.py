"""Slash command registry and handlers."""

from __future__ import annotations

import sys

from hephaistos.app.autocomplete import CommandSuggestion
from hephaistos.app.display import (
    STYLE_DIM,
    STYLE_PROMPT,
    print_error,
    print_info,
    print_success,
    styled,
)


class CommandResult:
    __slots__ = ("output", "should_exit", "new_session")

    def __init__(
        self,
        output: str | None = None,
        should_exit: bool = False,
        new_session: object | None = None,
    ) -> None:
        self.output = output
        self.should_exit = should_exit
        self.new_session = new_session


class Command:
    """Base class for slash commands. Subclasses set class-level attributes."""

    name: str = ""
    description: str = ""
    aliases: tuple[str, ...] = ()
    hidden: bool = False

    def handle(self, session: object, args: str) -> CommandResult:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------


class HelpCommand(Command):
    name = "help"
    description = "Show available commands"
    aliases = ("?", "h")

    def handle(self, session: object, args: str) -> CommandResult:
        registry = get_registry()
        visible = [c for c in registry.commands if not c.hidden]
        max_name = max(len(c.name) for c in visible)
        lines = []
        lines.append(styled("Commands:", STYLE_PROMPT))
        for cmd in sorted(visible, key=lambda c: c.name):
            padded = f"  /{cmd.name}".ljust(max_name + 4)
            lines.append(f"{padded} {cmd.description}")
        lines.append("")
        lines.append(styled("Modes:", STYLE_PROMPT))
        pad = max_name + 2
        lines.append(f"  !{'command'.ljust(pad)} Run a shell command")
        lines.append("")
        lines.append(styled("Shortcuts:", STYLE_PROMPT))
        lines.append("  Up/Down         Browse input history")
        lines.append("  Tab             Autocomplete slash commands")
        lines.append("  Ctrl+C          Cancel current response")
        lines.append("  Ctrl+D          Exit shell")
        lines.append("")
        print("\n".join(lines))
        return CommandResult()


class ExitCommand(Command):
    name = "exit"
    description = "Leave the shell"
    aliases = ("quit", "q")

    def handle(self, session: object, args: str) -> CommandResult:
        return CommandResult(should_exit=True)


class StatusCommand(Command):
    name = "status"
    description = "Show armory, session, and model info"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        armory = str(s.armory_path) if s.armory_path else styled("none", STYLE_DIM)
        title = s.title or styled("(untitled)", STYLE_DIM)
        msg_count = sum(1 for m in s.conversation.messages if m.role != "system")
        lines = [
            f"  Armory:   {armory}",
            f"  Session:  {s.session_id}",
            f"  Title:    {title}",
            f"  Model:    {s.config.model}",
            f"  API:      {s.config.base_url}",
            f"  Messages: {msg_count}",
            f"  Dirty:    {'yes' if s.dirty else 'no'}",
        ]
        print("\n".join(lines))
        return CommandResult()


class SaveCommand(Command):
    name = "save"
    description = "Save current chat to armory"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.chat import storage as chat_storage
        from hephaistos.chat.session import save_session

        s = _ensure_session(session)
        try:
            path = save_session(s)
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))
            return CommandResult()
        print_success(f"Saved to {path}")
        return CommandResult()


class ClearCommand(Command):
    name = "clear"
    description = "Start a fresh chat session"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.chat import storage as chat_storage
        from hephaistos.chat.session import (
            create_session,
            save_session,
            session_has_messages,
        )

        s = _ensure_session(session)
        if s.armory_path and s.dirty and session_has_messages(s):
            try:
                save_session(s)
                print_info("Previous session saved.")
            except chat_storage.ChatStorageError:
                pass
        new = create_session(s.config, s.armory_path)
        print_success("Started fresh session.")
        return CommandResult(new_session=new)


class ArmoryCommand(Command):
    name = "armory"
    description = "Open the armory management menu"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.app.shell import _handle_armory_command

        s = _ensure_session(session)
        new = _handle_armory_command(s)
        return CommandResult(new_session=new)


class ModelCommand(Command):
    name = "model"
    description = "Show or switch the active model"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        if not args.strip():
            has_key = bool(s.config.api_key)
            lines = [
                f"  Model:   {s.config.model}",
                f"  API:     {s.config.base_url}",
                f"  Key:     {'configured' if has_key else styled('not set', STYLE_DIM)}",
            ]
            print("\n".join(lines))
            return CommandResult()
        old = s.config.model
        s.config.model = args.strip()
        print_success(f"Model: {old} -> {s.config.model}")
        return CommandResult()


class ApiCommand(Command):
    name = "api"
    description = "Set API key or base URL"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        parts = args.strip().split(maxsplit=1)
        if not parts:
            bool(s.config.api_key)
            masked = f"{s.config.api_key[:8]}...{s.config.api_key[-4:]}" if len(s.config.api_key) > 12 else ("*" * len(s.config.api_key)) if s.config.api_key else styled("not set", STYLE_DIM)
            lines = [
                f"  Base URL:  {s.config.base_url}",
                f"  API Key:   {masked}",
            ]
            print("\n".join(lines))
            return CommandResult()

        subcmd = parts[0].lower()
        value = parts[1] if len(parts) > 1 else ""

        if subcmd in ("key", "set-key", "apikey"):
            if not value:
                print_error("Usage: /api key <your-api-key>")
                return CommandResult()
            s.config.api_key = value.strip()
            print_success("API key updated.")
            return CommandResult()

        if subcmd in ("url", "base-url", "baseurl"):
            if not value:
                print_error("Usage: /api url <base-url>")
                return CommandResult()
            s.config.base_url = value.strip().rstrip("/")
            print_success(f"Base URL: {s.config.base_url}")
            return CommandResult()

        print_error(f"Unknown subcommand: {subcmd}")
        print_info("Usage: /api key <key> | /api url <url>")
        return CommandResult()


class CompactCommand(Command):
    name = "compact"
    description = "Summarize conversation to reduce context size"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.chat.engine import Conversation, Message, stream_reply
        from hephaistos.chat.session import session_has_messages

        s = _ensure_session(session)
        if not session_has_messages(s):
            print_info("Nothing to compact.")
            return CommandResult()

        non_system = [m for m in s.conversation.messages if m.role != "system"]
        summary_prompt = (
            "Summarize the following conversation in a concise paragraph. "
            "Preserve key facts, decisions, and context needed to continue.\n\n"
        )
        for msg in non_system:
            summary_prompt += f"{msg.role}: {msg.content}\n"

        temp = Conversation()
        temp.add("system", "You are a helpful assistant that summarizes conversations.")
        temp.add("user", summary_prompt)

        print(styled("Compacting...", STYLE_DIM))
        parts: list[str] = []
        for chunk in stream_reply(s.config, temp):
            sys.stdout.write(chunk)
            sys.stdout.flush()
            parts.append(chunk)
        summary = "".join(parts)
        sys.stdout.write("\n")
        sys.stdout.flush()

        system_msgs = [m for m in s.conversation.messages if m.role == "system"]
        s.conversation.messages = system_msgs + [
            Message(
                role="system",
                content="[Conversation summary] " + summary,
            )
        ]
        s.dirty = True
        print_success("Compacted.")
        return CommandResult()


class HistoryCommand(Command):
    name = "history"
    description = "Show conversation turn count and token estimate"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        user_msgs = [m for m in s.conversation.messages if m.role == "user"]
        asst_msgs = [m for m in s.conversation.messages if m.role == "assistant"]
        total_chars = sum(len(m.content) for m in s.conversation.messages)
        est_tokens = total_chars // 4
        lines = [
            f"  Turns:     {len(user_msgs)}",
            f"  User:      {len(user_msgs)} messages",
            f"  Assistant: {len(asst_msgs)} messages",
            f"  Chars:     {total_chars}",
            f"  ~Tokens:   ~{est_tokens}",
        ]
        print("\n".join(lines))
        return CommandResult()


class EditCommand(Command):
    name = "edit"
    description = "Edit and resend the last user message"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        last_user = None
        last_user_idx = -1
        for i in range(len(s.conversation.messages) - 1, -1, -1):
            if s.conversation.messages[i].role == "user":
                last_user = s.conversation.messages[i]
                last_user_idx = i
                break
        if last_user is None:
            print_info("No user messages to edit.")
            return CommandResult()

        original = last_user.content
        print_info(
            f"Last message: {original[:100]}{'...' if len(original) > 100 else ''}"
        )
        print(styled("Enter new message (empty to cancel):", STYLE_PROMPT))
        try:
            new_text = input("  ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return CommandResult()

        if not new_text:
            print_info("Cancelled.")
            return CommandResult()

        # Remove messages from last_user_idx onward
        s.conversation.messages = s.conversation.messages[:last_user_idx]
        s.dirty = True

        return CommandResult(output=f"__RESEND__:{new_text}")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def _ensure_session(session: object):
    from hephaistos.chat.session import ChatSession

    assert isinstance(session, ChatSession)
    return session


class CommandRegistry:
    def __init__(self) -> None:
        self.commands: list[Command] = []

    def register(self, cmd: Command) -> None:
        self.commands.append(cmd)

    def find(self, name: str) -> Command | None:
        name_lower = name.lower()
        for cmd in self.commands:
            if cmd.name == name_lower or name_lower in cmd.aliases:
                return cmd
        return None

    def suggestions(self) -> list[CommandSuggestion]:
        return [
            CommandSuggestion(name=cmd.name, description=cmd.description)
            for cmd in self.commands
            if not cmd.hidden
        ]


_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
        for cmd_class in (
            HelpCommand,
            ExitCommand,
            StatusCommand,
            SaveCommand,
            ClearCommand,
            ArmoryCommand,
            ModelCommand,
            ApiCommand,
            CompactCommand,
            HistoryCommand,
            EditCommand,
        ):
            _registry.register(cmd_class())
    return _registry
