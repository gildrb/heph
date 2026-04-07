"""Slash command registry and handlers."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from hephaistos.app.autocomplete import CommandSuggestion
from hephaistos.app.display import (
    STYLE_DIM,
    STYLE_PROMPT,
    print_error,
    print_info,
    print_success,
    styled,
)
from hephaistos.app.menu import MenuOption, confirm, select_option
from hephaistos.providers.config import ProviderConfig

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession


class CommandResult:
    __slots__ = ("new_session", "output", "should_exit")

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
        tool_count = 7 if s.armory_path else 0
        mode = "agent (tools)" if s.armory_path else "plain chat"
        usage_summary = s.usage.summary()
        mem_count = len(s._memory.entries) if s._memory else 0

        lines = [
            f"  Armory:    {armory}",
            f"  Session:   {s.session_id}",
            f"  Title:     {title}",
            f"  Model:     {s.config.model}",
            f"  API:       {s.config.base_url}",
            (
                f"  Key:       configured"
                if s.config.resolved_api_key
                else f"  Key:       {styled('not set', STYLE_DIM)}"
            ),
            f"  Mode:      {mode}",
            f"  Tools:     {tool_count}",
            f"  Messages:  {msg_count}",
            f"  Memory:    {mem_count} concepts",
            f"  API calls: {usage_summary['api_calls']}",
            (
                f"  Tokens:    {usage_summary['total_tokens']}"
                f" (prompt: {usage_summary['prompt_tokens']},"
                f" completion: {usage_summary['completion_tokens']})"
            ),
            f"  Cost:      ${usage_summary['cost_usd']:.4f}",
            f"  Dirty:     {'yes' if s.dirty else 'no'}",
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

        if session_has_messages(s) and not confirm("Clear conversation?", default=False):
            print_info("Cancelled.")
            return CommandResult()

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

        # Direct set: /model <model-name>
        if args.strip():
            old = s.config.model
            s.config.model = args.strip()
            print_success(f"Model: {old} -> {s.config.model}")
            return CommandResult()

        # No args: show unified model picker
        pc = ProviderConfig.load()
        active = pc.get_active()
        current_model = s.config.model

        # Build flat list of (provider_slug, model_name) across all providers
        options: list[MenuOption] = []
        model_map: list[tuple[str, str]] = []  # parallel to options: (slug, model)

        for slug, provider in pc.providers.items():
            if slug == "custom" and not provider.models:
                continue
            for model in provider.models:
                is_current = (
                    (provider.active and model == current_model)
                    or (not active and model == current_model)
                )
                desc = f"via {provider.display_name}"
                if is_current:
                    desc += " ← current"
                options.append(MenuOption(model, desc, is_current=is_current))
                model_map.append((slug, model))

        if not options:
            has_key = bool(s.config.resolved_api_key)
            lines = [
                f"  Model:   {s.config.model}",
                f"  API:     {s.config.base_url}",
                f"  Key:     {'configured' if has_key else styled('not set', STYLE_DIM)}",
                "",
                "  No models configured. Use /provider to set up providers.",
            ]
            print("\n".join(lines))
            return CommandResult()

        selected = select_option("Model", options)
        if selected is None:
            return CommandResult()

        slug, model = model_map[selected]

        # Switch provider and model
        pc.set_active(slug)
        p = pc.providers[slug]
        p.current_model = model
        pc.apply_to_config(s.config)
        pc.save()
        print_success(f"Switched to {p.display_name} / {model}")
        return CommandResult()


class ApiCommand(Command):
    name = "api"
    description = "Manage API key (keychain) or base URL"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.providers.config import ProviderConfig
        from hephaistos.providers.keyring_store import (
            mask_key,
            resolve_key,
            set_volatile,
            store_key,
        )

        s = _ensure_session(session)
        parts = args.strip().split(maxsplit=1)

        if not parts:
            # Show current status — never reveal the raw key
            pc = ProviderConfig.load()
            active = pc.get_active()
            slug = active.slug if active else ""
            env_var = active.api_key_env if active else ""

            key = resolve_key(slug, env_var) if slug else ""
            key_display = mask_key(key) if key else styled("not set", STYLE_DIM)

            source = ""
            if key:
                from hephaistos.providers import keyring_store as ks
                if ks.retrieve_key(slug):
                    source = "keychain"
                elif env_var and os.environ.get(env_var, "").strip():
                    source = f"env ({env_var})"
                elif ks.get_volatile(slug):
                    source = "volatile (session-only)"
                else:
                    source = "unknown"

            lines = [
                f"  Base URL:  {s.config.base_url}",
                f"  API Key:   {key_display}",
            ]
            if source:
                lines.append(f"  Source:    {source}")
            print("\n".join(lines))
            return CommandResult()

        subcmd = parts[0].lower()
        value = parts[1] if len(parts) > 1 else ""

        if subcmd in ("key", "set-key", "apikey"):
            if not value:
                print_error("Usage: /api key <your-api-key>")
                return CommandResult()

            raw_key = value.strip()
            pc = ProviderConfig.load()
            active = pc.get_active()
            slug = active.slug if active else "custom"

            # Try keychain first; fall back to volatile
            try:
                store_key(slug, raw_key)
                print_success(f"API key saved to keychain for '{slug}'.")
            except Exception:
                set_volatile(slug, raw_key)
                print_success(
                    "API key set for this session only (keychain unavailable)."
                )

            # Also set volatile so the current session picks it up immediately
            set_volatile(slug, raw_key)
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
        s.conversation.messages = [
            *system_msgs,
            Message(
                role="system",
                content="[Conversation summary] " + summary,
            ),
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
        tool_msgs = [m for m in s.conversation.messages if m.role == "tool"]
        total_chars = sum(len(m.content) for m in s.conversation.messages)
        est_tokens = total_chars // 4
        usage_summary = s.usage.summary()
        lines = [
            f"  Turns:     {len(user_msgs)}",
            f"  User:      {len(user_msgs)} messages",
            f"  Assistant: {len(asst_msgs)} messages",
        ]
        if tool_msgs:
            lines.append(f"  Tool:      {len(tool_msgs)} results")
        mem_count = len(s._memory.entries) if s._memory else 0
        lines.extend([
            f"  Memory:    {mem_count} concepts learned",
            f"  Chars:     {total_chars}",
            f"  ~Tokens:   ~{est_tokens}",
            f"  Max tokens: {s.config.max_tokens}",
            "",
            f"  API calls: {usage_summary['api_calls']}",
            f"  Tokens:    {usage_summary['total_tokens']}",
            f"  Cost:      ${usage_summary['cost_usd']:.4f}",
        ])
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


class ProviderCommand(Command):
    name = "provider"
    description = "Show or switch LLM provider and model"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        pc = ProviderConfig.load()
        parts = args.strip().split()

        if not parts:
            return self._show(pc)

        sub = parts[0].lower()
        if sub == "use" and len(parts) >= 2:
            slug = parts[1].lower()
            model = parts[2] if len(parts) >= 3 else ""
            return self._use(pc, s, slug, model)
        if sub == "model" and len(parts) >= 2:
            return self._set_model(pc, s, parts[1])

        print_error("Usage: /provider [use <slug> [model] | model <name>]")
        return CommandResult()

    @staticmethod
    def _show(pc: ProviderConfig) -> CommandResult:
        active = pc.get_active()
        if active:
            print(f"  Current: {active.resolved_model} via {active.display_name}")
        else:
            print_info("No active provider configured.")
        print()
        print("  Configured providers & models:")

        for slug, p in pc.providers.items():
            bracket = f"    [{slug}]"
            if p.active:
                bracket += " \u2190 active"
            print(bracket)

            if slug == "custom":
                print(f"      endpoint: {p.endpoint}")
                print(f"      {styled('(use /provider use custom <model> to set)', STYLE_DIM)}")
            else:
                for m in p.models:
                    line = f"      {m}"
                    if p.active and m == p.current_model:
                        line += " \u2190 current"
                    print(line)
            print()

        return CommandResult()

    @staticmethod
    def _use(pc: ProviderConfig, session: ChatSession, slug: str, model: str) -> CommandResult:
        if slug not in pc.providers:
            print_error(f"Unknown provider: {slug}")
            print_info(f"Available: {', '.join(pc.providers)}")
            return CommandResult()

        pc.set_active(slug)
        p = pc.providers[slug]

        if model:
            if model in p.models:
                p.current_model = model
            elif p.models:
                print_error(f"Model '{model}' not found in {slug}")
                print_info(f"Available: {', '.join(p.models)}")
                pc.save()
                return CommandResult()
        elif not p.current_model and p.models:
            p.current_model = p.models[0]

        pc.apply_to_config(session.config)
        pc.save()
        print_success(f"Switched to {p.display_name} / {p.resolved_model}")
        return CommandResult()

    @staticmethod
    def _set_model(pc: ProviderConfig, session: ChatSession, model: str) -> CommandResult:
        active = pc.get_active()
        if active is None:
            print_error("No active provider. Use /provider use <slug> first.")
            return CommandResult()
        if model not in active.models:
            print_error(f"Model '{model}' not found in {active.slug}")
            print_info(f"Available: {', '.join(active.models)}")
            return CommandResult()

        active.current_model = model
        pc.apply_to_config(session.config)
        pc.save()
        print_success(f"Model: {model}")
        return CommandResult()


class LoginCommand(Command):
    name = "login"
    description = "Log in with a provider subscription (OAuth)"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.providers.oauth import available_providers, login as oauth_login

        providers = available_providers()
        if not providers:
            print_info("No OAuth providers available.")
            return CommandResult()

        # If a provider slug is given directly
        slug = args.strip().lower()
        if slug:
            matching = [p for p in providers if p["slug"] == slug]
            if not matching:
                print_error(f"Unknown provider: {slug}")
                print_info(f"Available: {', '.join(p['slug'] for p in providers)}")
                return CommandResult()
            result = oauth_login(slug)
            if result is None:
                print_error("Login failed.")
            return CommandResult()

        # Show picker
        options = []
        for p in providers:
            status = "✓ logged in" if p["logged_in"] else "not logged in"
            options.append(MenuOption(p["display_name"], status))

        selected = select_option("OAuth Login", options)
        if selected is None:
            return CommandResult()

        chosen = providers[selected]
        result = oauth_login(chosen["slug"])
        if result is None:
            print_error("Login failed.")
        return CommandResult()


class LogoutCommand(Command):
    name = "logout"
    description = "Log out of a provider subscription"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.providers.oauth import available_providers, logout as oauth_logout

        providers = available_providers()
        logged_in = [p for p in providers if p["logged_in"]]
        if not logged_in:
            print_info("No active OAuth sessions.")
            return CommandResult()

        slug = args.strip().lower()
        if slug:
            oauth_logout(slug)
            print_success(f"Logged out of {slug}.")
            return CommandResult()

        options = [MenuOption(p["display_name"], p["slug"]) for p in logged_in]
        selected = select_option("OAuth Logout", options)
        if selected is None:
            return CommandResult()
        oauth_logout(logged_in[selected]["slug"])
        print_success(f"Logged out of {logged_in[selected]['display_name']}.")
        return CommandResult()


class ModelsCommand(Command):
    name = "models"
    description = "List all available models across providers"

    def handle(self, session: object, args: str) -> CommandResult:
        from hephaistos.providers.registry import get_registry

        registry = get_registry()
        models = registry.list_models()

        if not models:
            print_info("No models in registry.")
            return CommandResult()

        # Group by provider
        current_provider = ""
        for m in models:
            if m.provider != current_provider:
                current_provider = m.provider
                print(f"\n  {styled(current_provider, STYLE_PROMPT)}")

            price = f"${m.prompt_price_per_1k:.4f}/${m.completion_price_per_1k:.4f}" if not m.is_free else "free"
            ctx = f"{m.context_window // 1000}k ctx"
            tags = f" [{', '.join(m.tags)}]" if m.tags else ""
            print(f"    {m.name:<45} {ctx:<12} {price}{tags}")

        print()
        return CommandResult()


class UsageCommand(Command):
    name = "usage"
    description = "Show token usage and cost for this session"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        summary = s.usage.summary()
        lines = [
            f"  API calls:     {summary['api_calls']}",
            f"  Prompt tokens: {summary['prompt_tokens']}",
            f"  Output tokens: {summary['completion_tokens']}",
            f"  Total tokens:  {summary['total_tokens']}",
            f"  Estimated cost: ${summary['cost_usd']:.4f}",
        ]
        print("\n".join(lines))
        return CommandResult()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def _ensure_session(session: object):
    from hephaistos.chat.session import ChatSession

    if not isinstance(session, ChatSession):
        raise TypeError(f"Expected ChatSession, got {type(session).__name__}")
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
            ProviderCommand,
            LoginCommand,
            LogoutCommand,
            ModelsCommand,
            UsageCommand,
        ):
            _registry.register(cmd_class())
    return _registry
