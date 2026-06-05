from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar, cast

from heph_ai.palette import TRANSPARENT
from heph_ai.providers.config import ProviderConfig
from parameters.settings import (
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
from privacy.consent import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)

from heph_interfaces.terminal import current_palette, set_theme
from heph_interfaces.tui.auth_flows import TuiAuthFlowMixin
from heph_interfaces.tui.display_text import COMPOSER_PLACEHOLDER
from heph_interfaces.tui.flow_state import InlineFlow
from heph_interfaces.tui.inline_menu import (
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
)
from heph_interfaces.tui.model_flow import (
    _model_choice_from_label,
    _model_choice_label,
)
from heph_interfaces.tui.model_flows import TuiModelFlowMixin
from heph_interfaces.tui.render_state import DirtyRegion, TuiRenderCache
from heph_interfaces.tui.session_flows import TuiSessionFlowMixin
from heph_interfaces.tui.session_state import TuiRuntimeState
from heph_interfaces.tui.slash_completion import (
    changed_highlight_indices,
    completion_menu_scroll_y,
)
from heph_interfaces.tui.style import _tui_css

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
    from chat import storage as chat_storage
    from chat.session import ChatSession
    from chat.turn_history import TurnSnapshot
    from textual import events
    from textual.widget import Widget

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")

_ACTIVITY_TRACE_DESCRIPTIONS = {
    ACTIVITY_TRACE_TOOL_CALLS: "live reads, commands, model calls, results",
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: "compact status and final summary",
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: "hide internal activity lines",
}
_ACTIVITY_TRACE_MODE_BY_LABEL = {label: mode for mode, label in ACTIVITY_TRACE_LABELS.items()}


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


def _inline_menu_actions(host: _InlineFlowHost) -> dict[str, Callable[[str], None]]:
    return {
        "settings": host._handle_settings_choice,
        "models": host._perform_model_switch,
        "logout": host._perform_logout,
        "sessions": host._perform_session_resume,
        "turn": host._perform_turn_branch,
    }


class TuiInlineFlowMixin(TuiAuthFlowMixin, TuiModelFlowMixin, TuiSessionFlowMixin):
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
