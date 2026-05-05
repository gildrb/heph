# ty: ignore
from __future__ import annotations

from typing import TYPE_CHECKING

from hephaistos.chat.model_selection import switch_model
from hephaistos.chat.provider_selection import activate_provider_for_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.providers import oauth
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.keyring_store import (
    clear_key,
    get_volatile,
    resolve_key,
    set_volatile,
    store_key,
)
from hephaistos.providers.model_choices import configured_model_choices
from hephaistos.tui.flow_state import InlineFlow

try:
    from textual.widgets import Input, OptionList
except ImportError:
    Input = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    OptionList = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from textual import events


class TuiInlineFlowMixin:
    def _handle_inline_command(self, value: str) -> None:
        if value == "/login":
            self._open_login_flow()
        elif value == "/logout":
            self._open_logout_flow()
        elif value == "/settings":
            self._open_settings_flow()
        elif value == "/models":
            self._open_models_flow()

    def _open_inline_menu(
        self,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
    ) -> None:
        self._inline_flow = InlineFlow(name=name, step=step, options=options)
        suggestions = self.query_one("#suggestions", OptionList)
        suggestions.set_options([f"{label:<22} {description}" for label, description in options])
        suggestions.add_class("visible")
        suggestions.highlighted = 0
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = "Use ↑/↓ and Enter, or Esc to cancel"
        composer.focus()
        self.set_focus(composer)

    def _open_login_flow(self) -> None:
        self._open_inline_menu(
            name="login",
            step="menu",
            title="Login · choose an account source",
            options=[
                ("OpenAI Codex", "ChatGPT Plus/Pro subscription"),
                ("OpenRouter", "API key"),
                ("Z.AI", "API key"),
                ("Custom endpoint", "OpenAI-compatible base URL, model, API key"),
            ],
        )

    def _open_settings_flow(self) -> None:
        active = ProviderConfig.load().get_active()
        current = active.display_name if active is not None else "none"
        self._open_inline_menu(
            name="settings",
            step="menu",
            title=f"Settings · current model source: {current}",
            options=[
                ("Login", "Connect subscription/API/custom access"),
                ("Logout", "Clear stored credentials"),
            ],
        )

    def _model_flow_options(
        self,
        pc: ProviderConfig,
        choices: list[tuple[str, str, str, bool]],
    ) -> list[tuple[str, str]]:
        active = pc.get_active()
        current_model = self.session.config.model
        options: list[tuple[str, str]] = []
        for slug, model, display_name, is_free in choices:
            is_current = active is not None and active.slug == slug and model == current_model
            desc = f"via {display_name}"
            if is_free:
                desc += "  free"
            if is_current:
                desc += "  current"
            options.append((model, desc))
        return options

    def _open_models_flow(self) -> None:
        pc = ProviderConfig.load()
        choices = configured_model_choices(pc)
        if not choices:
            self._append_notice("No models available. Use /login to connect a provider.")
            return
        self._open_inline_menu(
            name="models",
            step="menu",
            title=f"Models · current: {self.session.config.model}",
            options=self._model_flow_options(pc, choices),
        )
        self.run_worker(self._refresh_models_flow_worker, thread=True)

    def _refresh_models_flow_worker(self) -> None:
        try:
            pc = ProviderConfig.load()
            choices = configured_model_choices(pc, refresh_live=True)
        except Exception:
            return
        self.call_from_thread(self._refresh_models_flow_options, choices)

    def _refresh_models_flow_options(
        self,
        choices: list[tuple[str, str, str, bool]],
    ) -> None:
        if not self._inline_flow.active or self._inline_flow.name != "models":
            return
        pc = ProviderConfig.load()
        options = self._model_flow_options(pc, choices)
        if not options or options == self._inline_flow.options:
            return
        self._inline_flow.options = options
        suggestions = self.query_one("#suggestions", OptionList)
        suggestions.set_options([f"{label:<22} {description}" for label, description in options])
        suggestions.add_class("visible")
        highlighted = suggestions.highlighted if suggestions.highlighted is not None else 0
        suggestions.highlighted = min(highlighted, len(options) - 1)

    def _open_logout_flow(self) -> None:
        targets = self._logout_targets()
        if not targets:
            self._append_notice(
                "No stored credentials found. Env keys must be unset outside Hephaistos."
            )
            return
        options = [(slug, description) for slug, _kind, description in targets]
        options.append(("All", "Clear every stored subscription and API key"))
        self._inline_flow = InlineFlow(name="logout", step="menu", options=options)
        suggestions = self.query_one("#suggestions", OptionList)
        suggestions.set_options([f"{label:<22} {description}" for label, description in options])
        suggestions.add_class("visible")
        suggestions.highlighted = 0
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = "Use ↑/↓ and Enter, or Esc to cancel"
        composer.focus()
        self.set_focus(composer)

    def _logout_targets(self) -> list[tuple[str, str, str]]:
        pc = ProviderConfig.load()
        targets: list[tuple[str, str, str]] = []
        for slug in sorted(oauth.list_providers()):
            display = pc.providers[slug].display_name if slug in pc.providers else slug
            targets.append((slug, "oauth", f"{display} subscription"))
        for slug, provider in pc.providers.items():
            if resolve_key(slug, provider.api_key_env) or get_volatile(slug):
                targets.append((slug, "api_key", f"{provider.display_name} API key"))
        return targets

    def _handle_inline_flow_key(self, event: events.Key) -> bool:
        if event.key == "escape":
            self._close_inline_flow()
            event.prevent_default()
            event.stop()
            return True
        if event.key == "up" and self._inline_flow.step == "menu":
            self._move_completion(-1)
            event.prevent_default()
            event.stop()
            return True
        if event.key == "down" and self._inline_flow.step == "menu":
            self._move_completion(1)
            event.prevent_default()
            event.stop()
            return True
        return False

    def _select_inline_flow_option(self, index: int) -> None:
        if not (0 <= index < len(self._inline_flow.options)):
            return
        self._submit_inline_flow(self._inline_flow.options[index][0])

    def _submit_inline_flow(self, value: str) -> None:
        composer = self.query_one("#composer", Input)
        if self._inline_flow.step == "menu":
            suggestions = self.query_one("#suggestions", OptionList)
            selected = suggestions.highlighted if suggestions.highlighted is not None else 0
            label = value or self._inline_flow.options[selected][0]
            self._handle_inline_menu_choice(label)
            return
        self._handle_inline_text(value)
        composer.value = ""

    def _handle_inline_menu_choice(self, label: str) -> None:
        if self._inline_flow.name == "settings":
            self._close_inline_flow()
            if label == "Login":
                self._open_login_flow()
            elif label == "Logout":
                self._open_logout_flow()
            return
        if self._inline_flow.name == "models":
            self._perform_model_switch(label)
            return
        if self._inline_flow.name == "logout":
            self._perform_logout(label)
            return
        if label == "OpenAI Codex":
            self._close_inline_flow("Opening browser login for OpenAI Codex...")
            self.run_worker(self._login_openai_worker, thread=True)
        elif label == "OpenRouter":
            self._prompt_inline_text("login", "openrouter_key", "OpenRouter API key")
        elif label == "Z.AI":
            self._prompt_inline_text("login", "zai_key", "Z.AI API key")
        elif label == "Custom endpoint":
            self._prompt_inline_text("login", "custom_endpoint", "OpenAI-compatible base URL")

    def _prompt_inline_text(self, name: str, step: str, placeholder: str) -> None:
        self._inline_flow.name = name
        self._inline_flow.step = step
        self._inline_flow.options = []
        self._hide_completions()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = placeholder
        self._append_notice(placeholder)
        composer.focus()
        self.set_focus(composer)

    def _handle_inline_text(self, value: str) -> None:
        if not value:
            self._append_error("Value is required.")
            return
        step = self._inline_flow.step
        if step == "openrouter_key":
            self._store_provider_key("openrouter", value)
        elif step == "zai_key":
            self._store_provider_key("zai", value)
        elif step == "custom_endpoint":
            self._inline_flow.endpoint = value.rstrip("/")
            self._prompt_inline_text("login", "custom_model", "Model name")
        elif step == "custom_model":
            self._inline_flow.model = value
            self._prompt_inline_text("login", "custom_key", "API key")
        elif step == "custom_key":
            pc = ProviderConfig.load()
            provider = pc.providers["custom"]
            provider.endpoint = self._inline_flow.endpoint
            provider.models = [self._inline_flow.model]
            provider.current_model = self._inline_flow.model
            try:
                store_key("custom", value)
            except Exception:
                set_volatile("custom", value)
            p = activate_provider_for_session(pc, self.session, "custom")
            self._close_inline_flow(f"provider: {p.display_name}")
            self._refresh_status("ready")
            self._update_info_panel()

    def _store_provider_key(self, slug: str, key: str) -> None:
        try:
            store_key(slug, key)
        except Exception:
            set_volatile(slug, key)
        pc = ProviderConfig.load()
        p = activate_provider_for_session(pc, self.session, slug)
        self._close_inline_flow(f"provider: {p.display_name}")
        self._refresh_status("ready")
        self._update_info_panel()

    def _login_openai_worker(self) -> None:
        try:
            oauth.login_openai_codex()
        except Exception as exc:
            self.call_from_thread(self._append_error, f"Login failed: {exc}")
            return
        pc = ProviderConfig.load()
        p = activate_provider_for_session(pc, self.session, "openai-codex")
        self.call_from_thread(
            self._append_notice,
            f"provider: {p.display_name}",
        )
        self.call_from_thread(self._refresh_status, "ready")
        self.call_from_thread(self._update_info_panel)

    def _perform_logout(self, label: str) -> None:
        targets = self._logout_targets()
        if label == "All":
            for slug, kind, _description in targets:
                if kind == "oauth":
                    oauth.clear_credentials(slug)
                else:
                    clear_key(slug)
            self._close_inline_flow("logged out: all providers")
            return
        for slug, kind, _description in targets:
            if slug == label:
                if kind == "oauth":
                    oauth.clear_credentials(slug)
                else:
                    clear_key(slug)
                self._close_inline_flow(f"logged out: {slug}")
                return

    def _perform_model_switch(self, model: str) -> None:
        pc = ProviderConfig.load()
        choices = configured_model_choices(pc)
        matching = next((c for c in choices if c[1] == model), None)
        if matching is None:
            self._close_inline_flow("Model not found.")
            return
        slug, _model, _display_name, _is_free = matching
        old_model = self.session.config.model
        if not switch_model(self.session, slug, model):
            self._close_inline_flow("Model unavailable.")
            return
        capture_analytics(
            "model_changed",
            {"provider": slug, "from_model": old_model, "to_model": model},
        )
        self._close_inline_flow(f"model: {model}")
        self._refresh_status("ready")
        self._update_info_panel()

    def _close_inline_flow(self, notice: str = "") -> None:
        self._inline_flow = InlineFlow()
        self._hide_completions()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = 'Ask anything... "What do I need to study next?"'
        if notice:
            self._append_notice(notice)
        composer.focus()
        self.set_focus(composer)
