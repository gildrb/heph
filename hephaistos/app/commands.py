"""Slash command registry and handlers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.autocomplete import CommandSuggestion
from hephaistos.app.display import (
    STYLE_DIM,
    direct_input,
    print_error,
    print_info,
    print_success,
    styled,
)
from hephaistos.app.menu import MenuOption, browse_directory, confirm, select_option
from hephaistos.app.palette import STYLE_PROMPT, THEME_PRESETS, current_theme_name, set_theme
from hephaistos.app.workspace import (
    handle_armory_command,
    list_saved_chats,
    resume_saved_chat,
)
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import Conversation, Message, stream_reply
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    replace_system_prompt,
    save_session,
    session_has_messages,
    validate_armory_path,
)
from hephaistos.harness.persona import get_persona, list_personas
from hephaistos.memory.supermemory import (
    SUPERMEMORY_API_KEY_ENV,
    SUPERMEMORY_DEFAULT_PROFILE,
    SUPERMEMORY_PROVIDER_SLUG,
    SUPERMEMORY_URL_ENV,
    resolve_supermemory_key,
)
from hephaistos.parameters.settings import clear_setting, load_app_settings, save_setting
from hephaistos.providers import keyring_store, oauth
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.keyring_store import mask_key, resolve_key, set_volatile, store_key
from hephaistos.providers.model_support import is_supported_model_for_endpoint
from hephaistos.providers.registry import get_registry as get_provider_registry
from hephaistos.telemetry import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)
from hephaistos.vocab.drill import run_drill
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.state import load_schedule, save_schedule


class CommandResult:
    __slots__ = ("new_session", "output", "should_exit")

    def __init__(
        self,
        output: str | None = None,
        should_exit: bool = False,
        new_session: ChatSession | None = None,
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


class HelpCommand(Command):
    name = "help"
    description = "Show available commands"
    aliases = ("?", "h")

    def handle(self, session: object, args: str) -> CommandResult:
        registry = get_registry()
        visible = [c for c in registry.commands if not c.hidden]
        max_name = max(len(c.name) for c in visible)
        lines: list[str] = []
        lines.append(styled("Commands", STYLE_PROMPT))
        for cmd in sorted(visible, key=lambda c: c.name):
            padded = f"  /{cmd.name}".ljust(max_name + 4)
            lines.append(f"{padded} {cmd.description}")
        lines.append("")
        lines.append(styled("Input", STYLE_PROMPT))
        pad = max_name + 2
        lines.append(f"  !{'command'.ljust(pad)} Run a shell command")
        lines.append("  /help           Show command reference")
        lines.append("")
        lines.append(styled("Shortcuts", STYLE_PROMPT))
        lines.append("  Up/Down         Browse input history")
        lines.append("  Tab             Autocomplete slash commands")
        lines.append("  Alt+Enter       Insert newline")
        lines.append("  Ctrl+C          Cancel current response")
        lines.append("  Ctrl+D          Exit shell")
        lines.append("")
        print("\n".join(lines))
        return CommandResult()


class ExitCommand(Command):
    name = "exit"
    description = "Leave the shell"
    aliases = ()

    def handle(self, session: object, args: str) -> CommandResult:
        return CommandResult(should_exit=True)


class QuitCommand(Command):
    name = "quit"
    description = "Leave the shell"
    aliases = ("q",)

    def handle(self, session: object, args: str) -> CommandResult:
        print_info(f"Exiting... (/{self.name} \u2192 /exit)")
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
        mem_count = len(s.memory.entries) if s.memory else 0

        lines = [
            f"  Armory:    {armory}",
            f"  Session:   {s.session_id}",
            f"  Title:     {title}",
            f"  Model:     {s.config.model}",
            f"  Persona:   {s.persona.display_name}",
            f"  API:       {s.config.base_url}",
            (
                "  Key:       configured"
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
        new: ChatSession
        try:
            new = (
                create_plain_session(s.config)
                if s.armory_path is None
                else create_session(s.config, s.armory_path)
            )
        except SessionError as exc:
            print_error(str(exc))
            return CommandResult()
        print_success("Started fresh session.")
        capture_analytics(
            "session_cleared",
            {
                "mode": "armory" if new.armory_path is not None else "plain",
                "model": new.config.model,
            },
        )
        return CommandResult(new_session=new)


class ArmoryCommand(Command):
    name = "armory"
    description = "Open the armory management menu"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        new = handle_armory_command(s)
        return CommandResult(new_session=new)


class ChatsCommand(Command):
    name = "chats"
    description = "List saved chats in the active armory"
    aliases = ("sessions",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        list_saved_chats(s)
        return CommandResult()


class ResumeCommand(Command):
    name = "resume"
    description = "Resume a saved chat by menu or session ID prefix"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        new = resume_saved_chat(s, args.strip())
        return CommandResult(new_session=new)


class ModelCommand(Command):
    name = "model"
    description = "Show or switch the active model"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        if args.strip():
            model_name = args.strip()
            if not is_supported_model_for_endpoint(model_name, s.config.base_url):
                print_error("Model unavailable.")
                return CommandResult()
            old = s.config.model
            s.config.model = model_name
            print_success(f"Model: {old} -> {s.config.model}")
            capture_analytics("model_changed", {"from_model": old, "to_model": s.config.model})
            return CommandResult()
        pc = ProviderConfig.load()
        active = pc.get_active()
        current_model = s.config.model
        options: list[MenuOption] = []
        model_map: list[tuple[str, str]] = []  # parallel to options: (slug, model)

        for slug, provider in pc.providers.items():
            if slug == "custom" and not provider.models:
                continue
            for model in provider.models:
                is_current = (provider.active and model == current_model) or (
                    not active and model == current_model
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
        pc.set_active(slug)
        p = pc.providers[slug]
        p.current_model = model
        pc.apply_to_config(s.config)
        pc.save()
        print_success(f"Switched to {p.display_name} / {model}")
        capture_analytics(
            "model_changed",
            {
                "provider": slug,
                "to_model": model,
            },
        )
        return CommandResult()


class ApiCommand(Command):
    name = "api"
    description = "Manage API key (keychain) or base URL"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        parts = args.strip().split(maxsplit=1)

        if not parts:
            pc = ProviderConfig.load()
            active = pc.get_active()
            slug = active.slug if active else ""
            env_var = active.api_key_env if active else ""

            key = resolve_key(slug, env_var) if slug else ""
            key_display = mask_key(key) if key else styled("not set", STYLE_DIM)

            source = ""
            if key:
                if keyring_store.retrieve_key(slug):
                    source = "keychain"
                elif env_var and os.environ.get(env_var, "").strip():
                    source = f"env ({env_var})"
                elif keyring_store.get_volatile(slug):
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
            try:
                store_key(slug, raw_key)
                print_success(f"API key saved to keychain for '{slug}'.")
            except Exception:
                set_volatile(slug, raw_key)
                print_success("API key set for this session only (keychain unavailable).")
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
        capture_analytics(
            "conversation_compacted",
            {
                "model": s.config.model,
                "message_count": len(non_system),
                "summary_length": len(summary),
            },
        )
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
        mem_count = len(s.memory.entries) if s.memory else 0
        lines.extend(
            [
                f"  Memory:    {mem_count} concepts learned",
                f"  Chars:     {total_chars}",
                f"  ~Tokens:   ~{est_tokens}",
                f"  Max tokens: {s.config.max_tokens}",
                "",
                f"  API calls: {usage_summary['api_calls']}",
                f"  Tokens:    {usage_summary['total_tokens']}",
                f"  Cost:      ${usage_summary['cost_usd']:.4f}",
            ]
        )
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
        print_info(f"Last message: {original[:100]}{'...' if len(original) > 100 else ''}")
        print(styled("Enter new message (empty to cancel):", STYLE_PROMPT))
        try:
            new_text = direct_input("  ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return CommandResult()

        if not new_text:
            print_info("Cancelled.")
            return CommandResult()
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
                pc.apply_to_config(session.config)
                pc.save()
                return CommandResult()
        elif not p.current_model and p.models:
            p.current_model = p.models[0]

        pc.apply_to_config(session.config)
        pc.save()
        print_success(f"Switched to {p.display_name} / {p.resolved_model}")
        capture_analytics(
            "provider_changed",
            {
                "provider": slug,
                "model": p.resolved_model,
            },
        )
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
        capture_analytics(
            "model_changed",
            {
                "provider": active.slug,
                "to_model": model,
            },
        )
        return CommandResult()


class ModelsCommand(Command):
    name = "models"
    description = "List all available models across providers"

    def handle(self, session: object, args: str) -> CommandResult:
        registry = get_provider_registry()
        models = registry.list_models()
        if args.strip().lower() == "study":
            models = [model for model in models if "study" in model.tags]

        if not models:
            print_info("No models in registry.")
            return CommandResult()
        if args.strip().lower() == "study":
            print_info(
                "Study picks favor low cost, speed, and instruction following because "
                "Hephaistos handles RAG retrieval and citation checks."
            )
        current_provider = ""
        for m in models:
            if m.provider != current_provider:
                current_provider = m.provider
                print(f"\n  {styled(current_provider, STYLE_PROMPT)}")

            price = (
                f"${m.prompt_price_per_1k:.4f}/${m.completion_price_per_1k:.4f}"
                if not m.is_free
                else "free"
            )
            ctx = f"{m.context_window // 1000}k ctx"
            tags = f" [{', '.join(m.tags)}]" if m.tags else ""
            print(f"    {m.name:<45} {ctx:<12} {price}{tags}")

        print()
        return CommandResult()


class RecommendCommand(Command):
    name = "recommend"
    description = "Recommend models for study sessions"

    def handle(self, session: object, args: str) -> CommandResult:
        return ModelsCommand().handle(session, "study")


class MemoryCommand(Command):
    name = "memory"
    description = "Manage study memory and Supermemory setup"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        parts = args.strip().split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "status"
        value = parts[1] if len(parts) > 1 else ""

        if subcmd == "status":
            return self._status(s)
        if subcmd == "setup":
            return self._setup(value)
        if subcmd == "disable":
            save_setting("supermemory_enabled", False)
            save_setting("supermemory_onboarding_seen", True)
            print_success("Supermemory disabled. Local armory memory remains active.")
            return CommandResult()
        if subcmd == "profile":
            return self._profile(value)

        print_error("Usage: /memory [status | setup [api-key] | profile [name] | disable]")
        return CommandResult()

    @staticmethod
    def _status(session: ChatSession) -> CommandResult:
        settings = load_app_settings()
        key = resolve_supermemory_key()
        source = _supermemory_key_source()
        memory_backend = type(session.memory).__name__ if session.memory is not None else "none"
        mem_count = len(session.memory.entries) if session.memory else 0
        lines = [
            f"  Backend:     {memory_backend}",
            f"  Supermemory: {'enabled' if settings.supermemory_enabled else 'disabled'}",
            f"  Profile:     {settings.supermemory_profile or SUPERMEMORY_DEFAULT_PROFILE}",
            f"  Key:         {mask_key(key) if key else styled('not set', STYLE_DIM)}",
            f"  Key source:  {source or styled('none', STYLE_DIM)}",
            f"  URL env:     {os.environ.get(SUPERMEMORY_URL_ENV, 'default')}",
            f"  Entries:     {mem_count}",
        ]
        print("\n".join(lines))
        if not settings.supermemory_enabled:
            print_info("Run /memory setup to enable cross-armory semantic study memory.")
        return CommandResult()

    @staticmethod
    def _setup(value: str) -> CommandResult:
        print_info(
            "Supermemory stores extracted study concepts in a dedicated Hephaistos "
            "profile so they can be recalled across armories."
        )
        print_info("Only enable it if you are comfortable sending study memory to Supermemory.")
        raw_key = value.strip()
        if not raw_key and not resolve_supermemory_key():
            try:
                raw_key = direct_input(f"  {SUPERMEMORY_API_KEY_ENV}: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                print_info("Cancelled.")
                return CommandResult()
        if raw_key:
            try:
                store_key(SUPERMEMORY_PROVIDER_SLUG, raw_key)
                print_success("Supermemory API key saved to keychain.")
            except Exception:
                set_volatile(SUPERMEMORY_PROVIDER_SLUG, raw_key)
                print_success("Supermemory API key set for this session only.")
        if not resolve_supermemory_key():
            print_error("Supermemory API key is still not configured.")
            return CommandResult()

        settings = load_app_settings()
        profile = settings.supermemory_profile or SUPERMEMORY_DEFAULT_PROFILE
        try:
            entered = direct_input(f"  Profile [{profile}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            entered = ""
        if entered:
            profile = entered
        save_setting("supermemory_profile", profile)
        save_setting("supermemory_enabled", True)
        save_setting("supermemory_onboarding_seen", True)
        print_success(f"Supermemory enabled with profile '{profile}'.")
        print_info("Start a fresh armory session to use the Supermemory backend immediately.")
        return CommandResult()

    @staticmethod
    def _profile(value: str) -> CommandResult:
        if not value.strip():
            settings = load_app_settings()
            print(f"  Profile: {settings.supermemory_profile or SUPERMEMORY_DEFAULT_PROFILE}")
            return CommandResult()
        save_setting("supermemory_profile", value.strip())
        print_success(f"Supermemory profile: {value.strip()}")
        return CommandResult()


class LoginCommand(Command):
    name = "login"
    description = "Authenticate with an LLM provider via OAuth"

    def handle(self, session: object, args: str) -> CommandResult:
        options = [
            MenuOption("OpenAI Codex", "ChatGPT Plus/Pro subscription"),
        ]

        selected = select_option("Login to provider", options)
        if selected is None:
            return CommandResult()

        try:
            creds = oauth.login_openai_codex()
        except RuntimeError as exc:
            print_error(str(exc))
            return CommandResult()
        except Exception as exc:
            print_error(f"Login failed: {exc}")
            return CommandResult()

        set_volatile("openai-codex", creds.access_token)

        s = _ensure_session(session)
        pc = ProviderConfig.load()
        pc.set_active("openai-codex")
        p = pc.providers["openai-codex"]
        if not p.current_model and p.models:
            p.current_model = p.models[0]
        pc.apply_to_config(s.config)
        pc.save()
        print_success(
            f"Logged in to OpenAI Codex (account: {creds.account_id or 'unknown'}) "
            f"— switched to {p.resolved_model}"
        )
        capture_analytics("oauth_login", {"provider": "openai-codex", "model": p.resolved_model})
        return CommandResult()


class LogoutCommand(Command):
    name = "logout"
    description = "Clear stored OAuth credentials"

    def handle(self, session: object, args: str) -> CommandResult:
        providers = oauth.list_providers()
        if not providers:
            print_info("No OAuth sessions found.")
            return CommandResult()

        if len(providers) == 1:
            slug = providers[0]
            if confirm(f"Log out of {slug}?", default=True):
                oauth.clear_credentials(slug)
                print_success(f"Logged out of {slug}.")
            else:
                print_info("Cancelled.")
            return CommandResult()

        options = [MenuOption(p, "") for p in providers]
        options.append(MenuOption("All", "Log out of every provider"))
        selected = select_option("Log out of", options)
        if selected is None:
            return CommandResult()

        if selected == len(options) - 1:
            for p in providers:
                oauth.clear_credentials(p)
            print_success("Logged out of all providers.")
            capture_analytics("oauth_logout", {"provider": "all"})
        else:
            slug = providers[selected]
            oauth.clear_credentials(slug)
            print_success(f"Logged out of {slug}.")
            capture_analytics("oauth_logout", {"provider": slug})
        return CommandResult()


class PersonaCommand(Command):
    name = "persona"
    description = "Show or switch the agent persona"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        slug = args.strip().lower()

        if slug:
            persona = get_persona(slug)
            if persona is None:
                available = ", ".join(p.slug for p in list_personas())
                print_error(f"Unknown persona: {slug}")
                print_info(f"Available: {available}")
                return CommandResult()
            old_name = s.persona.display_name
            s.persona = persona
            replace_system_prompt(s)
            s.dirty = True
            print_success(f"Persona: {old_name} -> {persona.display_name}")
            return CommandResult()

        personas = list_personas()
        options = [
            MenuOption(
                p.display_name,
                f"{p.description} {'← current' if p.slug == s.persona.slug else ''}".strip(),
                is_current=(p.slug == s.persona.slug),
            )
            for p in personas
        ]

        selected = select_option("Persona", options)
        if selected is None:
            return CommandResult()

        persona = personas[selected]
        old_name = s.persona.display_name
        s.persona = persona
        replace_system_prompt(s)
        s.dirty = True
        print_success(f"Persona: {old_name} -> {persona.display_name}")
        return CommandResult()


class SettingsCommand(Command):
    name = "settings"
    description = "Manage cross-session preferences"

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        while True:
            settings = load_app_settings()
            default_armory = settings.default_armory_path or "none"
            options = [
                MenuOption(
                    "Telemetry",
                    "Usage analytics and crash reports",
                ),
                MenuOption(
                    "Appearance",
                    f"Theme: {settings.theme}",
                ),
                MenuOption(
                    "Startup",
                    f"Default armory: {default_armory}",
                ),
                MenuOption(
                    "Default model",
                    f"Current: {s.config.model}",
                ),
                MenuOption(
                    "Study memory",
                    "Local memory and Supermemory setup",
                ),
                MenuOption(
                    "Provider & credentials",
                    "Reuse /provider, /api, /login, and /logout flows",
                ),
                MenuOption("Back", "Return to the chat prompt."),
            ]
            selected = select_option("Settings", options)
            if selected is None or selected == len(options) - 1:
                return CommandResult()
            if selected == 0:
                self._telemetry_menu()
            elif selected == 1:
                self._appearance_menu()
            elif selected == 2:
                self._startup_menu()
            elif selected == 3:
                ModelCommand().handle(s, "")
            elif selected == 4:
                MemoryCommand().handle(s, "status")
            else:
                self._provider_credentials_menu(s)

    @staticmethod
    def _telemetry_description(
        *,
        enabled: bool,
        available: bool,
        overridden: bool,
    ) -> str:
        status = "enabled" if enabled else "disabled"
        availability = "available" if available else "inactive until configured"
        suffix = " · env override active" if overridden else ""
        return f"{status} · {availability}{suffix}"

    def _telemetry_menu(self) -> None:
        while True:
            settings = load_app_settings()
            options = [
                MenuOption(
                    f"[{'x' if analytics_enabled() else ' '}] Usage analytics",
                    self._telemetry_description(
                        enabled=analytics_enabled(),
                        available=analytics_backend_available(),
                        overridden=analytics_env_override(),
                    ),
                ),
                MenuOption(
                    f"[{'x' if crash_reports_enabled() else ' '}] Crash reports",
                    self._telemetry_description(
                        enabled=crash_reports_enabled(),
                        available=crash_reports_backend_available(),
                        overridden=crash_reports_env_override(),
                    ),
                ),
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Telemetry", options)
            if selected is None or selected == len(options) - 1:
                return
            if selected == 0:
                save_setting("analytics_enabled", str(not settings.analytics_enabled).lower())
                if analytics_env_override():
                    print_info(
                        "Saved analytics preference updated, but "
                        "HEPHAISTOS_ANALYTICS_ENABLED is overriding it right now."
                    )
            elif selected == 1:
                save_setting(
                    "crash_reports_enabled",
                    str(not settings.crash_reports_enabled).lower(),
                )
                if crash_reports_env_override():
                    print_info(
                        "Saved crash-report preference updated, but "
                        "HEPHAISTOS_CRASH_REPORTS_ENABLED is overriding it right now."
                    )

    def _appearance_menu(self) -> None:
        while True:
            current = current_theme_name()
            options = [
                MenuOption(
                    theme.replace("_", " ").title(),
                    "Theme preset",
                    is_current=(theme == current),
                )
                for theme in THEME_PRESETS
            ]
            options.append(MenuOption("Back", "Return to settings."))
            selected = select_option("Appearance", options)
            if selected is None or selected == len(options) - 1:
                return
            theme = THEME_PRESETS[selected]
            if theme == current:
                continue
            save_setting("theme", theme)
            set_theme(theme)

    def _startup_menu(self) -> None:
        while True:
            settings = load_app_settings()
            default_armory = settings.default_armory_path or styled("(not set)", STYLE_DIM)
            options = [
                MenuOption("Set default armory", str(default_armory)),
                MenuOption("Clear default armory", "Disable startup fallback armory"),
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Startup", options)
            if selected is None or selected == len(options) - 1:
                return
            if selected == 1:
                clear_setting("default_armory_path")
                print_success("Cleared default armory.")
                continue

            start_path = (
                Path(settings.default_armory_path) if settings.default_armory_path else Path.home()
            )
            chosen = browse_directory("Default Armory", start=start_path)
            if chosen is None:
                print_info("Cancelled.")
                continue
            try:
                armory_path = validate_armory_path(str(chosen))
            except Exception as exc:
                print_error(str(exc))
                continue
            save_setting("default_armory_path", str(armory_path))
            print_success(f"Default armory: {armory_path}")

    def _provider_credentials_menu(self, session: ChatSession) -> None:
        while True:
            active = ProviderConfig.load().get_active()
            provider_label = active.display_name if active else "none"
            options = [
                MenuOption("Provider status", f"Current: {provider_label}"),
                MenuOption("API key status", "Reuse the /api command"),
                MenuOption("Login OAuth", "Reuse the /login flow"),
                MenuOption("Logout OAuth", "Reuse the /logout flow"),
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Provider & Credentials", options)
            if selected is None or selected == len(options) - 1:
                return
            if selected == 0:
                ProviderCommand().handle(session, "")
                print_info("Use /provider use <slug> to switch providers directly.")
            elif selected == 1:
                ApiCommand().handle(session, "")
                print_info(
                    "Use /api key <key> or /api url <url> to change credentials or endpoint."
                )
            elif selected == 2:
                LoginCommand().handle(session, "")
            elif selected == 3:
                LogoutCommand().handle(session, "")


class VocabCommand(Command):
    name = "vocab"
    description = "Vocabulary drill with spaced repetition"
    aliases = ("v",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = _ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()

        subcmd = args.strip().lower()

        if subcmd == "status":
            return self._status(s)
        if subcmd == "reset":
            return self._reset(s)

        # Default: start drill.
        result = run_drill(s.armory_path)
        if result and result.cards_reviewed > 0:
            capture_analytics(
                "vocab_drill",
                {
                    "cards_reviewed": result.cards_reviewed,
                    "hard": result.hard_count,
                    "good": result.good_count,
                    "easy": result.easy_count,
                },
            )
        return CommandResult()

    @staticmethod
    def _status(session: ChatSession) -> CommandResult:
        armory_path = session.armory_path
        if armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()

        deck = scan_armory(armory_path)
        store = load_schedule(armory_path)
        store.sync_with_deck(deck)
        save_schedule(store)
        stats = store.stats()
        lines = [
            f"  Total cards:  {stats['total']}",
            f"  New:          {stats['new']}",
            f"  Due now:      {stats['due']}",
            f"  Mastered:     {stats['mastered']}",
            f"  Source files: {', '.join(deck.source_files) if deck.source_files else 'none'}",
        ]
        print("\n".join(lines))
        return CommandResult()

    @staticmethod
    def _reset(session: ChatSession) -> CommandResult:
        armory_path = session.armory_path
        if armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        if not confirm("Reset all vocabulary scheduling data?", default=False):
            print_info("Cancelled.")
            return CommandResult()
        deck = scan_armory(armory_path)
        store = load_schedule(armory_path)
        store.sync_with_deck(deck)
        store.reset_all()
        store.save()
        print_success("Vocabulary schedule reset. All cards are now new.")
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


def _ensure_session(session: object):
    if not isinstance(session, ChatSession):
        raise TypeError(f"Expected ChatSession, got {type(session).__name__}")
    return session


def _supermemory_key_source() -> str:
    if keyring_store.retrieve_key(SUPERMEMORY_PROVIDER_SLUG):
        return "keychain"
    if os.environ.get(SUPERMEMORY_API_KEY_ENV, "").strip():
        return f"env ({SUPERMEMORY_API_KEY_ENV})"
    if keyring_store.get_volatile(SUPERMEMORY_PROVIDER_SLUG):
        return "volatile (session-only)"
    return ""


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
            CommandSuggestion(name=cmd.name, description=cmd.description, aliases=cmd.aliases)
            for cmd in self.commands
            if not cmd.hidden
        ]


_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = CommandRegistry()
        for cmd_class in (
            HelpCommand,
            ExitCommand,
            QuitCommand,
            LoginCommand,
            LogoutCommand,
            StatusCommand,
            SaveCommand,
            ClearCommand,
            ArmoryCommand,
            ChatsCommand,
            ResumeCommand,
            ModelCommand,
            ApiCommand,
            CompactCommand,
            HistoryCommand,
            EditCommand,
            ProviderCommand,
            ModelsCommand,
            RecommendCommand,
            MemoryCommand,
            PersonaCommand,
            SettingsCommand,
            UsageCommand,
            VocabCommand,
        ):
            _registry.register(cmd_class())
    return _registry
