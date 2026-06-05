from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, ParamSpec, Protocol

from chat.provider_selection import activate_provider_for_session
from providers.config import ProviderConfig
from providers.keyring_store import (
    GLOBAL_API_KEY_ENV,
    clear_key,
    get_volatile,
    retrieve_key,
    set_volatile,
    store_key,
)
from providers.oauth import clear_credentials, list_providers, login_openai_codex

from tui.flow_state import InlineFlow

if TYPE_CHECKING:
    from chat.session import ChatSession

_P = ParamSpec("_P")


@dataclass(frozen=True)
class _LogoutTarget:
    slug: str
    kind: str
    label: str
    description: str


class _AuthFlowHost(Protocol):
    session: ChatSession
    _inline_flow: InlineFlow

    def run_worker(self, work: Callable[[], object], *, thread: bool = False) -> object: ...

    def call_from_thread(
        self,
        callback: Callable[_P, object],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> object: ...

    def _append_notice(self, text: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _refresh_status(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _open_inline_menu(
        self,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
        prompts: dict[str, str] | None = None,
        selected_label: str | None = None,
    ) -> None: ...

    def _prompt_inline_text(self, name: str, step: str, placeholder: str) -> None: ...

    def _close_inline_flow(self, notice: str = "") -> None: ...

    def _logout_targets(self) -> list[_LogoutTarget]: ...

    def _environment_logout_credentials(self) -> list[str]: ...

    def _login_openai_worker(self) -> None: ...

    def _store_provider_key(self, slug: str, key: str) -> None: ...

    def _custom_login_text_handler(self, step: str) -> Callable[[str], None] | None: ...

    def _store_custom_endpoint(self, value: str) -> None: ...

    def _store_custom_model(self, value: str) -> None: ...

    def _store_custom_provider(self, key: str) -> None: ...

    def _activate_provider(self, slug: str) -> None: ...


class TuiAuthFlowMixin:
    def _open_login_flow(self: _AuthFlowHost) -> None:
        self._open_inline_menu(
            name="login",
            step="menu",
            title="Login  choose an account source",
            options=[
                ("OpenAI Codex", "ChatGPT Plus/Pro subscription"),
                ("OpenAI API", "API key"),
                ("OpenRouter", "API key"),
                ("Z.AI", "API key"),
                ("Custom endpoint", "OpenAI-compatible base URL, model, API key"),
            ],
        )

    def _open_logout_flow(self: _AuthFlowHost) -> None:
        targets = self._logout_targets()
        environment_credentials = self._environment_logout_credentials()
        if not targets:
            if environment_credentials:
                self._append_notice(
                    "No stored credentials found. Environment credentials cannot be cleared "
                    f"inside Heph: {', '.join(environment_credentials)}."
                )
                return
            self._append_notice(
                "No stored credentials found. Env keys must be unset outside Heph."
            )
            return
        options = [(target.label, target.description) for target in targets]
        if environment_credentials:
            self._append_notice(
                f"Environment credentials stay outside Heph: {', '.join(environment_credentials)}."
            )
        options.append(("All", "clear shown"))
        self._open_inline_menu(
            name="logout",
            step="menu",
            title="Logout  choose stored credentials to clear",
            options=options,
        )

    def _handle_login_choice(self: _AuthFlowHost, label: str) -> None:
        if label == "OpenAI Codex":
            self._close_inline_flow("Opening browser login for OpenAI Codex...")
            self.run_worker(self._login_openai_worker, thread=True)
        elif label == "OpenAI API":
            self._prompt_inline_text("login", "openai_key", "OpenAI API key")
        elif label == "OpenRouter":
            self._prompt_inline_text("login", "openrouter_key", "OpenRouter API key")
        elif label == "Z.AI":
            self._prompt_inline_text("login", "zai_key", "Z.AI API key")
        elif label == "Custom endpoint":
            self._prompt_inline_text(
                "login",
                "custom_endpoint",
                "OpenAI-compatible base URL",
            )

    def _inline_text_handler(self: _AuthFlowHost) -> Callable[[str], None] | None:
        provider_handlers = {
            "openai_key": lambda value: self._store_provider_key("openai", value),
            "openrouter_key": lambda value: self._store_provider_key("openrouter", value),
            "zai_key": lambda value: self._store_provider_key("zai", value),
        }
        if handler := provider_handlers.get(self._inline_flow.step):
            return handler
        if handler := self._custom_login_text_handler(self._inline_flow.step):
            return handler
        return None

    def _custom_login_text_handler(
        self: _AuthFlowHost,
        step: str,
    ) -> Callable[[str], None] | None:
        handlers = {
            "custom_endpoint": self._store_custom_endpoint,
            "custom_model": self._store_custom_model,
            "custom_key": self._store_custom_provider,
        }
        return handlers.get(step)

    def _store_custom_endpoint(self: _AuthFlowHost, value: str) -> None:
        self._inline_flow.endpoint = value.rstrip("/")
        self._prompt_inline_text("login", "custom_model", "Model name")

    def _store_custom_model(self: _AuthFlowHost, value: str) -> None:
        self._inline_flow.model = value
        self._prompt_inline_text("login", "custom_key", "API key")

    def _store_custom_provider(self: _AuthFlowHost, key: str) -> None:
        pc = ProviderConfig.load()
        provider = pc.providers["custom"]
        provider.endpoint = self._inline_flow.endpoint
        provider.models = [self._inline_flow.model]
        provider.current_model = self._inline_flow.model
        try:
            store_key("custom", key)
        except Exception:
            set_volatile("custom", key)
        self._activate_provider("custom")

    def _store_provider_key(self: _AuthFlowHost, slug: str, key: str) -> None:
        try:
            store_key(slug, key)
        except Exception:
            set_volatile(slug, key)
        self._activate_provider(slug)

    def _activate_provider(self: _AuthFlowHost, slug: str) -> None:
        pc = ProviderConfig.load()
        provider = activate_provider_for_session(pc, self.session, slug)
        self._close_inline_flow(f"provider: {provider.display_name}")
        self._refresh_status()
        self._update_info_panel()

    def _login_openai_worker(self: _AuthFlowHost) -> None:
        try:
            login_openai_codex()
        except Exception as exc:
            self.call_from_thread(self._append_error, f"Login failed: {exc}")
            return
        pc = ProviderConfig.load()
        provider = activate_provider_for_session(pc, self.session, "openai-codex")
        self.call_from_thread(
            self._append_notice,
            f"provider: {provider.display_name}",
        )
        self.call_from_thread(self._refresh_status)
        self.call_from_thread(self._update_info_panel)

    def _perform_logout(self: _AuthFlowHost, label: str) -> None:
        targets = self._logout_targets()
        if label == "All":
            for target in targets:
                _clear_logout_target(target)
            self._close_inline_flow("logged out: all providers")
            return
        for target in targets:
            if target.label == label:
                _clear_logout_target(target)
                self._close_inline_flow(f"logged out: {target.label}")
                return

    def _logout_targets(self: _AuthFlowHost) -> list[_LogoutTarget]:
        pc = ProviderConfig.load()
        return [*_oauth_logout_targets(pc), *_api_key_logout_targets(pc)]

    def _environment_logout_credentials(self: _AuthFlowHost) -> list[str]:
        pc = ProviderConfig.load()
        credentials: list[str] = []
        if os.environ.get(GLOBAL_API_KEY_ENV, "").strip():
            credentials.append(f"{GLOBAL_API_KEY_ENV} global override")
        for provider in pc.providers.values():
            if not provider.api_key_env:
                continue
            if os.environ.get(provider.api_key_env, "").strip():
                credentials.append(f"{provider.display_name} ({provider.api_key_env})")
        return credentials


def _oauth_logout_targets(pc: ProviderConfig) -> list[_LogoutTarget]:
    targets: list[_LogoutTarget] = []
    for slug in sorted(list_providers()):
        display = pc.providers[slug].display_name if slug in pc.providers else slug
        targets.append(
            _LogoutTarget(
                slug=slug,
                kind="oauth",
                label="ChatGPT Plus/Pro" if slug == "openai-codex" else display,
                description="configured",
            )
        )
    return targets


def _api_key_logout_targets(pc: ProviderConfig) -> list[_LogoutTarget]:
    return [
        _LogoutTarget(
            slug=slug,
            kind="api_key",
            label=_api_key_logout_label(provider.display_name),
            description="configured",
        )
        for slug, provider in pc.providers.items()
        if _has_stored_provider_key(slug)
    ]


def _has_stored_provider_key(slug: str) -> bool:
    return retrieve_key(slug) is not None or get_volatile(slug) is not None


def _api_key_logout_label(display_name: str) -> str:
    display_label = {
        "Pollinations AI (free)": "Pollinations",
        "Z.AI / GLM": "Z.AI",
    }.get(display_name, display_name)
    if display_label != display_name or display_label.casefold().endswith((" api", " api key")):
        return display_label
    return f"{display_label} API key"


def _clear_logout_target(target: _LogoutTarget) -> None:
    if target.kind == "oauth":
        clear_credentials(target.slug)
    else:
        clear_key(target.slug)
