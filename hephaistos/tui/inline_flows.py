from __future__ import annotations

import contextlib
import inspect
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar, cast

from hephaistos.chat import storage as chat_storage
from hephaistos.chat.model_selection import switch_model
from hephaistos.chat.provider_selection import activate_provider_for_session
from hephaistos.chat.session import list_armory_sessions, resume_session, save_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.matching import ranked_matches
from hephaistos.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_MODES,
    ACTIVITY_TRACE_TOOL_CALLS,
    THEME_PRESETS,
    load_app_settings,
    save_setting,
)
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
    GLOBAL_API_KEY_ENV,
    clear_key,
    get_volatile,
    retrieve_key,
    set_volatile,
    store_key,
)
from hephaistos.providers.model_choices import configured_model_choices
from hephaistos.terminal import current_palette, set_theme
from hephaistos.tui.flow_state import InlineFlow
from hephaistos.tui.session_state import TuiRuntimeState
from hephaistos.tui.style import _tui_css

try:
    from rich.text import Text as _RichText
    from textual.widgets import Input, OptionList, RichLog
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from rich.text import Text
    from textual import events
    from textual.widget import Widget

    from hephaistos.chat.session import ChatSession

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")

_ACTIVITY_TRACE_LABELS = {
    ACTIVITY_TRACE_TOOL_CALLS: "Tool calls",
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: "Minimal tool calls",
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: "Hidden tool calls",
}
_ACTIVITY_TRACE_DESCRIPTIONS = {
    ACTIVITY_TRACE_TOOL_CALLS: "live reads, commands, model calls, results",
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: "compact status and final summary",
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: "hide internal activity lines",
}
_ACTIVITY_TRACE_MODE_BY_LABEL = {label: mode for mode, label in _ACTIVITY_TRACE_LABELS.items()}
_OVERVIEW_TOPIC_SECTION_HEADING = "These are the study topics I found in the material:"
_OVERVIEW_TOPIC_LINE_RE = re.compile(r"^- (?P<label>.+?)(?:\s+\[(?:e|E)\d+\])?\.?$")
_OVERVIEW_TOPIC_PROMPT = "Choose a topic to study next. In the shell, use ↑/↓"
_OVERVIEW_RECOMMENDATION_LINE_RE = re.compile(r"^- (?P<label>.+?)\.?$")
_OVERVIEW_RECOMMENDATION_HEADING_RE = re.compile(
    r"^Recommended options:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_OVERVIEW_STANDALONE_RECOMMENDATION_RE = re.compile(
    r"^Recommendation:\s*(?P<label>.+?)\.?$",
    re.IGNORECASE | re.MULTILINE,
)
_OVERVIEW_MENU_HINT_RE = re.compile(
    r"\b(?:(?:choose|pick|select)\b.{0,100}\b(?:menu|enter|arrows?|↑/↓)|"
    r"(?:menu|enter|arrows?|↑/↓)\b.{0,100}\b(?:choose|pick|select))\b",
    re.IGNORECASE,
)
_OVERVIEW_QUOTED_QUESTION_RE = re.compile(r"[\"“](?P<question>[^\"”]{8,180}\?)[\"”]")
_OVERVIEW_RECOMMENDATIONS_HEADING = "Recommended options:"
_OVERVIEW_CITATION_RE = re.compile(r"\s+\[(?:e|E)\d+\]")
_LANGUAGE_PRESERVING_TOPIC_PROMPT = (
    " Answer in the same language as the selected topic when that language is clear."
)
_CUSTOM_STUDY_PROMPT_LABEL = "Ask something else"
_CUSTOM_STUDY_PROMPT_DESCRIPTION = "custom study prompt"
_CUSTOM_STUDY_PROMPT_PLACEHOLDER = "What would you like to study or ask?"


@dataclass(frozen=True)
class _LogoutTarget:
    slug: str
    kind: str
    label: str
    description: str


@dataclass(frozen=True)
class OverviewTopicMenu:
    options: list[tuple[str, str]]
    prompts: dict[str, str]


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

    def _append_error(self, text: str) -> None: ...

    def _append_plain(self, text: str) -> None: ...

    def _append_entry(self, content: str, kind: str = "plain") -> None: ...

    def _hide_completions(self) -> None: ...

    def _move_completion(self, offset: int) -> None: ...

    def _refresh_status(self, state: str) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _refresh_completion_position(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _schedule_transcript_reflow(self) -> None: ...

    def _open_login_flow(self) -> None: ...

    def _open_logout_flow(self) -> None: ...

    def _open_settings_flow(self) -> None: ...

    def _open_models_flow(self) -> None: ...

    def _handle_sessions_command(self, value: str) -> None: ...

    def _submit_inline_chat_value(self, value: str) -> None: ...

    def on_input_submitted(self, event: Input.Submitted) -> None: ...

    def _open_inline_menu(
        self,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
        prompts: dict[str, str] | None = None,
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

    def _open_privacy_flow(self) -> None: ...

    def _open_appearance_flow(self) -> None: ...

    def _open_activity_trace_flow(self) -> None: ...

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

    def _format_sessions_listing(self, sessions: list[chat_storage.SessionRecord]) -> str: ...

    def _open_sessions_flow(self, sessions: list[chat_storage.SessionRecord]) -> None: ...

    def _select_inline_flow_option(self, index: int) -> None: ...

    def _submit_inline_flow(self, value: str) -> None: ...

    def _handle_inline_menu_choice(self, label: str) -> None: ...

    def _handle_privacy_choice(self, label: str) -> None: ...

    def _handle_appearance_choice(self, label: str) -> None: ...

    def _handle_activity_trace_choice(self, label: str) -> None: ...

    def _refresh_tui_css(self) -> None: ...

    def _perform_session_resume(self, session_id: str) -> None: ...

    def _prompt_inline_text(self, name: str, step: str, placeholder: str) -> None: ...

    def _handle_inline_text(self, value: str) -> None: ...

    def _store_provider_key(self, slug: str, key: str) -> None: ...

    def _login_openai_worker(self) -> None: ...

    def _perform_logout(self, label: str) -> None: ...

    def _perform_model_switch(self, model: str) -> None: ...

    def _close_inline_flow(self, notice: str = "") -> None: ...


def _inline_menu_option_text(
    label: str,
    description: str,
    *,
    selected: bool,
) -> str | Text:
    if _RichText is None:
        return f"{label}  {description}" if description else label
    palette = current_palette()
    label_style = f"bold {palette.action_primary_bg}" if selected else palette.text_primary
    text = _RichText()
    text.append(label, style=label_style)
    if description:
        text.append("  ", style=palette.text_muted)
        text.append(description, style=palette.text_muted)
    return text


def _changed_highlight_indices(
    previous: int | None,
    highlighted: int,
    option_count: int,
) -> tuple[int, ...]:
    indices = [
        index
        for index in (previous, highlighted)
        if index is not None and 0 <= index < option_count
    ]
    return tuple(dict.fromkeys(indices))


class TuiInlineFlowMixin:
    def _handle_inline_command(self: _InlineFlowHost, value: str) -> None:
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
    ) -> None:
        options = _dedupe_inline_options(options)
        self._inline_flow = InlineFlow(
            name=name,
            step=step,
            options=list(options),
            all_options=list(options),
            prompts=dict(prompts or {}),
        )
        self._hide_completions()
        self._render_inline_menu_options(options)
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
            suggestions.set_options(
                [
                    _inline_menu_option_text(
                        label,
                        description,
                        selected=index == selected,
                    )
                    for index, (label, description) in enumerate(options)
                ]
            )
            suggestions.highlighted = selected
        else:
            query = composer.value.strip()
            suffix = f" for {query}" if query else ""
            suggestions.set_options([f"No matches{suffix}"])
            suggestions.highlighted = None
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
        for option_index in _changed_highlight_indices(previous, highlighted, len(options)):
            label, description = options[option_index]
            suggestions.replace_option_prompt_at_index(
                option_index,
                _inline_menu_option_text(
                    label,
                    description,
                    selected=option_index == highlighted,
                ),
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

    def _open_settings_flow(self: _InlineFlowHost) -> None:
        active = ProviderConfig.load().get_active()
        current = active.display_name if active is not None else "none"
        settings = load_app_settings()
        self._open_inline_menu(
            name="settings",
            step="menu",
            title=f"Settings  current model source: {current}",
            options=[
                ("Privacy & Diagnostics", self._privacy_settings_summary()),
                ("Appearance", f"theme: {settings.theme}"),
                ("Activity trace", self._activity_trace_summary()),
                ("Login", f"model source: {current}"),
                ("Logout", "clear stored credentials"),
            ],
        )

    def _privacy_settings_summary(self: _InlineFlowHost) -> str:
        analytics = "analytics on" if analytics_enabled() else "analytics off"
        crashes = "crash reports on" if crash_reports_enabled() else "crash reports off"
        return f"{analytics}, {crashes}"

    def _activity_trace_summary(self: _InlineFlowHost) -> str:
        mode = load_app_settings().activity_trace_mode
        return _ACTIVITY_TRACE_LABELS.get(mode, _ACTIVITY_TRACE_LABELS[ACTIVITY_TRACE_TOOL_CALLS])

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

    def _open_privacy_flow(self: _InlineFlowHost) -> None:
        self._open_inline_menu(
            name="settings",
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
        )

    def _open_appearance_flow(self: _InlineFlowHost) -> None:
        current = load_app_settings().theme
        self._open_inline_menu(
            name="settings",
            step="appearance",
            title="Settings  Appearance",
            options=[
                (
                    theme,
                    "current theme" if theme == current else "theme preset",
                )
                for theme in THEME_PRESETS
            ],
        )

    def _open_activity_trace_flow(self: _InlineFlowHost) -> None:
        current = load_app_settings().activity_trace_mode
        self._open_inline_menu(
            name="settings",
            step="activity_trace",
            title="Settings  Activity trace",
            options=[
                (
                    _ACTIVITY_TRACE_LABELS[mode],
                    (
                        f"{_ACTIVITY_TRACE_DESCRIPTIONS[mode]}  current"
                        if mode == current
                        else _ACTIVITY_TRACE_DESCRIPTIONS[mode]
                    ),
                )
                for mode in ACTIVITY_TRACE_MODES
            ],
        )

    def _model_flow_options(
        self: _InlineFlowHost,
        pc: ProviderConfig,
        choices: list[tuple[str, str, str, bool]],
    ) -> list[tuple[str, str]]:
        active = pc.get_active()
        current_model = self.session.config.model
        duplicate_models = _duplicate_model_names(choices)
        options: list[tuple[str, str]] = []
        for slug, model, display_name, is_free in choices:
            is_current = active is not None and active.slug == slug and model == current_model
            desc = f"via {display_name}"
            if is_free:
                desc += "  free"
            if is_current:
                desc += "  current"
            options.append(
                (
                    _model_choice_label(
                        model,
                        display_name,
                        duplicate=model in duplicate_models,
                    ),
                    desc,
                )
            )
        return options

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
                    f"inside Hephaistos: {', '.join(environment_credentials)}."
                )
                return
            self._append_notice(
                "No stored credentials found. Env keys must be unset outside Hephaistos."
            )
            return
        options = [(target.label, target.description) for target in targets]
        if environment_credentials:
            self._append_notice(
                "Environment credentials stay outside Hephaistos: "
                f"{', '.join(environment_credentials)}."
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
        self: _InlineFlowHost,
        sessions: list[chat_storage.SessionRecord],
    ) -> str:
        lines = [f"Saved sessions for {self.session.armory_path}:"]
        for entry in sessions:
            title = entry["title"] or "(untitled)"
            lines.append(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")
        return "\n".join(lines)

    def _open_sessions_flow(
        self: _InlineFlowHost, sessions: list[chat_storage.SessionRecord]
    ) -> None:
        self._open_inline_menu(
            name="sessions",
            step="menu",
            title="Sessions  choose a chat to resume",
            options=[
                (
                    entry["session_id"],
                    f"{entry['title'] or '(untitled)'}  {entry['updated_at']}",
                )
                for entry in sessions
            ],
        )

    def _logout_targets(self: _InlineFlowHost) -> list[_LogoutTarget]:
        pc = ProviderConfig.load()
        targets: list[_LogoutTarget] = []
        for slug in sorted(oauth.list_providers()):
            display = pc.providers[slug].display_name if slug in pc.providers else slug
            targets.append(
                _LogoutTarget(
                    slug=slug,
                    kind="oauth",
                    label=_oauth_logout_label(slug, display),
                    description="configured",
                )
            )
        for slug, provider in pc.providers.items():
            has_keychain_key = retrieve_key(slug) is not None
            has_volatile_key = get_volatile(slug) is not None
            if not has_keychain_key and not has_volatile_key:
                continue
            targets.append(
                _LogoutTarget(
                    slug=slug,
                    kind="api_key",
                    label=_api_key_logout_label(provider.display_name),
                    description="configured",
                )
            )
        return targets

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

    def _select_inline_flow_option(self: _InlineFlowHost, index: int) -> None:
        if not (0 <= index < len(self._inline_flow.options)):
            return
        self._submit_inline_flow(self._inline_flow.options[index][0])

    def _submit_inline_flow(self: _InlineFlowHost, value: str) -> None:
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

    def _handle_inline_menu_choice(self: _InlineFlowHost, label: str) -> None:
        if self._inline_flow.name == "study_topic":
            if self._inline_flow.step == "topic":
                if prompt := self._inline_flow.prompts.get(label):
                    self._close_inline_flow(f"selected: {label}")
                    self._submit_inline_chat_value(prompt)
                    return
                if label == _CUSTOM_STUDY_PROMPT_LABEL:
                    self._prompt_inline_text(
                        "study_topic",
                        "custom_prompt",
                        _CUSTOM_STUDY_PROMPT_PLACEHOLDER,
                    )
                    return
                self._open_inline_menu(
                    name="study_topic",
                    step="action",
                    title=f"Study {label}",
                    options=[
                        ("Explain it", "build intuition from the selected topic"),
                        ("Practice it", "try one source-grounded exercise"),
                        ("Recall drill", "answer from memory, then get feedback"),
                    ],
                )
                self._inline_flow.slug = label
                return
            if self._inline_flow.step == "action":
                topic = self._inline_flow.slug
                prompt = _study_topic_action_prompt(label, topic)
                self._close_inline_flow(f"selected: {topic}")
                self._submit_inline_chat_value(prompt)
                return
        if self._inline_flow.name == "settings":
            if self._inline_flow.step == "menu":
                if label == "Privacy & Diagnostics":
                    self._open_privacy_flow()
                elif label == "Appearance":
                    self._open_appearance_flow()
                elif label == "Activity trace":
                    self._open_activity_trace_flow()
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
            if self._inline_flow.step == "activity_trace":
                self._handle_activity_trace_choice(label)
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
        elif label == "OpenAI API":
            self._prompt_inline_text("login", "openai_key", "OpenAI API key")
        elif label == "OpenRouter":
            self._prompt_inline_text("login", "openrouter_key", "OpenRouter API key")
        elif label == "Z.AI":
            self._prompt_inline_text("login", "zai_key", "Z.AI API key")
        elif label == "Custom endpoint":
            self._prompt_inline_text("login", "custom_endpoint", "OpenAI-compatible base URL")

    def _open_study_topic_flow(
        self: _InlineFlowHost,
        options: list[tuple[str, str]],
        prompts: dict[str, str] | None = None,
    ) -> None:
        self._open_inline_menu(
            name="study_topic",
            step="topic",
            title="Choose a topic to study",
            options=_study_topic_menu_options(options),
            prompts=prompts,
        )

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
        self._open_privacy_flow()

    def _handle_appearance_choice(self: _InlineFlowHost, label: str) -> None:
        if label not in THEME_PRESETS:
            return
        save_setting("theme", label)
        set_theme(label)
        self._refresh_tui_css()
        self._append_notice(f"theme: {label}")
        self._open_appearance_flow()

    def _handle_activity_trace_choice(self: _InlineFlowHost, label: str) -> None:
        mode = _ACTIVITY_TRACE_MODE_BY_LABEL.get(label)
        if mode is None:
            return
        save_setting("activity_trace_mode", mode)
        self._append_notice(f"activity trace: {_ACTIVITY_TRACE_LABELS[mode]}")
        self._open_activity_trace_flow()

    def _refresh_tui_css(self: _InlineFlowHost) -> None:
        self.CSS = _tui_css()
        screen_path = inspect.getfile(self.__class__)
        read_from = (screen_path, f"{self.__class__.__name__}.CSS")
        self.stylesheet.add_source(self.CSS, read_from=read_from, is_default_css=False)
        self.refresh_css(animate=False)
        palette = current_palette()
        self.styles.background = palette.bg_app
        self.styles.background_tint = palette.bg_app
        screen = cast("_ScreenObject", self.screen)
        screen.styles.background = palette.bg_app
        screen.styles.background_tint = palette.bg_app
        self._refresh_status("ready")
        self._refresh_footer_hints()
        self._update_info_panel()
        self._schedule_transcript_reflow()

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
        step = self._inline_flow.step
        if step == "openai_key":
            self._store_provider_key("openai", value)
        elif step == "openrouter_key":
            self._store_provider_key("openrouter", value)
        elif step == "zai_key":
            self._store_provider_key("zai", value)
        elif step == "custom_endpoint":
            self._inline_flow.endpoint = value.rstrip("/")
            self._prompt_inline_text("login", "custom_model", "Model name")
        elif step == "custom_model":
            self._inline_flow.model = value
            self._prompt_inline_text("login", "custom_key", "API key")
        elif self._inline_flow.name == "study_topic" and step == "custom_prompt":
            self._close_inline_flow("selected: custom prompt")
            self._submit_inline_chat_value(value)
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

    def _store_provider_key(self: _InlineFlowHost, slug: str, key: str) -> None:
        try:
            store_key(slug, key)
        except Exception:
            set_volatile(slug, key)
        pc = ProviderConfig.load()
        p = activate_provider_for_session(pc, self.session, slug)
        self._close_inline_flow(f"provider: {p.display_name}")
        self._refresh_status("ready")
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
        self.call_from_thread(self._refresh_status, "ready")
        self.call_from_thread(self._update_info_panel)

    def _perform_logout(self: _InlineFlowHost, label: str) -> None:
        targets = self._logout_targets()
        if label == "All":
            for target in targets:
                if target.kind == "oauth":
                    oauth.clear_credentials(target.slug)
                else:
                    clear_key(target.slug)
            self._close_inline_flow("logged out: all providers")
            return
        for target in targets:
            if target.label == label:
                if target.kind == "oauth":
                    oauth.clear_credentials(target.slug)
                else:
                    clear_key(target.slug)
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
        self._refresh_status("ready")
        self._update_info_panel()

    def _close_inline_flow(self: _InlineFlowHost, notice: str = "") -> None:
        self._inline_flow = InlineFlow()
        self._hide_completions()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = 'Ask anything... "Summarize the risks in this document set"'
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


def _dedupe_inline_options(options: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Keep inline menus compact when provider/model sources return duplicate rows."""
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for label, description in options:
        key = (label.strip().casefold(), description.strip().casefold())
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, description))
    return deduped


def _study_topic_action_prompt(action: str, topic: str) -> str:
    suffix = _LANGUAGE_PRESERVING_TOPIC_PROMPT
    if action == "Explain it":
        return (
            f"Teach me {topic} in simple terms, grounded in the evidence for this topic.{suffix}"
        )
    if action == "Practice it":
        return f"Give me one source-grounded practice question about {topic}.{suffix}"
    return f"Start a quick recall drill about {topic}.{suffix}"


def overview_topic_menu(reply: str) -> OverviewTopicMenu | None:
    if not _overview_reply_has_menu_context(reply):
        return None
    topics: list[tuple[str, str]] = []
    recommendation_options: list[tuple[str, str]] = []
    prompts: dict[str, str] = {}
    in_topics = False
    in_recommendations = False
    for line in reply.splitlines():
        stripped = line.strip()
        if stripped.startswith(_OVERVIEW_TOPIC_SECTION_HEADING.removesuffix(":")):
            in_topics = True
            in_recommendations = False
            continue
        if _OVERVIEW_RECOMMENDATION_HEADING_RE.match(stripped):
            in_topics = False
            in_recommendations = True
            continue
        standalone_recommendation = _overview_standalone_recommendation_option(stripped)
        if standalone_recommendation is not None:
            option, prompt = standalone_recommendation
            recommendation_options.append(option)
            prompts[option[0]] = prompt
            in_topics = False
            continue
        if not stripped:
            if in_topics and topics:
                in_topics = False
            elif in_recommendations and recommendation_options:
                in_recommendations = False
            continue
        if in_recommendations:
            recommendation = _overview_recommendation_option(stripped)
            if recommendation is not None:
                option, prompt = recommendation
                recommendation_options.append(option)
                prompts[option[0]] = prompt
            continue
        if not in_topics:
            continue
        if not stripped:
            break
        match = _OVERVIEW_TOPIC_LINE_RE.match(stripped)
        if match is None:
            if topics:
                break
            continue
        label = match.group("label").strip()
        if label:
            topics.append((label, _overview_topic_description(label)))
    if not topics and not recommendation_options:
        return None
    option_limit = 6
    topic_limit = max(0, option_limit - len(recommendation_options))
    options = [*topics[:topic_limit], *recommendation_options[:option_limit]]
    return OverviewTopicMenu(options=_study_topic_menu_options(options), prompts=prompts)


def _overview_reply_has_menu_context(reply: str) -> bool:
    if _OVERVIEW_TOPIC_PROMPT in reply:
        return True
    topic_heading = _OVERVIEW_TOPIC_SECTION_HEADING.removesuffix(":").casefold()
    if topic_heading not in reply.casefold():
        return False
    return (
        _OVERVIEW_MENU_HINT_RE.search(reply) is not None
        or _OVERVIEW_RECOMMENDATION_HEADING_RE.search(reply) is not None
    )


def overview_topic_options(reply: str) -> list[tuple[str, str]]:
    menu = overview_topic_menu(reply)
    return menu.options if menu is not None else []


def _study_topic_menu_options(options: list[tuple[str, str]]) -> list[tuple[str, str]]:
    content_options = [option for option in options if option[0] != _CUSTOM_STUDY_PROMPT_LABEL][:6]
    return [
        *content_options,
        (_CUSTOM_STUDY_PROMPT_LABEL, _CUSTOM_STUDY_PROMPT_DESCRIPTION),
    ]


def _overview_topic_description(topic: str) -> str:
    """Return a short, topic-specific hint for the study-topic menu."""
    words = _strip_overview_citations(topic).strip(" .")
    if not words:
        return "key ideas"
    normalized = " ".join(words.split())
    lowered = normalized.casefold()
    descriptions_by_topic = {
        "carrier waves": "signals carrying information",
        "eigenvalues": "matrix scaling factors",
        "enzyme kinetics": "enzyme reaction rates",
        "graph algorithms": "network problem solving",
        "matrix multiplication": "combining matrices",
        "protein folding": "how proteins take shape",
        "recurrence relations": "recursive sequence rules",
        "sequences": "ordered value patterns",
        "signal entropy": "uncertainty in signals",
    }
    if description := descriptions_by_topic.get(lowered):
        return description
    if " and " in lowered:
        return "relationship between ideas"
    if lowered.endswith(" kinetics"):
        return "rates of change"
    if lowered.endswith(" entropy"):
        return "uncertainty measure"
    if lowered.endswith(" algorithms"):
        return "problem-solving methods"
    if lowered.endswith(" waves"):
        return "wave behavior"
    return _trim_inline_option_label(f"what {normalized} means", limit=34)


def _overview_recommendation_option(
    line: str,
) -> tuple[tuple[str, str], str] | None:
    match = _OVERVIEW_RECOMMENDATION_LINE_RE.match(line)
    if match is None:
        return None
    recommendation = match.group("label").strip()
    if not recommendation:
        return None
    return (
        (_overview_recommendation_label(recommendation), "recommended"),
        _overview_recommendation_prompt(recommendation),
    )


def _overview_standalone_recommendation_option(
    line: str,
) -> tuple[tuple[str, str], str] | None:
    match = _OVERVIEW_STANDALONE_RECOMMENDATION_RE.match(line)
    if match is None:
        return None
    recommendation = match.group("label").strip()
    if not recommendation:
        return None
    return (
        (_overview_recommendation_label(recommendation), "recommended"),
        _overview_recommendation_prompt(recommendation),
    )


def _overview_recommendation_prompt(recommendation: str) -> str:
    question = _OVERVIEW_QUOTED_QUESTION_RE.search(recommendation)
    if question is not None:
        return question.group("question").strip()
    clean = _strip_overview_citations(recommendation).rstrip(".")
    explanation = re.fullmatch(r"Start with a guided explanation of (?P<topic>.+)", clean)
    if explanation is not None:
        topic = explanation.group("topic").strip()
        return (
            f"Teach me {topic} in simple terms, grounded in the evidence for this topic."
            f"{_LANGUAGE_PRESERVING_TOPIC_PROMPT}"
        )
    practice = re.fullmatch(
        r"Practice one exam-style or exercise question on (?P<topic>.+?)(?: using)?",
        clean,
    )
    if practice is not None:
        topic = practice.group("topic").strip()
        return (
            f"Give me one source-grounded practice question about {topic}."
            f"{_LANGUAGE_PRESERVING_TOPIC_PROMPT}"
        )
    compare = re.fullmatch(
        r"Compare (?P<left>.+?) and (?P<right>.+?) so you can separate the ideas",
        clean,
    )
    if compare is not None:
        left = compare.group("left").strip()
        right = compare.group("right").strip()
        return (
            f"Compare {left} and {right}, grounded in the evidence for these topics."
            f"{_LANGUAGE_PRESERVING_TOPIC_PROMPT}"
        )
    if clean.startswith("Make a short study order"):
        return f"{clean}, grounded in the source material.{_LANGUAGE_PRESERVING_TOPIC_PROMPT}"
    return f"{clean}.{_LANGUAGE_PRESERVING_TOPIC_PROMPT}"


def _overview_recommendation_label(recommendation: str) -> str:
    clean = _strip_overview_citations(recommendation)
    explanation = re.fullmatch(r"Start with a guided explanation of (?P<topic>.+)", clean)
    if explanation is not None:
        return f"Explain {explanation.group('topic')}"
    practice = re.fullmatch(
        r"Practice one exam-style or exercise question on (?P<topic>.+?)(?: using)?",
        clean,
    )
    if practice is not None:
        return f"Practice {practice.group('topic')}"
    compare = re.fullmatch(
        r"Compare (?P<left>.+?) and (?P<right>.+?) so you can separate the ideas",
        clean,
    )
    if compare is not None:
        return f"Compare {compare.group('left')} and {compare.group('right')}"
    if "contrastive question" in clean.casefold():
        return "Ask a contrastive question"
    if clean.startswith("Make a short study order"):
        return "Make a study order"
    return _trim_inline_option_label(clean)


def _strip_overview_citations(text: str) -> str:
    return " ".join(_OVERVIEW_CITATION_RE.sub("", text).split())


def _trim_inline_option_label(label: str, *, limit: int = 52) -> str:
    if len(label) <= limit:
        return label
    return label[: limit - 1].rstrip(" ,;:.") + "…"


def _api_key_logout_label(display_name: str) -> str:
    if display_name == "Pollinations AI (free)":
        return "Pollinations"
    if display_name == "Z.AI / GLM":
        return "Z.AI"
    if display_name.casefold().endswith(" api"):
        return display_name
    if display_name.casefold().endswith(" api key"):
        return display_name
    return f"{display_name} API key"


def _oauth_logout_label(slug: str, display_name: str) -> str:
    if slug == "openai-codex":
        return "ChatGPT Plus/Pro"
    return display_name


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


def _duplicate_model_names(choices: list[tuple[str, str, str, bool]]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for _slug, model, _display_name, _is_free in choices:
        if model in seen:
            duplicates.add(model)
        seen.add(model)
    return duplicates


def _model_choice_label(model: str, display_name: str, *, duplicate: bool) -> str:
    if not duplicate:
        return model
    return f"{model} [{display_name}]"


def _model_choice_from_label(
    label: str,
    choices: list[tuple[str, str, str, bool]],
) -> tuple[str, str, str, bool] | None:
    model, provider = _parse_model_choice_label(label)
    for choice in choices:
        _slug, choice_model, display_name, _is_free = choice
        if choice_model != model:
            continue
        if provider is not None and display_name != provider:
            continue
        return choice
    return None


def _parse_model_choice_label(label: str) -> tuple[str, str | None]:
    stripped = label.strip()
    if stripped.endswith("]") and " [" in stripped:
        model, provider = stripped.rsplit(" [", 1)
        return model, provider[:-1]
    return stripped, None
