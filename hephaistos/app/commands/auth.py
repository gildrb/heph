"""Authentication commands: api, login, logout."""

from __future__ import annotations

import os

from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands._base import Command, CommandResult, ensure_session
from hephaistos.app.display import STYLE_DIM, print_error, print_info, print_success, styled
from hephaistos.app.menu import MenuOption, confirm, select_option
from hephaistos.chat.engine import is_keyless_endpoint
from hephaistos.providers import keyring_store, oauth
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.keyring_store import mask_key, resolve_key, set_volatile, store_key


class ApiCommand(Command):
    name = "api"
    description = "Manage API key (keychain) or base URL"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        parts = args.strip().split(maxsplit=1)

        if not parts:
            pc = ProviderConfig.load()
            active = pc.get_active()
            slug = active.slug if active else ""
            env_var = active.api_key_env if active else ""

            if is_keyless_endpoint(s.config.base_url):
                key = ""
                key_display = styled("not required (free provider)", STYLE_DIM)
            else:
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


class LoginCommand(Command):
    name = "login"
    description = "Authenticate via OAuth"

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

        s = ensure_session(session)
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
