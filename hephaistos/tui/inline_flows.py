# ty: ignore
from __future__ import annotations

import contextlib
import inspect
from typing import TYPE_CHECKING

from hephaistos.chat import storage as chat_storage
from hephaistos.chat.model_selection import switch_model
from hephaistos.chat.provider_selection import activate_provider_for_session
from hephaistos.chat.session import list_armory_sessions, resume_session, save_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.matching import ranked_matches
from hephaistos.parameters.settings import THEME_PRESETS, load_app_settings, save_setting
from hephaistos.privacy.consent import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)
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
from hephaistos.terminal import set_theme
from hephaistos.tui.flow_state import InlineFlow
from hephaistos.tui.style import _tui_css

try:
    from textual.widgets import Input, OptionList, RichLog
except ImportError:
    Input = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    OptionList = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    RichLog = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

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
        elif value == "/sessions" or value.startswith("/sessions "):
            self._handle_sessions_command(value)

    def _open_inline_menu(
        self,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
    ) -> None:
        self._inline_flow = InlineFlow(
            name=name,
            step=step,
            options=list(options),
            all_options=list(options),
        )
        self._render_inline_menu_options(options)
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = f"{title} · type to filter · ↑/↓ enter · esc"
        composer.focus()
        self.set_focus(composer)

    def _render_inline_menu_options(self, options: list[tuple[str, str]]) -> None:
        suggestions = self.query_one("#suggestions", OptionList)
        composer = self.query_one("#composer", Input)
        if options:
            suggestions.set_options(
                [f"{label:<22} {description}" for label, description in options]
            )
            suggestions.highlighted = 0
        else:
            query = composer.value.strip()
            suffix = f" for {query}" if query else ""
            suggestions.set_options([f"No matches{suffix}"])
            suggestions.highlighted = None
        suggestions.add_class("visible")

    def _filter_inline_menu_options(self, query: str) -> None:
        if not self._inline_flow.all_options:
            return
        self._inline_flow.options = _filtered_inline_options(
            self._inline_flow.all_options,
            query,
        )
        self._render_inline_menu_options(self._inline_flow.options)

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
        settings = load_app_settings()
        self._open_inline_menu(
            name="settings",
            step="menu",
            title=f"Settings · current model source: {current}",
            options=[
                ("Privacy & Diagnostics", self._privacy_settings_summary()),
                ("Appearance", f"theme: {settings.theme}"),
                ("Login", f"model source: {current}"),
                ("Logout", "clear stored credentials"),
            ],
        )

    def _privacy_settings_summary(self) -> str:
        analytics = "analytics on" if analytics_enabled() else "analytics off"
        crashes = "crash reports on" if crash_reports_enabled() else "crash reports off"
        return f"{analytics}, {crashes}"

    def _privacy_option_description(
        self,
        *,
        enabled: bool,
        available: bool,
        overridden: bool,
    ) -> str:
        status = "enabled" if enabled else "disabled"
        availability = "available" if available else "inactive until configured"
        suffix = " · env override" if overridden else ""
        return f"{status} · {availability}{suffix}"

    def _open_privacy_flow(self) -> None:
        self._open_inline_menu(
            name="settings",
            step="privacy",
            title="Settings · Privacy & Diagnostics",
            options=[
                (
                    "Usage analytics",
                    self._privacy_option_description(
                        enabled=analytics_enabled(),
                        available=analytics_backend_available(),
                        overridden=analytics_env_override(),
                    ),
                ),
                (
                    "Crash reports",
                    self._privacy_option_description(
                        enabled=crash_reports_enabled(),
                        available=crash_reports_backend_available(),
                        overridden=crash_reports_env_override(),
                    ),
                ),
            ],
        )

    def _open_appearance_flow(self) -> None:
        current = load_app_settings().theme
        self._open_inline_menu(
            name="settings",
            step="appearance",
            title="Settings · Appearance",
            options=[
                (
                    theme,
                    "current theme" if theme == current else "theme preset",
                )
                for theme in THEME_PRESETS
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
        if not options or options == self._inline_flow.all_options:
            return
        self._inline_flow.all_options = options
        composer = self.query_one("#composer", Input)
        self._filter_inline_menu_options(composer.value)

    def _open_logout_flow(self) -> None:
        targets = self._logout_targets()
        if not targets:
            self._append_notice(
                "No stored credentials found. Env keys must be unset outside Hephaistos."
            )
            return
        options = [(slug, description) for slug, _kind, description in targets]
        options.append(("All", "Clear every stored subscription and API key"))
        self._open_inline_menu(
            name="logout",
            step="menu",
            title="Logout · choose credentials to clear",
            options=options,
        )

    def _handle_sessions_command(self, value: str) -> None:
        _, _, args = value.partition(" ")
        subcmd = args.strip().lower()
        if self.session.armory_path is None:
            self._append_notice("No armory attached. Use /armory to open one.")
            return
        sessions = sorted(
            list_armory_sessions(self.session.armory_path),
            key=lambda entry: entry.get("updated_at", ""),
            reverse=True,
        )
        if not sessions:
            self._append_notice("No saved chats found.")
            return
        if subcmd in {"list", "recent"}:
            self._append_plain(self._format_sessions_listing(sessions))
            return
        if subcmd in {"", "browse", "menu"}:
            self._open_sessions_flow(sessions)
            return
        if subcmd in {"resume", "last", "latest"}:
            self._perform_session_resume(sessions[0]["session_id"])
            return
        matches = [entry for entry in sessions if entry["session_id"].startswith(subcmd)]
        if len(matches) == 1:
            self._perform_session_resume(matches[0]["session_id"])
            return
        self._append_error("Usage: /sessions [list|recent|browse|resume]")

    def _format_sessions_listing(
        self,
        sessions: list[chat_storage.SessionRecord],
    ) -> str:
        lines = [f"Saved sessions for {self.session.armory_path}:"]
        for entry in sessions:
            title = entry["title"] or "(untitled)"
            lines.append(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")
        return "\n".join(lines)

    def _open_sessions_flow(self, sessions: list[chat_storage.SessionRecord]) -> None:
        self._open_inline_menu(
            name="sessions",
            step="menu",
            title="Sessions · choose a chat to resume",
            options=[
                (
                    entry["session_id"],
                    f"{entry['title'] or '(untitled)'}  {entry['updated_at']}",
                )
                for entry in sessions
            ],
        )

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
        composer = self.query_one("#composer", Input)
        if event.key == "escape":
            if self._inline_flow.all_options and composer.value:
                composer.value = ""
                self._filter_inline_menu_options("")
            elif self._inline_flow.name == "settings" and self._inline_flow.step != "menu":
                self._open_settings_flow()
            else:
                self._close_inline_flow()
            event.prevent_default()
            event.stop()
            return True
        if event.key == "up" and self._inline_flow.options:
            self._move_completion(-1)
            event.prevent_default()
            event.stop()
            return True
        if event.key == "down" and self._inline_flow.options:
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
        if self._inline_flow.all_options:
            if not self._inline_flow.options:
                self._append_error(f"No {self._inline_flow.name} matches: {value}")
                return
            suggestions = self.query_one("#suggestions", OptionList)
            selected = suggestions.highlighted if suggestions.highlighted is not None else 0
            selected = min(selected, len(self._inline_flow.options) - 1)
            label = _inline_option_label(
                value,
                self._inline_flow.options,
                self._inline_flow.all_options,
            )
            if not label:
                label = self._inline_flow.options[selected][0]
            self._handle_inline_menu_choice(label)
            return
        if self._inline_flow.options:
            suggestions = self.query_one("#suggestions", OptionList)
            selected = suggestions.highlighted if suggestions.highlighted is not None else 0
            label = self._inline_flow.options[selected][0]
            self._handle_inline_menu_choice(label)
            return
        self._handle_inline_text(value)
        composer.value = ""

    def _handle_inline_menu_choice(self, label: str) -> None:
        if self._inline_flow.name == "settings":
            if self._inline_flow.step == "menu":
                if label == "Privacy & Diagnostics":
                    self._open_privacy_flow()
                elif label == "Appearance":
                    self._open_appearance_flow()
                elif label == "Login":
                    self._open_login_flow()
                elif label == "Logout":
                    self._open_logout_flow()
                return
            if self._inline_flow.step == "privacy":
                self._handle_privacy_choice(label)
                return
            if self._inline_flow.step == "appearance":
                self._handle_appearance_choice(label)
                return
            return
        if self._inline_flow.name == "models":
            self._perform_model_switch(label)
            return
        if self._inline_flow.name == "logout":
            self._perform_logout(label)
            return
        if self._inline_flow.name == "sessions":
            self._perform_session_resume(label)
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

    def _handle_privacy_choice(self, label: str) -> None:
        settings = load_app_settings()
        if label == "Usage analytics":
            save_setting("analytics_enabled", str(not settings.analytics_enabled).lower())
            if analytics_env_override():
                self._append_notice("Analytics preference saved; env override is active.")
        elif label == "Crash reports":
            save_setting("crash_reports_enabled", str(not settings.crash_reports_enabled).lower())
            if crash_reports_env_override():
                self._append_notice("Crash-report preference saved; env override is active.")
        self._open_privacy_flow()

    def _handle_appearance_choice(self, label: str) -> None:
        if label not in THEME_PRESETS:
            return
        save_setting("theme", label)
        set_theme(label)
        self._refresh_tui_css()
        self._append_notice(f"theme: {label}")
        self._open_appearance_flow()

    def _refresh_tui_css(self) -> None:
        self.CSS = _tui_css()
        screen_path = inspect.getfile(self.__class__)
        read_from = (screen_path, f"{self.__class__.__name__}.CSS")
        self.stylesheet.add_source(self.CSS, read_from=read_from, is_default_css=False)
        self.refresh_css(animate=False)
        self.styles.background = "transparent"
        self.styles.background_tint = "transparent"
        self.screen.styles.background = "transparent"
        self.screen.styles.background_tint = "transparent"
        self._refresh_status("ready")
        self._refresh_footer_hints()
        self._update_info_panel()
        self._schedule_transcript_reflow()

    def _perform_session_resume(self, session_id: str) -> None:
        if self.session.armory_path is None:
            self._close_inline_flow("No armory attached. Use /armory to open one.")
            return
        if self.session.dirty:
            with contextlib.suppress(chat_storage.ChatStorageError):
                save_session(self.session)
        try:
            resumed = resume_session(self.session.config, self.session.armory_path, session_id)
        except chat_storage.ChatStorageError as exc:
            self._close_inline_flow(f"error: {exc}")
            return
        self.session = resumed
        self.state.transcript.clear()
        self.query_one("#transcript", RichLog).clear()
        for message in resumed.conversation.messages:
            if message.role == "user":
                self._append_entry(message.content, "user")
            elif message.role == "assistant":
                self._append_entry(message.content, "markdown")
        self._close_inline_flow(f"resumed session {resumed.session_id}")
        self._refresh_status("ready")
        self._update_info_panel()

    def _prompt_inline_text(self, name: str, step: str, placeholder: str) -> None:
        self._inline_flow.name = name
        self._inline_flow.step = step
        self._inline_flow.options = []
        self._inline_flow.all_options = []
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


def _filtered_inline_options(
    options: list[tuple[str, str]],
    query: str,
) -> list[tuple[str, str]]:
    cleaned = query.strip()
    if not cleaned:
        return list(options)

    normalized = cleaned.casefold()
    direct = [option for option in options if normalized in f"{option[0]} {option[1]}".casefold()]
    fuzzy = ranked_matches(
        cleaned,
        options,
        key=lambda option: f"{option[0]} {option[1]}",
        limit=len(options),
        min_score=45.0,
    )
    result: list[tuple[str, str]] = []
    for option in [*direct, *(match.value for match in fuzzy)]:
        if option not in result:
            result.append(option)
    return result


def _inline_option_label(
    value: str,
    options: list[tuple[str, str]],
    all_options: list[tuple[str, str]],
) -> str:
    cleaned = value.strip().casefold()
    if not cleaned:
        return ""
    for label, _description in [*options, *all_options]:
        if label.casefold() == cleaned:
            return label
    return ""
