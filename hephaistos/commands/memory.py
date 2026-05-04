"""Memory management command."""

from __future__ import annotations

import os

from hephaistos.chat.session import ChatSession
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.memory.supermemory import (
    SUPERMEMORY_API_KEY_ENV,
    SUPERMEMORY_DEFAULT_PROFILE,
    SUPERMEMORY_PROVIDER_SLUG,
    SUPERMEMORY_URL_ENV,
    resolve_supermemory_key,
)
from hephaistos.parameters.settings import (
    load_app_settings,
    save_setting,
)
from hephaistos.providers import keyring_store
from hephaistos.providers.keyring_store import mask_key, set_volatile, store_key
from hephaistos.terminal_display import (
    STYLE_DIM,
    direct_input,
    print_error,
    print_info,
    print_success,
    styled,
)


def _supermemory_key_source() -> str:
    if keyring_store.retrieve_key(SUPERMEMORY_PROVIDER_SLUG):
        return "keychain"
    if os.environ.get(SUPERMEMORY_API_KEY_ENV, "").strip():
        return f"env ({SUPERMEMORY_API_KEY_ENV})"
    if keyring_store.get_volatile(SUPERMEMORY_PROVIDER_SLUG):
        return "volatile (session-only)"
    return ""


class MemoryCommand(Command):
    name = "memory"
    description = "Manage study memory and Supermemory setup"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
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


# Re-export for test monkeypatching compatibility
__all__ = ["MemoryCommand", "mask_key", "resolve_supermemory_key", "set_volatile", "store_key"]
