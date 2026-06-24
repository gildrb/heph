"""Keyboard, composer, and completion controls for the TUI app."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeVar

from ai.providers.catalog import prefetch_provider_model_catalogs
from ai.providers.config import ProviderConfig
from ai.providers.reasoning import next_reasoning_level, reasoning_levels_for_model

import interfaces.tui.widgets as _tui_widgets
from interfaces.terminal.theme_state import current_palette
from interfaces.tui.cell_text import cell_width as _cell_width
from interfaces.tui.cell_text import pad_cell_right as _pad_cell_right
from interfaces.tui.display_text import footer_hints_text as _footer_hints_text
from interfaces.tui.display_text import menu_label_value
from interfaces.tui.display_text import status_render_width as _status_render_width
from interfaces.tui.display_text import status_text as _status_text
from interfaces.tui.ids import (
    COMPLETION_MENU_CLASS,
    COMPOSER_ID,
    COMPOSER_SELECTOR,
    FOOTER_HINTS_SELECTOR,
    SUGGESTIONS_ID,
    SUGGESTIONS_SELECTOR,
)
from interfaces.tui.keymap import RuntimeKeymap
from interfaces.tui.option_list_layout import visible_option_height
from interfaces.tui.slash_command import tui_command_suggestions as _tui_command_suggestions
from interfaces.tui.slash_completion import (
    CompletionCandidate,
    SlashCompletionEngine,
)
from interfaces.tui.slash_completion import (
    changed_highlight_indices as _changed_highlight_indices,
)
from interfaces.tui.slash_completion import (
    completion_menu_scroll_y as _completion_menu_scroll_y,
)
from interfaces.tui.slash_completion import (
    completion_menu_visible_slice as _completion_menu_visible_slice,
)

try:
    from rich.text import Text as _RichText
    from textual import events
    from textual.widgets import Input, OptionList, Static
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]
    events = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession
    from rich.text import Text
    from textual.widget import Widget

    from interfaces.tui.flow_state import InlineFlow
    from interfaces.tui.session_state import TuiRuntimeState

_WidgetT = TypeVar("_WidgetT")

_COMPLETION_DESCRIPTION_GAP = 4
_COMPLETION_MENU_MAX_VISIBLE_ROWS = 7
_COMPLETION_SELECTED_PREFIX = "→ "
_COMPLETION_UNSELECTED_PREFIX = "  "


@dataclass(frozen=True, slots=True)
class _CompletionDisplayWidths:
    provider: int = 0
    model: int = 0
    source: int = 0
    state: int = 0


class _ComposerControlsHost(Protocol):
    session: ChatSession
    state: TuiRuntimeState
    busy: bool
    completion_engine: SlashCompletionEngine
    completion_candidates: list[CompletionCandidate]
    _inline_flow: InlineFlow
    _transcript_render_width: int | None
    _armory_inline_active: bool
    _armory_creating: bool
    _armory_filter: str
    _materials_inline_active: bool
    _materials_filter: str
    _suggestions_mouse_hovering: bool
    _completion_command_column_width: int
    _completion_display_column_widths: _CompletionDisplayWidths
    _keymap: RuntimeKeymap

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    @property
    def focused(self) -> object | None: ...

    def set_focus(self, widget: Widget | None) -> None: ...

    def on_key(self, event: events.Key) -> None: ...

    def _handle_active_overlay_key(self, event: events.Key) -> bool: ...

    def _handle_input_key(self, event: events.Key) -> bool: ...

    def _handle_composer_shortcut(self, event: events.Key) -> bool: ...

    def _handle_keymap_shortcut(self, event: events.Key) -> bool: ...

    def _keymap_action_handler(self, action_id: str) -> Callable[[], None] | None: ...

    def _composer_shortcut_handler(self, key: str) -> Callable[[], bool] | None: ...

    def _run_shortcut(self, shortcut: Callable[[], None]) -> bool: ...

    def _cycle_reasoning_shortcut(self) -> bool: ...

    def _complete_shortcut(self) -> bool: ...

    def _insert_composer_newline_shortcut(self) -> bool: ...

    def _handle_escape_shortcut(self) -> bool: ...

    def _move_completion_or_history(self, offset: int) -> None: ...

    def _redirect_printable_key_to_composer(
        self,
        event: events.Key,
        composer: Input,
    ) -> None: ...

    def _composer_character_for_key(self, event: events.Key) -> str | None: ...

    def _consume_key(self, event: events.Key) -> None: ...

    def _suggestions_hover_index(
        self,
        event: events.MouseMove,
        suggestions: OptionList,
    ) -> int | None: ...

    def _suggestions_option_in_range(self, option_index: int) -> bool: ...

    def _set_suggestions_mouse_hovering(self, suggestions: OptionList) -> None: ...

    def _clear_suggestions_mouse_hovering(
        self,
        suggestions: OptionList | None = None,
    ) -> None: ...

    def _highlight_completion_option(
        self,
        highlighted: int,
        suggestions: OptionList | None = None,
    ) -> None: ...

    def action_complete(self) -> None: ...

    def action_cycle_reasoning_level(self) -> None: ...

    def action_command_palette(self) -> None: ...

    def action_open_armory_home(self) -> None: ...

    def action_open_materials(self) -> None: ...

    def action_open_search(self) -> None: ...

    def action_evidence(self) -> None: ...

    def action_clear_transcript(self) -> None: ...

    def _apply_highlighted_completion(self) -> None: ...

    def _refresh_live_token_status(self, draft: str) -> None: ...

    def _completion_menu_visible(self) -> bool: ...

    def _refresh_completions(self) -> None: ...

    def _hide_completions(self) -> None: ...

    def _move_completion(self, offset: int) -> None: ...

    def _apply_completion(self, index: int) -> None: ...

    def _set_completion_options(self, *, highlighted: int | None) -> None: ...

    def _completion_command_width(self, highlighted: int | None, rendered_height: int) -> int: ...

    def _completion_display_widths(
        self,
        highlighted: int | None,
        rendered_height: int,
    ) -> _CompletionDisplayWidths: ...

    def _format_completion_candidate(
        self,
        candidate: CompletionCandidate,
        *,
        selected: bool = False,
        command_width: int = 22,
        display_widths: _CompletionDisplayWidths | None = None,
    ) -> str | Text: ...

    def _completion_preview(self, candidate: CompletionCandidate) -> str: ...

    def _handle_inline_flow_key(self, event: events.Key) -> bool: ...

    def _handle_armory_key(self, event: events.Key) -> bool: ...

    def _handle_materials_key(self, event: events.Key) -> bool: ...

    def _focus_message(self, direction: int) -> None: ...

    def action_insert_composer_newline(self) -> None: ...

    def action_cancel_turn(self) -> None: ...

    def _history_previous(self) -> None: ...

    def _history_next(self) -> None: ...

    def _filter_inline_menu_options(self, query: str) -> None: ...

    def _refresh_armory_inline(self) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _refresh_status(self) -> None: ...

    def _status_title(self) -> str: ...

    def _refresh_materials_inline(self) -> None: ...

    def _armory_open_highlighted(self) -> None: ...

    def _handle_materials_option_selected(
        self,
        list_id: str,
        index: int,
    ) -> None: ...

    def _select_inline_flow_option(self, index: int) -> None: ...

    def _submit_composer_value(self, *, apply_highlighted_completion: bool) -> None: ...

    def _update_armory_preview(self) -> None: ...

    def _handle_materials_option_highlighted(
        self,
        list_id: str,
        index: int,
    ) -> None: ...

    def _highlight_inline_menu_option(
        self,
        highlighted: int,
        suggestions: OptionList | None = None,
        *,
        preserve_scroll: bool = False,
    ) -> None: ...

    def _refresh_completion_position(self) -> None: ...

    def _replace_last_notice(self, text: str) -> None: ...

    def _render_inline_menu_options(
        self,
        options: list[tuple[str, str]],
        *,
        highlighted: int | None = 0,
    ) -> None: ...


class TuiComposerControlsMixin:
    session: ChatSession
    state: TuiRuntimeState
    busy: bool
    completion_engine: SlashCompletionEngine
    completion_candidates: list[CompletionCandidate]
    _inline_flow: InlineFlow
    _armory_inline_active: bool
    _armory_creating: bool
    _armory_filter: str
    _materials_inline_active: bool
    _materials_filter: str
    _suggestions_mouse_hovering: bool
    _completion_command_column_width: int
    _completion_display_column_widths: _CompletionDisplayWidths

    def on_key(self: _ComposerControlsHost, event: events.Key) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        if self._handle_input_key(event):
            return
        if self._handle_composer_shortcut(event):
            return
        self._redirect_printable_key_to_composer(event, composer)

    def _handle_active_overlay_key(self: _ComposerControlsHost, event: events.Key) -> bool:
        return (
            (self._inline_flow.active and self._handle_inline_flow_key(event))
            or (self._armory_inline_active and self._handle_armory_key(event))
            or (self._materials_inline_active and self._handle_materials_key(event))
        )

    def _handle_input_key(self: _ComposerControlsHost, event: events.Key) -> bool:
        if self.busy and self._handle_keymap_shortcut(event):
            return True
        return self._handle_active_overlay_key(event) or self._handle_keymap_shortcut(event)

    def _handle_composer_shortcut(self: _ComposerControlsHost, event: events.Key) -> bool:
        shortcut = self._composer_shortcut_handler(event.key)
        if shortcut is None or not shortcut():
            return False

        self._consume_key(event)
        return True

    def _composer_shortcut_handler(
        self: _ComposerControlsHost,
        key: str,
    ) -> Callable[[], bool] | None:
        movement_offsets = {
            "ctrl+up": lambda: self._focus_message(-1),
            "ctrl+down": lambda: self._focus_message(1),
            "up": lambda: self._move_completion_or_history(-1),
            "down": lambda: self._move_completion_or_history(1),
        }
        actions = {
            "escape": self._handle_escape_shortcut,
        }
        if key in movement_offsets:
            return lambda: self._run_shortcut(movement_offsets[key])
        return actions.get(key)

    @staticmethod
    def _run_shortcut(shortcut: Callable[[], None]) -> bool:
        shortcut()
        return True

    def _cycle_reasoning_shortcut(self: _ComposerControlsHost) -> bool:
        self.action_cycle_reasoning_level()
        return True

    def _complete_shortcut(self: _ComposerControlsHost) -> bool:
        self.action_complete()
        return True

    def _insert_composer_newline_shortcut(self: _ComposerControlsHost) -> bool:
        self.action_insert_composer_newline()
        return True

    def _handle_escape_shortcut(self: _ComposerControlsHost) -> bool:
        if self._completion_menu_visible():
            self._hide_completions()
            return True
        return False

    def _handle_keymap_shortcut(self: _ComposerControlsHost, event: events.Key) -> bool:
        action_id = self._keymap.action_for_key(event.key)
        if action_id is None:
            return False
        if action_id == "cancel_turn" and not self.busy:
            return False
        handler = self._keymap_action_handler(action_id)
        if handler is None:
            return False
        handler()
        self._consume_key(event)
        return True

    def _keymap_action_handler(
        self: _ComposerControlsHost,
        action_id: str,
    ) -> Callable[[], None] | None:
        actions: dict[str, Callable[[], None]] = {
            "cancel_turn": self.action_cancel_turn,
            "clear_transcript": self.action_clear_transcript,
            "command_palette": self.action_command_palette,
            "complete": self.action_complete,
            "cycle_reasoning_level": self.action_cycle_reasoning_level,
            "evidence": self.action_evidence,
            "insert_composer_newline": self.action_insert_composer_newline,
            "open_armory_home": self.action_open_armory_home,
            "open_materials": self.action_open_materials,
            "open_search": self.action_open_search,
        }
        return actions.get(action_id)

    def _move_completion_or_history(self: _ComposerControlsHost, offset: int) -> None:
        if self._completion_menu_visible():
            self._move_completion(offset)
        elif offset < 0:
            self._history_previous()
        else:
            self._history_next()

    def _redirect_printable_key_to_composer(
        self: _ComposerControlsHost,
        event: events.Key,
        composer: Input,
    ) -> None:
        if self.focused is composer:
            return
        character = self._composer_character_for_key(event)
        if character is None:
            return
        composer.focus()
        self.set_focus(composer)
        composer.insert_text_at_cursor(character)
        self._consume_key(event)

    @staticmethod
    def _composer_character_for_key(event: events.Key) -> str | None:
        return _tui_widgets.key_event_text(event)

    @staticmethod
    def _consume_key(event: events.Key) -> None:
        event.prevent_default()
        event.stop()

    def on_input_changed(self: _ComposerControlsHost, event: Input.Changed) -> None:
        if event.input.id == COMPOSER_ID:
            if self._inline_flow.active:
                self._filter_inline_menu_options(event.value)
                return
            if self._armory_inline_active:
                if not self._armory_creating:
                    self._armory_filter = event.value
                    self._refresh_armory_inline()
                self._refresh_footer_hints()
                return
            if self._materials_inline_active:
                self._materials_filter = event.value
                self._refresh_materials_inline()
                return
            self._refresh_live_token_status(event.value)
            self._refresh_completions()

    def on_option_list_option_selected(
        self: _ComposerControlsHost,
        event: OptionList.OptionSelected,
    ) -> None:
        if event.option_list.id == "armory-current-inline":
            event.stop()
            self._armory_open_highlighted()
            self._refresh_armory_inline()
            return
        if event.option_list.id in ("materials-list", "materials-list-right"):
            event.stop()
            if not self._materials_inline_active:
                return
            self._handle_materials_option_selected(
                event.option_list.id,
                event.option_index,
            )
            return
        if event.option_list.id != SUGGESTIONS_ID:
            return
        if self._inline_flow.active:
            self._select_inline_flow_option(event.option_index)
        else:
            self._apply_completion(event.option_index)
            self._submit_composer_value(apply_highlighted_completion=False)
        event.stop()

    def on_option_list_option_highlighted(
        self: _ComposerControlsHost,
        event: OptionList.OptionHighlighted,
    ) -> None:
        if event.option_list.id == "armory-current-inline":
            event.stop()
            self._update_armory_preview()
            return
        if event.option_list.id in ("materials-list", "materials-list-right"):
            event.stop()
            if not self._materials_inline_active:
                return
            self._handle_materials_option_highlighted(
                event.option_list.id,
                event.option_index,
            )

    def _handle_suggestions_mouse_move(
        self: _ComposerControlsHost,
        event: events.MouseMove,
    ) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        option_index = self._suggestions_hover_index(event, suggestions)
        if option_index is None:
            self._clear_suggestions_mouse_hovering(suggestions)
            return

        self._set_suggestions_mouse_hovering(suggestions)
        if suggestions.highlighted == option_index:
            return
        if self._inline_flow.active:
            self._highlight_inline_menu_option(option_index, suggestions, preserve_scroll=True)
        else:
            self._highlight_completion_option(option_index, suggestions)

    def _suggestions_hover_index(
        self: _ComposerControlsHost,
        event: events.MouseMove,
        suggestions: OptionList,
    ) -> int | None:
        if getattr(getattr(event, "widget", None), "id", None) != SUGGESTIONS_ID:
            return None
        if not suggestions.has_class("visible"):
            return None
        option_index = event.style.meta.get("option")
        if not isinstance(option_index, int):
            return None
        if not self._suggestions_option_in_range(option_index):
            return None
        return option_index

    def _suggestions_option_in_range(
        self: _ComposerControlsHost,
        option_index: int,
    ) -> bool:
        option_count = (
            len(self._inline_flow.options)
            if self._inline_flow.active
            else len(self.completion_candidates)
        )
        return 0 <= option_index < option_count

    def _set_suggestions_mouse_hovering(
        self: _ComposerControlsHost,
        suggestions: OptionList,
    ) -> None:
        if self._suggestions_mouse_hovering:
            return
        suggestions.add_class("mouse-hovering")
        self._suggestions_mouse_hovering = True

    def _clear_suggestions_mouse_hovering(
        self: _ComposerControlsHost,
        suggestions: OptionList | None = None,
    ) -> None:
        if not self._suggestions_mouse_hovering:
            return
        if suggestions is None:
            suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        suggestions.remove_class("mouse-hovering")
        self._suggestions_mouse_hovering = False

    def _highlight_completion_option(
        self: _ComposerControlsHost,
        highlighted: int,
        suggestions: OptionList | None = None,
    ) -> None:
        if suggestions is None:
            suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        previous = suggestions.highlighted
        if previous == highlighted:
            return
        command_width = self._completion_command_width(highlighted, suggestions.size.height)
        display_widths = self._completion_display_widths(highlighted, suggestions.size.height)
        if (
            command_width != self._completion_command_column_width
            or display_widths != self._completion_display_column_widths
        ):
            self._set_completion_options(highlighted=highlighted)
        else:
            for option_index in _changed_highlight_indices(
                previous,
                highlighted,
                len(self.completion_candidates),
            ):
                suggestions.replace_option_prompt_at_index(
                    option_index,
                    self._format_completion_candidate(
                        self.completion_candidates[option_index],
                        selected=option_index == highlighted,
                        command_width=command_width,
                        display_widths=display_widths,
                    ),
                )
        suggestions.highlighted = highlighted
        self._refresh_completion_position()

    def action_complete(self: _ComposerControlsHost) -> None:
        if self._inline_flow.active:
            return
        if not self.completion_candidates:
            self._refresh_completions()
        if not self.completion_candidates:
            return
        self._apply_highlighted_completion()

    def action_cycle_reasoning_level(self: _ComposerControlsHost) -> None:
        if self.busy:
            return

        self._hide_completions()
        prefetch_provider_model_catalogs(ProviderConfig.load())
        levels = reasoning_levels_for_model(
            self.session.config.model,
            self.session.config.provider_slug or None,
        )
        if not levels:
            self._replace_last_notice("Reasoning unavailable.")
            return
        self.session.config.reasoning_level = next_reasoning_level(
            self.session.config.reasoning_level,
            levels=levels,
        )
        self.session.dirty = True
        status = self.query_one("#status", Static)
        status.update(
            _status_text(
                self.session,
                title=self._status_title(),
                width=_status_render_width(status.size.width),
            )
        )
        self.query_one(FOOTER_HINTS_SELECTOR, Static).update(
            _footer_hints_text(self.session, keymap=self._keymap)
        )
        self._replace_last_notice(f"Reasoning {self.session.config.reasoning_level}.")

    def _apply_highlighted_completion(self: _ComposerControlsHost) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        highlighted = suggestions.highlighted
        self._apply_completion(highlighted if highlighted is not None else 0)

    def _refresh_live_token_status(self: _ComposerControlsHost, draft: str) -> None:
        if not self.session.live_tokens_visible:
            return
        chat_draft = "" if draft.lstrip().startswith("/") else draft
        status = self.query_one("#status", Static)
        status.update(
            _status_text(
                self.session,
                draft=chat_draft,
                title=self._status_title(),
                width=_status_render_width(status.size.width),
            )
        )

    def _completion_menu_visible(self: _ComposerControlsHost) -> bool:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        return suggestions.has_class("visible") and (
            bool(self.completion_candidates) or self._inline_flow.active
        )

    def _refresh_completions(self: _ComposerControlsHost) -> None:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        before_cursor = composer.value[: composer.cursor_position]
        self.completion_candidates = self.completion_engine.candidates(
            before_cursor,
            _tui_command_suggestions(),
        )
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        suggestions.remove_class("inline-menu")
        if not self.completion_candidates:
            suggestions.set_options([])
            suggestions.remove_class(COMPLETION_MENU_CLASS)
            suggestions.remove_class("visible")
            self._refresh_status()
            self._refresh_footer_hints()
            return
        self._set_completion_options(highlighted=0)
        suggestions.add_class("visible")
        self._clear_suggestions_mouse_hovering(suggestions)
        suggestions.highlighted = 0
        suggestions.scroll_y = 0
        self._refresh_status()
        self._refresh_footer_hints()
        composer.focus()

    def _hide_completions(self: _ComposerControlsHost) -> None:
        self.completion_candidates = []
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        suggestions.set_options([])
        suggestions.remove_class("inline-menu")
        suggestions.remove_class(COMPLETION_MENU_CLASS)
        suggestions.remove_class("visible")
        self._clear_suggestions_mouse_hovering(suggestions)
        self._refresh_status()
        self._refresh_footer_hints()

    def _move_completion(self: _ComposerControlsHost, offset: int) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        self._clear_suggestions_mouse_hovering(suggestions)
        flow = self._inline_flow
        options = flow.options if flow.active else self.completion_candidates
        if not options:
            return
        highlighted = ((suggestions.highlighted or 0) + offset) % len(options)
        if flow.active:
            self._render_inline_menu_options(flow.options, highlighted=highlighted)
        elif self.completion_candidates:
            self._set_completion_options(highlighted=highlighted)
        suggestions.highlighted = highlighted
        suggestions.scroll_y = _completion_menu_scroll_y(
            highlighted,
            len(options),
            suggestions.size.height,
        )
        self._refresh_footer_hints()

    def _apply_completion(self: _ComposerControlsHost, index: int) -> None:
        if not (0 <= index < len(self.completion_candidates)):
            return
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        candidate = self.completion_candidates[index]
        before_cursor = composer.value[: composer.cursor_position]
        after_cursor = composer.value[composer.cursor_position :]
        replacement_start = len(before_cursor) + candidate.start_position
        next_value = before_cursor[:replacement_start] + candidate.text + after_cursor
        composer.value = next_value
        composer.cursor_position = replacement_start + len(candidate.text)
        composer.focus()
        self._refresh_completions()

    def _set_completion_options(
        self: _ComposerControlsHost,
        *,
        highlighted: int | None,
    ) -> None:
        suggestions = self.query_one(SUGGESTIONS_SELECTOR, OptionList)
        rendered_height = visible_option_height(
            next_option_count=len(self.completion_candidates),
            current_option_count=suggestions.option_count,
            rendered_height=suggestions.size.height,
            max_visible_rows=_COMPLETION_MENU_MAX_VISIBLE_ROWS,
        )
        command_width = self._completion_command_width(highlighted, rendered_height)
        display_widths = self._completion_display_widths(highlighted, rendered_height)
        self._completion_command_column_width = command_width
        self._completion_display_column_widths = display_widths
        suggestions.add_class(COMPLETION_MENU_CLASS)
        suggestions.set_options(
            [
                self._format_completion_candidate(
                    candidate,
                    selected=index == highlighted,
                    command_width=command_width,
                    display_widths=display_widths,
                )
                for index, candidate in enumerate(self.completion_candidates)
            ]
        )

    def _completion_command_width(
        self: _ComposerControlsHost,
        highlighted: int | None,
        rendered_height: int,
    ) -> int:
        candidates = self.completion_candidates
        if not candidates:
            return 0
        highlighted_index = highlighted if highlighted is not None else 0
        visible_slice = _completion_menu_visible_slice(
            highlighted_index,
            len(candidates),
            rendered_height,
        )
        visible_candidates = candidates[visible_slice]
        return max(
            (
                _cell_width(self._completion_preview(candidate).strip())
                for candidate in visible_candidates
            ),
            default=0,
        )

    def _completion_display_widths(
        self: _ComposerControlsHost,
        highlighted: int | None,
        rendered_height: int,
    ) -> _CompletionDisplayWidths:
        candidates = self.completion_candidates
        if not candidates:
            return _CompletionDisplayWidths()
        highlighted_index = highlighted if highlighted is not None else 0
        visible_slice = _completion_menu_visible_slice(
            highlighted_index,
            len(candidates),
            rendered_height,
        )
        visible_candidates = candidates[visible_slice]
        return _CompletionDisplayWidths(
            provider=max(
                (
                    _cell_width(_completion_display_provider(candidate))
                    for candidate in visible_candidates
                ),
                default=0,
            ),
            model=max(
                (
                    _cell_width(_completion_display_model(candidate))
                    for candidate in visible_candidates
                ),
                default=0,
            ),
            source=max(
                (
                    _cell_width(_completion_display_source(candidate))
                    for candidate in visible_candidates
                ),
                default=0,
            ),
            state=max(
                (
                    _cell_width(_completion_display_state(candidate))
                    for candidate in visible_candidates
                ),
                default=0,
            ),
        )

    def _format_completion_candidate(
        self: _ComposerControlsHost,
        candidate: CompletionCandidate,
        *,
        selected: bool = False,
        command_width: int = 22,
        display_widths: _CompletionDisplayWidths | None = None,
    ) -> str | Text:
        prefix = _COMPLETION_SELECTED_PREFIX if selected else _COMPLETION_UNSELECTED_PREFIX
        if candidate.display_provider:
            display_widths = display_widths or _completion_display_widths_for_candidate(candidate)
            return f"{prefix}{_completion_display_text(candidate, display_widths)}  "
        value = self._completion_preview(candidate).strip()
        if _RichText is None:
            if candidate.description:
                return (
                    f"{prefix}{_pad_cell_right(value, command_width)}"
                    f"{' ' * _COMPLETION_DESCRIPTION_GAP}{candidate.description}  "
                )
            return f"{prefix}{value}  "
        palette = current_palette()
        command_style = palette.brand_primary if selected else palette.text_secondary
        description_style = palette.text_muted
        prefix_style = palette.brand_primary if selected else palette.text_muted
        text = _RichText()
        text.append(prefix, style=prefix_style)
        if candidate.description:
            text.append(
                f"{_pad_cell_right(value, command_width)}{' ' * _COMPLETION_DESCRIPTION_GAP}",
                style=command_style,
            )
            text.append(f"{candidate.description}  ", style=description_style)
            return text
        text.append(f"{value}  ", style=command_style)
        return text

    def _completion_preview(
        self: _ComposerControlsHost,
        candidate: CompletionCandidate,
    ) -> str:
        composer = self.query_one(COMPOSER_SELECTOR, Input)
        before_cursor = composer.value[: composer.cursor_position]
        replacement_start = len(before_cursor) + candidate.start_position
        return before_cursor[:replacement_start] + candidate.text


def _completion_display_provider(candidate: CompletionCandidate) -> str:
    if not candidate.display_provider:
        return ""
    return menu_label_value("provider", candidate.display_provider)


def _completion_display_model(candidate: CompletionCandidate) -> str:
    return menu_label_value("model", candidate.display_model) if candidate.display_model else ""


def _completion_display_source(candidate: CompletionCandidate) -> str:
    return menu_label_value("source", candidate.display_source) if candidate.display_source else ""


def _completion_display_state(candidate: CompletionCandidate) -> str:
    return menu_label_value("state", candidate.display_tags) if candidate.display_tags else ""


def _completion_display_widths_for_candidate(
    candidate: CompletionCandidate,
) -> _CompletionDisplayWidths:
    return _CompletionDisplayWidths(
        provider=_cell_width(_completion_display_provider(candidate)),
        model=_cell_width(_completion_display_model(candidate)),
        source=_cell_width(_completion_display_source(candidate)),
        state=_cell_width(_completion_display_state(candidate)),
    )


def _completion_display_text(
    candidate: CompletionCandidate,
    widths: _CompletionDisplayWidths,
) -> str:
    fields = (
        (_completion_display_provider(candidate), widths.provider),
        (_completion_display_model(candidate), widths.model),
        (_completion_display_source(candidate), widths.source),
        (_completion_display_state(candidate), widths.state),
    )
    last_visible = max(
        (index for index, (field, width) in enumerate(fields) if field or width > 0),
        default=-1,
    )
    parts: list[str] = []
    for field, width in fields[: last_visible + 1]:
        parts.append(_pad_cell_right(field, width) if width else field)
    return "  ".join(parts).rstrip()
