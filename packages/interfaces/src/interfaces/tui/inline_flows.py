from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar, cast

from ai.providers.config import ProviderConfig
from hephaion.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_LABELS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_TOOL_CALLS,
    THEME_LABELS,
    THEME_PRESETS,
    THINKING_VISIBILITY_ALL,
    THINKING_VISIBILITY_LABELS,
    THINKING_VISIBILITY_MINIMAL,
    THINKING_VISIBILITY_OFF,
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

from interfaces.palette import TRANSPARENT
from interfaces.terminal import current_palette, set_theme
from interfaces.tui.auth_flows import TuiAuthFlowMixin
from interfaces.tui.display_text import COMPOSER_PLACEHOLDER
from interfaces.tui.flow_state import InlineFlow
from interfaces.tui.inline_menu import (
    _consume_inline_key,
    _dedupe_inline_options,
    _filtered_inline_options,
    _inline_menu_label_width,
    _inline_menu_option_text,
    _inline_menu_scrolled_label_width,
    _inline_menu_visible_label_width,
    _inline_option_index,
    _local_model_option_text,
    _prompt_width,
    _selected_inline_label,
    _session_menu_option_text,
)
from interfaces.tui.keymap import (
    TUI_KEYMAP_ACTIONS,
    RuntimeKeymap,
    TuiKeymapAction,
    display_key,
    keymap_action,
    keymap_config_summary,
    load_runtime_keymap,
    reset_keymap,
    reset_keymap_action,
    save_keymap_binding,
)
from interfaces.tui.local_flows import TuiLocalFlowMixin
from interfaces.tui.model_flow import (
    _model_choice_from_label,
    _model_choice_label,
)
from interfaces.tui.model_flows import TuiModelFlowMixin
from interfaces.tui.render_state import DirtyRegion, TuiRenderCache
from interfaces.tui.session_flows import TuiSessionFlowMixin
from interfaces.tui.session_state import TuiRuntimeState
from interfaces.tui.shortcut_hints import ShortcutHint, shortcut_hint_line
from interfaces.tui.slash_completion import (
    changed_highlight_indices,
    completion_menu_scroll_y,
)
from interfaces.tui.style import _tui_css

__all__ = [
    "TuiInlineFlowMixin",
    "_inline_menu_option_text",
    "_model_choice_from_label",
    "_model_choice_label",
]

try:
    from rich.text import Text as _RichText
    from textual import events
    from textual.widgets import Input, OptionList, RichLog
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]
    events = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    RichLog = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from hephaion.chat import storage as chat_storage
    from hephaion.chat.session import ChatSession
    from hephaion.chat.turn_history import TurnSnapshot
    from textual import events
    from textual.widget import Widget

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")
_INLINE_MENU_PLACEHOLDER_HINTS = shortcut_hint_line(
    (
        ShortcutHint("Filter", "type"),
        ShortcutHint("Move", "↑/↓"),
        ShortcutHint("Select", "enter"),
        ShortcutHint("Close", "esc"),
    )
)
_KEYMAP_MENU_PLACEHOLDER_HINTS = shortcut_hint_line(
    (
        ShortcutHint("Record", "enter"),
        ShortcutHint("Reset", "r"),
        ShortcutHint("Defaults", "d"),
        ShortcutHint("Close", "esc"),
    )
)
_KEYMAP_CAPTURE_PLACEHOLDER_HINTS = shortcut_hint_line(
    (
        ShortcutHint("Save", "next key"),
        ShortcutHint("Cancel", "esc"),
    )
)

_ACTIVITY_TRACE_CYCLE = (
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_TOOL_CALLS,
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
)
_THINKING_VISIBILITY_ALIASES = {
    THINKING_VISIBILITY_OFF: THINKING_VISIBILITY_OFF,
    "hidden": THINKING_VISIBILITY_OFF,
    THINKING_VISIBILITY_MINIMAL: THINKING_VISIBILITY_MINIMAL,
    THINKING_VISIBILITY_ALL: THINKING_VISIBILITY_ALL,
}
_THINKING_VISIBILITY_CYCLE = (
    THINKING_VISIBILITY_MINIMAL,
    THINKING_VISIBILITY_ALL,
    THINKING_VISIBILITY_OFF,
)
_LIVE_TOKENS_ALIASES = {
    "shown": True,
    "show": True,
    "on": True,
    "yes": True,
    "true": True,
    "1": True,
    "hidden": False,
    "hide": False,
    "off": False,
    "no": False,
    "false": False,
    "0": False,
}


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
    _keymap: RuntimeKeymap
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

    def _open_keymap_flow(self, selected_label: str | None = None) -> None: ...

    def _open_models_flow(self) -> None: ...

    def _handle_keymap_choice(self, label: str) -> None: ...

    def _handle_keymap_capture(self, event: events.Key) -> bool: ...

    def _handle_keymap_menu_key(self, event: events.Key) -> bool: ...

    def _open_local_flow(self, query: str = "") -> None: ...

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

    def _thinking_visibility_summary(self) -> str: ...

    def _live_tokens_summary(self) -> str: ...

    def _live_cost_summary(self) -> str: ...

    def _privacy_option_description(
        self,
        *,
        enabled: bool,
        available: bool,
        overridden: bool,
    ) -> str: ...

    def _open_privacy_flow(self, selected_label: str | None = None) -> None: ...

    def _cycle_appearance_setting(self) -> None: ...

    def _cycle_activity_trace_setting(self) -> None: ...

    def _cycle_thinking_visibility_setting(self) -> None: ...

    def _cycle_live_tokens_setting(self) -> None: ...

    def _cycle_live_cost_setting(self) -> None: ...

    def _cycle_vocabulary_setting(self) -> None: ...

    def _submit_live_tokens_command(self, value: str) -> None: ...

    def _submit_live_cost_command(self, value: str) -> None: ...

    def _submit_thinking_visibility_command(self, value: str) -> None: ...

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

    def _handle_local_choice(self, label: str) -> None: ...

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
        "Appearance": host._cycle_appearance_setting,
        "Activity trace": host._cycle_activity_trace_setting,
        "Model thinking": host._cycle_thinking_visibility_setting,
        "Live tokens": host._cycle_live_tokens_setting,
        "Live cost": host._cycle_live_cost_setting,
        "Vocabulary practice": host._cycle_vocabulary_setting,
        "Login": host._open_login_flow,
        "Logout": host._open_logout_flow,
    }


def _settings_step_actions(host: _InlineFlowHost) -> dict[str, Callable[[str], None]]:
    return {
        "privacy": host._handle_privacy_choice,
    }


def _inline_menu_actions(host: _InlineFlowHost) -> dict[str, Callable[[str], None]]:
    return {
        "keymap": host._handle_keymap_choice,
        "local": host._handle_local_choice,
        "settings": host._handle_settings_choice,
        "models": host._perform_model_switch,
        "logout": host._perform_logout,
        "sessions": host._perform_session_resume,
        "turn": host._perform_turn_branch,
    }


class TuiInlineFlowMixin(
    TuiAuthFlowMixin,
    TuiLocalFlowMixin,
    TuiModelFlowMixin,
    TuiSessionFlowMixin,
):
    def _handle_inline_command(self: _InlineFlowHost, value: str) -> None:
        command = value.split(maxsplit=1)[0]
        actions = {
            "/login": self._open_login_flow,
            "/local": self._open_local_flow,
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
        composer.placeholder = f"{title}  {_INLINE_MENU_PLACEHOLDER_HINTS}"
        composer.focus()
        self.set_focus(composer)
        self._refresh_status()

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
            elif self._inline_flow.name == "local":
                prompt_width = _prompt_width(
                    suggestions.size.width,
                    self._transcript_render_width,
                )
                prompts = [
                    _local_model_option_text(
                        label,
                        description,
                        selected=index == selected,
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
        elif self._inline_flow.name == "local":
            label_width = 0
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
            elif self._inline_flow.name == "local":
                prompt = _local_model_option_text(
                    label,
                    description,
                    selected=option_index == highlighted,
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
        selected_label = _highlighted_inline_label(self)
        self._inline_flow.options = _filtered_inline_options(
            self._inline_flow.all_options,
            query,
        )
        self._render_inline_menu_options(
            self._inline_flow.options,
            highlighted=_inline_option_index(self._inline_flow.options, selected_label),
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
                ("Model thinking", self._thinking_visibility_summary()),
                ("Live tokens", self._live_tokens_summary()),
                ("Live cost", self._live_cost_summary()),
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

    def _open_keymap_flow(
        self: _InlineFlowHost,
        selected_label: str | None = None,
    ) -> None:
        self._keymap = load_runtime_keymap()
        title = f"Keymap  {keymap_config_summary(self._keymap)}"
        self._open_inline_menu(
            name="keymap",
            step="menu",
            title=title,
            options=_keymap_options(self._keymap),
            selected_label=selected_label,
        )
        composer = self.query_one("#composer", Input)
        composer.placeholder = f"{title}  {_KEYMAP_MENU_PLACEHOLDER_HINTS}"
        if self._keymap.errors:
            self._replace_last_notice(f"Keymap config issue: {self._keymap.errors[0]}")

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

    def _thinking_visibility_summary(self: _InlineFlowHost) -> str:
        thinking_visibility = load_app_settings().thinking_visibility
        return THINKING_VISIBILITY_LABELS.get(thinking_visibility, thinking_visibility)

    def _live_tokens_summary(self: _InlineFlowHost) -> str:
        return _visibility_state(load_app_settings().live_tokens_visible)

    def _live_cost_summary(self: _InlineFlowHost) -> str:
        return _visibility_state(load_app_settings().live_cost_visible)

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

    def _cycle_appearance_setting(self: _InlineFlowHost) -> None:
        theme = _next_cycle_value(load_app_settings().theme, THEME_PRESETS)
        _apply_theme_setting(self, theme)

    def _cycle_activity_trace_setting(self: _InlineFlowHost) -> None:
        activity_trace_mode = _next_cycle_value(
            load_app_settings().activity_trace_mode,
            _ACTIVITY_TRACE_CYCLE,
        )
        _apply_activity_trace_setting(self, activity_trace_mode)

    def _cycle_thinking_visibility_setting(self: _InlineFlowHost) -> None:
        visibility = _next_cycle_value(
            load_app_settings().thinking_visibility,
            _THINKING_VISIBILITY_CYCLE,
        )
        _apply_thinking_visibility_setting(self, visibility)

    def _cycle_live_tokens_setting(self: _InlineFlowHost) -> None:
        _apply_live_tokens_setting(
            self,
            not load_app_settings().live_tokens_visible,
        )

    def _cycle_live_cost_setting(self: _InlineFlowHost) -> None:
        _apply_live_cost_setting(
            self,
            not load_app_settings().live_cost_visible,
        )

    def _cycle_vocabulary_setting(self: _InlineFlowHost) -> None:
        strictness = _next_cycle_value(
            load_app_settings().vocab_strictness,
            VOCAB_STRICTNESS_MODES,
        )
        _apply_vocabulary_setting(self, strictness)

    def _submit_live_tokens_command(self: _InlineFlowHost, value: str) -> None:
        is_valid, visible = _live_tokens_command_visibility(value)
        if not is_valid:
            self._append_error("Usage: /tokens [shown|hidden]")
            return
        if visible is None:
            self._cycle_live_tokens_setting()
            return
        _apply_live_tokens_setting(self, visible)

    def _submit_live_cost_command(self: _InlineFlowHost, value: str) -> None:
        is_valid, visible = _live_cost_command_visibility(value)
        if not is_valid:
            self._append_error("Usage: /cost [shown|hidden]")
            return
        if visible is None:
            self._cycle_live_cost_setting()
            return
        _apply_live_cost_setting(self, visible)

    def _submit_thinking_visibility_command(self: _InlineFlowHost, value: str) -> None:
        is_valid, visibility = _thinking_visibility_command_value(value)
        if not is_valid:
            self._append_error("Usage: /thinking [hidden|minimal|all]")
            return
        if visibility is None:
            self._cycle_thinking_visibility_setting()
            return
        _apply_thinking_visibility_setting(self, visibility)

    def _handle_inline_flow_key(self: _InlineFlowHost, event: events.Key) -> bool:
        if self._inline_flow.name == "keymap" and self._inline_flow.step == "capture":
            return self._handle_keymap_capture(event)
        if (
            self._inline_flow.name == "keymap"
            and self._inline_flow.step == "menu"
            and self._handle_keymap_menu_key(event)
        ):
            return True
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

    def _handle_keymap_choice(self: _InlineFlowHost, label: str) -> None:
        action = _keymap_action_for_label(label)
        if action is None:
            return
        current = "/".join(display_key(key) for key in self._keymap.keys_for_action(action.id))
        self._open_inline_menu(
            name="keymap",
            step="capture",
            title=f"Keymap  {action.label}",
            options=[("Press shortcut", f"ACTION {action.label}  CURRENT {current or 'unbound'}")],
        )
        self._inline_flow.slug = action.id
        composer = self.query_one("#composer", Input)
        composer.placeholder = f"Keymap  {action.label}  {_KEYMAP_CAPTURE_PLACEHOLDER_HINTS}"

    def _handle_keymap_capture(self: _InlineFlowHost, event: events.Key) -> bool:
        action = keymap_action(self._inline_flow.slug)
        if action is None:
            self._close_inline_flow("Keymap action disappeared.")
            return _consume_inline_key(event)
        if event.key == "escape":
            self._open_keymap_flow(selected_label=action.label)
            return _consume_inline_key(event)

        result = save_keymap_binding(action.id, event.key)
        if result.saved:
            self._keymap = load_runtime_keymap()
            self._replace_last_notice(result.message)
            self._open_keymap_flow(selected_label=action.label)
        else:
            self._replace_last_notice(result.message)
        self._refresh_footer_hints()
        return _consume_inline_key(event)

    def _handle_keymap_menu_key(self: _InlineFlowHost, event: events.Key) -> bool:
        if event.key == "d":
            result = reset_keymap()
            self._keymap = load_runtime_keymap()
            self._replace_last_notice(result.message)
            self._open_keymap_flow()
            return _consume_inline_key(event)
        if event.key != "r":
            return False
        label = _highlighted_inline_label(self)
        if label is None:
            return _consume_inline_key(event)
        action = _keymap_action_for_label(label)
        if action is None:
            return _consume_inline_key(event)
        result = reset_keymap_action(action.id)
        self._keymap = load_runtime_keymap()
        self._replace_last_notice(result.message)
        self._open_keymap_flow(selected_label=action.label)
        return _consume_inline_key(event)

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
        theme = label.strip().casefold()
        if theme not in THEME_PRESETS:
            theme = _theme_from_label(label)
        if theme not in THEME_PRESETS:
            return
        _apply_theme_setting(self, theme)

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
        self._refresh_status()


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
    host._refresh_status()


def _next_cycle_value(current: str, values: tuple[str, ...]) -> str:
    if not values:
        return current
    if current not in values:
        return values[0]
    index = values.index(current)
    return values[(index + 1) % len(values)]


def _highlighted_inline_label(host: _InlineFlowHost) -> str | None:
    suggestions = host.query_one("#suggestions", OptionList)
    highlighted = suggestions.highlighted
    if highlighted is None or not 0 <= highlighted < len(host._inline_flow.options):
        return None
    return host._inline_flow.options[highlighted][0]


def _keymap_options(keymap: RuntimeKeymap) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    for action in TUI_KEYMAP_ACTIONS:
        keys = "/".join(display_key(key) for key in keymap.keys_for_action(action.id))
        if not keys:
            keys = "unbound"
        state = "custom" if action.id in keymap.configured_actions else "default"
        options.append((action.label, f"KEY {keys}  STATE {state}  {action.description}"))
    return options


def _keymap_action_for_label(label: str) -> TuiKeymapAction | None:
    normalized = label.strip().casefold()
    for action in TUI_KEYMAP_ACTIONS:
        if action.label.casefold() == normalized:
            return action
    return None


def _command_arg(value: str) -> str:
    stripped = value.strip()
    if not stripped.startswith("/"):
        return ""
    return stripped[1:].partition(" ")[2].strip().casefold()


def _live_tokens_command_visibility(value: str) -> tuple[bool, bool | None]:
    arg = _command_arg(value)
    if not arg:
        return True, None
    if arg in _LIVE_TOKENS_ALIASES:
        return True, _LIVE_TOKENS_ALIASES[arg]
    return False, None


def _live_cost_command_visibility(value: str) -> tuple[bool, bool | None]:
    arg = _command_arg(value)
    if not arg:
        return True, None
    if arg in _LIVE_TOKENS_ALIASES:
        return True, _LIVE_TOKENS_ALIASES[arg]
    return False, None


def _thinking_visibility_command_value(value: str) -> tuple[bool, str | None]:
    arg = _command_arg(value)
    if not arg:
        return True, None
    if arg in _THINKING_VISIBILITY_ALIASES:
        return True, _THINKING_VISIBILITY_ALIASES[arg]
    return False, None


def _theme_from_label(label: str) -> str:
    for theme, theme_label in THEME_LABELS.items():
        if theme_label.casefold() == label.strip().casefold():
            return theme
    return ""


def _apply_theme_setting(host: _InlineFlowHost, theme: str) -> None:
    save_setting("theme", theme)
    set_theme(theme)
    host._refresh_tui_css()
    host._replace_last_notice(f"{THEME_LABELS[theme]} theme.")
    host._open_settings_flow(selected_label="Appearance")


def _apply_activity_trace_setting(host: _InlineFlowHost, activity_trace_mode: str) -> None:
    save_setting("activity_trace_mode", activity_trace_mode)
    host._replace_last_notice(f"Activity trace: {ACTIVITY_TRACE_LABELS[activity_trace_mode]}.")
    host._open_settings_flow(selected_label="Activity trace")


def _apply_thinking_visibility_setting(host: _InlineFlowHost, visibility: str) -> None:
    save_setting("thinking_visibility", visibility)
    host.session.config.thinking_visibility = visibility
    host._replace_last_notice(f"Model thinking: {THINKING_VISIBILITY_LABELS[visibility]}.")
    host._open_settings_flow(selected_label="Model thinking")


def _apply_live_tokens_setting(host: _InlineFlowHost, visible: bool) -> None:
    save_setting("live_tokens_visible", visible)
    host.session.live_tokens_visible = visible
    host._refresh_status()
    host._replace_last_notice(f"Live tokens {_visibility_state(visible)}.")
    host._open_settings_flow(selected_label="Live tokens")


def _apply_live_cost_setting(host: _InlineFlowHost, visible: bool) -> None:
    save_setting("live_cost_visible", visible)
    host.session.live_cost_visible = visible
    host._refresh_status()
    host._replace_last_notice(f"Live cost {_visibility_state(visible)}.")
    host._open_settings_flow(selected_label="Live cost")


def _apply_vocabulary_setting(host: _InlineFlowHost, strictness: str) -> None:
    save_setting("vocab_strictness", strictness)
    host._replace_last_notice(f"Vocabulary practice: {VOCAB_STRICTNESS_LABELS[strictness]}.")
    host._open_settings_flow(selected_label="Vocabulary practice")


def _visibility_state(visible: bool) -> str:
    return "shown" if visible else "hidden"
