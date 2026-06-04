from __future__ import annotations

import contextlib
import inspect
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar, cast

from hephaion.chat import storage as chat_storage
from hephaion.chat.model_selection import switch_model
from hephaion.chat.provider_selection import activate_provider_for_session
from hephaion.chat.session import (
    SessionError,
    fork_session_at_turn,
    list_armory_sessions,
    resume_session,
    save_session,
)
from hephaion.chat.turn_history import TurnSnapshot
from hephaion.diagnostics.events import capture as capture_analytics
from hephaion.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_LABELS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_MODES,
    ACTIVITY_TRACE_TOOL_CALLS,
    THEME_LABELS,
    THEME_PRESETS,
    VOCAB_STRICTNESS_LABELS,
    VOCAB_STRICTNESS_MODES,
    load_app_settings,
    save_setting,
)
from hephaion.privacy.consent import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)
from hephaion.providers import oauth
from hephaion.providers.config import ProviderConfig
from hephaion.providers.keyring_store import (
    GLOBAL_API_KEY_ENV,
    clear_key,
    get_volatile,
    retrieve_key,
    set_volatile,
    store_key,
)
from hephaion.providers.model_choices import configured_model_choices
from hephaion.terminal import current_palette, set_theme
from hephaion.terminal.palette import TRANSPARENT
from hephaion.tui.display_text import COMPOSER_PLACEHOLDER
from hephaion.tui.flow_state import InlineFlow
from hephaion.tui.inline_menu import (
    _consume_inline_key,
    _dedupe_inline_options,
    _filtered_inline_options,
    _inline_menu_label_width,
    _inline_menu_option_text,
    _inline_menu_scrolled_label_width,
    _inline_menu_visible_label_width,
    _inline_option_index,
    _prompt_width,
    _selected_inline_label,
    _session_menu_option_text,
    _session_option_description,
    _turn_option_description,
)
from hephaion.tui.model_flow import (
    _duplicate_model_names,
    _model_choice_from_label,
    _model_choice_label,
    _model_flow_option,
)
from hephaion.tui.render_state import DirtyRegion, TuiRenderCache
from hephaion.tui.session_state import TuiRuntimeState
from hephaion.tui.slash_completion import (
    changed_highlight_indices,
    completion_menu_scroll_y,
)
from hephaion.tui.style import _tui_css

__all__ = [
    "TuiInlineFlowMixin",
    "_inline_menu_option_text",
    "_model_choice_from_label",
    "_model_choice_label",
]

try:
    from rich.text import Text as _RichText
    from textual.widgets import Input, OptionList, RichLog
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from textual import events
    from textual.widget import Widget

    from hephaion.chat.session import ChatSession

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")

_ACTIVITY_TRACE_DESCRIPTIONS = {
    ACTIVITY_TRACE_TOOL_CALLS: "live reads, commands, model calls, results",
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: "compact status and final summary",
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: "hide internal activity lines",
}
_ACTIVITY_TRACE_MODE_BY_LABEL = {label: mode for mode, label in ACTIVITY_TRACE_LABELS.items()}
_SESSION_LIST_COMMANDS = {"list", "recent"}
_SESSION_BROWSE_COMMANDS = {"", "browse", "menu"}
_SESSION_LATEST_COMMANDS = {"resume", "last", "latest"}
_TURN_LIST_COMMANDS = {"list", "history"}
_TURN_BROWSE_COMMANDS = {"", "browse", "menu"}
_TURN_LATEST_COMMANDS = {"resume", "last", "latest"}


@dataclass(frozen=True)
class _LogoutTarget:
    slug: str
    kind: str
    label: str
    description: str


class _StyleObject(Protocol):
    background: str
    background_tint: str


class _ScreenObject(Protocol):
    styles: _StyleObject


class _StylesheetObject(Protocol):
    def add_source(
        self,
        css: str,
        *,
        read_from: tuple[str, str],
        is_default_css: bool,
    ) -> None: ...


class _InlineFlowHost(Protocol):
    CSS: str
    session: ChatSession
    state: TuiRuntimeState
    _inline_flow: InlineFlow
    _transcript_render_width: int | None
    _render_cache: TuiRenderCache

    @property
    def stylesheet(self) -> _StylesheetObject: ...

    @property
    def styles(self) -> _StyleObject: ...

    @property
    def screen(self) -> object: ...

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def set_focus(self, widget: Widget | None) -> None: ...

    def run_worker(self, work: Callable[[], object], *, thread: bool = False) -> object: ...

    def call_from_thread(
        self,
        callback: Callable[_P, object],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> object: ...

    def refresh_css(self, *, animate: bool = True) -> None: ...

    def _append_notice(self, text: str) -> None: ...

    def _replace_last_notice(self, text: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _append_plain(self, text: str) -> None: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _hide_completions(self) -> None: ...

    def _move_completion(self, offset: int) -> None: ...

    def _refresh_status(self) -> None: ...

    def _sync_busy_to_current_session(self) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _refresh_completion_position(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _schedule_transcript_reflow(self) -> None: ...

    def _reflow_transcript_entries(self) -> None: ...

    def _open_login_flow(self) -> None: ...

    def _open_logout_flow(self) -> None: ...

    def _open_settings_flow(self, selected_label: str | None = None) -> None: ...

    def _open_models_flow(self) -> None: ...

    def _handle_sessions_command(self, value: str) -> None: ...

    def _handle_turn_command(self, value: str) -> None: ...

    def _handle_known_sessions_subcommand(
        self,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool: ...

    def _handle_known_turn_subcommand(
        self,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool: ...

    def _session_records(self) -> list[chat_storage.SessionRecord] | None: ...

    def _show_session_records(self, sessions: list[chat_storage.SessionRecord]) -> None: ...

    def _open_session_menu(self, sessions: list[chat_storage.SessionRecord]) -> None: ...

    def _show_turn_records(self, snapshots: list[TurnSnapshot]) -> None: ...

    def _open_turn_menu(self, snapshots: list[TurnSnapshot]) -> None: ...

    def _resume_matching_session(
        self,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool: ...

    def _branch_matching_turn(
        self,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool: ...

    def _submit_inline_chat_value(self, value: str) -> None: ...

    def _replace_transcript_with_resumed_session(self, resumed: ChatSession) -> None: ...

    def on_input_submitted(self, event: Input.Submitted) -> None: ...

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

    def _render_inline_menu_options(
        self,
        options: list[tuple[str, str]],
        *,
        highlighted: int | None = 0,
    ) -> None: ...

    def _filter_inline_menu_options(self, query: str) -> None: ...

    def _privacy_settings_summary(self) -> str: ...

    def _activity_trace_summary(self) -> str: ...

    def _privacy_option_description(
        self,
        *,
        enabled: bool,
        available: bool,
        overridden: bool,
    ) -> str: ...

    def _open_privacy_flow(self, selected_label: str | None = None) -> None: ...

    def _open_appearance_flow(self, selected_label: str | None = None) -> None: ...

    def _open_activity_trace_flow(self, selected_label: str | None = None) -> None: ...

    def _open_vocabulary_flow(self, selected_label: str | None = None) -> None: ...

    def _model_flow_options(
        self,
        pc: ProviderConfig,
        choices: list[tuple[str, str, str, bool]],
    ) -> list[tuple[str, str]]: ...

    def _refresh_models_flow_worker(self) -> None: ...

    def _refresh_models_flow_options(
        self,
        choices: list[tuple[str, str, str, bool]],
    ) -> None: ...

    def _logout_targets(self) -> list[_LogoutTarget]: ...

    def _environment_logout_credentials(self) -> list[str]: ...

    def _select_inline_flow_option(self, index: int) -> None: ...

    def _submit_inline_flow(self, value: str) -> None: ...

    def _handle_inline_escape(self) -> None: ...

    def _move_inline_flow_selection(self, key: str) -> bool: ...

    def _inline_text_handler(self) -> Callable[[str], None] | None: ...

    def _custom_login_text_handler(self, step: str) -> Callable[[str], None] | None: ...

    def _store_custom_endpoint(self, value: str) -> None: ...

    def _store_custom_model(self, value: str) -> None: ...

    def _handle_inline_menu_choice(self, label: str) -> None: ...

    def _handle_settings_choice(self, label: str) -> None: ...

    def _handle_login_choice(self, label: str) -> None: ...

    def _handle_privacy_choice(self, label: str) -> None: ...

    def _handle_appearance_choice(self, label: str) -> None: ...

    def _handle_activity_trace_choice(self, label: str) -> None: ...

    def _handle_vocabulary_choice(self, label: str) -> None: ...

    def _refresh_tui_css(self) -> None: ...

    def _perform_session_resume(self, session_id: str) -> None: ...

    def _perform_turn_branch(self, turn_id: str) -> None: ...

    def _prompt_inline_text(self, name: str, step: str, placeholder: str) -> None: ...

    def _handle_inline_text(self, value: str) -> None: ...

    def _store_custom_provider(self, key: str) -> None: ...

    def _store_provider_key(self, slug: str, key: str) -> None: ...

    def _activate_provider(self, slug: str) -> None: ...

    def _login_openai_worker(self) -> None: ...

    def _perform_logout(self, label: str) -> None: ...

    def _perform_model_switch(self, model: str) -> None: ...

    def _close_inline_flow(self, notice: str = "") -> None: ...


def _settings_menu_actions(host: _InlineFlowHost) -> dict[str, Callable[[], None]]:
    return {
        "Privacy & Diagnostics": host._open_privacy_flow,
        "Appearance": host._open_appearance_flow,
        "Activity trace": host._open_activity_trace_flow,
        "Vocabulary practice": host._open_vocabulary_flow,
        "Login": host._open_login_flow,
        "Logout": host._open_logout_flow,
    }


def _settings_step_actions(host: _InlineFlowHost) -> dict[str, Callable[[str], None]]:
    return {
        "privacy": host._handle_privacy_choice,
        "appearance": host._handle_appearance_choice,
        "activity_trace": host._handle_activity_trace_choice,
        "vocabulary": host._handle_vocabulary_choice,
    }


def _login_menu_actions(host: _InlineFlowHost) -> dict[str, Callable[[], None]]:
    return {
        "OpenAI Codex": lambda: _start_openai_oauth_login(host),
        "OpenAI API": lambda: host._prompt_inline_text("login", "openai_key", "OpenAI API key"),
        "OpenRouter": lambda: host._prompt_inline_text(
            "login",
            "openrouter_key",
            "OpenRouter API key",
        ),
        "Z.AI": lambda: host._prompt_inline_text("login", "zai_key", "Z.AI API key"),
        "Custom endpoint": lambda: host._prompt_inline_text(
            "login",
            "custom_endpoint",
            "OpenAI-compatible base URL",
        ),
    }


def _start_openai_oauth_login(host: _InlineFlowHost) -> None:
    host._close_inline_flow("Opening browser login for OpenAI Codex...")
    host.run_worker(host._login_openai_worker, thread=True)


def _inline_menu_actions(host: _InlineFlowHost) -> dict[str, Callable[[str], None]]:
    return {
        "settings": host._handle_settings_choice,
        "models": host._perform_model_switch,
        "logout": host._perform_logout,
        "sessions": host._perform_session_resume,
        "turn": host._perform_turn_branch,
    }


class TuiInlineFlowMixin:
    def _handle_inline_command(self: _InlineFlowHost, value: str) -> None:
        command = value.split(maxsplit=1)[0]
        actions = {
            "/login": self._open_login_flow,
            "/logout": self._open_logout_flow,
            "/settings": self._open_settings_flow,
            "/models": self._open_models_flow,
        }
        if action := actions.get(command):
            action()
        elif command == "/sessions":
            self._handle_sessions_command(value)
        elif command == "/turn":
            self._handle_turn_command(value)

    def _submit_inline_chat_value(self: _InlineFlowHost, value: str) -> None:
        composer = self.query_one("#composer", Input)
        composer.value = value
        self.on_input_submitted(Input.Submitted(composer, value, None))

    def _open_inline_menu(
        self: _InlineFlowHost,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
        prompts: dict[str, str] | None = None,
        selected_label: str | None = None,
    ) -> None:
        options = _dedupe_inline_options(options)
        highlighted = _inline_option_index(options, selected_label)
        self._inline_flow = InlineFlow(
            name=name,
            step=step,
            options=list(options),
            all_options=list(options),
            prompts=dict(prompts or {}),
        )
        self._hide_completions()
        self._render_inline_menu_options(options, highlighted=highlighted)
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = f"{title}  type to filter  ↑/↓ enter  esc"
        composer.focus()
        self.set_focus(composer)

    def _render_inline_menu_options(
        self: _InlineFlowHost,
        options: list[tuple[str, str]],
        *,
        highlighted: int | None = 0,
    ) -> None:
        suggestions = self.query_one("#suggestions", OptionList)
        composer = self.query_one("#composer", Input)
        if options:
            selected = 0 if highlighted is None else min(highlighted, len(options) - 1)
            rendered_height = suggestions.size.height
            if self._inline_flow.name == "sessions":
                label_width = _inline_menu_label_width(options)
                prompt_width = _prompt_width(suggestions.size.width, self._transcript_render_width)
                prompts = [
                    _session_menu_option_text(
                        label,
                        description,
                        selected=index == selected,
                        label_width=label_width,
                        prompt_width=prompt_width,
                    )
                    for index, (label, description) in enumerate(options)
                ]
            else:
                label_width = _inline_menu_visible_label_width(
                    options,
                    highlighted=selected,
                    rendered_height=rendered_height,
                )
                prompts = [
                    _inline_menu_option_text(
                        label,
                        description,
                        selected=index == selected,
                        label_width=label_width,
                    )
                    for index, (label, description) in enumerate(options)
                ]
            scroll_y = completion_menu_scroll_y(selected, len(options), rendered_height)
            suggestions.set_options(
                prompts,
            )
            suggestions.highlighted = selected
            suggestions.scroll_y = scroll_y
        else:
            query = composer.value.strip()
            suffix = f" for {query}" if query else ""
            suggestions.set_options([f"No matches{suffix}"])
            suggestions.highlighted = None
            suggestions.scroll_y = 0
        suggestions.add_class("inline-menu")
        suggestions.add_class("visible")
        self._refresh_footer_hints()

    def _highlight_inline_menu_option(
        self: _InlineFlowHost,
        highlighted: int,
        suggestions: OptionList | None = None,
    ) -> None:
        if suggestions is None:
            suggestions = self.query_one("#suggestions", OptionList)
        previous = suggestions.highlighted
        if previous == highlighted:
            return
        options = self._inline_flow.options
        if self._inline_flow.name == "sessions":
            label_width = _inline_menu_label_width(options)
            prompt_width = _prompt_width(suggestions.size.width, self._transcript_render_width)
        else:
            label_width = _inline_menu_scrolled_label_width(
                options,
                scroll_y=int(suggestions.scroll_y),
                rendered_height=suggestions.size.height,
            )
            prompt_width = 0
        for option_index in changed_highlight_indices(previous, highlighted, len(options)):
            label, description = options[option_index]
            if self._inline_flow.name == "sessions":
                prompt = _session_menu_option_text(
                    label,
                    description,
                    selected=option_index == highlighted,
                    label_width=label_width,
                    prompt_width=prompt_width,
                )
            else:
                prompt = _inline_menu_option_text(
                    label,
                    description,
                    selected=option_index == highlighted,
                    label_width=label_width,
                )
            suggestions.replace_option_prompt_at_index(
                option_index,
                prompt,
            )
        suggestions.highlighted = highlighted
        self._refresh_completion_position()

    def _filter_inline_menu_options(self: _InlineFlowHost, query: str) -> None:
        if not self._inline_flow.all_options:
            return
        self._inline_flow.options = _filtered_inline_options(
            self._inline_flow.all_options,
            query,
        )
        self._render_inline_menu_options(self._inline_flow.options)

    def _open_login_flow(self: _InlineFlowHost) -> None:
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

    def _open_settings_flow(
        self: _InlineFlowHost,
        selected_label: str | None = None,
    ) -> None:
        active = ProviderConfig.load().get_active()
        current = active.display_name if active is not None else "none"
        settings = load_app_settings()
        self._open_inline_menu(
            name="settings",
            step="menu",
            title=f"Settings  current model source: {current}",
            options=[
                ("Privacy & Diagnostics", self._privacy_settings_summary()),
                ("Appearance", f"theme: {THEME_LABELS.get(settings.theme, settings.theme)}"),
                ("Activity trace", self._activity_trace_summary()),
                (
                    "Vocabulary practice",
                    VOCAB_STRICTNESS_LABELS.get(
                        settings.vocab_strictness,
                        settings.vocab_strictness,
                    ),
                ),
                ("Login", f"model source: {current}"),
                ("Logout", "clear stored credentials"),
            ],
            selected_label=selected_label,
        )

    def _privacy_settings_summary(self: _InlineFlowHost) -> str:
        analytics = "analytics on" if analytics_enabled() else "analytics off"
        crashes = "crash reports on" if crash_reports_enabled() else "crash reports off"
        return f"{analytics}, {crashes}"

    def _activity_trace_summary(self: _InlineFlowHost) -> str:
        activity_trace_mode = load_app_settings().activity_trace_mode
        return ACTIVITY_TRACE_LABELS.get(
            activity_trace_mode,
            ACTIVITY_TRACE_LABELS[ACTIVITY_TRACE_TOOL_CALLS],
        )

    def _privacy_option_description(
        self: _InlineFlowHost,
        *,
        enabled: bool,
        available: bool,
        overridden: bool,
    ) -> str:
        status = "enabled" if enabled else "disabled"
        availability = "available" if available else "inactive until configured"
        suffix = "  env override" if overridden else ""
        return f"{status}  {availability}{suffix}"

    def _open_privacy_flow(self: _InlineFlowHost, selected_label: str | None = None) -> None:
        _open_settings_submenu(
            self,
            parent_label="Privacy & Diagnostics",
            step="privacy",
            title="Settings  Privacy & Diagnostics",
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
            selected_label=selected_label,
        )

    def _open_appearance_flow(self: _InlineFlowHost, selected_label: str | None = None) -> None:
        current = load_app_settings().theme
        _open_settings_submenu(
            self,
            parent_label="Appearance",
            step="appearance",
            title="Settings  Appearance",
            options=[
                (
                    THEME_LABELS[theme],
                    "current theme" if theme == current else "theme preset",
                )
                for theme in THEME_PRESETS
            ],
            selected_label=selected_label,
        )

    def _open_activity_trace_flow(
        self: _InlineFlowHost,
        selected_label: str | None = None,
    ) -> None:
        current_activity_trace_mode = load_app_settings().activity_trace_mode
        _open_settings_submenu(
            self,
            parent_label="Activity trace",
            step="activity_trace",
            title="Settings  Activity trace",
            options=[
                (
                    ACTIVITY_TRACE_LABELS[activity_trace_mode],
                    (
                        f"{_ACTIVITY_TRACE_DESCRIPTIONS[activity_trace_mode]}  current"
                        if activity_trace_mode == current_activity_trace_mode
                        else _ACTIVITY_TRACE_DESCRIPTIONS[activity_trace_mode]
                    ),
                )
                for activity_trace_mode in ACTIVITY_TRACE_MODES
            ],
            selected_label=selected_label,
        )

    def _open_vocabulary_flow(self: _InlineFlowHost, selected_label: str | None = None) -> None:
        current_strictness = load_app_settings().vocab_strictness
        _open_settings_submenu(
            self,
            parent_label="Vocabulary practice",
            step="vocabulary",
            title="Settings  Vocabulary practice",
            options=[
                (
                    VOCAB_STRICTNESS_LABELS[strictness],
                    "current" if strictness == current_strictness else "answer matching",
                )
                for strictness in VOCAB_STRICTNESS_MODES
            ],
            selected_label=selected_label,
        )

    def _model_flow_options(
        self: _InlineFlowHost,
        pc: ProviderConfig,
        choices: list[tuple[str, str, str, bool]],
    ) -> list[tuple[str, str]]:
        active = pc.get_active()
        current_model = self.session.config.model
        duplicate_models = _duplicate_model_names(choices)
        active_slug = active.slug if active is not None else None
        return [
            _model_flow_option(
                model=model,
                display_name=display_name,
                is_free=is_free,
                is_duplicate=model in duplicate_models,
                is_current=active_slug == slug and model == current_model,
            )
            for slug, model, display_name, is_free in choices
        ]

    def _open_models_flow(self: _InlineFlowHost) -> None:
        pc = ProviderConfig.load()
        choices = configured_model_choices(pc)
        if not choices:
            self._append_notice("No models available. Use /login to connect a provider.")
            return
        self._open_inline_menu(
            name="models",
            step="menu",
            title=f"Models  current: {self.session.config.model}",
            options=self._model_flow_options(pc, choices),
        )
        self.run_worker(self._refresh_models_flow_worker, thread=True)

    def _refresh_models_flow_worker(self: _InlineFlowHost) -> None:
        try:
            pc = ProviderConfig.load()
            choices = configured_model_choices(pc, refresh_live=True)
        except Exception:
            return
        self.call_from_thread(self._refresh_models_flow_options, choices)

    def _refresh_models_flow_options(
        self: _InlineFlowHost,
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

    def _open_logout_flow(self: _InlineFlowHost) -> None:
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
        title = "Logout  choose stored credentials to clear"
        self._open_inline_menu(
            name="logout",
            step="menu",
            title=title,
            options=options,
        )

    def _handle_sessions_command(self: _InlineFlowHost, value: str) -> None:
        _, _, args = value.partition(" ")
        subcommand = args.strip().lower()
        sessions = self._session_records()
        if sessions is None:
            return
        if not sessions:
            self._append_notice("No saved chats found.")
            return
        if self._handle_known_sessions_subcommand(sessions, subcommand):
            return
        if self._resume_matching_session(sessions, subcommand):
            return
        self._append_error("Usage: /sessions [list|recent|browse|resume]")

    def _handle_turn_command(self: _InlineFlowHost, value: str) -> None:
        _, _, args = value.partition(" ")
        subcommand = args.strip().upper()
        snapshots = list(self.session.turn_history)
        if not snapshots:
            self._append_notice("No completed turns in this chat yet.")
            return
        if self._handle_known_turn_subcommand(snapshots, subcommand.lower()):
            return
        if self._branch_matching_turn(snapshots, subcommand):
            return
        self._append_error("Usage: /turn [list|browse|T#]")

    def _handle_known_sessions_subcommand(
        self: _InlineFlowHost,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool:
        actions: dict[str, Callable[[], None]] = {}
        for commands, action in (
            (_SESSION_LIST_COMMANDS, lambda: self._show_session_records(sessions)),
            (_SESSION_BROWSE_COMMANDS, lambda: self._open_session_menu(sessions)),
            (
                _SESSION_LATEST_COMMANDS,
                lambda: self._perform_session_resume(sessions[0]["session_id"]),
            ),
        ):
            for command in commands:
                actions[command] = action
        action = actions.get(subcommand)
        if action is None:
            return False
        action()
        return True

    def _handle_known_turn_subcommand(
        self: _InlineFlowHost,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool:
        actions: dict[str, Callable[[], None]] = {}
        for commands, action in (
            (_TURN_LIST_COMMANDS, lambda: self._show_turn_records(snapshots)),
            (_TURN_BROWSE_COMMANDS, lambda: self._open_turn_menu(snapshots)),
            (_TURN_LATEST_COMMANDS, lambda: self._perform_turn_branch(snapshots[-1].turn_id)),
        ):
            for command in commands:
                actions[command] = action
        action = actions.get(subcommand)
        if action is None:
            return False
        action()
        return True

    def _session_records(self: _InlineFlowHost) -> list[chat_storage.SessionRecord] | None:
        if self.session.armory_path is None:
            self._append_notice("No armory attached. Use /armory to open one.")
            return None
        return sorted(
            list_armory_sessions(self.session.armory_path),
            key=lambda entry: entry.get("updated_at", ""),
            reverse=True,
        )

    def _show_session_records(
        self: _InlineFlowHost,
        sessions: list[chat_storage.SessionRecord],
    ) -> None:
        lines = [f"Saved sessions for {self.session.armory_path}:"]
        for entry in sessions:
            title = entry["title"] or "(untitled)"
            lines.append(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")
        self._append_plain("\n".join(lines))

    def _open_session_menu(
        self: _InlineFlowHost,
        sessions: list[chat_storage.SessionRecord],
    ) -> None:
        self._open_inline_menu(
            name="sessions",
            step="menu",
            title="Sessions  choose a chat to resume",
            options=[
                (
                    entry["session_id"],
                    _session_option_description(entry),
                )
                for entry in sessions
            ],
        )

    def _show_turn_records(self: _InlineFlowHost, snapshots: list[TurnSnapshot]) -> None:
        lines = ["Completed turns in this chat:"]
        lines.extend(
            f"  {snapshot.turn_id}  {_turn_option_description(snapshot)}" for snapshot in snapshots
        )
        self._append_plain("\n".join(lines))

    def _open_turn_menu(
        self: _InlineFlowHost,
        snapshots: list[TurnSnapshot],
    ) -> None:
        self._open_inline_menu(
            name="turn",
            step="menu",
            title="Turn  choose a message to branch from",
            options=[
                (
                    snapshot.turn_id,
                    _turn_option_description(snapshot),
                )
                for snapshot in snapshots
            ],
        )

    def _resume_matching_session(
        self: _InlineFlowHost,
        sessions: list[chat_storage.SessionRecord],
        subcommand: str,
    ) -> bool:
        matches = [entry for entry in sessions if entry["session_id"].startswith(subcommand)]
        if len(matches) != 1:
            return False
        self._perform_session_resume(matches[0]["session_id"])
        return True

    def _branch_matching_turn(
        self: _InlineFlowHost,
        snapshots: list[TurnSnapshot],
        subcommand: str,
    ) -> bool:
        matches = [snapshot for snapshot in snapshots if snapshot.turn_id.startswith(subcommand)]
        if len(matches) != 1:
            return False
        self._perform_turn_branch(matches[0].turn_id)
        return True

    def _logout_targets(self: _InlineFlowHost) -> list[_LogoutTarget]:
        pc = ProviderConfig.load()
        return [*_oauth_logout_targets(pc), *_api_key_logout_targets(pc)]

    def _environment_logout_credentials(self: _InlineFlowHost) -> list[str]:
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

    def _handle_inline_flow_key(self: _InlineFlowHost, event: events.Key) -> bool:
        if event.key == "escape":
            self._handle_inline_escape()
            return _consume_inline_key(event)
        if self._move_inline_flow_selection(event.key):
            return _consume_inline_key(event)
        return False

    def _move_inline_flow_selection(self: _InlineFlowHost, key: str) -> bool:
        offsets = {"up": -1, "down": 1}
        offset = offsets.get(key)
        if offset is None or not self._inline_flow.options:
            return False
        self._move_completion(offset)
        return True

    def _handle_inline_escape(self: _InlineFlowHost) -> None:
        composer = self.query_one("#composer", Input)
        if self._inline_flow.all_options and composer.value:
            composer.value = ""
            self._filter_inline_menu_options("")
            return
        if self._inline_flow.name == "settings" and self._inline_flow.step != "menu":
            self._open_settings_flow(selected_label=self._inline_flow.slug)
            return
        self._close_inline_flow()

    def _select_inline_flow_option(self: _InlineFlowHost, index: int) -> None:
        if not (0 <= index < len(self._inline_flow.options)):
            return
        self._submit_inline_flow(self._inline_flow.options[index][0])

    def _submit_inline_flow(self: _InlineFlowHost, value: str) -> None:
        composer = self.query_one("#composer", Input)
        if self._inline_flow.all_options and not self._inline_flow.options:
            self._append_error(f"No {self._inline_flow.name} matches: {value}")
            return
        if self._inline_flow.options:
            self._handle_inline_menu_choice(_selected_inline_label(self, value))
            return
        self._handle_inline_text(value)
        composer.value = ""

    def _handle_inline_menu_choice(self: _InlineFlowHost, label: str) -> None:
        action = _inline_menu_actions(self).get(self._inline_flow.name, self._handle_login_choice)
        action(label)

    def _handle_settings_choice(self: _InlineFlowHost, label: str) -> None:
        if self._inline_flow.step == "menu":
            action = _settings_menu_actions(self).get(label)
            if action is not None:
                action()
            return
        if action := _settings_step_actions(self).get(self._inline_flow.step):
            action(label)

    def _handle_login_choice(self: _InlineFlowHost, label: str) -> None:
        if action := _login_menu_actions(self).get(label):
            action()

    def _handle_privacy_choice(self: _InlineFlowHost, label: str) -> None:
        settings = load_app_settings()
        if label == "Usage analytics":
            save_setting("analytics_enabled", str(not settings.analytics_enabled).lower())
            if analytics_env_override():
                self._append_notice("Analytics preference saved; env override is active.")
        elif label == "Crash reports":
            save_setting("crash_reports_enabled", str(not settings.crash_reports_enabled).lower())
            if crash_reports_env_override():
                self._append_notice("Crash-report preference saved; env override is active.")
        self._open_privacy_flow(selected_label=label)

    def _handle_appearance_choice(self: _InlineFlowHost, label: str) -> None:
        theme = _setting_value_from_label(THEME_LABELS, label)
        if theme is None and label in THEME_PRESETS:
            theme = label
        if theme is None:
            return
        save_setting("theme", theme)
        set_theme(theme)
        self._refresh_tui_css()
        display_label = THEME_LABELS[theme]
        self._replace_last_notice(f"{display_label} theme.")
        self._open_appearance_flow(selected_label=display_label)

    def _handle_activity_trace_choice(self: _InlineFlowHost, label: str) -> None:
        activity_trace_mode = _ACTIVITY_TRACE_MODE_BY_LABEL.get(label)
        if activity_trace_mode is None:
            return
        save_setting("activity_trace_mode", activity_trace_mode)
        self._append_notice(f"activity trace: {ACTIVITY_TRACE_LABELS[activity_trace_mode]}")
        self._open_activity_trace_flow(selected_label=label)

    def _handle_vocabulary_choice(self: _InlineFlowHost, label: str) -> None:
        strictness = _setting_value_from_label(VOCAB_STRICTNESS_LABELS, label)
        if strictness is None:
            return
        save_setting("vocab_strictness", strictness)
        self._append_notice(f"vocabulary practice: {VOCAB_STRICTNESS_LABELS[strictness]}")
        self._open_vocabulary_flow(selected_label=label)

    def _refresh_tui_css(self: _InlineFlowHost) -> None:
        palette = current_palette()
        self.CSS = _tui_css()
        screen_path = inspect.getfile(self.__class__)
        read_from = (screen_path, f"{self.__class__.__name__}.CSS")
        self.stylesheet.add_source(self.CSS, read_from=read_from, is_default_css=False)
        self.refresh_css(animate=False)
        self.styles.background = palette.bg_app
        self.styles.background_tint = TRANSPARENT
        screen = cast("_ScreenObject", self.screen)
        screen.styles.background = palette.bg_app
        screen.styles.background_tint = TRANSPARENT
        self._render_cache.forget(*DirtyRegion)
        self._refresh_status()
        self._refresh_footer_hints()
        self._update_info_panel()
        self._transcript_render_width = None
        self._reflow_transcript_entries()

    def _perform_session_resume(self: _InlineFlowHost, session_id: str) -> None:
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
        self._replace_transcript_with_resumed_session(resumed)
        self._close_inline_flow(f"resumed session {resumed.session_id}")
        self._sync_busy_to_current_session()
        self._update_info_panel()

    def _perform_turn_branch(self: _InlineFlowHost, turn_id: str) -> None:
        try:
            branched = fork_session_at_turn(self.session, turn_id)
        except SessionError as exc:
            self._close_inline_flow(f"error: {exc}")
            return
        self.session = branched
        self._replace_transcript_with_resumed_session(branched)
        self._close_inline_flow(
            f"branched from {turn_id.upper()} into session {branched.session_id}"
        )
        self._sync_busy_to_current_session()
        self._update_info_panel()

    def _replace_transcript_with_resumed_session(
        self: _InlineFlowHost,
        resumed: ChatSession,
    ) -> None:
        self.state.transcript.clear()
        self.query_one("#transcript", RichLog).clear()
        for message in resumed.conversation.messages:
            if message.role == "user":
                self._append_entry(message.content, "user")
            elif message.role == "assistant":
                self._append_entry(message.content, "markdown")

    def _prompt_inline_text(self: _InlineFlowHost, name: str, step: str, placeholder: str) -> None:
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

    def _handle_inline_text(self: _InlineFlowHost, value: str) -> None:
        if not value:
            self._append_error("Value is required.")
            return
        handler = self._inline_text_handler()
        if handler is not None:
            handler(value)

    def _inline_text_handler(self: _InlineFlowHost) -> Callable[[str], None] | None:
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
        self: _InlineFlowHost,
        step: str,
    ) -> Callable[[str], None] | None:
        handlers = {
            "custom_endpoint": self._store_custom_endpoint,
            "custom_model": self._store_custom_model,
            "custom_key": self._store_custom_provider,
        }
        return handlers.get(step)

    def _store_custom_endpoint(self: _InlineFlowHost, value: str) -> None:
        self._inline_flow.endpoint = value.rstrip("/")
        self._prompt_inline_text("login", "custom_model", "Model name")

    def _store_custom_model(self: _InlineFlowHost, value: str) -> None:
        self._inline_flow.model = value
        self._prompt_inline_text("login", "custom_key", "API key")

    def _store_custom_provider(self: _InlineFlowHost, key: str) -> None:
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

    def _store_provider_key(self: _InlineFlowHost, slug: str, key: str) -> None:
        try:
            store_key(slug, key)
        except Exception:
            set_volatile(slug, key)
        self._activate_provider(slug)

    def _activate_provider(self: _InlineFlowHost, slug: str) -> None:
        pc = ProviderConfig.load()
        p = activate_provider_for_session(pc, self.session, slug)
        self._close_inline_flow(f"provider: {p.display_name}")
        self._refresh_status()
        self._update_info_panel()

    def _login_openai_worker(self: _InlineFlowHost) -> None:
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
        self.call_from_thread(self._refresh_status)
        self.call_from_thread(self._update_info_panel)

    def _perform_logout(self: _InlineFlowHost, label: str) -> None:
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

    def _perform_model_switch(self: _InlineFlowHost, model: str) -> None:
        pc = ProviderConfig.load()
        choices = configured_model_choices(pc)
        matching = _model_choice_from_label(model, choices)
        if matching is None:
            self._close_inline_flow("Model not found.")
            return
        slug, _model, _display_name, _is_free = matching
        old_model = self.session.config.model
        if not switch_model(self.session, slug, _model):
            self._close_inline_flow("Model unavailable.")
            return
        capture_analytics(
            "model_changed",
            {"provider": slug, "from_model": old_model, "to_model": _model},
        )
        self._close_inline_flow(f"model: {_model}")
        self._refresh_status()
        self._update_info_panel()

    def _close_inline_flow(self: _InlineFlowHost, notice: str = "") -> None:
        self._inline_flow = InlineFlow()
        self._hide_completions()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = COMPOSER_PLACEHOLDER
        if notice:
            self._append_notice(notice)
        composer.focus()
        self.set_focus(composer)


def _open_settings_submenu(
    host: _InlineFlowHost,
    *,
    parent_label: str,
    step: str,
    title: str,
    options: list[tuple[str, str]],
    selected_label: str | None = None,
) -> None:
    host._open_inline_menu(
        name="settings",
        step=step,
        title=title,
        options=options,
        selected_label=selected_label,
    )
    host._inline_flow.slug = parent_label


def _setting_value_from_label(labels_by_value: dict[str, str], label: str) -> str | None:
    for value, value_label in labels_by_value.items():
        if value_label == label:
            return value
    return None


def _oauth_logout_targets(pc: ProviderConfig) -> list[_LogoutTarget]:
    targets: list[_LogoutTarget] = []
    for slug in sorted(oauth.list_providers()):
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
        oauth.clear_credentials(target.slug)
    else:
        clear_key(target.slug)
