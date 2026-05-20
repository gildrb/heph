"""Authentication commands: login and logout."""

from __future__ import annotations

import os

from hephaistos.chat.provider_selection import activate_provider_for_session
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.providers import keyring_store, oauth
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.keyring_store import clear_key, get_volatile, set_volatile, store_key
from hephaistos.terminal import (
    MenuOption,
    confirm,
    direct_input,
    print_error,
    print_info,
    print_success,
    select_option,
)


class LoginCommand(Command):
    name = "login"
    description = "Authenticate with a subscription or API key"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        options = [
            MenuOption("OpenAI Codex", "ChatGPT Plus/Pro subscription"),
            MenuOption("OpenAI API key", "Use OpenAI API billing and models"),
            MenuOption("OpenRouter API key", "Unlock OpenRouter models"),
            MenuOption("Z.AI API key", "Unlock GLM models"),
            MenuOption("Custom endpoint", "OpenAI-compatible base URL, model, and API key"),
        ]

        selected = select_option("Login to provider", options)
        if selected is None:
            return CommandResult()
        if selected == 0:
            return self._login_openai_codex(session)
        api_key_providers = ("openai", "openrouter", "zai")
        if 1 <= selected <= len(api_key_providers):
            return self._login_api_key(session, api_key_providers[selected - 1])
        return self._login_custom_endpoint(session)

    @staticmethod
    def _login_openai_codex(session: object) -> CommandResult:
        try:
            creds = oauth.login_openai_codex()
        except RuntimeError as exc:
            print_error(str(exc))
            return CommandResult()
        except Exception as exc:
            print_error(f"Login failed: {exc}")
            return CommandResult()

        s = ensure_session(session)
        pc = ProviderConfig.load()
        p = activate_provider_for_session(pc, s, "openai-codex")
        print_success(
            f"Logged in to OpenAI Codex (account: {creds.account_id or 'unknown'}) "
            f"— switched to {p.resolved_model}"
        )
        capture_analytics("oauth_login", {"provider": "openai-codex", "model": p.resolved_model})
        return CommandResult()

    @staticmethod
    def _login_custom_endpoint(session: object) -> CommandResult:
        s = ensure_session(session)
        pc = ProviderConfig.load()
        provider = pc.providers["custom"]
        try:
            endpoint = direct_input("  OpenAI-compatible base URL > ").strip().rstrip("/")
            model = direct_input("  Model name > ").strip()
            raw_key = direct_input("  API key > ").strip()
        except (KeyboardInterrupt, EOFError):
            print_info("Cancelled.")
            return CommandResult()
        if not endpoint:
            print_error("Base URL is required.")
            return CommandResult()
        if not model:
            print_error("Model name is required.")
            return CommandResult()
        if not raw_key:
            print_error("API key is required.")
            return CommandResult()

        provider.endpoint = endpoint
        provider.models = [model]
        provider.current_model = model
        storage = _store_api_key("custom", raw_key)

        p = activate_provider_for_session(pc, s, "custom")
        print_success(
            f"Custom endpoint saved to {storage}; switched to {p.display_name} / {model}"
        )
        capture_analytics("api_key_login", {"provider": "custom", "model": model})
        return CommandResult()

    @staticmethod
    def _login_api_key(session: object, slug: str) -> CommandResult:
        s = ensure_session(session)
        pc = ProviderConfig.load()
        provider = pc.providers[slug]
        try:
            raw_key = direct_input(f"  {provider.display_name} API key > ").strip()
        except (KeyboardInterrupt, EOFError):
            print_info("Cancelled.")
            return CommandResult()
        if not raw_key:
            print_error("API key is required.")
            return CommandResult()

        storage = _store_api_key(slug, raw_key)

        p = activate_provider_for_session(pc, s, slug)
        print_success(
            f"API key saved to {storage}; switched to {p.display_name} / {p.resolved_model}"
        )
        capture_analytics("api_key_login", {"provider": slug, "model": p.resolved_model})
        return CommandResult()


def _logout_targets() -> list[tuple[str, str, str]]:
    pc = ProviderConfig.load()
    targets: list[tuple[str, str, str]] = []
    oauth_providers = set(oauth.list_providers())
    for slug in sorted(oauth_providers):
        display = pc.providers[slug].display_name if slug in pc.providers else slug
        targets.append((slug, "oauth", f"{display} subscription"))

    for slug, provider in pc.providers.items():
        has_keychain_key = keyring_store.retrieve_key(slug) is not None
        has_volatile_key = get_volatile(slug) is not None
        if not has_keychain_key and not has_volatile_key:
            continue
        source = "keychain" if has_keychain_key else "session-only key"
        targets.append((slug, "api_key", f"{provider.display_name} API key ({source})"))
    return targets


def _env_only_targets() -> list[str]:
    pc = ProviderConfig.load()
    targets: list[str] = []
    for slug, provider in pc.providers.items():
        if keyring_store.retrieve_key(slug) is not None or get_volatile(slug) is not None:
            continue
        if provider.api_key_env and os.environ.get(provider.api_key_env, "").strip():
            targets.append(slug)
    return targets


def _clear_logout_target(slug: str, kind: str) -> None:
    if kind == "oauth":
        oauth.clear_credentials(slug)
        return
    clear_key(slug)


def _store_api_key(slug: str, raw_key: str) -> str:
    try:
        store_key(slug, raw_key)
        return "keychain"
    except Exception:
        set_volatile(slug, raw_key)
        return "this session only (keychain unavailable)"


class LogoutCommand(Command):
    name = "logout"
    description = "Clear stored subscription or API-key credentials"

    def handle(self, session: object, args: str) -> CommandResult:
        del session, args
        credentials = _logout_targets()
        env_locked = _env_only_targets()
        if not credentials:
            if env_locked:
                print_info(
                    "No stored credentials found. Environment-provided keys must be unset "
                    "outside Heph."
                )
            else:
                print_info("No stored credentials found.")
            return CommandResult()

        if len(credentials) == 1:
            slug, kind, _description = credentials[0]
            if confirm(f"Log out of {slug}?", default=True):
                _clear_logout_target(slug, kind)
                print_success(f"Logged out of {slug}.")
                capture_analytics("logout", {"provider": slug, "kind": kind})
            else:
                print_info("Cancelled.")
            return CommandResult()

        options = [MenuOption(slug, description) for slug, _kind, description in credentials]
        options.append(MenuOption("All", "Clear every stored subscription and API key"))
        selected = select_option("Log out of", options)
        if selected is None:
            return CommandResult()

        if selected == len(options) - 1:
            for slug, kind, _description in credentials:
                _clear_logout_target(slug, kind)
            print_success("Logged out of all stored providers.")
            capture_analytics("logout", {"provider": "all", "kind": "all"})
        else:
            slug, kind, _description = credentials[selected]
            _clear_logout_target(slug, kind)
            print_success(f"Logged out of {slug}.")
            capture_analytics("logout", {"provider": slug, "kind": kind})
        return CommandResult()
