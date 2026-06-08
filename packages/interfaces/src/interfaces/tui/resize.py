"""Resize and terminal protocol behavior for the Heph TUI."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

from ai.providers.catalog import prefetch_provider_model_catalogs
from ai.providers.config import ProviderConfig

from interfaces.tui.ids import (
    COMPLETION_STACK_SELECTOR,
    COMPOSER_FRAME_SELECTOR,
    COMPOSER_SELECTOR,
    FOOTER_HINTS_SELECTOR,
    INFO_PANEL_SELECTOR,
    SUGGESTIONS_SELECTOR,
    TRANSCRIPT_SELECTOR,
)
from interfaces.tui.render_state import DirtyRegion

try:
    from textual import events
    from textual.css.query import NoMatches
    from textual.geometry import Size
    from textual.widget import Widget
    from textual.widgets import Input, OptionList, Static
except ImportError:
    events = None  # ty:ignore[invalid-assignment]
    NoMatches = Exception  # ty:ignore[invalid-assignment]
    Size = None  # ty:ignore[invalid-assignment]
    Widget = object  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession
    from rich.text import Text

    from interfaces.tui.render_state import TuiRenderCache
    from interfaces.tui.session_state import TuiRuntimeState, TuiTranscriptEntry


class _SizeObject(Protocol):
    width: int
    height: int
    region: object


class _ScreenObject(Protocol):
    def refresh(
        self,
        region: object,
        *,
        repaint: bool = False,
        layout: bool = False,
    ) -> object: ...

    def clear_cached_dimensions(self) -> object: ...


class _ResizableWidget(Protocol):
    styles: object

    def clear_cached_dimensions(self) -> object: ...

    def refresh(self, *, repaint: bool = False, layout: bool = False) -> object: ...

    def add_class(self, class_name: str) -> object: ...

    def remove_class(self, class_name: str) -> object: ...


class _ResizeHost(Protocol):
    state: TuiRuntimeState
    session: ChatSession
    _armory_inline_active: bool
    _materials_inline_active: bool
    _materials_highlighted_index: int | None
    _materials_columns: tuple[list[str], list[str]]
    _sidebar_width_visible: bool
    _sidebar_actual_visible: bool | None
    _resize_redraw: _ResizeRedrawState
    _resize_redraw_timer: object
    _render_cache: TuiRenderCache
    _transcript_render_width: int | None
    _focused_msg_index: int | None

    @property
    def size(self) -> _SizeObject: ...

    @property
    def screen(self) -> object: ...

    @property
    def focused(self) -> object | None: ...

    def set_focus(self, widget: Widget | None) -> object: ...

    def refresh(self, *, repaint: bool = False, layout: bool = False) -> object: ...

    def set_timer(self, delay: float, callback: Callable[[], object]) -> object: ...

    def post_message(self, message: events.Resize) -> object: ...

    def _write_transcript_gap(self) -> None: ...

    def _write_transcript_entry(self, entry: TuiTranscriptEntry) -> None: ...

    def _reflow_transcript_entries(self) -> None: ...

    def _append_armory_home(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _refresh_status(self) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _schedule_transcript_reflow(self) -> None: ...

    def _handle_suggestions_mouse_move(self, event: events.MouseMove) -> None: ...

    def _write_terminal_control(self, sequence: str) -> None: ...

    def _focus_composer(self) -> None: ...

    def _set_sidebar_visible(self, visible: bool) -> None: ...

    def _refresh_compact_layout_class(self, *, height: int | None = None) -> None: ...

    def _handle_resize_dimensions(self, width: int, height: int) -> None: ...

    def _invalidate_after_resize(self) -> None: ...

    def _finish_resize_refresh(self) -> None: ...

    def _schedule_resize_refresh(self) -> None: ...

    def _terminal_size_from_tty(self) -> tuple[int, int] | None: ...

    def _clear_terminal_viewport(self) -> None: ...

    def _force_full_screen_repaint(self) -> None: ...

    def _clear_resize_sensitive_widget_caches(self) -> None: ...

    def _restore_focus_after_resize(self) -> None: ...

    def _materials_focus_target_after_resize(self) -> OptionList: ...

    def _core_widgets_available(self) -> bool: ...


def _screen(host: _ResizeHost) -> _ScreenObject:
    return cast("_ScreenObject", host.screen)


def _query_one[WidgetT](
    host: object,
    selector: str,
    expect_type: type[WidgetT] | None = None,
) -> WidgetT:
    query_one = cast("Callable[..., object]", object.__getattribute__(host, "query_one"))
    if expect_type is None:
        return cast("WidgetT", query_one(selector))
    return cast("WidgetT", query_one(selector, expect_type))


_SIDEBAR_MIN_WINDOW_WIDTH = 120
_COMPACT_COMPLETION_STACK_MAX_HEIGHT = 12
_RESIZE_REDRAW_DELAY_SECONDS = 0.075
_TERMINAL_CLEAR_SCREEN = "\x1b[0m\x1b[2J\x1b[H"
_TERMINAL_KEYBOARD_PROTOCOL_MODIFIED_ENTER = "\x1b[>9u"
_TERMINAL_XTERM_MODIFIED_KEYS = "\x1b[>4;1m"
_TERMINAL_KEYBOARD_PROTOCOL_POP = "\x1b[<u"
_TERMINAL_XTERM_MODIFIED_KEYS_RESET = "\x1b[>4;0m"
_RESIZE_SENSITIVE_SELECTORS = (
    "#status",
    TRANSCRIPT_SELECTOR,
    "#transcript-spacer",
    "#thinking-indicator",
    "#armory-inline",
    "#materials-inline",
    COMPOSER_FRAME_SELECTOR,
    "#composer-prompt",
    COMPOSER_SELECTOR,
    COMPLETION_STACK_SELECTOR,
    SUGGESTIONS_SELECTOR,
    "#completion-position",
    FOOTER_HINTS_SELECTOR,
    INFO_PANEL_SELECTOR,
)
_RESIZE_MATERIALS_FOCUS_IDS = ("materials-list", "materials-list-right")
_LIVE_RESIZE_POLL_SECONDS = 1 / 60


@dataclass(slots=True)
class _ResizeRedrawState:
    """Track terminal-size observations separately from completed repair frames."""

    last_size: tuple[int, int] | None = None
    refresh_pending: bool = False
    changed_while_pending: bool = False
    quiet_until: float | None = None
    timer_running: bool = False

    def note_size(self, size: tuple[int, int]) -> bool:
        if self.last_size == size:
            return False
        if self.refresh_pending:
            self.changed_while_pending = True
        self.last_size = size
        return True

    def schedule_trailing_refresh(self, *, now: float, delay: float) -> bool:
        self.quiet_until = now + delay
        self.refresh_pending = True
        if self.timer_running:
            return False
        self.timer_running = True
        return True

    def refresh_delay(self, *, now: float) -> float | None:
        if self.quiet_until is None:
            self.timer_running = False
            self.refresh_pending = False
            return None
        remaining = self.quiet_until - now
        if remaining > 0:
            return remaining
        return 0.0

    def finish_trailing_refresh(self) -> bool:
        changed_while_pending = self.changed_while_pending
        self.quiet_until = None
        self.timer_running = False
        self.refresh_pending = False
        self.changed_while_pending = False
        return changed_while_pending


class TuiResizeMixin:
    def _push_terminal_keyboard_protocol(self: _ResizeHost) -> None:
        self._write_terminal_control(_TERMINAL_KEYBOARD_PROTOCOL_MODIFIED_ENTER)
        self._write_terminal_control(_TERMINAL_XTERM_MODIFIED_KEYS)

    def _pop_terminal_keyboard_protocol(self: _ResizeHost) -> None:
        self._write_terminal_control(_TERMINAL_XTERM_MODIFIED_KEYS_RESET)
        self._write_terminal_control(_TERMINAL_KEYBOARD_PROTOCOL_POP)

    def _write_terminal_control(self: _ResizeHost, sequence: str) -> None:
        driver = getattr(self, "_driver", None)
        write = getattr(driver, "write", None)
        flush = getattr(driver, "flush", None)
        if not callable(write):
            return
        write(sequence)
        if callable(flush):
            flush()

    def _initialize_layout_visibility(self: _ResizeHost) -> None:
        visible = self.size.width >= _SIDEBAR_MIN_WINDOW_WIDTH
        self._sidebar_width_visible = visible
        self._set_sidebar_visible(
            visible and not self._armory_inline_active and not self._materials_inline_active
        )
        self._refresh_compact_layout_class()

    def _replay_transcript(self: _ResizeHost) -> None:
        for index, entry in enumerate(self.state.transcript):
            if index > 0:
                self._write_transcript_gap()
            self._write_transcript_entry(entry)

    def _focus_composer(self: _ResizeHost) -> None:
        composer = _query_one(self, COMPOSER_SELECTOR, Input)
        composer.select_on_focus = False
        composer.focus()
        self.set_focus(composer)

    def _append_initial_cards(self: _ResizeHost) -> None:
        if self.session.armory_path is None and not self.state.armory_home_shown:
            self.state.armory_home_shown = True
            self._append_armory_home()

    def _prefetch_model_catalogs(self: _ResizeHost) -> None:
        try:
            pc = ProviderConfig.load()
        except Exception:
            return
        active = pc.get_active()
        if active is not None:
            prefetch_provider_model_catalogs(pc, provider_slugs={active.slug})

    def on_app_focus(self: _ResizeHost, event: events.AppFocus) -> None:
        if self._armory_inline_active or self._materials_inline_active:
            composer = _query_one(self, COMPOSER_SELECTOR, Input)
            composer.focus()
            self.set_focus(composer)
            event.stop()

    def on_click(self: _ResizeHost, event: events.Click) -> None:
        if isinstance(event.widget, OptionList):
            return
        composer = _query_one(self, COMPOSER_SELECTOR, Input)
        if self.focused is not composer:
            composer.focus()
            self.set_focus(composer)

    def on_mouse_move(self: _ResizeHost, event: events.MouseMove) -> None:
        self._handle_suggestions_mouse_move(event)

    def on_resize(self: _ResizeHost, event: events.Resize) -> None:
        self._handle_resize_dimensions(event.size.width, event.size.height)

    def _handle_resize_dimensions(self: _ResizeHost, width: int, height: int) -> None:
        if not self._core_widgets_available():
            return
        size = (width, height)
        if not self._resize_redraw.note_size(size):
            return
        visible = width >= _SIDEBAR_MIN_WINDOW_WIDTH
        self._sidebar_width_visible = visible
        target = visible and not self._armory_inline_active and not self._materials_inline_active
        self._set_sidebar_visible(target)
        self._refresh_compact_layout_class(height=height)
        self._invalidate_after_resize()

    def _invalidate_after_resize(self: _ResizeHost) -> None:
        self._clear_terminal_viewport()
        self._clear_resize_sensitive_widget_caches()
        self._render_cache.forget(*DirtyRegion)
        self._transcript_render_width = None
        self._refresh_status()
        self._refresh_footer_hints()
        self._update_info_panel()
        self._reflow_transcript_entries()
        self.refresh(repaint=True, layout=True)
        self._schedule_resize_refresh()

    def _finish_resize_refresh(self: _ResizeHost) -> None:
        self._resize_redraw_timer = None
        refresh_delay = self._resize_redraw.refresh_delay(now=time.monotonic())
        if refresh_delay is None:
            return
        if refresh_delay > 0:
            self._resize_redraw_timer = self.set_timer(
                refresh_delay,
                self._finish_resize_refresh,
            )
            return
        self._resize_redraw.finish_trailing_refresh()
        if not self._core_widgets_available():
            return
        self._clear_resize_sensitive_widget_caches()
        self._render_cache.forget(*DirtyRegion)
        self._transcript_render_width = None
        self._refresh_status()
        self._refresh_footer_hints()
        self._update_info_panel()
        self._reflow_transcript_entries()
        self._restore_focus_after_resize()
        self.refresh(repaint=True, layout=True)

    def _schedule_resize_refresh(self: _ResizeHost) -> None:
        should_start_timer = self._resize_redraw.schedule_trailing_refresh(
            now=time.monotonic(),
            delay=_RESIZE_REDRAW_DELAY_SECONDS,
        )
        if should_start_timer:
            self._resize_redraw_timer = self.set_timer(
                _RESIZE_REDRAW_DELAY_SECONDS,
                self._finish_resize_refresh,
            )

    def _install_tty_resize_reader(self: _ResizeHost) -> None:
        driver = getattr(self, "_driver", None)
        fallback = getattr(driver, "_get_terminal_size", None)
        if driver is None or not callable(fallback):
            return

        def get_terminal_size() -> tuple[int, int]:
            terminal_size = self._terminal_size_from_tty()
            if terminal_size is not None:
                return terminal_size
            return cast("Callable[[], tuple[int, int]]", fallback)()

        driver._get_terminal_size = get_terminal_size

    def _sync_terminal_size_from_tty(self: _ResizeHost) -> None:
        terminal_size = self._terminal_size_from_tty()
        if terminal_size is None or terminal_size == (self.size.width, self.size.height):
            return

        driver = getattr(self, "_driver", None)
        if driver is not None:
            with suppress(AttributeError):
                driver._size = terminal_size
        if Size is None:
            return
        width, height = terminal_size
        resize_event = events.Resize(Size(width, height), Size(width, height))
        self.post_message(resize_event)

    def _terminal_size_from_tty(self: _ResizeHost) -> tuple[int, int] | None:
        driver = getattr(self, "_driver", None)
        fileno = getattr(driver, "fileno", None)
        if not isinstance(fileno, int):
            return None
        try:
            size = os.get_terminal_size(fileno)
        except OSError:
            return None
        if size.columns <= 0 or size.lines <= 0:
            return None
        return size.columns, size.lines

    def _clear_terminal_viewport(self: _ResizeHost) -> None:
        driver = getattr(self, "_driver", None)
        write = getattr(driver, "write", None)
        flush = getattr(driver, "flush", None)
        if not callable(write):
            return
        write(_TERMINAL_CLEAR_SCREEN)
        if callable(flush):
            flush()
        self._force_full_screen_repaint()

    def _force_full_screen_repaint(self: _ResizeHost) -> None:
        _screen(self).refresh(self.size.region, repaint=True, layout=True)

    def _clear_resize_sensitive_widget_caches(self: _ResizeHost) -> None:
        _screen(self).clear_cached_dimensions()
        self._force_full_screen_repaint()
        for selector in _RESIZE_SENSITIVE_SELECTORS:
            try:
                widget = cast("_ResizableWidget", _query_one(self, selector))
            except NoMatches:
                continue
            widget.clear_cached_dimensions()
            widget.refresh(repaint=True, layout=True)

    def _restore_focus_after_resize(self: _ResizeHost) -> None:
        if self._materials_inline_active:
            focused_id = getattr(self.focused, "id", None)
            if focused_id in _RESIZE_MATERIALS_FOCUS_IDS:
                return
            target = self._materials_focus_target_after_resize()
            target.focus()
            self.set_focus(target)
            return
        self._focus_composer()

    def _materials_focus_target_after_resize(self: _ResizeHost) -> OptionList:
        highlighted = self._materials_highlighted_index
        if highlighted is not None and highlighted >= len(self._materials_columns[0]):
            return _query_one(self, "#materials-list-right", OptionList)
        return _query_one(self, "#materials-list", OptionList)

    def _core_widgets_available(self: _ResizeHost) -> bool:
        try:
            _query_one(self, COMPOSER_FRAME_SELECTOR, Widget)
            _query_one(self, COMPOSER_SELECTOR, Input)
            _query_one(self, COMPLETION_STACK_SELECTOR, Widget)
            _query_one(self, SUGGESTIONS_SELECTOR, OptionList)
            _query_one(self, FOOTER_HINTS_SELECTOR, Static)
            _query_one(self, INFO_PANEL_SELECTOR, Static)
        except NoMatches:
            return False
        return True

    def _set_sidebar_visible(self: _ResizeHost, visible: bool) -> None:
        if self._sidebar_actual_visible is visible:
            return
        self._sidebar_actual_visible = visible
        display = "block" if visible else "none"
        info_panel = _query_one(self, INFO_PANEL_SELECTOR, Static)
        info_panel.styles.display = display
        self._transcript_render_width = None
        self._schedule_transcript_reflow()

    def _update_static_region(
        self: _ResizeHost,
        selector: str,
        widget_type: type[Static],
        region: DirtyRegion,
        renderable: object,
    ) -> None:
        plain = getattr(renderable, "plain", None)
        snapshot = plain if isinstance(plain, str) else str(renderable)
        if self._render_cache.should_update(region, snapshot):
            content = renderable if isinstance(renderable, str) else cast("Text", renderable)
            try:
                _query_one(self, selector, widget_type).update(content)
            except NoMatches:
                self._render_cache.forget(region)

    def _refresh_compact_layout_class(
        self: _ResizeHost,
        *,
        height: int | None = None,
    ) -> None:
        stack = cast("_ResizableWidget", _query_one(self, COMPLETION_STACK_SELECTOR))
        frame = cast("_ResizableWidget", _query_one(self, COMPOSER_FRAME_SELECTOR))
        layout_height = self.size.height if height is None else height
        if layout_height <= _COMPACT_COMPLETION_STACK_MAX_HEIGHT:
            stack.add_class("compact")
            frame.add_class("compact")
        else:
            stack.remove_class("compact")
            frame.remove_class("compact")
