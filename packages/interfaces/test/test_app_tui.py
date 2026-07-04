"""Tests for the Textual app."""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import heph.commands as heph_commands
import interfaces.tui.display_text as tui_display_text
import pytest
from ai.providers.config import ProviderConfig, default_config
from ai.providers.llama_cpp import LlamaCppCandidate
from ai.providers.registry import ModelInfo, get_registry
from ai.runtime import ChatConfig, Conversation, EngineError, EngineErrorCode
from harness._types import is_string_mapping
from harness.armory.search import ArmoryEntry, SearchResult, remember_armory
from harness.armory.storage import initialize
from harness.chat import storage as chat_storage
from harness.chat.events import (
    AssistantDeltaEvent,
    NoticeEvent,
    ReasoningDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from harness.chat.session import ChatSession, record_turn_snapshot, save_session
from harness.chat.usage import TokenUsage
from harness.parameters import settings as settings_store
from harness.rag.chunker import Chunk
from harness.rag.context import EvidenceChunk, TurnEvidence
from interfaces import tui
from interfaces.palette import DARK_THEME, LIGHT_THEME
from interfaces.terminal import current_theme_name, set_theme
from interfaces.tui import armory as tui_armory
from interfaces.tui import keybinds, keymap
from interfaces.tui import streaming as tui_streaming
from interfaces.tui import transcript as tui_transcript
from interfaces.tui import widgets as tui_widgets
from interfaces.tui.armory_browser import armory_detail, build_entries, default_armory_home
from interfaces.tui.cell_text import cell_width
from interfaces.tui.inline_menu import (
    _dedupe_inline_options,
    _inline_menu_option_text,
    _local_model_fixed_metadata_text,
    _local_model_option_text,
    _LocalModelMetadataWidths,
    local_model_option_description,
)
from interfaces.tui.keyboard_protocol import install_textual_modified_key_compat
from interfaces.tui.local_flows import _local_flow_options
from interfaces.tui.model_flow import (
    _duplicate_model_names,
    _model_choice_from_label,
    _model_choice_label,
)
from interfaces.tui.option_list_layout import visible_option_height
from interfaces.tui.search_screen import _format_result as _format_search_result
from interfaces.tui.transparent import Region as _Region
from interfaces.tui.transparent import style_without_black_background
from rich.segment import Segment
from rich.text import Text
from textual import events
from textual._xterm_parser import XTermParser
from textual.strip import Strip

tui.set_command_registry_fn(heph_commands.get_registry)

if TYPE_CHECKING:
    from textual.app import App as TextualApp
    from textual.screen import Screen
    from textual.widget import Widget
    from textual.widgets import OptionList as TextualOptionList


class _SelectionWidgetType(Protocol):
    ALLOW_SELECT: bool


def _allow_select(widget_cls: type) -> bool:
    return cast("_SelectionWidgetType", widget_cls).ALLOW_SELECT


class _SelectableClass(Protocol):
    ALLOW_SELECT: bool


class _TerminalSizeReader(Protocol):
    def _get_terminal_size(self) -> tuple[int, int]: ...


class _InputKeyHandler(Protocol):
    value: str

    def on_key(self, event: events.Key) -> None: ...


def _allow_select(widget_class: type) -> bool:
    return cast("_SelectableClass", widget_class).ALLOW_SELECT


def _composited_screen_text(app: tui.HephTui) -> str:
    compositor = app.screen._compositor
    region = compositor.size.region
    rows = [[" "] * region.width for _ in range(region.height)]
    chops = compositor._render_chops(region, lambda _line_y: True)
    for row_index, chops_line in enumerate(chops):
        for start_column, strip in chops_line.items():
            if strip is None:
                continue
            column = start_column
            for segment in strip:
                for char in segment.text:
                    if 0 <= row_index < region.height and 0 <= column < region.width:
                        rows[row_index][column] = char
                    column += 1
    return "\n".join("".join(row).rstrip() for row in rows)


def _strip_plain_text(strip: Strip) -> str:
    return "".join(segment.text for segment in strip)


def _option_prompt_plain(option_list: object, index: int) -> str:
    typed_list = cast("TextualOptionList", option_list)
    return str(typed_list.get_option_at_index(index).prompt)


def _screen_line_with(app: tui.HephTui, text: str) -> str:
    return next(line for line in _composited_screen_text(app).splitlines() if text in line)


def _completion_description_columns(app: tui.HephTui) -> list[int]:
    suggestions = app.query_one("#suggestions", tui.OptionList)
    columns: list[int] = []
    for index, candidate in enumerate(app.completion_candidates):
        if not candidate.description:
            continue
        prompt = _option_prompt_plain(suggestions, index)
        columns.append(prompt.index(candidate.description))
    return columns


def _inline_description_columns(app: tui.HephTui) -> list[int]:
    suggestions = app.query_one("#suggestions", tui.OptionList)
    columns: list[int] = []
    for index, (_label, description) in enumerate(app._inline_flow.options):
        if not description:
            continue
        prompt = _option_prompt_plain(suggestions, index)
        columns.append(prompt.index(description))
    return columns


def _armory_description_columns(app: tui.HephTui) -> list[int]:
    armories = app.query_one("#armory-current-inline", tui.OptionList)
    columns: list[int] = []
    for index, entry in enumerate(app._armory_entries):
        active = (
            entry.path is not None
            and app._turn_key_for_armory_path(entry.path) in app._active_turn_sessions
        )
        description = tui_armory._armory_entry_description(entry, active=active)
        if not description:
            continue
        prompt = _option_prompt_plain(armories, index)
        columns.append(prompt.index(description))
    return columns


def _footer_armory_hint() -> str:
    return f"ARMORY {keymap.armory_shortcut_key()}"


def _default_binding(action_id: str) -> str:
    keys = keymap.default_runtime_keymap().keys_for_action(action_id)
    assert keys
    return keys[0]


def _default_display_key(action_id: str) -> str:
    return keymap.default_runtime_keymap().primary_key(action_id)


def _plain_session() -> ChatSession:
    conversation = Conversation()
    conversation.add("system", "test")
    return ChatSession(
        config=ChatConfig(base_url="https://example.test", model="test-model"),
        conversation=conversation,
        session_id="session-test",
    )


def _turn_evidence_with_sources(
    *sources: str,
    total_source_count: int | None = None,
) -> TurnEvidence:
    return TurnEvidence(
        tuple(
            EvidenceChunk(
                evidence_id=f"E{index + 1}",
                chunk=Chunk(
                    text="evidence",
                    source=source,
                    index=index,
                    char_start=0,
                    char_end=8,
                ),
                score=0.8,
                content="evidence",
            )
            for index, source in enumerate(sources)
        ),
        sampled_source_count=len(sources),
        total_source_count=total_source_count or len(sources),
    )


def _text_style_for_fragment(text: Text, fragment: str, *, occurrence: int = 0) -> str:
    search_from = 0
    start = -1
    for _ in range(occurrence + 1):
        start = text.plain.index(fragment, search_from)
        search_from = start + len(fragment)
    end = start + len(fragment)
    styles = [str(span.style) for span in text.spans if span.start <= start and span.end >= end]
    if styles:
        return styles[0]
    return str(text.style)


def _mark_active_turn(
    app: tui.HephTui,
    session: ChatSession | None = None,
) -> threading.Event:
    active_session = session or app.session
    event = threading.Event()
    turn_key = app._turn_key_for_session(active_session)
    app._next_turn_token += 1
    app._active_turns[turn_key] = event
    app._active_turn_sessions[turn_key] = active_session
    app._active_turn_tokens[turn_key] = app._next_turn_token
    app._sync_busy_to_current_session()
    return event


def _configured_status_session() -> ChatSession:
    conversation = Conversation()
    conversation.add("system", "test")
    return ChatSession(
        config=ChatConfig(
            base_url="https://example.test",
            model="glm-5v-turbo",
            api_key="test-key",
        ),
        conversation=conversation,
        session_id="session-test",
    )


def _keyless_session() -> ChatSession:
    conversation = Conversation()
    conversation.add("system", "test")
    return ChatSession(
        config=ChatConfig(
            base_url="https://text.pollinations.ai/openai",
            model="openai",
        ),
        conversation=conversation,
        session_id="session-test",
    )


def _clear_credential_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "HARNESS_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ZAI_API_KEY",
        "CUSTOM_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


def test_session_status_for_plain_session() -> None:
    status = tui._status_lines(_plain_session())

    assert status == "Heph  ARMORY none  MODEL test-model  REASONING low"
    assert "Heph" in status
    assert "test-model" in status
    assert "ARMORY" in status
    assert " mode " not in status
    assert "api" not in status
    assert "materials" not in status
    assert "enter" not in status
    assert "/help" not in status


def test_session_status_normalizes_labels_without_lowercasing_values() -> None:
    session = _plain_session()
    session.config.model = "Test-MODEL"

    status = tui._status_lines(session)

    assert "MODEL Test-MODEL" in status
    assert "REASONING low" in status


def test_session_status_keeps_full_model_name_when_width_is_tight() -> None:
    session = _plain_session()
    session.config.model = "gpt-5.5"

    status = tui._status_lines(session, width=40)

    assert "ARMORY none" in status
    assert "MODEL gpt-5.5" in status
    assert ".g." not in status


def test_session_status_supports_menu_title_replacement() -> None:
    status = tui._status_lines(_plain_session(), title="Materials")

    assert status.startswith("Materials  ARMORY none")
    assert not status.startswith("Heph")


def test_status_render_width_does_not_constrain_auto_width_status() -> None:
    assert tui_display_text.status_render_width(80) is None
    assert tui_display_text.status_render_width(0) is None


def test_session_status_omits_api_badge_for_keyless_provider() -> None:
    status = tui._status_lines(_keyless_session())

    assert "api" not in status
    assert "free" not in status
    assert "configured" not in status
    assert "missing" not in status


def test_session_status_shows_live_tokens_when_enabled() -> None:
    session = _plain_session()
    session.live_tokens_visible = True
    session.usage.record(
        TokenUsage(prompt_tokens=1_500, completion_tokens=250, total_tokens=1_750),
        session.config.model,
    )

    status = tui._status_lines(session)

    assert "TOKENS ↑1.5k ↓250" in status
    assert "prompt/" not in status
    assert "left" not in status


def test_session_status_shows_zero_live_tokens_before_usage() -> None:
    session = _plain_session()
    session.live_tokens_visible = True

    status = tui._status_lines(session)

    assert "TOKENS 0" in status


def test_session_status_shows_live_cost_when_enabled() -> None:
    session = _plain_session()
    session.live_cost_visible = True
    session.usage.estimate_from_chars(400, 80, session.config.model)

    status = tui._status_lines(session)

    assert "COST $0.000" in status


def test_session_status_marks_subscription_cost_estimate() -> None:
    session = _plain_session()
    session.config.apply_provider_reference("openai-codex", "OPENAI_CODEX_OAUTH_TOKEN")
    session.live_cost_visible = True

    status = tui._status_lines(session)

    assert "COST $0.000 (sub)" in status


def test_shift_tab_opens_reasoning_level_control(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setattr(
        "interfaces.tui.composer_controls.prefetch_provider_model_catalogs",
        lambda _config, **_kwargs: None,
    )
    session = _plain_session()
    session.config.model = "reasoning-model"
    get_registry().register(
        ModelInfo(
            "reasoning-model",
            "custom",
            "Reasoning Model",
            128_000,
            8_192,
            0.0,
            0.0,
            tags=("reasoning",),
            reasoning_efforts=("low", "medium", "high", "xhigh"),
        )
    )
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_reasoning_cycle() -> None:
        async with typed_app.run_test(size=(100, 20)) as pilot:
            await pilot.press("shift+tab")
            await pilot.pause()
            assert session.config.reasoning_level == "medium"
            assert " mode " not in tui._status_lines(session)
            assert "REASONING medium" in tui._status_lines(session)
            assert [entry.content for entry in app.state.transcript] == ["Reasoning medium."]

    asyncio.run(check_reasoning_cycle())


def test_shift_tab_replaces_reasoning_notice(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setattr(
        "interfaces.tui.composer_controls.prefetch_provider_model_catalogs",
        lambda _config, **_kwargs: None,
    )
    session = _plain_session()
    session.config.model = "reasoning-model-2"
    get_registry().register(
        ModelInfo(
            "reasoning-model-2",
            "custom",
            "Reasoning Model 2",
            128_000,
            8_192,
            0.0,
            0.0,
            tags=("reasoning",),
            reasoning_efforts=("low", "medium", "high"),
        )
    )
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_reasoning_notice_replacement() -> None:
        async with typed_app.run_test(size=(100, 20)) as pilot:
            await pilot.press("shift+tab")
            await pilot.press("shift+tab")
            await pilot.pause()
            assert session.config.reasoning_level == "high"
            assert [entry.content for entry in app.state.transcript] == ["Reasoning high."]

    asyncio.run(check_reasoning_notice_replacement())


def test_render_cache_skips_unchanged_region_updates() -> None:
    cache = tui.TuiRenderCache()

    assert cache.should_update(tui.DirtyRegion.STATUS, "ready")
    assert not cache.should_update(tui.DirtyRegion.STATUS, "ready")

    cache.mark(tui.DirtyRegion.STATUS)

    assert cache.should_update(tui.DirtyRegion.STATUS, "ready")
    assert not cache.should_update(tui.DirtyRegion.STATUS, "ready")


def test_resize_redraw_state_tracks_follow_up_frame_after_resize_spam() -> None:
    state = tui._ResizeRedrawState()

    assert state.note_size((120, 24))
    assert state.schedule_trailing_refresh(now=10.0, delay=0.075)
    assert state.refresh_pending
    assert not state.note_size((120, 24))
    assert state.note_size((80, 10))
    assert not state.schedule_trailing_refresh(now=10.03, delay=0.075)
    assert state.refresh_delay(now=10.05) == pytest.approx(0.055)
    assert state.refresh_delay(now=10.105) == 0.0
    assert state.finish_trailing_refresh()

    assert state.schedule_trailing_refresh(now=20.0, delay=0.075)
    assert state.refresh_pending
    assert not state.finish_trailing_refresh()


def test_footer_hints_show_idle_shortcuts(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch

    hints = tui._footer_hints_text(_plain_session())
    plain = hints.plain
    armory_key = _default_display_key("open_armory_home")
    materials_key = _default_display_key("open_materials")
    commands_key = _default_display_key("command_palette")

    assert armory_key in plain
    assert f"ARMORY {armory_key}" in plain
    assert f"MATERIALS {materials_key}" in plain
    assert f"COMMANDS {commands_key}" in plain
    assert "REASONING shift+tab" in plain
    assert plain.startswith(
        f"ARMORY {armory_key}  MATERIALS {materials_key}  "
        f"COMMANDS {commands_key}  REASONING shift+tab"
    )
    assert "enter" not in plain
    assert "tab complete" not in plain
    assert "ctrl+c" not in plain
    assert "ctrl+d" not in plain
    assert "test-model" not in plain


def test_footer_hints_derive_labels_and_keys_from_keybind_specs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del monkeypatch

    specs_by_action = {spec.action: spec for spec in keybinds.tui_keybinds()}
    hints = keybinds.footer_keybind_hints()
    armory_key = _default_display_key("open_armory_home")
    materials_key = _default_display_key("open_materials")
    commands_key = _default_display_key("command_palette")

    assert specs_by_action["open_armory_home"].keys == _default_binding("open_armory_home")
    assert specs_by_action["open_materials"].keys == _default_binding("open_materials")
    assert specs_by_action["command_palette"].keys == _default_binding("command_palette")
    assert specs_by_action["cycle_reasoning_level"].keys == "shift+tab"
    assert [(hint.label, hint.key) for hint in hints] == [
        ("ARMORY", armory_key),
        ("MATERIALS", materials_key),
        ("COMMANDS", commands_key),
        ("REASONING", "shift+tab"),
    ]


def test_footer_hints_show_escape_cancel_and_ctrl_c_exit_when_busy() -> None:
    hints = tui._footer_hints_text(_plain_session(), busy=True)
    plain = hints.plain

    assert "STOP esc" in plain
    assert "EXIT ctrl+c" in plain
    assert "esc stop" not in plain
    assert "ctrl+c exit" not in plain
    assert "cancel" not in plain
    assert "enter" not in plain
    assert "/help" not in plain


def test_ctrl_c_binding_exits_tui() -> None:
    binding_actions = {binding.key: binding.action for binding in tui.HephTui.BINDINGS}

    assert binding_actions["ctrl+c"] == "quit"


def test_keymap_text_lists_materials_shortcut() -> None:
    text = keybinds.keymap_text()

    assert text.startswith("KEYMAP shortcuts")
    assert _default_display_key("open_armory_home") in text
    assert _default_display_key("open_materials") in text
    assert "MATERIALS" in text
    assert "STATE default" in text
    assert " alt+m" not in text
    assert "f4" not in text
    assert "ctrl+t" not in text


@pytest.mark.parametrize(
    ("raw_key", "normalized"),
    [
        (" Control - Shift - F8 ", "ctrl+shift+f8"),
        ("option + page-down", "alt+pagedown"),
        ("esc", "escape"),
        ("spacebar", "space"),
    ],
)
def test_keymap_normalizes_aliases_and_modifier_order(
    raw_key: str,
    normalized: str,
) -> None:
    assert keymap.normalize_key_spec(raw_key) == normalized


def test_keymap_defaults_avoid_function_keys() -> None:
    runtime = keymap.default_runtime_keymap()

    assert runtime.keys_for_action("command_palette") == ("ctrl+p",)
    assert runtime.keys_for_action("open_armory_home") == ("ctrl+a",)
    assert runtime.keys_for_action("open_materials") == ("ctrl+o",)
    assert runtime.keys_for_action("open_search") == ("ctrl+r",)
    assert runtime.keys_for_action("evidence") == ("ctrl+g",)
    assert not any(
        key.startswith("f") and key[1:].isdigit()
        for action in keymap.TUI_KEYMAP_ACTIONS
        for key in runtime.keys_for_action(action.id)
    )


@pytest.mark.parametrize("raw_key", ["f3", "ctrl+f5", "shift+f8"])
def test_keymap_rejects_function_key_bindings(raw_key: str) -> None:
    result = keymap.save_keymap_binding("open_materials", raw_key)

    assert result.saved is False
    assert "function keys can trigger hardware" in result.message


@pytest.mark.parametrize(
    ("raw_key", "message"),
    [
        ("", "keybinding cannot be empty"),
        ("ctrl-control-a", "duplicate modifier"),
        ("ctrl+", "missing key"),
        ("ctrl+a+b", "invalid keybinding"),
        ("ctrl+moon", "unknown key"),
    ],
)
def test_keymap_normalization_rejects_invalid_specs(raw_key: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        keymap.normalize_key_spec(raw_key)


def test_keymap_rejects_terminal_reserved_ctrl_m() -> None:
    result = keymap.save_keymap_binding("open_materials", "ctrl+m")

    assert result.saved is False
    assert "terminals as Enter" in result.message


@pytest.mark.parametrize(
    ("raw_key", "expected_message"),
    [
        ("ctrl+c", "reserved for quitting"),
        ("ctrl+d", "reserved for quitting"),
    ],
)
def test_keymap_rejects_quit_shortcuts(raw_key: str, expected_message: str) -> None:
    result = keymap.save_keymap_binding("open_materials", raw_key)

    assert result.saved is False
    assert expected_message in result.message


def test_keymap_ignores_reserved_manual_config_binding() -> None:
    settings_store.save_raw_settings(
        {
            "tui_keymap": {
                "app": {
                    "open_materials": "alt+m",
                    "open_search": "f3",
                },
            },
        }
    )

    runtime = keymap.load_runtime_keymap()

    assert runtime.keys_for_action("open_materials") == (_default_binding("open_materials"),)
    assert runtime.keys_for_action("open_search") == (_default_binding("open_search"),)
    assert any("alt+m is reserved by macOS" in error for error in runtime.errors)
    assert any(
        "open_search: function keys can trigger hardware" in error for error in runtime.errors
    )


def test_keymap_loads_valid_bindings_from_mixed_manual_config() -> None:
    settings_store.save_raw_settings(
        {
            "tui_keymap": {
                "app": {
                    "open_materials": ["ctrl+y", "ctrl+y", "ctrl+c", 7],
                    "open_search": [],
                    "missing": "ctrl+x",
                },
                "composer": "bad",
                "unknown": {},
            },
        }
    )

    runtime = keymap.load_runtime_keymap()

    assert runtime.keys_for_action("open_materials") == ("ctrl+y",)
    assert runtime.keys_for_action("open_search") == ()
    assert any("Unknown keymap action: app.missing" in error for error in runtime.errors)
    assert any("open_materials: ctrl+c is reserved" in error for error in runtime.errors)
    assert any(
        "open_materials: binding list values must be strings" in error for error in runtime.errors
    )
    assert any("Keymap context composer must be an object." in error for error in runtime.errors)
    assert any("Unknown keymap context: unknown" in error for error in runtime.errors)


def test_footer_hints_show_api_missing_when_unconfigured() -> None:
    session = _plain_session()
    session.config.api_key = None  # ty:ignore[invalid-assignment]
    hints = tui._footer_hints_text(session)
    plain = hints.plain

    assert "api missing" in plain


def test_footer_action_labels_share_neutral_label_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del monkeypatch

    hints = tui._footer_hints_text(_plain_session())
    palette = tui.current_palette()
    footer_label_style = palette.text_muted
    shortcut_style = palette.text_secondary
    labels = ("ARMORY", "MATERIALS", "COMMANDS", "REASONING")
    label_styles: dict[str, list[str]] = {}
    for label in labels:
        start = hints.plain.index(label)
        end = start + len(label)
        label_styles[label] = [
            str(span.style) for span in hints.spans if span.start <= start and span.end >= end
        ]

    assert str(hints.style) == footer_label_style
    for styles in label_styles.values():
        assert styles == [shortcut_style]
        assert not any(palette.action_primary_bg in style for style in styles)
        assert not any(palette.text_primary in style for style in styles)
        assert not any("bold" in style.lower() for style in styles)


def test_status_sidebar_and_footer_chrome_labels_share_one_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del monkeypatch
    session = _plain_session()
    session.source_files = ("materials/calculus.md",)
    palette = tui.current_palette()

    labelled_texts = (
        (tui._status_text(session), ("ARMORY", "MODEL")),
        (tui._info_panel_default_text(session), ("SCOPE", "EVIDENCE")),
        (
            tui._footer_hints_text(session),
            ("ARMORY", "MATERIALS", "COMMANDS", "REASONING"),
        ),
    )

    for text, labels in labelled_texts:
        for label in labels:
            start = text.plain.index(label)
            end = start + len(label)
            styles = [
                str(span.style) for span in text.spans if span.start <= start and span.end >= end
            ]
            assert styles == [palette.text_secondary]


def test_secondary_chrome_details_share_darker_tint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del monkeypatch
    session = _plain_session()
    session.armory_path = Path.home() / ".armories" / "sample-course"
    session.source_files = tuple(f"materials/source-{index}.md" for index in range(9))
    palette = tui.current_palette()

    def effective_style(text: Text, label: str) -> str:
        start = text.plain.index(label)
        end = start + len(label)
        styles = [
            str(span.style) for span in text.spans if span.start <= start and span.end >= end
        ]
        if styles:
            return styles[0]
        return str(text.style)

    footer = tui._footer_hints_text(session)
    for keybind in (
        _default_display_key("open_armory_home"),
        _default_display_key("open_materials"),
        _default_display_key("command_palette"),
        "shift+tab",
    ):
        assert effective_style(footer, keybind) == palette.text_muted

    status = tui._status_text(session)
    armory_value = status.plain.split("ARMORY ", maxsplit=1)[1].split("  MODEL ", maxsplit=1)[0]
    assert effective_style(status, armory_value) == palette.text_muted
    assert effective_style(status, session.config.model) == palette.text_muted

    panel = tui._info_panel_default_text(session)
    assert effective_style(panel, "+1") == palette.text_muted

    assert palette.text_muted != palette.text_secondary


def test_info_panel_material_paths_are_truncated_to_one_line() -> None:
    session = _plain_session()
    session.source_files = (
        "materials/public-academic/mit-missing-semester/2020/command-line/index.html",
        "materials/short.md",
    )

    panel = tui._info_panel_default_text(session)
    material_lines = [line for line in panel.plain.splitlines() if line.strip().startswith("@")]

    assert len(material_lines) == 2
    assert material_lines[0].endswith("...")
    assert len(material_lines[0]) <= 38
    assert "command-line/index.html" not in material_lines[0]
    assert material_lines[1].strip() == "@short.md"


def test_dark_routine_labels_use_neutral_emphasis() -> None:
    set_theme("dark")
    try:
        session = _plain_session()
        status = tui._status_text(session)
        hints = tui._footer_hints_text(session)
        panel = tui._info_panel_default_text(session)
        palette = tui.current_palette()

        assert palette.text_primary != palette.action_primary_bg

        brand_start = status.plain.index("Heph")
        brand_styles = [
            str(span.style)
            for span in status.spans
            if span.start <= brand_start and span.end >= brand_start + len("Heph")
        ]
        reasoning_start = status.plain.index("REASONING")
        reasoning_styles = [
            str(span.style)
            for span in status.spans
            if span.start <= reasoning_start and span.end >= reasoning_start + len("REASONING")
        ]
        footer_label_start = hints.plain.index("COMMANDS")
        footer_label_styles = [
            str(span.style)
            for span in hints.spans
            if (
                span.start <= footer_label_start
                and span.end >= footer_label_start + len("COMMANDS")
            )
        ]
        scope_start = panel.plain.index("SCOPE")
        scope_styles = [
            str(span.style)
            for span in panel.spans
            if span.start <= scope_start and span.end >= scope_start + len("SCOPE")
        ]

        assert reasoning_styles == [palette.text_secondary]
        assert not any(palette.action_primary_bg in style for style in reasoning_styles)
        for styles in (scope_styles,):
            assert styles == [palette.text_secondary]
            assert not any(palette.action_primary_bg in style for style in styles)
        assert brand_styles == [f"bold {palette.brand_primary}"]
        assert str(hints.style) == palette.text_muted
        assert footer_label_styles == [palette.text_secondary]
        assert not any(palette.text_primary in style for style in footer_label_styles)
        assert not any(palette.action_primary_bg in style for style in footer_label_styles)
    finally:
        set_theme("dark")


def test_tui_config_error_allows_pollinations_without_api_key() -> None:
    assert tui._config_error(_keyless_session()) is None


def test_tui_config_error_allows_openai_codex_oauth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = ChatSession(
        config=ChatConfig(
            base_url="https://api.openai.com/v1",
            model="gpt-5.5",
            _provider_slug="openai-codex",
        ),
        conversation=Conversation(),
        session_id="session-test",
    )
    monkeypatch.setattr(
        "ai.runtime.engine.load_credentials",
        lambda _provider, **_kwargs: object(),
    )

    assert "api configured" not in tui._status_lines(session)
    assert tui._config_error(session) is None


def test_tui_config_error_names_missing_openai_codex_oauth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = ChatSession(
        config=ChatConfig(
            base_url="https://api.openai.com/v1",
            model="gpt-5.5",
            _provider_slug="openai-codex",
        ),
        conversation=Conversation(),
        session_id="session-test",
    )
    monkeypatch.setattr(
        "ai.runtime.engine.load_credentials",
        lambda _provider, **_kwargs: None,
    )

    assert tui._config_error(session) == (
        "OpenAI Codex subscription requires /login OAuth credentials. "
        "Use the OpenAI API provider for OPENAI_API_KEY billing."
    )


def test_tui_css_keeps_surface_transparent() -> None:
    css = tui._tui_css()

    assert "App {\n    background: transparent;" in css
    assert "Screen {\n    layout: vertical;\n    background: transparent;" in css
    assert "#status {\n    height: 1;\n    max-height: 1;\n    width: auto;" in css
    assert ("#footer-hints {\n    height: 1;\n    width: auto;\n    max-width: 100%;") in css
    assert "#completion-stack {\n    height: 9;\n    min-height: 1;" in css
    assert "#transcript-spacer {\n    height: 1;" in css
    assert "#transcript:focus" in css
    assert "background-tint: transparent;" in css
    suggestions_start = css.index("#suggestions {")
    suggestions_end = css.index("}", suggestions_start)
    suggestions_block = css[suggestions_start:suggestions_end]
    armory_start = css.index("#armory-current-inline {")
    armory_end = css.index("}", armory_start)
    armory_block = css[armory_start:armory_end]

    option_start = css.index("OptionList > .option-list--option {")
    option_end = css.index("}", option_start)
    option_block = css[option_start:option_end]
    transcript_start = css.index("#transcript {")
    transcript_end = css.index("}", transcript_start)
    transcript_block = css[transcript_start:transcript_end]
    composer_start = css.index("#composer {")
    composer_end = css.index("}", composer_start)
    composer_block = css[composer_start:composer_end]
    composer_frame_start = css.index("#composer-frame {")
    composer_frame_end = css.index("}", composer_frame_start)
    composer_frame_block = css[composer_frame_start:composer_frame_end]
    prompt_start = css.index("#composer-prompt {")
    prompt_end = css.index("}", prompt_start)
    prompt_block = css[prompt_start:prompt_end]
    assert "background: transparent;" in transcript_block
    assert f"background: {tui.current_palette().bg_raised};" in composer_frame_block
    assert f"background: {tui.current_palette().bg_raised};" in prompt_block
    assert f"background: {tui.current_palette().bg_raised};" in composer_block
    assert "scrollbar-size: 0 0;" in suggestions_block
    assert "scrollbar-size-vertical" not in suggestions_block
    assert "padding: 0 0;" in armory_block
    assert "padding: 0 2;" in option_block
    assert "border-bottom: tall" not in css
    assert "App {\n    background: #FFFFFF;" not in css
    assert "Screen {\n    layout: vertical;\n    background: #FFFFFF;" not in css
    assert "#suggestions:focus > .option-list--option-highlighted" in css


def test_inline_options_remove_exact_repetitions() -> None:
    assert _dedupe_inline_options(
        [
            ("model-a", "via OpenRouter"),
            ("model-a", "via OpenRouter"),
            ("model-a", "via Z.AI"),
        ]
    ) == [
        ("model-a", "via OpenRouter"),
        ("model-a", "via Z.AI"),
    ]


def test_duplicate_model_choices_keep_provider_identity() -> None:
    choices = [
        ("openai", "gpt-5.5", "OpenAI API", False),
        ("openai-codex", "gpt-5.5", "OpenAI Codex", False),
    ]

    duplicates = _duplicate_model_names(choices)
    label = _model_choice_label("gpt-5.5", "OpenAI Codex", duplicate=True)
    selected = _model_choice_from_label(label, choices)

    assert duplicates == {"gpt-5.5"}
    assert label == "gpt-5.5 [OpenAI Codex]"
    assert selected == ("openai-codex", "gpt-5.5", "OpenAI Codex", False)


def test_light_theme_paints_bright_app_background() -> None:
    try:
        set_theme("light")
        palette = tui.current_palette()
        css = tui._tui_css()

        assert palette.bg_app != "transparent"
        assert f"App {{\n    background: {palette.bg_app};" in css
        assert f"Screen {{\n    layout: vertical;\n    background: {palette.bg_app};" in css
        assert "#main-layout {\n    layer: base;\n    layout: horizontal;" in css
        assert f"background: {palette.bg_app};" in css
        assert f"color: {palette.text_primary};" in css
    finally:
        set_theme("dark")


def test_resize_invalidates_transient_surfaces_without_duplicate_composer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_resize_sequence() -> None:
        async with typed_app.run_test(size=(130, 24)) as pilot:
            app._append_user("A long transcript line " * 12, mark_working=False)
            clear_writes: list[str] = []
            driver = app._driver
            assert driver is not None
            original_write = driver.write

            def record_write(data: str) -> None:
                clear_writes.append(data)
                original_write(data)

            monkeypatch.setattr(driver, "write", record_write)
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/"
            composer.cursor_position = 1
            app._refresh_completions()
            await pilot.pause()

            assert app.query_one("#suggestions", tui.OptionList).has_class("visible")

            for width, height in ((90, 11), (132, 26), (80, 9), (140, 24)):
                await pilot.resize_terminal(width, height)
                await pilot.pause(0.03)

            composers = list(app.query("#composer"))
            assert len(composers) == 1
            assert app.focused is composers[0]
            assert app.query_one("#suggestions", tui.OptionList).has_class("visible")
            assert app.completion_candidates
            assert app.query_one("#info-panel").styles.display == "block"
            assert app._sidebar_width_visible is True
            assert not app.query_one("#completion-stack").has_class("compact")
            assert not app.query_one("#composer-frame").has_class("compact")
            assert app._transcript_render_width == app.query_one("#transcript").size.width
            assert tui._TERMINAL_CLEAR_SCREEN in clear_writes
            screen_text = _composited_screen_text(app)
            assert screen_text.count("→") == 2
            assert "Ask anything" not in screen_text
            assert screen_text.count(_footer_armory_hint()) == 1
            assert "→ /help" in screen_text
            assert screen_text.count("/help") <= 1

    asyncio.run(check_resize_sequence())


def test_compact_resize_keeps_layout_deterministic_and_focus_on_composer() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_compact_resize() -> None:
        async with typed_app.run_test(size=(130, 24)) as pilot:
            app._append_user("Prompt that should reflow cleanly " * 8, mark_working=False)
            await pilot.resize_terminal(82, 10)
            await pilot.pause(0.1)

            assert list(app.query("#composer")) == [app.query_one("#composer")]
            assert app.query_one("#info-panel").styles.display == "none"
            assert app._sidebar_width_visible is False
            assert app.query_one("#completion-stack").has_class("compact")
            assert app.query_one("#composer-frame").has_class("compact")
            assert app.focused is app.query_one("#composer", tui.Input)

            await pilot.resize_terminal(124, 18)
            await pilot.pause(0.03)

            assert app.query_one("#info-panel").styles.display == "block"
            assert app._sidebar_width_visible is True
            assert not app.query_one("#completion-stack").has_class("compact")
            assert app.focused is app.query_one("#composer", tui.Input)

    asyncio.run(check_compact_resize())


def test_empty_composer_resize_keeps_single_placeholder_and_footer() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_empty_resize() -> None:
        async with typed_app.run_test(size=(130, 24)) as pilot:
            assert app.focused is app.query_one("#composer", tui.Input)

            for width, height in ((84, 9), (132, 22), (76, 8), (140, 24)):
                await pilot.resize_terminal(width, height)
                await pilot.pause(0.03)

            assert list(app.query("#composer")) == [app.query_one("#composer")]
            assert app.focused is app.query_one("#composer", tui.Input)
            assert app.query_one("#info-panel").styles.display == "block"

            screen_text = _composited_screen_text(app)
            assert screen_text.count("→") == 1
            assert screen_text.count(tui.COMPOSER_PLACEHOLDER) == 1
            assert screen_text.count(_footer_armory_hint()) == 1
            assert "/help" not in screen_text

    asyncio.run(check_empty_resize())


def test_resize_reflows_active_inline_menu_without_duplicate_composer() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_inline_resize() -> None:
        async with typed_app.run_test(size=(130, 24)) as pilot:
            app._open_settings_flow()
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            assert app._inline_flow.active
            assert suggestions.has_class("visible")

            for width, height in ((86, 10), (132, 22), (78, 8), (126, 24)):
                await pilot.resize_terminal(width, height)
                await pilot.pause(0.03)

            assert app._inline_flow.active
            assert suggestions.has_class("visible")
            assert app.focused is app.query_one("#composer", tui.Input)
            assert list(app.query("#composer")) == [app.query_one("#composer")]

            screen_text = _composited_screen_text(app)
            assert screen_text.count("→") == 2
            assert "→ Privacy & Diagnostics" in screen_text
            assert screen_text.count("Settings") <= 2

    asyncio.run(check_inline_resize())


def test_resize_preserves_materials_inline_focus_without_duplicate_chrome() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = tuple(f"materials/source-{index}.md" for index in range(8))
    session.source_file_count = len(session.source_files)
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_materials_resize() -> None:
        async with typed_app.run_test(size=(130, 24)) as pilot:
            app._open_materials_inline()
            await pilot.pause()

            focused_before_resize = app.focused
            assert getattr(focused_before_resize, "id", None) == "materials-list"

            for width, height in ((88, 10), (132, 22), (78, 8), (126, 24)):
                await pilot.resize_terminal(width, height)
                await pilot.pause(0.03)

            assert app._materials_inline_active
            assert getattr(app.focused, "id", None) == "materials-list"
            assert list(app.query("#composer")) == [app.query_one("#composer")]
            assert app.query_one("#info-panel").styles.display == "none"

            screen_text = _composited_screen_text(app)
            assert screen_text.count("FILTER materials") == 1
            assert screen_text.count("Materials") <= 1

    asyncio.run(check_materials_resize())


def test_resize_preserves_armory_inline_without_duplicate_chrome(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    (tmp_path / "math").mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_armory_resize() -> None:
        async with typed_app.run_test(size=(130, 24)) as pilot:
            app._open_armory_inline("manage")
            await pilot.pause()

            for width, height in ((86, 10), (132, 22), (78, 8), (126, 24)):
                await pilot.resize_terminal(width, height)
                await pilot.pause(0.03)

            assert app._armory_inline_active
            assert app.focused is app.query_one("#composer", tui.Input)
            assert list(app.query("#composer")) == [app.query_one("#composer")]
            assert app.query_one("#info-panel").styles.display == "none"

            screen_text = _composited_screen_text(app)
            assert screen_text.count("FILTER armory paths") == 1
            assert screen_text.count(_footer_armory_hint()) <= 1
            assert tui.COMPOSER_PLACEHOLDER not in screen_text

    asyncio.run(check_armory_resize())


def test_resize_spam_coalesces_repair_frames(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    original_set_timer = app.set_timer
    resize_repair_delays: list[float] = []

    class _PendingResizeTimer:
        def stop(self) -> None:
            return

    def record_timer(
        delay: float,
        callback: Callable[[], object] | None = None,
        *,
        name: str | None = None,
        pause: bool = False,
    ):
        if callback == app._finish_resize_refresh:
            resize_repair_delays.append(delay)
            return _PendingResizeTimer()
        return original_set_timer(delay, callback, name=name, pause=pause)

    monkeypatch.setattr(app, "set_timer", record_timer)

    async def check_resize_spam() -> None:
        sizes = (
            (119, 24),
            (118, 23),
            (100, 18),
            (82, 10),
            (78, 8),
            (90, 12),
            (121, 20),
            (130, 24),
            (88, 9),
            (126, 22),
            (80, 8),
            (140, 24),
        )
        async with typed_app.run_test(size=(130, 24)) as pilot:
            for width, height in sizes:
                await pilot.resize_terminal(width, height)

            assert resize_repair_delays == [tui._RESIZE_REDRAW_DELAY_SECONDS]
            app._resize_redraw.quiet_until = time.monotonic() - 1
            app._finish_resize_refresh()
            await pilot.pause(0.1)

            assert app.query_one("#info-panel").styles.display == "block"
            assert not app.query_one("#completion-stack").has_class("compact")
            assert app.focused is app.query_one("#composer", tui.Input)

            screen_text = _composited_screen_text(app)
            assert screen_text.count("→") == 1
            assert tui.COMPOSER_PLACEHOLDER in screen_text

    asyncio.run(check_resize_spam())


def test_busy_thinking_indicator_resize_has_no_duplicate_surface() -> None:
    if tui.Input is None or tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_busy_resize() -> None:
        async with typed_app.run_test(size=(130, 24)) as pilot:
            app.busy = True
            app._thinking_label = "thinking"
            app._start_thinking_animation()
            await pilot.pause(0.15)

            for width, height in ((86, 10), (132, 22), (78, 8), (126, 24)):
                await pilot.resize_terminal(width, height)
                await pilot.pause(0.03)

            thinking = app.query_one("#thinking-indicator", tui.Static)
            assert thinking.has_class("active")
            assert app.focused is app.query_one("#composer", tui.Input)
            assert list(app.query("#composer")) == [app.query_one("#composer")]

            screen_text = _composited_screen_text(app)
            assert screen_text.count("→") == 1
            assert screen_text.count("thinking...") == 1
            assert screen_text.count("STOP esc") == 1
            assert _footer_armory_hint() not in screen_text

            app.busy = False
            app._stop_thinking_animation()

    asyncio.run(check_busy_resize())


def test_tty_resize_poll_uses_actual_pty_size(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def fake_terminal_size(fileno: int) -> os.terminal_size:
        assert fileno == 77
        return os.terminal_size((92, 10))

    async def check_tty_resize_poll() -> None:
        async with typed_app.run_test(size=(160, 24)) as pilot:
            assert app.query_one("#info-panel").styles.display == "block"
            driver = app._driver
            assert driver is not None
            monkeypatch.setattr(driver, "fileno", 77, raising=False)
            monkeypatch.setattr(os, "get_terminal_size", fake_terminal_size)

            app._sync_terminal_size_from_tty()
            await pilot.pause(0.1)

            assert app.size.width == 92
            assert app.size.height == 10
            assert app.query_one("#info-panel").styles.display == "none"
            assert app.query_one("#completion-stack").has_class("compact")

    asyncio.run(check_tty_resize_poll())


def test_tty_resize_reader_overrides_textual_shutil_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    terminal_size_fds: list[int] = []

    def fake_terminal_size(fileno: int = 0) -> os.terminal_size:
        terminal_size_fds.append(fileno)
        if fileno == 88:
            return os.terminal_size((101, 12))
        return os.terminal_size((160, 24))

    async def check_tty_reader() -> None:
        async with typed_app.run_test(size=(160, 24)):
            driver = app._driver
            assert driver is not None
            monkeypatch.setattr(driver, "fileno", 88, raising=False)
            monkeypatch.setattr(os, "get_terminal_size", fake_terminal_size)

            app._install_tty_resize_reader()

            assert cast("_TerminalSizeReader", driver)._get_terminal_size() == (101, 12)
            assert 88 in terminal_size_fds

    asyncio.run(check_tty_reader())


def test_runtime_theme_switch_applies_light_background_and_dark_transparency() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def assert_core_widgets_are_transparent() -> None:
        for selector in (
            "#main-layout",
            "#shell",
            "#status",
            "#footer-hints",
            "#info-panel",
        ):
            widget = app.query_one(selector)
            for line_number in range(widget.size.height):
                strip = widget.render_line(line_number)
                assert all(
                    segment.style is None or segment.style.bgcolor is None for segment in strip
                )
        transcript = app.query_one("#transcript")
        palette = tui.current_palette()
        for line_number in range(transcript.size.height):
            strip = transcript.render_line(line_number)
            assert all(
                segment.style is None
                or segment.style.bgcolor is None
                or segment.style.bgcolor.name == palette.bg_raised.lower()
                for segment in strip
            )

    async def check_runtime_switch() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_settings_flow()
            app._handle_inline_menu_choice("Appearance")
            app._handle_appearance_choice("Light")
            await pilot.pause()

            assert app.styles.background is not None
            assert app.styles.background.a == 1.0
            assert app.screen.styles.background is not None
            assert app.screen.styles.background.a == 1.0
            assert tui.current_palette().bg_app in app.CSS

            app._handle_appearance_choice("Dark")
            await pilot.pause()

            assert app.styles.background is not None
            assert app.styles.background.a == 0.0
            assert app.screen.styles.background is not None
            assert app.screen.styles.background.a == 0.0
            assert_core_widgets_are_transparent()

    asyncio.run(check_runtime_switch())


def test_runtime_theme_switch_repaints_existing_user_messages() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    set_theme("dark")
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def transcript_background_names() -> set[str]:
        transcript = app.query_one("#transcript", tui.RichLog)
        names: set[str] = set()
        for line_number in range(transcript.size.height):
            for segment in transcript.render_line(line_number):
                if segment.style is not None and segment.style.bgcolor is not None:
                    names.add(segment.style.bgcolor.name.lower())
        return names

    async def check_runtime_switch_repaints_transcript() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._append_user("/settings", mark_working=False)
            await pilot.pause()

            dark_panel_bg = DARK_THEME.bg_raised.lower()
            light_panel_bg = LIGHT_THEME.bg_raised.lower()
            assert dark_panel_bg in transcript_background_names()

            app._handle_appearance_choice("Light")
            await pilot.pause()

            backgrounds = transcript_background_names()
            assert dark_panel_bg not in backgrounds
            assert light_panel_bg in backgrounds

    try:
        asyncio.run(check_runtime_switch_repaints_transcript())
    finally:
        set_theme("dark")


def test_runtime_theme_switch_repaints_cached_status_text() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    set_theme("dark")
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def status_brand_style() -> str:
        status = app.query_one("#status")
        for segment in status.render_line(0):
            if segment.text.strip():
                return str(segment.style).lower()
        raise AssertionError("status brand segment was not rendered")

    async def check_runtime_switch_repaints_status() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._handle_appearance_choice("Light")
            await pilot.pause()

            assert LIGHT_THEME.brand_primary.lower() in status_brand_style()

            app._handle_appearance_choice("Dark")
            await pilot.pause()

            dark_brand_style = status_brand_style()
            assert DARK_THEME.brand_primary.lower() in dark_brand_style
            assert LIGHT_THEME.brand_primary.lower() not in dark_brand_style

    try:
        asyncio.run(check_runtime_switch_repaints_status())
    finally:
        set_theme("dark")


def test_tui_uses_transparent_widgets_for_all_palettes() -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")

    try:
        for theme_name in settings_store.THEME_PRESETS:
            set_theme(theme_name)
            widgets = tui._WidgetClasses.from_palette(tui.current_palette())

            assert widgets.screen.__name__ == "BlankBackgroundWidget"
            assert widgets.vertical.__name__ == "SelectionPassthroughTransparentWidget"
            assert widgets.horizontal.__name__ == "SelectionPassthroughTransparentWidget"
            assert _allow_select(widgets.vertical) is True
            assert _allow_select(widgets.horizontal) is True
            assert issubclass(widgets.rich_log, tui.RichLog)
            assert widgets.rich_log.can_focus is False
    finally:
        set_theme("dark")


def test_tui_mouse_mode_passes_selection_through_layouts_to_text_widgets() -> None:
    if tui.RichLog is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    widgets = tui._WidgetClasses.from_palette(tui.current_palette())

    assert tui._TUI_ENABLE_MOUSE is True
    assert _allow_select(widgets.vertical) is True
    assert _allow_select(widgets.horizontal) is True
    assert _allow_select(widgets.static) is True
    assert _allow_select(widgets.rich_log) is True
    assert _allow_select(widgets.input) is True
    assert _allow_select(widgets.option_list) is True


def test_composer_mouse_drag_uses_screen_text_selection() -> None:
    if tui.Input is None or tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_drag_selection() -> None:
        async with typed_app.run_test(size=(100, 20)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "Ask anything"
            composer.cursor_position = len(composer.value)
            await pilot.pause()

            await pilot.mouse_down("#composer", offset=(1, 0))
            await pilot.hover("#footer-hints", offset=(20, 0))
            await pilot.pause()

            selected_widget_ids = {widget.id for widget in app.screen.selections}
            selected_text = app.screen.get_selected_text()
            assert "composer" in selected_widget_ids
            assert "footer-hints" in selected_widget_ids
            assert selected_text is not None
            assert selected_text.startswith("sk anything")
            assert composer.selection.start == len("Ask anything")
            assert composer.selection.end == len("Ask anything")

    asyncio.run(check_drag_selection())


def test_empty_composer_selection_does_not_copy_placeholder() -> None:
    if tui.Input is None or tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_empty_selection() -> None:
        async with typed_app.run_test(size=(100, 20)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            assert composer.value == ""
            await pilot.pause()

            await pilot.mouse_down("#composer", offset=(1, 0))
            await pilot.hover("#composer", offset=(30, 0))
            await pilot.pause()

            selected_text = app.screen.get_selected_text()
            assert selected_text is None or tui.COMPOSER_PLACEHOLDER not in selected_text

    asyncio.run(check_empty_selection())


def test_mouse_selection_normalizes_neutral_label_highlights() -> None:
    if tui.Static is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/enabled.pdf",)
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    palette = tui.current_palette()
    typed_app = cast("TextualApp[None]", app)

    async def check_selection_colours() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()

            await pilot.mouse_down("#info-panel", offset=(3, 0))
            await pilot.hover("#info-panel", offset=(11, 0))
            await pilot.pause()

            panel = app.query_one("#info-panel", tui.Static)
            selected_styles = [
                str(segment.style).lower()
                for segment in panel.render_line(0)
                if segment.text.strip() and "reverse" in str(segment.style)
            ]

            assert selected_styles
            assert all(palette.text_primary.lower() in style for style in selected_styles)
            assert all(palette.text_muted.lower() not in style for style in selected_styles)

    asyncio.run(check_selection_colours())


def test_info_panel_default_text_starts_at_sidebar_edge() -> None:
    if tui.Static is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = tuple(f"materials/source-{index}.pdf" for index in range(21))
    panel_text = tui._info_panel_default_text(session).plain
    panel_lines = panel_text.splitlines()

    assert panel_lines[:5] == [
        f"EVIDENCE {_default_display_key('evidence')}",
        "",
        "SCOPE 21/21",
        "",
        "FILES 21",
    ]
    assert "Grounding" not in panel_lines
    assert next(line for line in panel_lines if "MORE +13" in line) == "MORE +13"


def test_tui_css_has_info_panel_layout() -> None:
    css = tui._tui_css()

    assert "#info-panel" in css
    assert "#info-panel-resizer" in css
    assert "#info-separator" not in css
    assert "#shell" in css
    shell_start = css.index("#shell {")
    shell_end = css.index("}", shell_start)
    shell_block = css[shell_start:shell_end]
    assert "min-width: 0;" in shell_block
    resizer_start = css.index("#info-panel-resizer {")
    resizer_end = css.index("}", resizer_start)
    resizer_block = css[resizer_start:resizer_end]
    assert "width: 2;" in resizer_block
    assert "min-width: 2;" in resizer_block
    assert "max-width: 2;" in resizer_block
    info_start = css.index("#info-panel {")
    info_end = css.index("}", info_start)
    info_block = css[info_start:info_end]
    assert "width: 38;" in info_block
    assert "min-width: 24;" in info_block
    assert "max-width: 100%;" in info_block
    assert "padding: 0 0;" in info_block


def test_info_panel_resizer_keeps_sidebar_gutter_and_default_width() -> None:
    if tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sidebar_gutter() -> None:
        async with typed_app.run_test(size=(160, 24)) as pilot:
            await pilot.pause()

            shell = app.query_one("#shell")
            resizer = app.query_one("#info-panel-resizer")
            info_panel = app.query_one("#info-panel")

            assert shell.size.width == 120
            assert resizer.size.width == 2
            assert info_panel.size.width == 38
            assert resizer.region.x == shell.region.x + shell.size.width
            assert info_panel.region.x == resizer.region.x + resizer.size.width

    asyncio.run(check_sidebar_gutter())


def test_info_panel_width_can_be_dragged_within_visible_layout() -> None:
    if tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sidebar_drag() -> None:
        async with typed_app.run_test(size=(160, 24)) as pilot:
            await pilot.pause()
            resizer = app.query_one("#info-panel-resizer")
            info_panel = app.query_one("#info-panel")

            assert info_panel.size.width == 38

            await pilot.mouse_down("#info-panel-resizer", offset=(0, 0))
            await pilot.hover("#shell", offset=(100, 0))
            await pilot.pause()

            assert app._sidebar_resizing is True
            assert app._sidebar_width == 58
            assert info_panel.styles.display == "block"
            assert info_panel.size.width == 58

            app.on_mouse_up(
                events.MouseUp(
                    resizer,
                    x=158,
                    y=0,
                    delta_x=58,
                    delta_y=0,
                    button=1,
                    shift=False,
                    meta=False,
                    ctrl=False,
                    screen_x=158,
                    screen_y=0,
                )
            )
            await pilot.pause()

            assert app._sidebar_resizing is False
            assert app._sidebar_width == 24
            assert info_panel.styles.display == "block"
            assert info_panel.size.width == 24

    asyncio.run(check_sidebar_drag())


def test_tui_css_transparent_container_defaults_prevent_panel_stripes() -> None:
    css = tui._tui_css()

    assert "Horizontal,\nVertical,\nStatic,\nRichLog {" in css
    container_start = css.index("Horizontal,\nVertical,\nStatic,\nRichLog {")
    container_end = css.index("}", container_start)
    container_block = css[container_start:container_end]

    assert "background: transparent;" in container_block
    assert "background-tint: transparent;" in container_block


def test_transcript_panel_background_only_paints_user_entries() -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app.session.config.base_url = ""
    app.session.config.model = ""
    typed_app = cast("TextualApp[None]", app)

    async def check_transcript_backgrounds() -> None:
        async with typed_app.run_test(size=(100, 18)) as pilot:
            app._append_user("User prompt", mark_working=False)
            app._append_assistant_reply("Assistant reply")
            await pilot.pause()

            transcript = app.query_one("#transcript")
            panel = tui.current_palette().bg_raised.lower()
            user_segments: list[str] = []
            assistant_segments: list[str] = []
            panel_scroll_y = -1
            panel_line_index = -1
            for scroll_y in range(int(transcript.max_scroll_y) + 1):
                transcript.scroll_y = scroll_y
                await pilot.pause(0)
                for line_number in range(transcript.size.height):
                    strip = transcript.render_line(line_number)
                    line_text = "".join(segment.text for segment in strip)
                    if "User prompt" in line_text and 0 < line_number < transcript.size.height - 1:
                        panel_scroll_y = scroll_y
                        panel_line_index = line_number
                    for segment in strip:
                        style = str(segment.style)
                        if "User prompt" in segment.text:
                            user_segments.append(style)
                        if "Assistant reply" in segment.text:
                            assistant_segments.append(style)

            assert user_segments
            assert assistant_segments
            assert all(f"on {panel}" in style.lower() for style in user_segments)
            assert all(f"on {panel}" not in style.lower() for style in assistant_segments)
            assert panel_scroll_y >= 0
            assert panel_line_index >= 1
            transcript.scroll_y = panel_scroll_y
            await pilot.pause(0)
            assert _strip_is_panel_filled(transcript.render_line(panel_line_index - 1), panel)
            assert _strip_is_panel_filled(transcript.render_line(panel_line_index), panel)
            assert _strip_is_panel_filled(transcript.render_line(panel_line_index + 1), panel)

    asyncio.run(check_transcript_backgrounds())


def test_transcript_pads_assistant_replies_but_not_system_messages() -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")

    state = tui._TuiRuntimeState(armory_home_shown=True)
    app = tui.HephTui(
        _plain_session(),
        state,
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_transcript_padding() -> None:
        async with typed_app.run_test(size=(40, 16)) as pilot:
            app._append_assistant_reply("Assistant reply " * 12)
            app._append_notice("System notice")
            await pilot.pause()

            transcript = app.query_one("#transcript", tui.RichLog)
            rendered = [
                "".join(segment.text for segment in line).rstrip() for line in transcript.lines
            ]
            system_index, system_line = next(
                (index, line) for index, line in enumerate(rendered) if "System notice" in line
            )
            reply_lines = [line for line in rendered[:system_index] if line.strip()]

            assert len(reply_lines) > 1
            assert all(line.startswith("  ") for line in reply_lines)
            assert system_line.startswith("System notice")

    asyncio.run(check_transcript_padding())


def test_activity_trace_lines_are_muted_but_readable() -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")

    state = tui._TuiRuntimeState(armory_home_shown=True)
    app = tui.HephTui(
        _plain_session(),
        state,
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_activity_style() -> None:
        async with typed_app.run_test(size=(50, 16)) as pilot:
            app._append_activity("    Ran search_materials `sequence`")
            app._append_notice("System notice")
            await pilot.pause()

            transcript = app.query_one("#transcript", tui.RichLog)
            activity_styles = [
                str(segment.style).lower()
                for line in transcript.lines
                for segment in line
                if "search_materials" in segment.text
            ]
            notice_styles = [
                str(segment.style).lower()
                for line in transcript.lines
                for segment in line
                if "System notice" in segment.text
            ]
            palette = tui.current_palette()

            assert activity_styles
            assert notice_styles
            assert any(palette.text_muted.lower() in style for style in activity_styles)
            assert any(palette.text_muted.lower() in style for style in notice_styles)

    asyncio.run(check_activity_style())


def test_activity_trace_lines_clip_and_group_without_spacer() -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")

    state = tui._TuiRuntimeState(armory_home_shown=True)
    app = tui.HephTui(
        _plain_session(),
        state,
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_activity_layout() -> None:
        async with typed_app.run_test(size=(52, 16)) as pilot:
            app._append_activity(
                "    Preparing the material index and reading enabled evidence "
                "for a corpus overview."
            )
            app._append_activity("    Material index ready: 21 enabled sources, 423 chunks.")
            await pilot.pause()

            transcript = app.query_one("#transcript", tui.RichLog)
            rendered = [_strip_plain_text(line).rstrip() for line in transcript.lines]
            activity_indexes = [
                index
                for index, line in enumerate(rendered)
                if "Preparing the material index" in line or "Material index ready" in line
            ]

            assert len(activity_indexes) == 2
            assert activity_indexes[1] == activity_indexes[0] + 1
            assert all(len(rendered[index]) <= transcript.size.width for index in activity_indexes)
            assert rendered[activity_indexes[0]].endswith("...")

    asyncio.run(check_activity_layout())


def _strip_is_panel_filled(strip: Strip, panel: str) -> bool:
    segments: list[Segment] = list(strip)
    return all(
        segment.text == "" or f"on {panel}" in str(segment.style).lower() for segment in segments
    )


def test_transparent_style_strips_standard_and_truecolor_black_backgrounds() -> None:
    if tui._RichStyle is None:
        pytest.skip("Rich is not installed")

    standard = style_without_black_background(tui._RichStyle.parse("red on black"))
    truecolor = style_without_black_background(tui._RichStyle.parse("red on #000000"))
    nonblack = style_without_black_background(tui._RichStyle.parse("red on #111111"))

    assert standard.bgcolor is None
    assert truecolor.bgcolor is None
    assert nonblack.bgcolor is not None


def test_tui_css_suggestion_scrollbar_is_hidden() -> None:
    css = tui._tui_css()
    suggestions_start = css.index("#suggestions {")
    suggestions_end = css.index("}", suggestions_start)
    suggestions_block = css[suggestions_start:suggestions_end]
    assert "scrollbar-size: 0 0;" in suggestions_block
    assert "scrollbar-background:" not in suggestions_block
    assert "scrollbar-background: #1C1C1C;" not in suggestions_block


def test_tui_css_materials_highlight_uses_neutral_selection_colour() -> None:
    css = tui._tui_css()
    palette = tui.current_palette()

    assert "#materials-list > .option-list--option-highlighted" not in css
    assert "#materials-list.material-enabled > .option-list--option-highlighted" in css
    assert "#materials-list.material-disabled > .option-list--option-highlighted" in css
    assert "#materials-list-right.material-enabled > .option-list--option-highlighted" in css
    assert "#materials-list-right.material-disabled > .option-list--option-highlighted" in css
    disabled_start = css.index(
        "#materials-list.material-disabled > .option-list--option-highlighted"
    )
    disabled_end = css.index("}", disabled_start)
    disabled_block = css[disabled_start:disabled_end]
    enabled_start = css.index(
        "#materials-list.material-enabled > .option-list--option-highlighted"
    )
    enabled_end = css.index("}", enabled_start)
    enabled_block = css[enabled_start:enabled_end]
    assert "background: transparent;" in enabled_block
    assert "background: transparent;" in disabled_block
    assert f"color: {palette.brand_primary};" in enabled_block
    assert f"color: {palette.brand_primary};" in disabled_block
    assert "text-style: not bold;" in enabled_block
    assert "text-style: not bold;" in disabled_block
    assert f"background: {palette.action_primary_bg};" not in enabled_block
    assert f"background: {palette.status_error_text};" not in disabled_block


def test_tui_css_materials_header_and_gaps_are_status_weight() -> None:
    css = tui._tui_css()
    palette = tui.current_palette()

    header_start = css.index("#materials-header {")
    header_end = css.index("}", header_start)
    header_block = css[header_start:header_end]
    top_gap_start = css.index("#materials-top-gap,")
    top_gap_end = css.index("}", top_gap_start)
    gap_block = css[top_gap_start:top_gap_end]

    assert f"color: {palette.text_muted};" in header_block
    assert "text-style: bold;" not in header_block
    assert "#materials-bottom-gap" in gap_block
    assert "height: 1;" in gap_block


def test_materials_selected_label_uses_quiet_brand_highlight() -> None:
    if tui._RichText is None:
        pytest.skip("Rich is not installed")

    session = _plain_session()
    session.source_files = ("materials/biology.pdf",)
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    selected = app._format_material_option("materials/biology.pdf", selected=True)
    unselected = app._format_material_option("materials/biology.pdf", selected=False)
    palette = tui.current_palette()

    assert not isinstance(selected, str)
    assert not isinstance(unselected, str)
    assert selected.plain == "→ @biology.pdf"
    assert unselected.plain == "  @biology.pdf"
    selected_styles = [str(span.style) for span in selected.spans]
    unselected_styles = [str(span.style) for span in unselected.spans]
    assert all(palette.brand_primary in style for style in selected_styles)
    assert not any("bold" in style.lower() for style in selected_styles)
    assert palette.text_primary in unselected_styles
    assert palette.status_success_text not in unselected_styles
    assert not any(" on " in style for style in selected_styles)


def test_materials_disabled_label_uses_only_disabled_state_colour() -> None:
    if tui._RichText is None:
        pytest.skip("Rich is not installed")

    session = _plain_session()
    session.source_files = ("materials/biology.pdf",)
    session.disabled_source_files.add("materials/biology.pdf")
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    selected = app._format_material_option("materials/biology.pdf", selected=True)
    unselected = app._format_material_option("materials/biology.pdf", selected=False)
    palette = tui.current_palette()

    assert not isinstance(selected, str)
    assert not isinstance(unselected, str)
    assert selected.plain == "→ @biology.pdf"
    assert unselected.plain == "  @biology.pdf"
    selected_styles = [str(span.style) for span in selected.spans]
    unselected_styles = [str(span.style) for span in unselected.spans]
    assert all(palette.brand_primary in style for style in selected_styles)
    assert not any("bold" in style.lower() for style in selected_styles)
    assert palette.text_muted in unselected_styles
    assert palette.status_error_text not in unselected_styles
    assert palette.action_primary_bg not in selected_styles


def test_materials_header_and_sidebar_use_label_value_layout() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/enabled.pdf", "materials/disabled.pdf")
    session.disabled_source_files.add("materials/disabled.pdf")
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_material_layout() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_materials_inline()
            await pilot.pause()

            header = app.query_one("#materials-header", tui.Static)
            sidebar = app.query_one("#info-panel", tui.Static)
            header_text = str(header.render())
            sidebar_text = str(sidebar.render())

            assert "SCOPE materials" in header_text
            assert "ACTIVE 1/2" in header_text
            assert "MATERIAL @enabled.pdf" in sidebar_text
            assert "STATE active" in sidebar_text
            assert "PATH materials/enabled.pdf" in sidebar_text
            assert "\n\n" not in sidebar_text

    asyncio.run(check_material_layout())


def test_materials_highlight_uses_neutral_selection_without_state_stripe() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/enabled.pdf", "materials/disabled.pdf")
    session.disabled_source_files.add("materials/disabled.pdf")
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    palette = tui.current_palette()
    typed_app = cast("TextualApp[None]", app)

    async def check_material_selection() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_materials_inline()
            await pilot.pause()

            app._handle_materials_option_highlighted("materials-list", 1)
            await pilot.pause()

            material_list = app.query_one("#materials-list", tui.OptionList)
            first_line_styles = [
                str(segment.style)
                for segment in material_list.render_line(0)
                if "enabled.pdf" in segment.text
            ]
            second_line_styles = [
                str(segment.style)
                for segment in material_list.render_line(1)
                if "disabled." in segment.text
            ]

            assert len(first_line_styles) == 1
            assert palette.text_primary.lower() in first_line_styles[0].lower()
            assert palette.status_success_text.lower() not in first_line_styles[0].lower()
            assert palette.brand_primary.lower() not in first_line_styles[0].lower()
            assert len(second_line_styles) == 1
            assert palette.brand_primary.lower() in second_line_styles[0].lower()
            assert palette.status_error_text.lower() not in second_line_styles[0].lower()

    asyncio.run(check_material_selection())


def test_tui_css_completion_highlight_has_quiet_selection_contrast() -> None:
    css = tui._tui_css()
    palette = tui.current_palette()
    highlight_start = css.index("#suggestions > .option-list--option-highlighted")
    highlight_end = css.index("}", highlight_start)
    highlight_block = css[highlight_start:highlight_end]
    hover_start = css.index("#suggestions.mouse-hovering > .option-list--option-highlighted")
    hover_end = css.index("}", hover_start)
    hover_block = css[hover_start:hover_end]

    assert "background: transparent;" in highlight_block
    assert f"color: {palette.brand_primary};" in highlight_block
    assert "text-style: not bold;" in highlight_block
    assert "#suggestions > .option-list--option-hover" in hover_block
    assert "background: transparent;" in hover_block
    assert f"color: {palette.brand_primary};" in hover_block
    assert "text-style: not bold;" in hover_block
    assert f"color: {palette.action_primary_text};" not in hover_block


def test_tui_css_inline_menu_highlight_has_no_brand_stripe() -> None:
    css = tui._tui_css()
    selector = "#suggestions.inline-menu > .option-list--option-highlighted"
    block_start = css.index(selector)
    block_end = css.index("}", block_start)
    block = css[block_start:block_end]

    assert "padding: 0 0;" in block
    assert "background:" not in block
    assert "color:" not in block


def test_inline_menu_selected_label_uses_brand_without_bold_row() -> None:
    selected = _inline_menu_option_text(
        "Signal Entropy",
        "uncertainty in signals",
        selected=True,
    )
    unselected = _inline_menu_option_text(
        "Signal Entropy",
        "uncertainty in signals",
        selected=False,
    )
    palette = tui.current_palette()

    assert not isinstance(selected, str)
    assert not isinstance(unselected, str)
    selected_styles = [str(span.style) for span in selected.spans]
    unselected_styles = [str(span.style) for span in unselected.spans]
    assert any(palette.brand_primary in style for style in selected_styles)
    assert any(palette.text_muted in style for style in selected_styles)
    assert not any("bold" in style.lower() for style in selected_styles)
    assert any(palette.text_secondary in style for style in unselected_styles)
    assert any(palette.text_muted in style for style in unselected_styles)
    assert not any("bold" in style.lower() for style in unselected_styles)


def test_inline_menu_option_text_collapses_newline_spam() -> None:
    prompt = _inline_menu_option_text(
        "a470954cc5be",
        "hey\n\n\nfwafawf\n\n\n\n\n\nwwafw  2026-06-02T14:44:18.165289+00:00",
        selected=True,
    )

    plain = prompt if isinstance(prompt, str) else prompt.plain
    assert plain == "→ a470954cc5be    hey fwafawf wwafw 2026-06-02T14:44:18.165289+00:00"


def test_search_result_text_reserves_selection_prefix() -> None:
    result = SearchResult(
        armory_path=Path("/tmp/demo-armory"),
        source_rel="materials/notes.pdf",
        chunk_index=0,
        chunk_text="first line\nsecond line",
        score=0.82,
    )

    selected = _format_search_result(result, selected=True)
    unselected = _format_search_result(result, selected=False)

    assert selected.startswith("→ demo-armory    SOURCE materials/notes.pdf  SCORE 82%")
    assert unselected.startswith("  demo-armory    SOURCE materials/notes.pdf  SCORE 82%")
    assert "\n    first line second line" in selected


def test_local_model_option_text_uses_structured_columns() -> None:
    prompt = _local_model_option_text(
        "llama-cpp/unsloth/Qwen3-Coder-Next-GGUF:Q4_K_M",
        local_model_option_description(
            "search",
            "install",
            "Q4_K_M",
            "3.7 GB",
            "2,656,128 downloads, 700 likes",
        ),
        selected=True,
        prompt_width=120,
    )

    plain = prompt if isinstance(prompt, str) else prompt.plain
    assert len(plain) == 120
    assert not plain.startswith("llama-cpp/")
    assert plain.startswith("→ unsloth/Qwen3-Coder-Next-GGUF:Q4_K_M search install")
    assert plain.index("search install") == len("→ unsloth/Qwen3-Coder-Next-GGUF:Q4_K_M ")
    assert "search" in plain
    assert "install" in plain
    assert "Q4_K_M" in plain
    assert "3.7 GB" in plain
    assert plain.endswith("2,656,128 downloads, 700 likes")


def test_local_model_option_text_drops_detail_when_narrow() -> None:
    label = "llama-cpp/Andyvurrent/Gemma-3-1B-it-GLM-4.7-Flash-Heretic-Uncensored-Thinking_GGUF"
    description = local_model_option_description(
        "search",
        "install",
        "Q4_K_M",
        "721 MB",
        "2,433,843 downloads, 54 likes",
    )
    prompt = _local_model_option_text(
        label,
        description,
        selected=False,
        prompt_width=54,
    )

    plain = prompt if isinstance(prompt, str) else prompt.plain
    assert len(plain) == 54
    assert plain.startswith("  Andy... search install")
    assert "search" in plain
    assert "Q4_K_M" in plain
    assert "721 MB" in plain
    assert plain.endswith("2,433,843...")

    tight_prompt = _local_model_option_text(
        label,
        description,
        selected=False,
        prompt_width=46,
    )
    tight_plain = tight_prompt if isinstance(tight_prompt, str) else tight_prompt.plain
    assert len(tight_plain) == 46
    assert "Q4_K_M" in tight_plain
    assert "721 MB" in tight_plain
    assert tight_plain.endswith("2...")


def test_local_model_fixed_metadata_text_reserves_visible_columns() -> None:
    widths = _LocalModelMetadataWidths(quant=6, size=6, detail=12)

    assert _local_model_fixed_metadata_text("Q4", "3 GB", "", widths) == "    Q4    3 GB"
    assert _local_model_fixed_metadata_text("", "3 GB", "needs RAM", widths) == ("          3 GB")
    assert _local_model_fixed_metadata_text("Q4", "", "needs RAM", widths) == "    Q4        "


def test_local_model_fixed_metadata_text_without_widths_keeps_available_fields() -> None:
    assert _local_model_fixed_metadata_text("Q4", "3 GB", "", None) == "Q4  3 GB"
    assert _local_model_fixed_metadata_text("", "3 GB", "", None) == "3 GB"


def test_local_inline_menu_entries_align_with_counter() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_local_menu_alignment() -> None:
        async with typed_app.run_test(size=(200, 24)) as pilot:
            app._open_inline_menu(
                name="local",
                step="menu",
                title="Local models",
                options=[
                    (
                        "llama-cpp/unsloth/Qwen3-Coder-Next-GGUF:Q4_K_M",
                        local_model_option_description(
                            "search",
                            "install",
                            "Q4_K_M",
                            "3.7 GB",
                            "2,656,128 downloads, 700 likes",
                        ),
                    ),
                    (
                        "llama-cpp/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0",
                        local_model_option_description(
                            "search",
                            "install",
                            "Q8_0",
                            "1.1 GB",
                            "656,450 downloads, 46 likes",
                        ),
                    ),
                ],
            )
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            entry_line = _screen_line_with(app, "unsloth/Qwen3-Coder-Next-GGUF")
            position_line = _screen_line_with(app, f"(1/{suggestions.option_count})")
            label = "unsloth/Qwen3-Coder-Next-GGUF:Q4_K_M"
            action = "search install"
            metadata = "2,656,128 downloads, 700 likes"

            assert entry_line.index("unsloth/") == position_line.index("(")
            assert entry_line.index(action) == entry_line.index(label) + len(label) + 1
            assert entry_line.rstrip().endswith(metadata)
            assert entry_line.index(metadata) > entry_line.index(action) + len(action)

    asyncio.run(check_local_menu_alignment())


def test_local_inline_menu_metadata_columns_follow_visible_rows() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_local_metadata_alignment() -> None:
        async with typed_app.run_test(size=(200, 24)) as pilot:
            app._open_inline_menu(
                name="local",
                step="menu",
                title="Local models",
                options=[
                    (
                        "llama-cpp/Phi-3 Mini 4K Instruct",
                        local_model_option_description(
                            "search",
                            "install",
                            "Q4_0",
                            "2.2 GB",
                            "needs 8 GB RAM",
                        ),
                    ),
                    (
                        "llama-cpp/Qwen3 4B",
                        local_model_option_description(
                            "search",
                            "install",
                            "Q4_K_M",
                            "2.3 GB",
                            "needs 8 GB RAM",
                        ),
                    ),
                    (
                        "llama-cpp/Gemma 4 E2B Instruct",
                        local_model_option_description(
                            "search",
                            "install",
                            "Q4_0",
                            "3.1 GB",
                            "needs 8 GB RAM",
                        ),
                    ),
                    (
                        "llama-cpp/Gemma 4 E4B Instruct",
                        local_model_option_description(
                            "search",
                            "install",
                            "Q4_0",
                            "4.8 GB",
                            "needs 12 GB RAM",
                        ),
                    ),
                ],
            )
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            needs_8_row = _option_prompt_plain(suggestions, 2)
            needs_12_row = _option_prompt_plain(suggestions, 3)

            assert needs_8_row.index("3.1 GB") == needs_12_row.index("4.8 GB")
            assert needs_8_row.index("needs") == needs_12_row.index("needs")
            assert needs_8_row.index("GB RAM") == needs_12_row.index("GB RAM")

    asyncio.run(check_local_metadata_alignment())


def test_local_inline_menu_catalog_ram_columns_follow_visible_rows() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_local_catalog_alignment() -> None:
        async with typed_app.run_test(size=(200, 24)) as pilot:
            options = _local_flow_options(
                (),
                (
                    LlamaCppCandidate(
                        repo_id="google/gemma-4-E2B-it-qat-q4_0-gguf",
                        filename="gemma-4-E2B_q4_0-it.gguf",
                        quant="Q4_0",
                        downloads=0,
                        likes=0,
                        size_bytes=3_349_514_112,
                        display_name="Gemma 4 E2B Instruct",
                        recommended_ram_gb=8,
                    ),
                    LlamaCppCandidate(
                        repo_id="google/gemma-4-E4B-it-qat-q4_0-gguf",
                        filename="gemma-4-E4B_q4_0-it.gguf",
                        quant="Q4_0",
                        downloads=0,
                        likes=0,
                        size_bytes=5_154_939_136,
                        display_name="Gemma 4 E4B Instruct",
                        recommended_ram_gb=12,
                    ),
                ),
                current_model="gpt-5.5",
            )
            app._open_inline_menu(
                name="local",
                step="menu",
                title="Local models",
                options=options,
            )
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            ram_8_row = _option_prompt_plain(suggestions, 0)
            ram_12_row = _option_prompt_plain(suggestions, 1)

            assert ram_8_row.index("3.1 GB") == ram_12_row.index("4.8 GB")
            assert ram_8_row.index("RAM") == ram_12_row.index("RAM")
            assert ram_8_row.index("gb") == ram_12_row.index("gb")

    asyncio.run(check_local_catalog_alignment())


def test_tui_css_option_list_highlights_use_selection_tokens() -> None:
    css = tui._tui_css()
    palette = tui.current_palette()
    for selector in (
        "OptionList > .option-list--option-highlighted",
        "OptionList:focus > .option-list--option-highlighted",
    ):
        block_start = css.index(selector)
        block_end = css.index("}", block_start)
        block = css[block_start:block_end]
        assert f"background: {palette.action_primary_bg};" in block
        assert f"color: {palette.action_primary_text};" in block
        assert "text-style: not bold;" in block


def test_tui_css_text_selection_uses_reverse_video() -> None:
    css = tui._tui_css()
    palette = tui.current_palette()

    selection_start = css.index("Screen .screen--selection {")
    selection_end = css.index("}", selection_start)
    selection_block = css[selection_start:selection_end]
    input_start = css.index("Input > .input--selection {")
    input_end = css.index("}", input_start)
    input_block = css[input_start:input_end]

    assert "background: transparent;" in selection_block
    assert "text-style: reverse;" in selection_block
    assert f"background: {palette.action_primary_bg};" not in selection_block
    assert "background: transparent;" in input_block
    assert "text-style: reverse;" in input_block


def test_info_panel_material_colours_match_materials_picker() -> None:
    session = _plain_session()
    session.source_files = ("materials/enabled.pdf", "materials/disabled.pdf")
    session.disabled_source_files.add("materials/disabled.pdf")

    panel = tui._info_panel_default_text(session)
    spans = {(span.start, span.end, str(span.style)) for span in panel.spans}
    palette = tui.current_palette()

    enabled_start = panel.plain.index("@enabled.pdf")
    disabled_start = panel.plain.index("@disabled.pdf")
    assert (
        enabled_start,
        enabled_start + len("@enabled.pdf"),
        palette.text_primary,
    ) in spans
    assert (
        disabled_start,
        disabled_start + len("@disabled.pdf"),
        palette.text_muted,
    ) in spans


def test_tui_css_prevents_full_width_status_and_footer_bars() -> None:
    css = tui._tui_css()

    for selector in ("#status", "#footer-hints"):
        block_start = css.index(f"{selector} {{")
        block_end = css.index("}", block_start)
        block = css[block_start:block_end]

        assert "width: auto;" in block
        assert "max-width: 100%;" in block


def test_tui_css_pads_composer_as_full_width_user_block() -> None:
    css = tui._tui_css()
    composer_bar = tui.current_palette().bg_raised

    frame_start = css.index("#composer-frame {")
    frame_end = css.index("}", frame_start)
    frame_block = css[frame_start:frame_end]
    prompt_start = css.index("#composer-prompt {")
    prompt_end = css.index("}", prompt_start)
    prompt_block = css[prompt_start:prompt_end]
    composer_start = css.index("#composer {")
    composer_end = css.index("}", composer_start)
    composer_block = css[composer_start:composer_end]
    input_start = css.index("Input {")
    input_end = css.index("}", input_start)
    input_block = css[input_start:input_end]

    assert "height: auto;" in frame_block
    assert "min-height: 3;" in frame_block
    assert "max-height: 8;" in frame_block
    assert "width: 100%;" in frame_block
    assert "layout: horizontal;" in frame_block
    assert "padding: 1 0;" in frame_block
    assert f"background: {composer_bar};" in frame_block
    assert "width: 2;" in prompt_block
    assert "padding: 0 0;" in prompt_block
    assert f"background: {composer_bar};" in prompt_block
    assert "width: 100%;" in composer_block
    assert "height: auto;" in composer_block
    assert "max-height: 6;" in composer_block
    assert "padding: 0 0;" in composer_block
    assert f"background: {composer_bar};" in composer_block
    assert "padding: 0 0;" in input_block
    placeholder_start = css.index("Input > .input--placeholder,")
    placeholder_end = css.index("}", placeholder_start)
    placeholder_block = css[placeholder_start:placeholder_end]
    cursor_start = css.index("Input > .input--cursor {")
    cursor_end = css.index("}", cursor_start)
    cursor_block = css[cursor_start:cursor_end]
    assert f"color: {tui.current_palette().text_secondary};" in placeholder_block
    assert f"color: {composer_bar};" in cursor_block


def test_composer_text_is_inset_inside_full_width_chatbox() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_composer_inset() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            frame = app.query_one("#composer-frame")
            prompt = app.query_one("#composer-prompt", tui.Static)
            composer.value = "eyf"
            await pilot.pause()

            assert frame.region.x == 0
            assert frame.region.width == 80
            assert prompt.region.x == frame.region.x
            assert str(prompt.render()) == "→"
            assert composer.region.x == frame.region.x + 2

    asyncio.run(check_composer_inset())


def test_tui_css_reserves_inline_completion_stack_below_composer() -> None:
    css = tui._tui_css()

    composer_start = css.index("#composer-frame {")
    composer_end = css.index("}", composer_start)
    composer_block = css[composer_start:composer_end]
    stack_start = css.index("#completion-stack {")
    stack_end = css.index("}", stack_start)
    stack_block = css[stack_start:stack_end]
    suggestions_start = css.index("#suggestions {")
    suggestions_end = css.index("}", suggestions_start)
    suggestions_block = css[suggestions_start:suggestions_end]
    position_start = css.index("#completion-position {")
    position_end = css.index("}", position_start)
    position_block = css[position_start:position_end]
    footer_start = css.index("#footer-hints {")
    footer_end = css.index("}", footer_start)
    footer_block = css[footer_start:footer_end]

    assert "margin-top: 1;" in composer_block
    assert "height: 9;" in stack_block
    assert "min-height: 1;" in stack_block
    assert "max-height: 9;" in stack_block
    assert "#completion-stack.compact" in css
    assert "width: 100%;" in suggestions_block
    assert "max-width: 100%;" in suggestions_block
    assert "padding-right: 0;" in suggestions_block
    assert "width: 85%;" not in suggestions_block
    assert "max-width: 85%;" not in suggestions_block
    assert "max-height: 7;" in suggestions_block
    assert "padding: 0 2;" in position_block
    assert "dock: bottom;" not in suggestions_block
    assert "layer: suggestions;" not in suggestions_block
    assert "margin-top: 1;" not in footer_block


def test_completion_menu_expands_below_stationary_composer() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_inline_menu_layout() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            frame = app.query_one("#composer-frame")
            stack = app.query_one("#completion-stack")
            footer = app.query_one("#footer-hints")

            frame_y = frame.region.y
            stack_y = stack.region.y
            assert stack_y > frame_y
            assert stack.size.height == 9
            assert footer.region.y == stack_y

            await pilot.press("/")
            await pilot.pause()

            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),
            )  # ty:ignore[redundant-cast]
            position = app.query_one("#completion-position", tui.Static)
            footer = app.query_one("#footer-hints", tui.Static)
            assert frame.region.y == frame_y
            assert stack.region.y == stack_y
            assert frame.region.width == stack.region.width
            assert str(position.render()) == f"  (1/{suggestions.option_count})"
            assert str(footer.render()).startswith(_footer_armory_hint())
            assert suggestions.size.width == stack.size.width
            assert suggestions.has_class("visible")
            assert suggestions.size.height <= 7
            assert position.region.y == suggestions.region.y + suggestions.size.height
            assert footer.region.y == position.region.y + 1
            screen_text = _composited_screen_text(app)
            screen_lines = screen_text.splitlines()
            command_line = next(line for line in screen_lines if "/help" in line)
            position_label = f"(1/{suggestions.option_count})"
            position_line = next(line for line in screen_lines if position_label in line)
            assert command_line.index("/help") == position_line.index("(")

    asyncio.run(check_inline_menu_layout())


def test_compact_terminal_collapses_completion_stack_to_footer_row() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_compact_stack() -> None:
        async with typed_app.run_test(size=(80, 8)):
            stack = app.query_one("#completion-stack")
            frame = app.query_one("#composer-frame")
            footer = app.query_one("#footer-hints")
            composer = app.query_one("#composer")

            assert stack.has_class("compact")
            assert frame.has_class("compact")
            assert stack.size.height == 1
            assert frame.size.height == 1
            assert footer.region.y > composer.region.y
            assert footer.region.y < app.size.height

    asyncio.run(check_compact_stack())


def test_transcript_overflow_scrolls_without_moving_composer() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_transcript_overflow() -> None:
        async with typed_app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            frame = app.query_one("#composer-frame")
            stack = app.query_one("#completion-stack")
            baseline_y = frame.region.y
            baseline_stack_gap = stack.region.y - frame.region.y

            for index in range(18):
                app._append_user(f"stress history message {index}", mark_working=False)
                app._append_assistant_reply(
                    "No armory is attached. Open or create an armory with /armory, "
                    "then add materials so I can answer from your sources."
                )
            await pilot.pause()

            transcript = app.query_one("#transcript", tui.RichLog)
            assert transcript.max_scroll_y > 0
            assert frame.region.y == baseline_y
            assert stack.region.y - frame.region.y == baseline_stack_gap
            assert baseline_stack_gap > 0
            assert frame.region.y < 30

    asyncio.run(check_transcript_overflow())


def test_status_and_footer_hints_segments_do_not_paint_black_background() -> None:
    if tui.Static is None:
        pytest.skip("Textual is not installed")

    class Stress(tui.App[None]):
        CSS = tui._tui_css()

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            status_text = tui._status_text(session)
            hints_text = tui._footer_hints_text(session)
            with tui.Vertical(id="main-layout"):
                yield tui.Static(status_text, id="status")
                yield tui.Static(hints_text, id="footer-hints")

    async def check_segments() -> None:
        app = Stress()
        async with app.run_test(size=(120, 12)) as pilot:
            await pilot.pause()
            for selector in ("#status", "#footer-hints"):
                widget = app.query_one(selector, tui.Static)
                for line_number in range(widget.size.height):
                    for segment in widget.render_line(line_number):
                        style = str(segment.style)
                        assert "on #000000" not in style

    asyncio.run(check_segments())


def test_tui_layout_blanks_do_not_paint_black_background() -> None:
    if tui.Static is None or tui.Strip is None:
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()
    vertical_class = tui._transparent_vertical_class()
    static_class = tui._transparent_static_class()
    rich_log_class = tui._transparent_rich_log_class()
    input_class = tui._transparent_input_class()

    class Stress(tui.App[None]):
        CSS = tui._tui_css()

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with vertical_class(id="main-layout"):
                yield static_class(tui._status_text(session), id="status")
                yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)
                yield static_class("", id="thinking-indicator")
                with vertical_class(id="composer-frame"):
                    yield input_class(
                        placeholder='Ask anything... "What should I review next?"',
                        id="composer",
                    )
                    yield static_class(
                        tui._footer_hints_text(session),
                        id="footer-hints",
                    )

    async def check_layout_blanks() -> None:
        app = Stress()
        async with app.run_test(size=(120, 12)) as pilot:
            await pilot.pause()
            widgets: tuple[Widget, ...] = (
                cast("Widget", app.screen),
                app.query_one("#main-layout"),
                app.query_one("#status"),
                app.query_one("#transcript"),
                app.query_one("#thinking-indicator"),
                app.query_one("#composer-frame"),
                app.query_one("#composer"),
                app.query_one("#footer-hints"),
            )
            for widget in widgets:
                for line_number in range(widget.size.height):
                    segments = widget.render_line(line_number)
                    assert all("on #000000" not in str(segment.style) for segment in segments)

    asyncio.run(check_layout_blanks())


def test_info_separator_is_not_rendered() -> None:
    if tui.Input is None or tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_separator_absent() -> None:
        async with typed_app.run_test(size=(160, 24)) as pilot:
            await pilot.pause()
            assert list(app.query("#info-separator")) == []

            # The gutter between #shell and #info-panel must also be free of any
            # synthetic ``rgb(0,0,0)`` cells. Textual's styles cache pads
            # widget content with the resolved background style, which
            # collapses the ``Color(0,0,0,a=0)`` produced by
            # ``background: transparent`` into opaque black -- exactly the
            # stripe the user sees at the shell/info-panel boundary.
            shell = app.query_one("#shell")
            resizer = app.query_one("#info-panel-resizer")
            info_panel = app.query_one("#info-panel")
            for sibling in (shell, resizer, info_panel):
                crop = _Region(0, 0, sibling.size.width, sibling.size.height)
                strips = sibling.render_lines(crop)
                for strip in strips:
                    for segment in strip:
                        assert "on #000000" not in str(segment.style)

    asyncio.run(check_separator_absent())


def test_shell_info_panel_seam_has_no_black_background() -> None:
    if tui.Input is None or tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_seam_transparent() -> None:
        # 160 cols is comfortably above the sidebar visibility threshold
        # (currently 120), so #info-panel is composed alongside #shell.
        async with typed_app.run_test(size=(160, 24)) as pilot:
            await pilot.pause()

            shell = app.query_one("#shell")
            resizer = app.query_one("#info-panel-resizer")
            info_panel = app.query_one("#info-panel")
            # Sanity: the sidebar must actually be visible for this test to
            # exercise the gutter between the shell and sidebar.
            assert info_panel.styles.display != "none"
            assert shell.size.width > 0
            assert resizer.size.width > 0
            assert info_panel.size.width > 0

            # Inspect the actual composited frame via the screen's
            # compositor: the boundary column is at shell.size.width, and the
            # chop covering the gutter starts there. Any segment in that
            # chop with an ``rgb(0,0,0)`` background reproduces the visible
            # stripe.
            screen = app.screen
            compositor = screen._compositor
            chops = compositor._render_chops(compositor.size.region, lambda y: True)
            boundary_col = shell.size.width
            for y, chops_line in enumerate(chops):
                for cut, strip in chops_line.items():
                    if strip is None:
                        continue
                    if cut < boundary_col - 1 or cut > boundary_col + 1:
                        continue
                    for segment in strip:
                        bgcolor = segment.style.bgcolor if segment.style is not None else None
                        triplet = bgcolor.triplet if bgcolor is not None else None
                        if triplet is None:
                            continue
                        assert (triplet.red, triplet.green, triplet.blue) != (
                            0,
                            0,
                            0,
                        ), f"Black seam segment at y={y} cut={cut}: {segment.text!r}"

            # Also assert the per-widget rendered strips that the compositor
            # consumes are clean -- this is the layer where the bug
            # originates (StylesCache padding cells with ``inner.rich_style``
            # for a transparent background resolved to ``#000000``).
            for sibling in (shell, resizer, info_panel):
                crop = _Region(0, 0, sibling.size.width, sibling.size.height)
                strips = sibling.render_lines(crop)
                for strip in strips:
                    for segment in strip:
                        assert "on #000000" not in str(segment.style)

    asyncio.run(check_seam_transparent())


def test_tui_status_short_rows_are_padded_transparently() -> None:
    if tui.Static is None or tui.Strip is None:
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()
    vertical_class = tui._transparent_vertical_class()
    static_class = tui._transparent_static_class()

    class Stress(tui.App[None]):
        CSS = tui._tui_css()

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            with vertical_class(id="shell"):
                yield static_class(
                    tui._status_text(_configured_status_session()),
                    id="status",
                )

    async def check_status_padding() -> None:
        app = Stress()
        async with app.run_test(size=(160, 10)) as pilot:
            await pilot.pause()
            widget = app.query_one("#status")
            widths: list[int] = []
            for line_number in range(widget.size.height):
                strip = widget.render_line(line_number)
                widths.append(strip.cell_length)
                assert strip.cell_length == widget.size.width
                assert all(
                    segment.style is None or segment.style.bgcolor is None for segment in strip
                )

            assert len(set(widths)) == 1

    asyncio.run(check_status_padding())


def test_command_help_is_command_first() -> None:
    help_text = tui._command_help()

    assert "/help" in help_text
    assert "/models" in help_text
    assert "/materials" in help_text
    assert "/sessions" in help_text
    assert "/status" in help_text
    assert "/sources" not in help_text
    assert "/history" not in help_text


def test_command_help_aligns_descriptions_to_longest_command() -> None:
    help_text = tui._command_help()
    lines = [line for line in help_text.splitlines() if line.strip()]
    descriptions_by_command = {
        "/help": "Show available commands",
        "/materials": "Choose which materials are used for retrieval",
        "/vocabulary": "Practice vocabulary translations from your materials",
    }

    columns = {
        line.index(description)
        for line in lines
        for command, description in descriptions_by_command.items()
        if line.strip().startswith(command)
    }

    assert len(columns) == 1
    assert columns == {len("  /vocabulary") + 4}


def test_tui_slash_suggestion_uses_shared_registry() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/sta")

    assert suggestion == "/status "


def test_tui_slash_suggestion_uses_canonical_materials_command() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/mat")

    assert suggestion == "/materials "


def test_info_panel_shows_new_layout_and_material_names_without_session_duration() -> None:
    session = _plain_session()
    session.source_files = ("materials/exam-review.pdf", "materials/calculus.md")
    session.source_file_count = 2

    panel = tui._info_panel_default_text(session)

    lines = panel.plain.splitlines()
    assert lines[:5] == [
        f"EVIDENCE {_default_display_key('evidence')}",
        "",
        "SCOPE 2/2",
        "",
        "FILES 2",
    ]
    assert "\u2500" not in panel.plain
    assert "time" not in panel.plain
    assert "materials active" not in panel.plain
    assert "@exam-review.pdf" in panel.plain
    assert "@calculus.md" in panel.plain
    assert "☑" not in panel.plain
    assert "☐" not in panel.plain
    assert "..." not in panel.plain
    assert "model" not in panel.plain
    assert "armory" not in panel.plain


def test_info_panel_ignores_generated_session_title() -> None:
    session = _plain_session()
    session.title = (
        "Build a careful comparison of very long research goals\n"
        "that should never wrap into the Scope lines"
    )

    panel = tui._info_panel_default_text(session)
    lines = panel.plain.splitlines()

    assert lines[:6] == [
        f"EVIDENCE {_default_display_key('evidence')}",
        "",
        "SCOPE 0/0",
        "",
        "FILES 0",
        "STATE no materials",
    ]
    assert len(lines[0]) <= 38
    assert "Build a careful comparison" not in panel.plain
    assert "that should never wrap" not in panel.plain
    assert "Grounding" not in panel.plain


def test_info_panel_evidence_summarizes_evidence_without_tool_details() -> None:
    session = _plain_session()
    session.last_turn_evidence = _turn_evidence_with_sources(
        "materials/week-01-foundations.pdf",
        "materials/week-02-methods.pdf",
        "materials/week-03-results.pdf",
        total_source_count=21,
    )

    panel = tui._info_panel_default_text(session)
    lines = panel.plain.splitlines()

    assert lines[:5] == [
        f"EVIDENCE {_default_display_key('evidence')}",
        "",
        "SCOPE 3/21",
        "",
        "EXCERPTS 3",
    ]
    assert "EXCERPTS 3" in lines
    assert any(line.startswith("E1 @week-01-foundations.pdf") for line in lines)
    assert any(line.startswith("E2 @week-02-methods.pdf") for line in lines)
    assert any(line.startswith("E3 @week-03-results.pdf") for line in lines)
    assert all(not line.startswith("OPEN ") for line in lines)
    assert "tool" not in panel.plain
    assert all(len(line) <= 38 for line in lines)


def test_info_panel_evidence_has_single_overflow_summary_and_muted_sources() -> None:
    session = _plain_session()
    session.source_files = (
        *(f"materials/visible-{index}.pdf" for index in range(8)),
        "materials/hidden-evidence.pdf",
    )
    session.last_turn_evidence = _turn_evidence_with_sources(
        "materials/hidden-evidence.pdf",
        "materials/visible-1.pdf",
        "materials/result-2.pdf",
        "materials/result-3.pdf",
        "materials/result-4.pdf",
        "materials/result-5.pdf",
        "materials/result-6.pdf",
        "materials/result-7.pdf",
        "materials/result-8.pdf",
        "materials/result-9.pdf",
        total_source_count=21,
    )

    panel = tui._info_panel_default_text(session)
    lines = panel.plain.splitlines()
    palette = tui.current_palette()

    assert lines[:5] == [
        f"EVIDENCE {_default_display_key('evidence')}",
        "",
        "SCOPE 9/9",
        "",
        "EXCERPTS 10",
    ]
    assert "EVIDENCE E1 E2 E3 E4" not in lines
    assert "EVIDENCE E1 E2 E3 E4 +6" not in lines
    assert "EXCERPTS 10" in lines
    assert "MORE +6" not in lines
    assert "MORE +1" not in lines
    assert "@visible-0.pdf" not in lines
    assert _text_style_for_fragment(panel, "@visible-1.pdf") == palette.text_muted
    assert _text_style_for_fragment(panel, "@hidden-evidence.pdf") == palette.text_muted
    assert _text_style_for_fragment(panel, "E1") == palette.text_secondary


def test_info_panel_evidence_row_click_opens_source_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.Static is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/alpha.pdf", "materials/beta.pdf")
    session.last_turn_evidence = _turn_evidence_with_sources(
        "materials/alpha.pdf",
        "materials/beta.pdf",
    )
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    calls: list[str] = []
    monkeypatch.setattr(app, "_handle_external_input", calls.append)
    typed_app = cast("TextualApp[None]", app)

    async def check_evidence_click() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()

            await pilot.click("#info-panel", offset=(3, 6))
            await pilot.pause()

            assert calls == ["/evidence E2 open"]

    asyncio.run(check_evidence_click())


def test_info_panel_message_text_starts_at_sidebar_edge() -> None:
    session = _plain_session()
    entry = tui.TuiTranscriptEntry("How do I prepare for the exam?", kind="user")

    panel = tui._info_panel_message_text(entry, session)

    lines = panel.plain.splitlines()
    assert lines[0] == "You message"
    assert lines[1].startswith("\u2500")


def test_info_panel_busy_progress_is_clipped_inside_sidebar_width() -> None:
    session = _plain_session()
    panel = tui._info_panel_default_text(
        session,
        busy=True,
        progress="checking answer",
    )

    lines = panel.plain.splitlines()

    assert "EVIDENCE checking answer" in lines
    assert "tool call" not in panel.plain
    assert all(len(line) <= 38 for line in lines)


def test_turn_progress_uses_reader_facing_source_labels() -> None:
    tool_call = ToolCallEvent(
        call_id="call-1",
        name="search_materials",
        arguments={"query": "weak points"},
        display="searching materials",
    )
    tool_result = ToolResultEvent(
        call_id="call-1",
        name="search_materials",
        content="[]",
        summary="No matches.",
    )
    model_complete = NoticeEvent(
        "Read complete model response from gpt-5.4-mini: 0 tool call(s).",
        code="model_complete",
    )

    assert tui_streaming._progress_text(tool_call) == "checking sources"
    assert tui_streaming._progress_text(tool_result) == "source check complete"
    assert tui_streaming._progress_text(model_complete) == "checking answer"


def test_run_tui_turn_reports_reasoning_activity_without_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _plain_session()

    def fake_iter_chat_events(
        _session: ChatSession,
        _prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> list[object]:
        assert abort is not None
        return [
            ReasoningDeltaEvent("short summary", summary=True),
            AssistantDeltaEvent("Final reply."),
        ]

    monkeypatch.setattr(tui_streaming, "iter_chat_events", fake_iter_chat_events)
    replies: list[str] = []
    notices: list[str] = []
    errors: list[str] = []
    progress: list[str] = []
    activity: list[str] = []
    finished: list[bool] = []

    tui_streaming.run_tui_turn(
        session,
        "prompt",
        threading.Event(),
        on_reply=replies.append,
        on_notice=notices.append,
        on_error=errors.append,
        on_finish=lambda: finished.append(True),
        on_progress=progress.append,
        on_activity=activity.append,
    )

    assert replies == ["Final reply."]
    assert activity == ["    thinking summary: short summary"]
    assert progress == ["reading model thinking"]
    assert notices == []
    assert errors == []
    assert finished == [True]


def test_run_tui_turn_adds_heph_hint_for_account_setup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _plain_session()

    def fake_iter_chat_events(
        _session: ChatSession,
        _prompt: str,
        *,
        abort: threading.Event | None = None,
    ) -> list[object]:
        assert abort is not None
        raise EngineError(
            "Provider rejected the request: billing is inactive.",
            code=EngineErrorCode.ACCOUNT_SETUP,
        )

    monkeypatch.setattr(tui_streaming, "iter_chat_events", fake_iter_chat_events)
    errors: list[str] = []
    finished: list[bool] = []

    tui_streaming.run_tui_turn(
        session,
        "prompt",
        threading.Event(),
        on_reply=lambda _reply: None,
        on_notice=lambda _notice: None,
        on_error=errors.append,
        on_finish=lambda: finished.append(True),
    )

    assert errors == [
        "Provider rejected the request: billing is inactive. "
        "In Heph, use /login to update provider credentials or /models to choose another model."
    ]
    assert finished == [True]


def test_run_tui_reports_missing_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tui, "Markdown", None)

    with pytest.raises(tui.TuiDependencyError) as exc_info:
        tui.run_tui(_plain_session())

    message = str(exc_info.value)
    assert "repository root" in message
    assert "uv sync --frozen" in message
    assert "uv run --project" not in message
    assert "-m pip install -e ." in message


@pytest.mark.parametrize(
    ("pending_input", "expected_output"),
    [
        ("/help", "COMMANDS"),
        ("/status", "Model:"),
    ],
)
def test_run_tui_appends_pending_command_output_to_transcript(
    monkeypatch: pytest.MonkeyPatch,
    pending_input: str,
    expected_output: str,
) -> None:
    captured_state: tui._TuiRuntimeState | None = None
    run_count = 0

    class FakeTui:
        def __init__(
            self,
            _session: ChatSession,
            state: tui._TuiRuntimeState,
            _palette: tui.Theme,
        ) -> None:
            nonlocal captured_state
            captured_state = state

        def run(self, *, mouse: bool = True) -> None:
            nonlocal run_count
            assert mouse is True
            run_count += 1
            assert captured_state is not None
            if run_count == 1:
                captured_state.pending_input = pending_input

    def fake_save_on_exit(_session: ChatSession) -> None:
        return

    def fake_load_history(_cls: type[tui.InputHistory], _path: Path) -> tui.InputHistory:
        return tui.InputHistory()

    monkeypatch.setattr(tui, "HephTui", FakeTui)
    monkeypatch.setattr(tui, "save_on_exit", fake_save_on_exit)
    monkeypatch.setattr(tui.InputHistory, "load", classmethod(fake_load_history))

    tui.run_tui(_plain_session())

    assert captured_state is not None
    assert run_count == 2
    assert any(expected_output in entry.content for entry in captured_state.transcript)


def test_run_tui_applies_saved_theme_on_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_palette: tui.Theme | None = None

    class FakeTui:
        def __init__(
            self,
            _session: ChatSession,
            _state: tui._TuiRuntimeState,
            palette: tui.Theme,
        ) -> None:
            nonlocal captured_palette
            captured_palette = palette

        def run(self, *, mouse: bool = True) -> None:
            assert mouse is True

    def fake_save_on_exit(_session: ChatSession) -> None:
        return

    def fake_load_history(_cls: type[tui.InputHistory], _path: Path) -> tui.InputHistory:
        return tui.InputHistory()

    monkeypatch.setattr(tui, "HephTui", FakeTui)
    monkeypatch.setattr(tui, "save_on_exit", fake_save_on_exit)
    monkeypatch.setattr(tui.InputHistory, "load", classmethod(fake_load_history))
    monkeypatch.setattr(
        tui,
        "load_app_settings",
        lambda: settings_store.AppSettings(theme="light"),
    )

    try:
        set_theme("dark")
        tui.run_tui(_plain_session())
        assert captured_palette is not None
        assert captured_palette == tui.current_palette()
        assert current_theme_name() == "light"
    finally:
        set_theme("dark")


def test_run_tui_for_path_resolves_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_session: ChatSession | None = None

    def fake_resolve(path: str) -> ChatSession:
        assert path == str(tmp_path)
        return _plain_session()

    def fake_run_tui(session: ChatSession | None = None) -> None:
        nonlocal captured_session
        captured_session = session

    monkeypatch.setattr(tui, "resolve_armory_session", fake_resolve)
    monkeypatch.setattr(tui, "run_tui", fake_run_tui)

    tui.run_tui_for_path(tmp_path)

    assert captured_session is not None


def test_run_tui_for_path_passes_session_with_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """run_tui_for_path resolves the armory and passes the resulting session to run_tui."""
    resolved_session = _plain_session()

    def fake_resolve(path: str) -> ChatSession:
        assert path == str(tmp_path)
        return resolved_session

    captured_session: ChatSession | None = None

    def fake_run_tui(session: ChatSession | None = None) -> None:
        nonlocal captured_session
        captured_session = session

    monkeypatch.setattr(tui, "resolve_armory_session", fake_resolve)
    monkeypatch.setattr(tui, "run_tui", fake_run_tui)

    tui.run_tui_for_path(tmp_path)

    assert captured_session is resolved_session


def test_status_lines_shows_armory_name() -> None:
    """Status bar text includes the armory name when session has one."""
    session = _plain_session()
    session.armory_path = Path("/tmp/Sample-Armory")

    status = tui._status_lines(session)

    assert "ARMORY Sample-Armory" in status


def test_status_lines_preserves_actual_armory_name_casing(tmp_path: Path) -> None:
    session = _plain_session()
    actual_armory = tmp_path / "MixedCase-2"
    actual_armory.mkdir()
    session.armory_path = tmp_path / "mixedcase-2"

    status = tui._status_lines(session)

    assert "ARMORY MixedCase-2" in status
    assert "ARMORY mixedcase-2" not in status


def test_status_lines_preserves_long_armory_name_before_model() -> None:
    session = _plain_session()
    session.armory_path = Path("/tmp/heph-qa-status/nested/folder/very-long-armory-name")

    status = tui._status_lines(session, width=40)

    assert "ARMORY very-long-armory-name" in status
    assert "MODEL test-model" in status
    assert "REASONING" not in status
    assert " mode " not in status


def test_status_lines_preserves_armory_name_before_optional_cost() -> None:
    session = _plain_session()
    session.armory_path = Path("/tmp/heph-qa-status/nested/folder/very-long-armory-name")
    session.config.apply_provider_reference("openai-codex", "OPENAI_CODEX_OAUTH_TOKEN")
    session.live_cost_visible = True
    session.usage.estimate_from_chars(400, 80, session.config.model)

    status = tui._status_lines(session, width=50)

    assert "ARMORY very-long-armory-name" in status
    assert "MODEL test-model" in status
    assert "COST" not in status


def test_status_text_preserves_armory_when_reasoning_is_omitted() -> None:
    session = _plain_session()
    session.armory_path = Path("/tmp/heph-qa-status/nested/folder/very-long-armory-name")

    status = tui._status_text(session, width=40)

    assert "ARMORY very-long-armory-name" in status.plain
    assert "MODEL test-model" in status.plain
    assert "REASONING low" not in status.plain


def test_status_text_handles_label_words_inside_values() -> None:
    session = _plain_session()
    session.armory_path = Path("/tmp/heph-qa-status/nested/folder/very-long-armory-name")
    session.config.model = "foo ARMORY bar"

    status = tui._status_text(session, width=52)

    assert "ARMORY" in status.plain.split("MODEL", maxsplit=1)[0]
    assert "MODEL foo ARMORY bar" in status.plain


def test_status_lines_shows_none_when_no_armory() -> None:
    """Status bar shows 'none' for armory when no armory is attached."""
    session = _plain_session()

    status = tui._status_lines(session)

    assert "ARMORY none" in status


def test_create_startup_session_applies_live_usage_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_store.save_setting("thinking_visibility", "all")
    settings_store.save_setting("live_tokens_visible", True)
    settings_store.save_setting("live_cost_visible", True)
    monkeypatch.setattr(
        "interfaces.tui.session_actions.discover_startup_armory",
        lambda: None,
    )
    monkeypatch.setattr(
        "interfaces.tui.session_actions.discover_available_armories",
        list,
    )

    session = tui.create_startup_session(
        ChatConfig(base_url="https://example.test", model="test-model")
    )

    assert session.live_tokens_visible is True
    assert session.live_cost_visible is True
    assert session.config.thinking_visibility == "all"


def test_tui_new_chat_applies_live_usage_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)
    settings_store.save_setting("thinking_visibility", "minimal")
    settings_store.save_setting("live_tokens_visible", True)
    settings_store.save_setting("live_cost_visible", True)
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_new_chat_settings() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._handle_new()

            assert app.session.live_tokens_visible is True
            assert app.session.live_cost_visible is True
            assert app.session.config.thinking_visibility == "minimal"

    asyncio.run(check_new_chat_settings())


def test_status_lines_omits_removed_practice_mode() -> None:
    session = _plain_session()

    status = tui._status_lines(session)

    assert " mode " not in status


def test_status_text_omits_removed_practice_mode() -> None:
    session = _plain_session()

    status = tui._status_text(session)

    assert " mode " not in status.plain
    assert "autopilot" not in status.plain


def test_status_text_styles_live_usage_labels() -> None:
    session = _plain_session()
    session.live_tokens_visible = True
    session.live_cost_visible = True
    palette = tui.current_palette()

    status = tui._status_text(session)

    for label in ("TOKENS", "COST"):
        start = status.plain.index(label)
        end = start + len(label)
        styles = [
            str(span.style) for span in status.spans if span.start <= start and span.end >= end
        ]
        assert styles == [palette.text_secondary]


def test_live_token_status_ignores_draft_until_usage_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setattr(
        "interfaces.tui.composer_controls.prefetch_provider_model_catalogs",
        lambda _config, **_kwargs: None,
    )
    session = _plain_session()
    session.live_tokens_visible = True
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_live_token_status() -> None:
        async with typed_app.run_test(size=(120, 24)):
            composer = app.query_one("#composer", tui.Input)
            status = app.query_one("#status", tui.Static)
            initial = str(status.content)

            composer.value = "This draft should be counted in the live token estimate."
            app._refresh_live_token_status(composer.value)

            expected = tui._status_text(
                session,
                draft=composer.value,
                width=tui_display_text.status_render_width(status.size.width),
            ).plain
            assert str(status.content) == expected

            session.usage.record(
                TokenUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
                session.config.model,
            )
            app._refresh_live_token_status(composer.value)

            assert str(status.content) != initial
            assert "TOKENS ↑100 ↓20" in str(status.content)

    asyncio.run(check_live_token_status())


def test_run_tui_for_path_none_delegates_to_run_tui(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_tui_for_path(None) calls run_tui() which creates a default session."""
    called = False

    def fake_run_tui(session: ChatSession | None = None) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(tui, "run_tui", fake_run_tui)

    tui.run_tui_for_path(None)

    assert called


def test_is_armory_command_matches_inline_forms() -> None:
    assert tui._is_armory_command("/armory")
    assert tui._is_armory_command("/armory open")
    assert tui._is_armory_command("/armory create")
    assert tui._is_armory_command("/armory detach")
    assert tui._is_armory_command("  /armory  ")
    assert tui._is_armory_command("/ARMORY OPEN")

    assert not tui._is_armory_command("/model")
    assert not tui._is_armory_command("hello")


@pytest.mark.parametrize(
    ("value", "route"),
    [
        ("", tui._TuiInputRoute.EMPTY),
        ("   ", tui._TuiInputRoute.EMPTY),
        ("hello", tui._TuiInputRoute.CHAT),
        ("/models", tui._TuiInputRoute.EXTERNAL),
        ("/models openai", tui._TuiInputRoute.EXTERNAL),
        ("/sources", tui._TuiInputRoute.EXTERNAL),
        ("/sources notes", tui._TuiInputRoute.EXTERNAL),
        ("/materials", tui._TuiInputRoute.MATERIALS),
        ("/materials notes", tui._TuiInputRoute.MATERIALS),
        ("/keymap", tui._TuiInputRoute.KEYMAP),
        ("/keymap all", tui._TuiInputRoute.KEYMAP),
        ("/sessions", tui._TuiInputRoute.SESSIONS),
        ("/sessions list", tui._TuiInputRoute.SESSIONS),
        ("/turn", tui._TuiInputRoute.TURN),
        ("/turn T1", tui._TuiInputRoute.TURN),
        ("/history browse", tui._TuiInputRoute.EXTERNAL),
        ("/history stats", tui._TuiInputRoute.EXTERNAL),
        ("/new", tui._TuiInputRoute.NEW),
        ("/detach", tui._TuiInputRoute.DETACH),
        ("/armory", tui._TuiInputRoute.ARMORY),
        ("/armory open", tui._TuiInputRoute.ARMORY),
        ("/tokens", tui._TuiInputRoute.LIVE_TOKENS),
        ("/tokens show", tui._TuiInputRoute.LIVE_TOKENS),
        ("/cost", tui._TuiInputRoute.LIVE_COST),
        ("/cost show", tui._TuiInputRoute.LIVE_COST),
        ("/thinking", tui._TuiInputRoute.THINKING_VISIBILITY),
        ("/thinking all", tui._TuiInputRoute.THINKING_VISIBILITY),
        ("/reasoning", tui._TuiInputRoute.THINKING_VISIBILITY),
        ("/help", tui._TuiInputRoute.HELP),
        ("!echo hi", tui._TuiInputRoute.CHAT),
    ],
)
def test_tui_input_route_classifies_submissions(
    value: str,
    route: tui._TuiInputRoute,
) -> None:
    assert tui._tui_input_route(value) == route


def test_pending_terminal_commands_are_registered() -> None:
    registered = {
        token
        for cmd in heph_commands.get_registry().commands
        for token in (cmd.name, *cmd.aliases)
    }

    assert registered >= tui._TERMINAL_INTERACTIVE_COMMANDS


def test_tui_input_route_covers_visible_command_suggestions() -> None:
    routes = {
        f"/{suggestion.name}": tui._tui_input_route(f"/{suggestion.name}")
        for suggestion in tui._tui_command_suggestions()
    }

    assert routes["/models"] is tui._TuiInputRoute.EXTERNAL
    assert routes["/cost"] is tui._TuiInputRoute.LIVE_COST
    assert "/sources" not in routes
    assert "/history" not in routes
    assert "/tokens" not in routes
    assert "/thinking" not in routes
    assert "/reasoning" not in routes
    assert routes["/materials"] is tui._TuiInputRoute.MATERIALS
    assert routes["/keymap"] is tui._TuiInputRoute.KEYMAP
    assert routes["/sessions"] is tui._TuiInputRoute.SESSIONS
    assert routes["/turn"] is tui._TuiInputRoute.TURN
    assert routes["/local"] is tui._TuiInputRoute.LOCAL
    assert routes["/new"] is tui._TuiInputRoute.NEW
    assert routes["/detach"] is tui._TuiInputRoute.DETACH
    assert routes["/armory"] is tui._TuiInputRoute.ARMORY
    assert all(
        route is tui._TuiInputRoute.EXTERNAL
        for command, route in routes.items()
        if command
        not in {
            "/materials",
            "/keymap",
            "/sessions",
            "/turn",
            "/local",
            "/new",
            "/detach",
            "/armory",
            "/cost",
            "/help",
        }
    )


@pytest.mark.parametrize(
    ("value", "selected_label", "expected_notice", "expected_value"),
    [
        ("/tokens", "Live tokens", "Live tokens shown.", "shown"),
        ("/tokens hidden", "Live tokens", "Live tokens hidden.", "hidden"),
        ("/cost", "Live cost", "Live cost shown.", "shown"),
        ("/cost hidden", "Live cost", "Live cost hidden.", "hidden"),
        ("/thinking", "Model thinking", "Model thinking: All.", "all"),
        ("/thinking hidden", "Model thinking", "Model thinking: Hidden.", "off"),
        ("/reasoning", "Model thinking", "Model thinking: All.", "all"),
    ],
)
def test_display_setting_input_cycles_settings_without_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: str,
    selected_label: str,
    expected_notice: str,
    expected_value: str,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_route() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = value
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.name == "settings"
            assert app._inline_flow.step == "menu"
            assert app.state.history == []
            suggestions = app.query_one("#suggestions", tui.OptionList)
            labels = [label for label, _description in app._inline_flow.options]
            assert suggestions.highlighted == labels.index(selected_label)
            assert app.state.transcript[-1].kind == "notice"
            assert app.state.transcript[-1].content == expected_notice
            settings = settings_store.load_app_settings()
            if selected_label == "Live tokens":
                assert settings.live_tokens_visible is (expected_value == "shown")
            elif selected_label == "Live cost":
                assert settings.live_cost_visible is (expected_value == "shown")
            else:
                assert settings.thinking_visibility == expected_value

    asyncio.run(check_settings_route())


def test_armory_command_flow_validates_supported_subcommands() -> None:
    assert tui._armory_command_flow("/armory") == "manage"
    assert tui._armory_command_flow("/armory menu") == "manage"
    assert tui._armory_command_flow("/armory open") == "open"
    assert tui._armory_command_flow("/armory create") == "create"
    assert tui._armory_command_flow("/armory new") == "create"

    assert tui._armory_command_flow("/armory detach") is None


def test_armory_browser_entries_include_recent_and_missing_armories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    existing = armory_home / "exam-prep"
    initialize(existing)
    missing = armory_home / "missing"
    monkeypatch.setattr(
        "interfaces.tui.armory_browser.load_remembered_armory_entries",
        lambda: [
            ArmoryEntry(existing, exists=True, valid=True),
            ArmoryEntry(missing, exists=False, valid=False),
        ],
    )

    entries = build_entries(allow_create=True)
    recent_labels = [entry.label for entry in entries if entry.is_recent]

    assert len(recent_labels) == 1
    assert "exam-prep" in recent_labels[0]
    assert "recent  " not in recent_labels[0]


def test_armory_browser_detail_describes_material_layout(tmp_path: Path) -> None:
    armory = tmp_path / "exam-prep"
    initialize(armory)
    (armory / "materials" / "exam.md").write_text("# Exam\n", encoding="utf-8")

    detail = armory_detail(armory)

    assert "STATE valid" in detail
    assert "FILES 1" in detail
    assert "MATERIALS materials/" in detail
    assert "STATE DIR .harness/" in detail


def test_default_shortcut_opens_command_palette() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_command_palette() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press(_default_binding("command_palette"))
            await pilot.pause()
            composer = app.query_one("#composer", tui.Input)
            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),
            )  # ty:ignore[redundant-cast]

            assert composer.value == "/"
            assert composer.cursor_position == 1
            assert suggestions.has_class("visible")
            assert app.completion_candidates

    asyncio.run(check_command_palette())


def test_default_shortcut_opens_materials_inline() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/calculus.md",)
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_materials_shortcut() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press(_default_binding("open_materials"))
            await pilot.pause()
            composer = app.query_one("#composer", tui.Input)

            assert app._materials_inline_active is True
            assert composer.placeholder == "FILTER materials"
            assert getattr(app.focused, "id", None) == "materials-list"

    asyncio.run(check_materials_shortcut())


def test_settings_inline_menu_exposes_privacy_and_appearance() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_menu() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()
            labels = [label for label, _description in app._inline_flow.options]

            assert app._inline_flow.name == "settings"
            assert app._inline_flow.step == "menu"
            assert "Privacy & Diagnostics" in labels
            assert "Appearance" in labels
            assert "Activity trace" in labels
            assert "Model thinking" in labels
            assert "Live tokens" in labels
            assert "Live cost" in labels
            assert "Vocabulary practice" in labels
            assert "Login" in labels
            assert "Logout" in labels

    asyncio.run(check_settings_menu())


def test_settings_inline_privacy_submenu_exposes_and_toggles_telemetry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_submenus() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()
            app._handle_inline_menu_choice("Privacy & Diagnostics")
            privacy_labels = [label for label, _description in app._inline_flow.options]

            assert app._inline_flow.step == "privacy"
            assert "Usage analytics" in privacy_labels
            assert "Crash reports" in privacy_labels
            assert "Back" not in privacy_labels

            app._submit_inline_flow("Usage analytics")

            assert settings_store.load_app_settings().analytics_enabled is True
            assert app._inline_flow.step == "privacy"

    asyncio.run(check_settings_submenus())


def test_settings_inline_escape_returns_from_privacy_submenu() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_escape_back_navigation() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_settings_flow()
            app._handle_inline_menu_choice("Privacy & Diagnostics")

            await pilot.press("escape")

            assert app._inline_flow.active is True
            assert app._inline_flow.name == "settings"
            assert app._inline_flow.step == "menu"
            labels = [label for label, _description in app._inline_flow.options]
            suggestions = app.query_one("#suggestions", tui.OptionList)
            assert suggestions.highlighted == labels.index("Privacy & Diagnostics")

            await pilot.press("escape")

            assert app._inline_flow.active is False

    asyncio.run(check_escape_back_navigation())


def test_settings_inline_cycles_display_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_changes() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()
            descriptions = dict(app._inline_flow.options)

            assert descriptions["Appearance"] == "theme: Dark"
            assert descriptions["Activity trace"] == "Minimal tool calls"
            assert descriptions["Model thinking"] == "Minimal"
            assert descriptions["Live tokens"] == "hidden"
            assert descriptions["Live cost"] == "hidden"
            assert descriptions["Vocabulary practice"] == "Strict"

            app._submit_inline_flow("Appearance")

            assert settings_store.load_app_settings().theme == "light"
            assert tui.current_palette().text_primary in app.CSS
            assert [entry.content for entry in app.state.transcript if entry.kind == "notice"] == [
                "Light theme."
            ]
            assert app._inline_flow.step == "menu"
            assert dict(app._inline_flow.options)["Appearance"] == "theme: Light"

            app._submit_inline_flow("Appearance")

            assert settings_store.load_app_settings().theme == "dark"
            assert [entry.content for entry in app.state.transcript if entry.kind == "notice"] == [
                "Dark theme."
            ]

            app._submit_inline_flow("Activity trace")

            assert settings_store.load_app_settings().activity_trace_mode == (
                settings_store.ACTIVITY_TRACE_TOOL_CALLS
            )
            assert dict(app._inline_flow.options)["Activity trace"] == "All tool calls"

            app._submit_inline_flow("Activity trace")

            assert settings_store.load_app_settings().activity_trace_mode == (
                settings_store.ACTIVITY_TRACE_HIDDEN_TOOL_CALLS
            )
            assert dict(app._inline_flow.options)["Activity trace"] == "Hidden tool calls"

            app._submit_inline_flow("Model thinking")

            assert settings_store.load_app_settings().thinking_visibility == "all"
            assert app.session.config.thinking_visibility == "all"
            assert dict(app._inline_flow.options)["Model thinking"] == "All"

            app._submit_inline_flow("Model thinking")

            assert settings_store.load_app_settings().thinking_visibility == "off"
            assert app.session.config.thinking_visibility == "off"
            assert dict(app._inline_flow.options)["Model thinking"] == "Hidden"

            app._submit_inline_flow("Live tokens")

            assert settings_store.load_app_settings().live_tokens_visible is True
            assert app.session.live_tokens_visible is True
            assert "TOKENS 0" in str(app.query_one("#status", tui.Static).content)
            assert app.state.transcript[-1].content == "Live tokens shown."

            app._submit_inline_flow("Live cost")

            assert settings_store.load_app_settings().live_cost_visible is True
            assert app.session.live_cost_visible is True
            assert "COST $0.000" in str(app.query_one("#status", tui.Static).content)
            assert app.state.transcript[-1].content == "Live cost shown."

            app._submit_inline_flow("Vocabulary practice")

            assert settings_store.load_app_settings().vocab_strictness == (
                settings_store.VOCAB_STRICTNESS_LENIENT
            )
            assert dict(app._inline_flow.options)["Vocabulary practice"] == "Lenient punctuation"

            labels = [label for label, _description in app._inline_flow.options]
            suggestions = app.query_one("#suggestions", tui.OptionList)
            assert suggestions.highlighted == labels.index("Vocabulary practice")

    try:
        asyncio.run(check_settings_changes())
    finally:
        set_theme("dark")


@pytest.mark.parametrize(
    ("setting", "session_attr", "settings_attr", "status_label", "expected_notice"),
    [
        (
            "Live tokens",
            "live_tokens_visible",
            "live_tokens_visible",
            "TOKENS ",
            "Live tokens hidden.",
        ),
        (
            "Live cost",
            "live_cost_visible",
            "live_cost_visible",
            "COST ",
            "Live cost hidden.",
        ),
    ],
)
def test_settings_live_usage_replaces_notice_and_marks_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    setting: str,
    session_attr: str,
    settings_attr: str,
    status_label: str,
    expected_notice: str,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_live_usage_notice() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()
            app._submit_inline_flow(setting)
            app._submit_inline_flow(setting)

            notices = [entry.content for entry in app.state.transcript if entry.kind == "notice"]
            descriptions = dict(app._inline_flow.options)

            assert notices == [expected_notice]
            assert getattr(app.session, session_attr) is False
            assert getattr(settings_store.load_app_settings(), settings_attr) is False
            assert descriptions[setting] == "hidden"
            assert status_label not in str(app.query_one("#status", tui.Static).content)

    asyncio.run(check_live_usage_notice())


def test_login_inline_menu_aligns_descriptions_after_filter_reset() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_login_columns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_login_flow()
            await pilot.pause()

            columns = _inline_description_columns(app)
            assert columns
            assert len(set(columns)) == 1

            composer = app.query_one("#composer", tui.Input)
            composer.value = "z"
            app._filter_inline_menu_options(composer.value)
            await pilot.pause()
            assert [label for label, _description in app._inline_flow.options] == ["Z.AI"]

            composer.value = ""
            app._filter_inline_menu_options("")
            await pilot.pause()

            columns = _inline_description_columns(app)
            assert len(set(columns)) == 1
            suggestions = app.query_one("#suggestions", tui.OptionList)
            first_prompt = _option_prompt_plain(suggestions, 0)
            assert columns[0] == first_prompt.index("ACCOUNT")

    asyncio.run(check_login_columns())


def test_models_inline_menu_aligns_descriptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    choices = [
        ("pollinations", "openai", "Pollinations", True),
        ("zai", "glm-5-air", "Z.AI", False),
        ("openrouter", "qwen/qwen3.6-plus:free", "OpenRouter", True),
    ]

    def fake_model_choices(
        _config: ProviderConfig,
        *,
        refresh_live: bool = False,
    ) -> list[tuple[str, str, str, bool]]:
        del refresh_live
        return choices

    monkeypatch.setattr(
        "interfaces.tui.model_flows.configured_model_choices",
        fake_model_choices,
    )
    app = tui.HephTui(
        _keyless_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    monkeypatch.setattr(app, "_refresh_models_flow_worker", lambda: None)
    typed_app = cast("TextualApp[None]", app)

    async def check_model_columns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_models_flow()
            await pilot.pause()

            columns = _inline_description_columns(app)
            assert columns
            assert len(set(columns)) == 1
            assert columns[0] == len("→ qwen/qwen3.6-plus:free") + 4

    asyncio.run(check_model_columns())


def test_inline_menu_description_column_tracks_visible_rows_while_scrolling() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scrolled_columns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_inline_menu(
                name="test",
                step="menu",
                title="Choose",
                options=[
                    ("extra-wide-visible-first", "first option"),
                    ("aa", "second option"),
                    ("bb", "third option"),
                    ("cc", "fourth option"),
                    ("dd", "fifth option"),
                    ("ee", "sixth option"),
                    ("ff", "seventh option"),
                    ("gg", "eighth option"),
                ],
            )
            await pilot.pause()

            columns = _inline_description_columns(app)
            assert len(set(columns[:7])) == 1
            assert columns[0] == len("→ extra-wide-visible-first") + 4

            app._move_completion(7)
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            assert suggestions.scroll_y == 1
            columns = _inline_description_columns(app)
            assert len(set(columns[1:])) == 1
            assert columns[1] == len("  aa") + 4

    asyncio.run(check_scrolled_columns())


def test_settings_inline_keeps_selected_row_after_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_stable_selection() -> None:
        async with typed_app.run_test(size=(120, 24)):
            cases = [
                "Appearance",
                "Activity trace",
                "Model thinking",
                "Live tokens",
                "Live cost",
                "Vocabulary practice",
            ]
            for setting in cases:
                app._open_settings_flow()
                before = list(app._inline_flow.options)

                app._submit_inline_flow(setting)

                after = list(app._inline_flow.options)
                labels = [label for label, _description in after]
                suggestions = app.query_one("#suggestions", tui.OptionList)
                assert [label for label, _description in before] == labels
                assert suggestions.highlighted == labels.index(setting)

            app._open_settings_flow()
            app._submit_inline_flow("Privacy & Diagnostics")
            before = list(app._inline_flow.options)

            app._submit_inline_flow("Crash reports")

            after = list(app._inline_flow.options)
            labels = [label for label, _description in after]
            suggestions = app.query_one("#suggestions", tui.OptionList)
            assert [label for label, _description in before] == labels
            assert suggestions.highlighted == labels.index("Crash reports")

    try:
        asyncio.run(check_stable_selection())
    finally:
        set_theme("dark")


def test_logout_inline_menu_lists_only_clearable_stored_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    _clear_credential_env(monkeypatch)
    monkeypatch.setenv("HARNESS_API_KEY", "sk-global")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-env")
    monkeypatch.setattr(ProviderConfig, "load", classmethod(lambda _cls: default_config()))
    monkeypatch.setattr(
        "interfaces.tui.auth_flows.list_providers",
        lambda: ["openai-codex"],
    )

    def fake_retrieve_key(slug: str) -> str | None:
        return "sk-keychain" if slug == "openai" else None

    def fake_get_volatile(slug: str) -> str | None:
        return "sk-session" if slug == "zai" else None

    monkeypatch.setattr("interfaces.tui.auth_flows.retrieve_key", fake_retrieve_key)
    monkeypatch.setattr("interfaces.tui.auth_flows.get_volatile", fake_get_volatile)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_logout_menu() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_logout_flow()

            labels = [label for label, _description in app._inline_flow.options]
            descriptions = dict(app._inline_flow.options)

            assert labels == [
                "CODEX ACCOUNT",
                "OPENAI KEY",
                "Z.AI KEY",
                "ALL",
            ]
            assert descriptions["CODEX ACCOUNT"] == "STATE configured"
            assert descriptions["OPENAI KEY"] == "STATE configured"
            assert descriptions["Z.AI KEY"] == "STATE configured"
            assert descriptions["ALL"] == "ACTION clear shown"
            assert "Pollinations" not in " ".join(labels)
            assert all(len(label) <= 22 for label in labels)
            rendered_rows = [
                f"{label:<22} {description}" for label, description in app._inline_flow.options
            ]
            configured_columns = [
                row.index("configured") for row in rendered_rows if "configured" in row
            ]
            assert len(set(configured_columns)) == 1
            assert any(
                "HARNESS_API_KEY global override" in entry.content
                for entry in app.state.transcript
            )
            assert any(
                "OpenRouter (OPENROUTER_API_KEY)" in entry.content
                for entry in app.state.transcript
            )

    asyncio.run(check_logout_menu())


def test_logout_inline_names_environment_credentials_when_none_clearable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    _clear_credential_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setattr(ProviderConfig, "load", classmethod(lambda _cls: default_config()))
    monkeypatch.setattr("interfaces.tui.auth_flows.list_providers", list)
    monkeypatch.setattr("interfaces.tui.auth_flows.retrieve_key", lambda _slug: None)
    monkeypatch.setattr("interfaces.tui.auth_flows.get_volatile", lambda _slug: None)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_logout_notice() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_logout_flow()

            assert app._inline_flow.active is False
            assert any(
                "Environment credentials cannot be cleared inside Heph" in entry.content
                for entry in app.state.transcript
            )
            assert any(
                "OpenAI API (OPENAI_API_KEY)" in entry.content for entry in app.state.transcript
            )

    asyncio.run(check_logout_notice())


def test_logout_inline_clears_selected_credential_kind_for_duplicate_slug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    _clear_credential_env(monkeypatch)
    monkeypatch.setattr(ProviderConfig, "load", classmethod(lambda _cls: default_config()))
    monkeypatch.setattr(
        "interfaces.tui.auth_flows.list_providers",
        lambda: ["openai-codex"],
    )
    monkeypatch.setattr(
        "interfaces.tui.auth_flows.retrieve_key",
        lambda slug: "sk-keychain" if slug == "openai-codex" else None,
    )
    monkeypatch.setattr("interfaces.tui.auth_flows.get_volatile", lambda _slug: None)
    cleared_oauth: list[str] = []
    cleared_keys: list[str] = []
    monkeypatch.setattr(
        "interfaces.tui.auth_flows.clear_credentials",
        cleared_oauth.append,
    )
    monkeypatch.setattr("interfaces.tui.auth_flows.clear_key", cleared_keys.append)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_selected_kind() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_logout_flow()

            labels = [label for label, _description in app._inline_flow.options]
            assert "CODEX ACCOUNT" in labels
            assert "CODEX KEY" in labels

            app._submit_inline_flow("CODEX KEY")

            assert cleared_keys == ["openai-codex"]
            assert cleared_oauth == []

    asyncio.run(check_selected_kind())


def test_armory_home_text_omits_available_armory_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("interfaces.tui.display_text.armory_shortcut_key", lambda: "ctrl+a")

    text = tui_display_text.armory_home_text()

    assert "No armory attached." not in text
    assert "What document" not in text
    assert "Available armories:" not in text
    assert "ctrl+a" in text
    assert "OPEN exact armory name" in text
    assert "materials/" in text
    assert "linear-algebra" not in text
    assert "algorithms" not in text
    assert "/linear-algebra" not in text
    assert max(len(line) for line in text.splitlines()) <= 40


def test_armory_home_text_uses_runtime_keymap() -> None:
    runtime = keymap.default_runtime_keymap()
    runtime.bindings["open_armory_home"] = ("ctrl+y",)

    text = tui_display_text.armory_home_text(runtime)

    assert "ctrl+y" in text
    assert "ctrl+a" not in text


def test_startup_copy_stays_readable_in_narrow_panes() -> None:
    startup_text = tui._startup_card_text()
    startup_lines = startup_text.splitlines()

    assert "materials/" in startup_text
    assert "ARMORY exact names or paths" in startup_text
    assert startup_lines[0] == "MATERIALS materials/"
    assert startup_lines[1] == "ARMORY exact names or paths"
    assert startup_lines[6] == ""
    assert startup_lines[7] == "VERIFY important claims"
    assert max(len(line) for line in startup_lines) <= 39


def test_tui_launch_does_not_append_startup_copy_to_transcript() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    state = tui._TuiRuntimeState(
        armory_home_shown=True,
        history_obj=tui.InputHistory(),
    )
    app = tui.HephTui(
        _plain_session(),
        state,
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_no_startup_copy() -> None:
        async with typed_app.run_test(size=(120, 24)):
            assert state.transcript == []

    asyncio.run(check_no_startup_copy())


def test_plain_tui_shows_armory_home_notice() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_home_notice() -> None:
        async with typed_app.run_test(size=(120, 24)):
            assert app.state.armory_home_shown is True
            assert not any("No armory attached" in entry.content for entry in app.state.transcript)
            assert any("materials/" in entry.content for entry in app.state.transcript)
            assert any(
                _default_display_key("open_armory_home") in entry.content
                for entry in app.state.transcript
            )

    asyncio.run(check_home_notice())


def test_plain_tui_shows_start_home_without_auto_opening_armory_menu(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    armory = armory_home / "known"
    initialize(armory)
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    remember_armory(armory)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_armory_menu() -> None:
        async with typed_app.run_test(size=(120, 24)):
            assert app.state.armory_home_shown is True
            assert app._armory_inline_active is False
            assert not any("No armory attached" in entry.content for entry in app.state.transcript)
            assert any("OPEN exact armory name" in entry.content for entry in app.state.transcript)
            assert not any("Available armories" in entry.content for entry in app.state.transcript)
            assert not any("known" in entry.content for entry in app.state.transcript)

    asyncio.run(check_armory_menu())


def test_plain_tui_no_armory_question_requires_model_configuration() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app.session.source_files = ("materials/enabled.pdf",)
    app.session.config.base_url = ""
    app.session.config.model = ""
    typed_app = cast("TextualApp[None]", app)

    async def check_model_configuration() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "What is 2+2?"
            await pilot.press("enter")
            await pilot.pause()

            assert app.busy is False
            assert any(
                "No model source configured" in entry.content for entry in app.state.transcript
            )

    asyncio.run(check_model_configuration())


def test_handle_armory_browser_invalid_subcommand_shows_usage() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_invalid_usage() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._handle_armory_browser("/armory detach")
            assert any("Usage: /armory" in entry.content for entry in app.state.transcript)
            composer = app.query_one("#composer", tui.Input)
            assert app.focused is composer

    asyncio.run(check_invalid_usage())


def test_armory_input_executes_without_user_transcript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def fake_handle_armory_browser(value: str) -> None:
        assert value == "/armory"
        app._append_notice("opened armory browser")

    async def check_inline_command() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "_handle_armory_browser", fake_handle_armory_browser)
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/armory"
            await pilot.press("enter")
            await pilot.pause()
            assert not any("You:" in entry.content for entry in app.state.transcript)
            assert any("opened armory browser" in entry.content for entry in app.state.transcript)

    asyncio.run(check_inline_command())


def test_plain_tui_opens_named_armory_without_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "module-2"
    initialize(armory_path)
    (armory_path / "materials" / "notes.md").write_text("grounded notes", encoding="utf-8")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_named_armory() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "module-2"
            await pilot.press("enter")
            await pilot.pause()

            assert app.session.armory_path == armory_path.resolve()
            assert app.session.source_file_count == 1
            assert app.busy is False
            assert any(entry.content == "Using armory module-2" for entry in app.state.transcript)

    asyncio.run(check_named_armory())


def test_plain_tui_opens_armory_named_detach_instead_of_detaching(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "detach"
    initialize(armory_path)
    (armory_path / "materials" / "notes.md").write_text("grounded notes", encoding="utf-8")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_named_detach_armory() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "detach"
            await pilot.press("enter")
            await pilot.pause()

            assert app.session.armory_path == armory_path.resolve()
            assert any("Using armory" in entry.content for entry in app.state.transcript)
            assert not any("Armory detached" in entry.content for entry in app.state.transcript)

    asyncio.run(check_named_detach_armory())


def test_busy_plain_tui_keeps_named_armory_input_as_steering(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "module-2"
    initialize(armory_path)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_busy_named_armory() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            _mark_active_turn(app)
            composer = app.query_one("#composer", tui.Input)
            composer.value = "module-2"
            await pilot.press("enter")
            await pilot.pause()

            assert app.session.armory_path is None
            assert app.session.steering.drain() == ["module-2"]
            assert any(
                "Steering queued: module-2" in entry.content for entry in app.state.transcript
            )
            assert not any("Using armory" in entry.content for entry in app.state.transcript)

    asyncio.run(check_busy_named_armory())


def test_detach_command_returns_to_plain_tui(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "module"
    initialize(armory_path)
    (armory_path / "materials" / "notes.md").write_text("grounded notes", encoding="utf-8")
    session = _plain_session()
    session.armory_path = armory_path
    session.source_file_count = 1

    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_detach() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/detach"
            await pilot.press("enter")
            await pilot.pause()

            assert app.session.armory_path is None
            assert app.busy is False
            assert any("Armory detached" in entry.content for entry in app.state.transcript)
            assert any("OPEN exact armory name" in entry.content for entry in app.state.transcript)

    asyncio.run(check_detach())


def test_bare_detach_returns_attached_tui_to_plain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "module"
    initialize(armory_path)
    session = _plain_session()
    session.armory_path = armory_path

    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_bare_detach() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "detach"
            await pilot.press("enter")
            await pilot.pause()

            assert app.session.armory_path is None
            assert app.busy is False
            assert any("Armory detached" in entry.content for entry in app.state.transcript)

    asyncio.run(check_bare_detach())


def test_armory_reference_resolver_stays_inside_armory_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    armory_home = tmp_path / ".armories"
    outside_home = tmp_path / "outside"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    inside = armory_home / "inside"
    outside = outside_home / "outside"
    initialize(inside)
    initialize(outside)

    assert tui_armory._resolve_armory_reference("inside") == inside.resolve()
    assert tui_armory._resolve_armory_reference(str(outside)) is None
    assert tui_armory._resolve_armory_reference("../outside/outside") is None
    assert tui_armory._resolve_armory_reference("what is inside?") is None


def test_sessions_command_lists_saved_sessions_inline(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    armory = tmp_path / "module"
    initialize(armory)
    saved_session = _plain_session()
    saved_session.session_id = "abc123"
    saved_session.armory_path = armory
    saved_session.conversation.add("user", "What did I review?")
    save_session(saved_session)

    session = _plain_session()
    session.armory_path = armory
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sessions_listing() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/sessions list"
            await pilot.press("enter")
            await pilot.pause()

            assert any("SESSIONS 1" in entry.content for entry in app.state.transcript)
            assert any("SESSION abc123" in entry.content for entry in app.state.transcript)
            assert any(
                "TITLE What did I review?" in entry.content for entry in app.state.transcript
            )
            assert app.state.pending_input is None

    asyncio.run(check_sessions_listing())


def test_sessions_command_defaults_to_filtered_resume_menu(tmp_path: Path) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    armory = tmp_path / "module"
    initialize(armory)
    first_conversation = Conversation()
    first_conversation.add("user", "What did I review?")
    first_conversation.add("assistant", "You reviewed modal logic.")
    chat_storage.save(armory, "logic123", first_conversation, title="Modal logic recap")
    second_conversation = Conversation()
    second_conversation.add("user", "What about calculus?")
    chat_storage.save(armory, "calc456", second_conversation, title="Calculus notes")

    session = _plain_session()
    session.armory_path = armory
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sessions_menu() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/sessions"
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.name == "sessions"
            assert app._inline_flow.all_options
            composer.value = "logic"
            await pilot.pause()

            session_labels = [label for label, _description in app._inline_flow.options]
            assert session_labels == ["logic123"]

            await pilot.press("enter")
            await pilot.pause()

            assert app.session.session_id == "logic123"
            assert any("modal logic" in entry.content for entry in app.state.transcript)
            assert any(
                "resumed session logic123" in entry.content for entry in app.state.transcript
            )

    asyncio.run(check_sessions_menu())


def test_sessions_menu_legacy_newline_titles_do_not_wrap_or_trap_highlight(
    tmp_path: Path,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    armory = tmp_path / "module"
    initialize(armory)
    chats = armory / ".harness" / "chats"
    chats.mkdir(parents=True, exist_ok=True)
    for index in range(6):
        session_id = f"legacy{index}"
        title = "hey\n\n\nfwafawf\n\n\n\n\n\nwwafw" if index == 0 else f"session {index}"
        (chats / f"{session_id}.json").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "title": title,
                    "created_at": f"2026-06-02T14:4{index}:18.165289+00:00",
                    "updated_at": f"2026-06-02T14:4{index}:18.165289+00:00",
                    "messages": [{"role": "user", "content": f"question {index}"}],
                }
            ),
            encoding="utf-8",
        )

    session = _plain_session()
    session.armory_path = armory
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sessions_menu_layout() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/sessions"
            await pilot.press("enter")
            await pilot.pause()

            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),
            )  # ty:ignore[redundant-cast]
            prompts = [_option_prompt_plain(suggestions, index) for index in range(6)]
            assert all("\n" not in prompt for prompt in prompts)
            assert any("hey fwafawf wwafw" in prompt for prompt in prompts)
            assert suggestions.option_count == 6
            assert suggestions.virtual_size.height == suggestions.option_count
            assert suggestions.highlighted == 0
            entry_line = _screen_line_with(app, "legacy0")
            position_line = _screen_line_with(app, f"(1/{suggestions.option_count})")
            assert entry_line.index("legacy0") == position_line.index("(")

            for expected in range(1, 6):
                await pilot.press("down")
                await pilot.pause()
                assert suggestions.highlighted == expected

    asyncio.run(check_sessions_menu_layout())


def test_sessions_command_browses_and_resumes_saved_session_inline(tmp_path: Path) -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    armory = tmp_path / "module"
    initialize(armory)
    saved_conversation = Conversation()
    saved_conversation.add("user", "What did I review?")
    saved_conversation.add("assistant", "You reviewed modal logic.")
    chat_storage.save(armory, "abc123", saved_conversation, title="Session recap")

    session = _plain_session()
    session.armory_path = armory
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sessions_resume() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/sessions browse"
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.name == "sessions"
            app._submit_inline_flow("abc123")

            assert app.session.session_id == "abc123"
            assert any("What did I review?" in entry.content for entry in app.state.transcript)
            assert any(
                "You reviewed modal logic." in entry.content for entry in app.state.transcript
            )
            assert any("resumed session abc123" in entry.content for entry in app.state.transcript)

    asyncio.run(check_sessions_resume())


def _session_with_turn_snapshots() -> ChatSession:
    session = _plain_session()
    session.conversation.add("user", "First question about evidence")
    session.conversation.add("assistant", "First answer")
    record_turn_snapshot(
        session,
        user_input="First question about evidence",
        assistant_reply="First answer",
        evidence=None,
        plan_intent="source_qa",
        contract=None,
    )
    session.conversation.add("user", "Second question about citations")
    session.conversation.add("assistant", "Second answer")
    record_turn_snapshot(
        session,
        user_input="Second question about citations",
        assistant_reply="Second answer",
        evidence=None,
        plan_intent="source_qa",
        contract=None,
    )
    return session


def test_turn_command_defaults_to_filtered_branch_menu() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _session_with_turn_snapshots()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_turn_menu() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/turn"
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.name == "turn"
            assert [label for label, _description in app._inline_flow.options] == ["T1", "T2"]
            composer.value = "second"
            await pilot.pause()

            assert [label for label, _description in app._inline_flow.options] == ["T2"]

    asyncio.run(check_turn_menu())


def test_turn_command_branches_from_selected_turn() -> None:
    if tui.Input is None or tui.OptionList is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _session_with_turn_snapshots()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_turn_branch() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/turn T1"
            await pilot.press("enter")
            await pilot.pause()

            assert app.session.session_id != session.session_id
            assert [message.content for message in app.session.conversation.messages[1:]] == [
                "First question about evidence",
                "First answer",
            ]
            assert [snapshot.turn_id for snapshot in app.session.turn_history] == ["T1"]
            assert any("branched from T1" in entry.content for entry in app.state.transcript)
            assert not any("Second answer" in entry.content for entry in app.state.transcript)

    asyncio.run(check_turn_branch())


def test_ctrl_a_moves_composer_cursor_home_without_opening_armory() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_ctrl_a() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "draft"
            composer.cursor_position = len(composer.value)
            await pilot.press("ctrl+a")
            await pilot.pause()

            assert app._armory_inline_active is False
            assert composer.cursor_position == 0

    asyncio.run(check_ctrl_a())


def test_ctrl_d_deletes_right_in_non_empty_composer() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_ctrl_d() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "abcd"
            composer.cursor_position = 1
            await pilot.press("ctrl+d")
            await pilot.pause()

            assert composer.value == "acd"
            assert composer.cursor_position == 1

    asyncio.run(check_ctrl_d())


def test_ctrl_p_and_ctrl_n_move_composer_history() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    state = tui._TuiRuntimeState(history=["first", "second"])
    app = tui.HephTui(
        _plain_session(),
        state,
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_history_shortcuts() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "draft"
            composer.cursor_position = len(composer.value)

            await pilot.press("ctrl+p")
            await pilot.pause()

            assert composer.value == "second"
            assert app._inline_flow.active is False

            await pilot.press("ctrl+n")
            await pilot.pause()

            assert composer.value == "draft"
            assert app._inline_flow.active is False

    asyncio.run(check_history_shortcuts())


@pytest.mark.parametrize("key", ["ctrl+o", "ctrl+s"])
def test_composer_readline_reserved_keys_do_not_trigger_app_shortcuts(key: str) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_reserved_shortcut() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "draft"
            composer.cursor_position = len(composer.value)
            await pilot.press(key)
            await pilot.pause()

            assert composer.value == "draft"
            assert app._inline_flow.active is False
            assert app._armory_inline_active is False
            assert app._materials_inline_active is False
            assert app.focused is composer

    asyncio.run(check_reserved_shortcut())


def test_shift_enter_inserts_visible_composer_newline() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_shift_enter_newline() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            frame = app.query_one("#composer-frame")
            composer.value = "hello"
            composer.cursor_position = len(composer.value)

            await pilot.press("shift+enter")
            for key in "world":
                await pilot.press(key)
            await pilot.pause()

            assert composer.value == "hello\nworld"
            assert composer.region.height == 2
            assert frame.region.height == 4
            assert "hello" in "".join(segment.text for segment in composer.render_line(0))
            assert "world" in "".join(segment.text for segment in composer.render_line(1))

    asyncio.run(check_shift_enter_newline())


def test_ctrl_j_inserts_visible_composer_newline() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_ctrl_j_newline() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "hello"
            composer.cursor_position = len(composer.value)

            await pilot.press("ctrl+j")
            for key in "world":
                await pilot.press(key)
            await pilot.pause()

            assert composer.value == "hello\nworld"
            assert composer.region.height == 2

    asyncio.run(check_ctrl_j_newline())


def test_report_all_csi_u_printable_keys_insert_in_focused_composer() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_csi_u_printable_keys() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            del pilot
            composer = cast("_InputKeyHandler", app.query_one("#composer", tui.Input))

            for key in ("shift+a", "slash", "shift+slash", "space", "shift+1"):
                composer.on_key(events.Key(key, None))

            assert composer.value == "A/? !"

    asyncio.run(check_csi_u_printable_keys())


def test_german_report_all_csi_u_shift_7_inserts_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HEPH_TUI_KEYBOARD_LAYOUT", "de")
    tui_widgets._clear_csi_u_keyboard_layout_cache()
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_german_shift_7() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            del pilot
            composer = cast("_InputKeyHandler", app.query_one("#composer", tui.Input))

            composer.on_key(events.Key("shift+7", None))

            assert composer.value == "/"

    try:
        asyncio.run(check_german_shift_7())
    finally:
        tui_widgets._clear_csi_u_keyboard_layout_cache()


def test_option_delete_word_editing_aliases_work_in_composer() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_word_editing_aliases() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            composer = app.query_one("#composer", tui.Input)

            composer.value = "hello world"
            composer.cursor_position = len(composer.value)
            await pilot.press("alt+backspace")
            await pilot.pause()

            assert composer.value == "hello "
            assert composer.cursor_position == len("hello ")

            composer.value = "hello world"
            composer.cursor_position = 0
            await pilot.press("alt+delete")
            await pilot.pause()

            assert composer.value == "world"
            assert composer.cursor_position == 0

    asyncio.run(check_word_editing_aliases())


def test_tmux_xterm_modified_enter_sequence_decodes_as_shift_enter() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    install_textual_modified_key_compat()
    key_events = [
        event for event in XTermParser().feed("\x1b[27;2;13~") if isinstance(event, events.Key)
    ]

    assert [(event.key, event.character) for event in key_events] == [("shift+enter", None)]


def test_default_shortcut_opens_armory_home() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_armory_shortcut() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press(_default_binding("open_armory_home"))
            await pilot.pause()

            assert app._armory_inline_active is True

    asyncio.run(check_armory_shortcut())


def test_keymap_flow_rebinds_materials_shortcut() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/calculus.md",)
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_keymap_rebind() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            materials_default_key = _default_display_key("open_materials")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/keymap"
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.active is True
            assert app._inline_flow.name == "keymap"
            assert app._inline_flow.step == "menu"
            suggestions = app.query_one("#suggestions", tui.OptionList)
            materials_prompt = _option_prompt_plain(suggestions, 2)
            assert materials_prompt.startswith("  MATERIALS")
            assert f"KEY {materials_default_key}" in materials_prompt
            assert "SCOPE app" in materials_prompt
            assert "STATE default" in materials_prompt

            app._submit_inline_flow("MATERIALS")
            await pilot.pause()
            assert app._inline_flow.step == "review"
            assert composer.placeholder.startswith("Keymap  materials  RECORD enter")
            review_options = dict(app._inline_flow.options)
            assert list(review_options) == ["RECORD", "RESET"]
            assert review_options["RECORD"] == f"current {materials_default_key}"
            assert review_options["RESET"] == f"restores {materials_default_key}"

            await pilot.press("ctrl+y")
            await pilot.pause()
            assert settings_store.load_raw_settings().get("tui_keymap") is None
            assert app._inline_flow.step == "review"

            app._submit_inline_flow("RECORD")
            await pilot.pause()
            assert app._inline_flow.step == "capture"
            assert (
                dict(app._inline_flow.options)["NEXT KEY"]
                == f"materials current {materials_default_key}"
            )

            await pilot.press("ctrl+y")
            await pilot.pause()

            raw_keymap = settings_store.load_raw_settings().get("tui_keymap")
            assert is_string_mapping(raw_keymap)
            app_keymap = raw_keymap.get("app")
            assert is_string_mapping(app_keymap)
            assert app_keymap.get("open_materials") == "ctrl+y"
            assert app._keymap.keys_for_action("open_materials") == ("ctrl+y",)
            assert (
                "MATERIALS ctrl+y"
                in tui._footer_hints_text(
                    app.session,
                    keymap=app._keymap,
                ).plain
            )

            await pilot.press("escape")
            await pilot.pause()
            assert app._inline_flow.active is False

            await pilot.press("ctrl+y")
            await pilot.pause()
            assert app._materials_inline_active is True

    asyncio.run(check_keymap_rebind())


def test_keymap_menu_rows_align_with_counter_and_key_column() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_keymap_columns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            command_key = _default_display_key("command_palette")
            materials_key = _default_display_key("open_materials")
            app._open_keymap_flow()
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            command_prompt = _option_prompt_plain(suggestions, 0)
            materials_prompt = _option_prompt_plain(suggestions, 2)
            position_line = _screen_line_with(app, f"(1/{suggestions.option_count})")
            screen_text = _composited_screen_text(app)
            command_line = next(
                line for line in screen_text.splitlines() if "COMMANDS" in line and "STATE" in line
            )

            assert command_line.index("COMMANDS") == position_line.index("(")
            assert command_prompt.startswith("→ COMMANDS")
            assert materials_prompt.startswith("  MATERIALS")
            assert command_prompt.index("KEY") == materials_prompt.index("KEY")
            assert command_prompt.index(command_key) == materials_prompt.index(materials_key)
            assert command_prompt.index("SCOPE") == materials_prompt.index("SCOPE")
            assert command_prompt.index("STATE") == materials_prompt.index("STATE")
            assert "Keyboard shortcuts" not in screen_text

    asyncio.run(check_keymap_columns())


def test_keymap_menu_rows_fit_narrow_width_without_wrapping() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_keymap_rows_fit() -> None:
        async with typed_app.run_test(size=(82, 24)) as pilot:
            app._open_keymap_flow()
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            assert suggestions.size.width > 0
            prompts = [
                _option_prompt_plain(suggestions, index)
                for index in range(suggestions.option_count)
            ]

            assert prompts
            assert all(cell_width(prompt) <= suggestions.size.width for prompt in prompts)
            assert any(prompt.startswith("→ COMMANDS") for prompt in prompts)
            command_key_text = f"KEY {_default_display_key('command_palette')}"
            assert any(command_key_text in prompt for prompt in prompts)
            assert any(prompt.startswith("  NEWLINE") for prompt in prompts)
            assert any("KEY shift+enter (+3)" in prompt for prompt in prompts)
            assert all("ctrl+enter/alt+enter/ctrl+j" not in prompt for prompt in prompts)
            assert any(prompt.startswith("  RESET") for prompt in prompts)

    asyncio.run(check_keymap_rows_fit())


def test_keymap_flow_exposes_reset_as_searchable_choice() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    result = keymap.save_keymap_binding("open_materials", "ctrl+y")
    assert result.saved is True

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_reset_search() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/keymap"
            await pilot.press("enter")
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            materials_prompt = _option_prompt_plain(suggestions, 2)
            reset_prompt = _option_prompt_plain(suggestions, suggestions.option_count - 1)
            assert "KEY ctrl+y" in materials_prompt
            assert "SCOPE app" in materials_prompt
            assert "STATE custom" in materials_prompt
            assert "RESET" in reset_prompt
            assert "RESET ALL KEYBINDS" not in reset_prompt
            assert "restores all defaults" in reset_prompt
            assert "ACTION restore all defaults" not in reset_prompt
            assert "REVIEW enter" in composer.placeholder
            assert "RESET SELECTED r" not in composer.placeholder
            assert "RESET ALL d" not in composer.placeholder

            await pilot.press("d")
            await pilot.pause()
            assert settings_store.load_raw_settings().get("tui_keymap") is not None
            assert composer.value == "d"
            composer.value = ""
            app._filter_inline_menu_options("")

            composer.value = "reset"
            app._filter_inline_menu_options(composer.value)
            reset_labels = [label for label, _description in app._inline_flow.options]
            assert reset_labels == ["RESET"]

            composer.value = "defaults"
            app._filter_inline_menu_options(composer.value)
            assert app._inline_flow.options == [("RESET", "restores all defaults")]

            app._submit_inline_flow("RESET")
            await pilot.pause()

            assert app._inline_flow.step == "reset-all"
            assert dict(app._inline_flow.options) == {
                "CONFIRM": "restores all defaults",
                "CANCEL": "",
            }
            assert settings_store.load_raw_settings().get("tui_keymap") is not None

            app._submit_inline_flow("CANCEL")
            await pilot.pause()
            assert app._inline_flow.step == "menu"
            assert app._keymap.keys_for_action("open_materials") == ("ctrl+y",)

            app._submit_inline_flow("RESET")
            await pilot.pause()
            app._submit_inline_flow("CONFIRM")
            await pilot.pause()

            assert settings_store.load_raw_settings().get("tui_keymap") is None
            assert app._keymap.keys_for_action("open_materials") == (
                _default_binding("open_materials"),
            )

    asyncio.run(check_reset_search())


def test_keymap_flow_copy_avoids_internal_metadata_labels() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    seen_surfaces: list[str] = []

    def capture_surface() -> None:
        composer = app.query_one("#composer", tui.Input)
        suggestions = app.query_one("#suggestions", tui.OptionList)
        status = app.query_one("#status", tui.Static)
        seen_surfaces.append(composer.placeholder)
        seen_surfaces.append(str(status.render()))
        seen_surfaces.extend(
            _option_prompt_plain(suggestions, index) for index in range(suggestions.option_count)
        )

    async def check_keymap_copy() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_keymap_flow()
            await pilot.pause()
            capture_surface()

            for action in keymap.TUI_KEYMAP_ACTIONS:
                app._open_keymap_flow()
                app._submit_inline_flow(action.label.upper())
                await pilot.pause()
                capture_surface()

                app._submit_inline_flow("RECORD")
                await pilot.pause()
                capture_surface()

            app._open_keymap_flow()
            app._submit_inline_flow("RESET")
            await pilot.pause()
            capture_surface()

    asyncio.run(check_keymap_copy())

    rendered_copy = "\n".join(seen_surfaces)
    forbidden_fragments = (
        "ACTION ",
        "CURRENT ",
        "DEFAULT ",
        "RESET ALL",
        "RESET ALL KEYBINDS",
        "PRESS KEY",
        "ctrl+enter/alt+enter/ctrl+j",
    )
    for fragment in forbidden_fragments:
        assert fragment not in rendered_copy
    assert "Keymap  newline" in rendered_copy
    assert "current shift+enter (+3)" in rendered_copy
    assert "restores shift+enter (+3)" in rendered_copy
    assert "newline current shift+enter (+3)" in rendered_copy
    assert "CONFIRM" in rendered_copy
    assert "restores all defaults" in rendered_copy


def test_composer_input_retains_ctrl_a_home_binding() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_composer_bindings() -> None:
        async with typed_app.run_test(size=(120, 24)):
            composer = app.query_one("#composer", tui.Input)
            key_to_bindings = composer._bindings.key_to_bindings

            assert "ctrl+a" in key_to_bindings
            assert "home" in key_to_bindings

    asyncio.run(check_composer_bindings())


@pytest.mark.parametrize(
    "command_input",
    [f"/{suggestion.name}" for suggestion in tui._tui_command_suggestions()],
)
def test_command_input_executes_without_user_transcript(
    monkeypatch: pytest.MonkeyPatch,
    command_input: str,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_command_input() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "exit", lambda: None)
            composer = app.query_one("#composer", tui.Input)
            composer.value = command_input
            await pilot.press("enter")
            await pilot.pause()
            assert not any(
                entry.kind == "user" and entry.content == command_input
                for entry in app.state.transcript
            )
            assert not any(
                message.role == "user" and message.content == command_input
                for message in app.session.conversation.messages
            )
            if command_input == "/armory":
                assert app._armory_inline_active is True
            elif command_input == "/materials":
                assert app._materials_inline_active is True
            elif command_input == "/keymap":
                assert app._inline_flow.active is True
                assert app._inline_flow.name == "keymap"
                assert app._inline_flow.step == "menu"
                suggestions = app.query_one("#suggestions", tui.OptionList)
                materials_prompt = _option_prompt_plain(suggestions, 2)
                assert f"KEY {_default_display_key('open_materials')}" in materials_prompt
                assert "SCOPE app" in materials_prompt
                assert "STATE default" in materials_prompt
                assert not any(
                    "Keyboard shortcuts" in entry.content for entry in app.state.transcript
                )
            elif command_input == "/new":
                assert any("New chat started" in entry.content for entry in app.state.transcript)
            elif command_input == "/detach":
                assert any("No armory attached" in entry.content for entry in app.state.transcript)
            elif command_input.startswith(("/models", "/help", "/status", "!")):
                assert app.state.pending_input is None
                assert app.state.transcript
            elif tui._pending_input_requires_terminal(command_input):
                assert app.state.pending_input == command_input
            else:
                assert app.state.pending_input is None

    asyncio.run(check_command_input())


def test_busy_submit_routes_commands_without_steering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    calls: list[tuple[str, str]] = []

    def record_materials(value: str) -> None:
        calls.append(("materials", value))

    def record_sessions(value: str) -> None:
        calls.append(("sessions", value))

    def record_new() -> None:
        calls.append(("new", ""))

    def record_detach() -> None:
        calls.append(("detach", ""))

    def record_armory(value: str) -> None:
        calls.append(("armory", value))

    def record_inline(value: str) -> None:
        calls.append(("inline", value))

    def record_external(value: str) -> None:
        calls.append(("external", value))

    async def check_busy_dispatch() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            _mark_active_turn(app)
            monkeypatch.setattr(app, "_open_materials_inline", record_materials)
            monkeypatch.setattr(app, "_handle_sessions_command", record_sessions)
            monkeypatch.setattr(app, "_handle_new", record_new)
            monkeypatch.setattr(app, "_handle_detach", record_detach)
            monkeypatch.setattr(app, "_handle_armory_browser", record_armory)
            monkeypatch.setattr(app, "_handle_inline_command", record_inline)
            monkeypatch.setattr(app, "_handle_external_input", record_external)
            composer = app.query_one("#composer", tui.Input)

            for value in (
                "/materials notes",
                "/sessions",
                "/new",
                "/detach",
                "/armory",
                "/settings",
                "/models",
            ):
                composer.value = value
                await pilot.press("enter")
                await pilot.pause()

            composer.value = "/help"
            await pilot.press("enter")
            await pilot.pause()

            composer.value = "extra context"
            await pilot.press("enter")
            await pilot.pause()

            assert calls == [
                ("materials", "/materials notes"),
                ("sessions", "/sessions"),
                ("new", ""),
                ("detach", ""),
                ("armory", "/armory"),
                ("inline", "/settings"),
                ("inline", "/models"),
            ]
            assert any("COMMANDS" in entry.content for entry in app.state.transcript)
            assert any(
                "Steering queued: extra context" in entry.content for entry in app.state.transcript
            )
            assert not any("Steering queued: /" in entry.content for entry in app.state.transcript)

    asyncio.run(check_busy_dispatch())


def test_busy_materials_and_settings_remain_interactive() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/biology.pdf",)
    session.source_file_count = 1
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_busy_inline_commands() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            _mark_active_turn(app)
            composer = app.query_one("#composer", tui.Input)

            composer.value = "/materials"
            await pilot.press("enter")
            await pilot.pause()
            assert app._materials_inline_active is True
            assert app.busy is True

            await pilot.press("escape")
            await pilot.pause()
            assert app._materials_inline_active is True
            assert app.busy is False

            await pilot.press("escape")
            await pilot.pause()
            assert app._materials_inline_active is False

            _mark_active_turn(app)
            composer.value = "/settings"
            await pilot.press("enter")
            await pilot.pause()
            assert app._inline_flow.active is True
            assert app._inline_flow.name == "settings"
            assert app.busy is True
            assert not any("Steering queued: /" in entry.content for entry in app.state.transcript)

    asyncio.run(check_busy_inline_commands())


@pytest.mark.parametrize(
    ("command_input", "flow_name"),
    [
        ("/settings", "settings"),
        ("/local", "local"),
    ],
)
def test_inline_command_opens_menu_without_command_transcript(
    monkeypatch: pytest.MonkeyPatch,
    command_input: str,
    flow_name: str,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def fake_run_worker(work: object, *, thread: bool = False) -> None:
        del work, thread

    async def check_command_transcript() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "run_worker", fake_run_worker)
            app._append_notice("Previous action finished.")
            composer = app.query_one("#composer", tui.Input)
            composer.value = command_input
            await pilot.press("enter")
            await pilot.pause()

            assert not any(
                entry.kind == "user" and entry.content == command_input
                for entry in app.state.transcript
            )
            assert app._inline_flow.active is True
            assert app._inline_flow.name == flow_name
            assert command_input not in app.state.history

    asyncio.run(check_command_transcript())


def test_materials_inline_toggles_rag_sources() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/biology.pdf", "materials/calculus.md")
    session.source_file_count = 2
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_materials_toggle() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/materials"
            await pilot.press("enter")
            await pilot.pause()
            assert app._materials_inline_active is True
            assert app.query_one("#info-panel").styles.display == "none"
            assert "materials/biology.pdf" not in session.disabled_source_files

            await pilot.press("enter")
            await pilot.pause()
            assert "materials/biology.pdf" in session.disabled_source_files

            await pilot.press("enter")
            await pilot.pause()
            assert "materials/biology.pdf" not in session.disabled_source_files

            await pilot.press("escape")
            await pilot.pause()
            assert app.query_one("#info-panel").styles.display == "block"

    asyncio.run(check_materials_toggle())


def test_materials_inline_splits_long_lists_into_two_columns() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = tuple(f"materials/week-{index:02}.md" for index in range(30))
    session.source_file_count = len(session.source_files)
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_two_columns() -> None:
        async with typed_app.run_test(size=(100, 18)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/materials"
            await pilot.press("enter")
            await pilot.pause()

            columns = app.query_one("#materials-columns")
            left = app.query_one("#materials-list", tui.OptionList)
            right = app.query_one("#materials-list-right", tui.OptionList)

            assert columns.has_class("two-column")
            assert left.option_count > 0
            assert right.option_count > 0
            assert left.option_count + right.option_count == len(session.source_files)

    asyncio.run(check_two_columns())


def test_materials_mouse_click_toggles_single_source() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = tuple(f"materials/source-{index}.md" for index in range(6))
    session.source_file_count = len(session.source_files)
    session.disabled_source_files.update(session.source_files[:5])
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_mouse_materials() -> None:
        async with typed_app.run_test(size=(100, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/materials"
            await pilot.press("enter")
            await pilot.pause()

            await pilot.click("#materials-list", offset=(2, 4))
            await pilot.pause()
            assert session.source_files[4] not in session.disabled_source_files
            assert getattr(app.focused, "id", None) == "materials-list"

            await pilot.click("#materials-list", offset=(2, 4))
            await pilot.pause()
            assert session.source_files[4] in session.disabled_source_files
            for file in session.source_files[:4]:
                assert file in session.disabled_source_files

    asyncio.run(check_mouse_materials())


def test_transcript_reflows_when_resize_crosses_sidebar_threshold() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.armory_path = Path.home()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    long_line = (
        "The PDF covers the fundamentals of number theory, explaining residue classes modulo n "
        "and the ring structure of Z/nZ, criteria for multiplicative inverses via coprimality. "
    ) * 3

    async def check_reflow() -> None:
        async with typed_app.run_test(size=(119, 24)) as pilot:
            await pilot.pause()
            assert app.query_one("#info-panel").styles.display == "none"

            app._append_plain(long_line)
            await pilot.pause()
            log = app.query_one("#transcript", tui.RichLog)
            width_before = log.size.width
            widest_before = max((line.cell_length for line in log.lines), default=0)
            assert widest_before <= width_before

            await pilot.resize_terminal(120, 24)
            await pilot.pause()
            await pilot.pause()
            await pilot.pause()

            assert app.query_one("#info-panel").styles.display == "block"
            width_after = log.size.width
            widest_after = max((line.cell_length for line in log.lines), default=0)
            assert width_after < width_before
            assert widest_after <= width_after
            assert widest_after < widest_before

    asyncio.run(check_reflow())


def test_transcript_wrap_preserves_continuation_indent() -> None:
    wrapped = tui_transcript._wrap_transcript_plain_line(
        "  Ask for summaries, contradictions, gaps, timelines, and action items.",
        31,
    )

    assert wrapped[0] == "  Ask for summaries,"
    assert len(wrapped) > 1
    assert all(line.startswith("  ") for line in wrapped)
    assert max(len(line) for line in wrapped) <= 31


def test_transcript_wrap_uses_hanging_indent_for_lists() -> None:
    wrapped = tui_transcript._wrap_transcript_plain_line(
        "- Heph keeps transparent dark UI, resizes from actual PTY pane dimensions.",
        32,
    )

    assert wrapped[0].startswith("- ")
    assert len(wrapped) > 1
    assert all(line.startswith("  ") for line in wrapped[1:])
    assert max(len(line) for line in wrapped) <= 32


def test_transcript_renders_indented_wrapped_lines_aligned() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(armory_home_shown=True),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_rendered_wrap() -> None:
        async with typed_app.run_test(size=(32, 12)) as pilot:
            await pilot.pause()
            app._append_entry(
                "  Ask for summaries, contradictions, gaps, timelines, and action items.",
                "startup",
            )
            await pilot.pause()

            log = app.query_one("#transcript", tui.RichLog)
            rendered = [_strip_plain_text(line).rstrip() for line in log.lines]
            wrapped = [line for line in rendered if line]

            assert len(wrapped) > 1
            assert all(line.startswith("  ") for line in wrapped)
            assert max(len(line) for line in wrapped) <= log.size.width

    asyncio.run(check_rendered_wrap())


def test_resize_preserves_completion_menu_at_current_width() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_resize_completion_cleanup() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            suggestions = app.query_one("#suggestions", tui.OptionList)

            composer.value = "/"
            composer.cursor_position = 1
            app._refresh_completions()
            await pilot.pause()

            assert suggestions.has_class("visible")
            assert suggestions.option_count > 0

            await pilot.resize_terminal(100, 18)
            await pilot.pause()
            await pilot.pause()

            assert suggestions.has_class("visible")
            assert suggestions.option_count > 0
            assert app.query_one("#composer", tui.Input) is composer
            assert getattr(app.focused, "id", None) == "composer"

    asyncio.run(check_resize_completion_cleanup())


def test_transcript_scrolls_to_latest_entry_after_long_output() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scroll() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            await pilot.pause()
            app._append_plain("\n".join(f"old line {i}" for i in range(60)))
            app._append_plain("latest exam question line")
            await pilot.pause()

            log = app.query_one("#transcript", tui.RichLog)
            assert log.scroll_y > 0
            assert "latest exam question line" in str(log.lines[-1])

    asyncio.run(check_scroll())


def test_transcript_does_not_follow_new_activity_while_reviewing_history() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scroll() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            await pilot.pause()
            app._append_plain("\n".join(f"old line {i}" for i in range(60)))
            await pilot.pause()

            log = app.query_one("#transcript", tui.RichLog)
            assert log.max_scroll_y > 0
            log.scroll_y = 0
            await pilot.pause()

            app._append_notice("info: background tool call completed")
            await pilot.pause()

            assert log.scroll_y == 0
            assert "background tool call completed" in str(log.lines[-1])

    asyncio.run(check_scroll())


def test_transcript_scrolls_to_final_line_of_multiline_command_output() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scroll() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            await pilot.pause()
            app._append_plain("\n".join(f"old line {i}" for i in range(60)))
            app._append_entry(
                "\n".join(
                    [
                        "Exam question",
                        "Time limit: 8 minutes",
                        (
                            "Explain what a neural network is and why hidden layers matter. "
                            "[10 marks]"
                        ),
                        "Answer from memory. Do not open the material unless your exam allows it.",
                    ]
                ),
                "notice",
            )
            await pilot.pause()

            log = app.query_one("#transcript", tui.RichLog)
            visible = "\n".join(str(line) for line in log.lines[-6:])
            assert "Explain what a neural network is" in visible
            assert "Answer from memory" in visible

    asyncio.run(check_scroll())


def test_multiline_notice_does_not_emit_broken_markup() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_notice() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            await pilot.pause()
            app._append_notice(
                "Can't reach openai-codex. You're offline.\n"
                "Heph will reconnect automatically when connectivity returns."
            )
            await pilot.pause()

            log = app.query_one("#transcript", tui.RichLog)
            rendered = "\n".join(str(line) for line in log.lines)
            assert "Can't reach openai-codex" in rendered
            assert "reconnect automatically" in rendered

    asyncio.run(check_notice())


def test_help_executes_inline_without_restarting_tui(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    exit_calls = 0

    def fake_exit() -> None:
        nonlocal exit_calls
        exit_calls += 1

    async def check_inline_help() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "exit", fake_exit)
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/help"
            await pilot.press("enter")
            await pilot.pause()
            assert exit_calls == 0
            assert app.state.pending_input is None
            assert any("COMMANDS" in entry.content for entry in app.state.transcript)
            assert not any(
                entry.kind == "user" and entry.content == "/help" for entry in app.state.transcript
            )

    asyncio.run(check_inline_help())


def test_armory_inline_composer_filters_without_chat_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    _make_child = tmp_path / "biology"
    _make_child.mkdir()
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_filter() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "bio"
            await pilot.pause()
            labels = [entry.label for entry in app._armory_entries]
            assert any("biology" in label for label in labels)
            assert not any("You:" in entry.content for entry in app.state.transcript)

    asyncio.run(check_filter())


def test_armory_inline_new_armory_uses_composer_without_chat_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_create() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "maths"
            await pilot.press("enter")
            await pilot.pause()
            assert (tmp_path / "maths").exists()
            assert not any("You:" in entry.content for entry in app.state.transcript)

    asyncio.run(check_create())


def test_armory_inline_opens_fresh_empty_armory_after_create(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_create_then_open() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "empty-armory"
            await pilot.press("enter")
            await pilot.pause()

            armory_path = tmp_path / "empty-armory"
            assert (armory_path / ".harness" / "armory.toml").is_file()

            app._handle_armory_browser("/armory")
            labels = [entry.label for entry in app._armory_entries]
            index = next(i for i, label in enumerate(labels) if "empty-armory" in label)
            current = app.query_one("#armory-current-inline", tui.OptionList)
            current.highlighted = index
            await pilot.press("enter")
            await pilot.pause()

            assert app._armory_inline_active is False
            assert app.session.armory_path == armory_path
            assert app.session.source_file_count == 0
            assert any(
                entry.content == "Using armory empty-armory" for entry in app.state.transcript
            )
            assert any(
                "No materials yet. Add files to" in entry.content for entry in app.state.transcript
            )
            assert not any(
                "Could not open armory" in entry.content for entry in app.state.transcript
            )

    asyncio.run(check_create_then_open())


def test_armory_inline_create_starts_in_default_armory_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    default_home = Path.home() / ".armories"
    monkeypatch.delenv("HARNESS_ARMORY_HOME", raising=False)
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_default_home() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("create")
            assert app._armory_current == default_home.resolve()

    asyncio.run(check_default_home())


def test_default_armory_home_honors_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path / ".armory-home"))
    assert default_armory_home() == (tmp_path / ".armory-home").resolve()


def test_default_armory_home_falls_back_to_dot_armory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HARNESS_ARMORY_HOME", raising=False)
    assert default_armory_home() == (Path.home() / ".armories").resolve()


def test_armory_inline_place_entries_stay_inside_armory_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_places() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")
            place_entries = [entry for entry in app._armory_entries if entry.is_place]
            assert not any(entry.path == Path("/") for entry in place_entries)
            assert all(
                entry.path is not None
                and entry.path.resolve(strict=False).is_relative_to(armory_home)
                for entry in place_entries
            )

    asyncio.run(check_places())


def test_armory_inline_left_does_not_navigate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    armory_home = tmp_path / ".armories"
    child = armory_home / "child"
    child.mkdir(parents=True)
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_left_navigation() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            app._armory_current = child
            app._refresh_armory_inline()
            await pilot.press("left")
            await pilot.pause()
            assert app._armory_current == child
            await pilot.press("left")
            await pilot.pause()
            assert app._armory_current == child

    asyncio.run(check_left_navigation())


def test_armory_inline_rejects_open_outside_armory_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    armory_home = tmp_path / ".armories"
    outside = tmp_path / "outside"
    armory_home.mkdir()
    initialize(outside)
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory_home))
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_rejected_open() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")
            app._open_selected_armory(outside)
            error = app.query_one("#armory-error-inline", tui.Static)
            assert "outside armory home" in str(error.render())

    asyncio.run(check_rejected_open())


def test_armory_inline_create_rejects_existing_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))

    (tmp_path / "existing").mkdir()
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_reject_existing() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "existing"
            await pilot.press("enter")
            await pilot.pause()
            error = app.query_one("#armory-error-inline", tui.Static)
            assert "already exists" in str(error.render())
            assert not (tmp_path / "existing" / ".harness").exists()
            assert app._armory_inline_active is True

    asyncio.run(check_reject_existing())


def test_armory_inline_create_rejects_path_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_reject_escape() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "../outside"
            await pilot.press("enter")
            await pilot.pause()
            error = app.query_one("#armory-error-inline", tui.Static)
            assert "inside the selected folder" in str(error.render())
            assert not (tmp_path.parent / "outside").exists()
            assert app._armory_inline_active is True

    asyncio.run(check_reject_escape())


def test_armory_inline_escape_clears_filter_then_exits(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_escape_flow() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "math"
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is True
            assert composer.value == ""
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is False

    asyncio.run(check_escape_flow())


def test_armory_inline_escape_cancels_create_then_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_create_escape() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "math"
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is True
            assert app._armory_creating is False
            assert composer.value == ""
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is False
            assert not (tmp_path / "math").exists()

    asyncio.run(check_create_escape())


def test_armory_footer_hints_follow_mode() -> None:
    normal = tui._armory_footer_hints_text()
    filtering = tui._armory_footer_hints_text(filtering=True)
    creating = tui._armory_footer_hints_text(creating=True)

    assert normal.plain == "OPEN enter  CLOSE esc"
    assert filtering.plain == "OPEN enter  CLEAR esc  MOVE arrows"
    assert creating.plain == "CREATE enter  CANCEL esc"


def test_materials_footer_hints_follow_action_then_key_order() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app.session.source_files = ("materials/enabled.pdf",)

    app._materials_flow = "toggle"
    assert app._materials_footer_text() == "TOGGLE space/enter  CLOSE esc"

    app._materials_flow = "open"
    assert app._materials_footer_text() == "OPEN enter  CLOSE esc"


def test_inline_menu_placeholder_hints_follow_action_then_key_order() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_placeholder() -> None:
        async with typed_app.run_test(size=(100, 24)):
            app._open_inline_menu(
                name="test",
                step="menu",
                title="Test menu",
                options=[("Open", "Current item")],
            )
            composer = app.query_one("#composer", tui.Input)
            assert composer.placeholder == (
                "Test menu  FILTER type  MOVE ↑/↓  SELECT enter  CLOSE esc"
            )
            assert "type to filter" not in composer.placeholder

    asyncio.run(check_placeholder())


def test_active_armory_menu_title_moves_to_status_bar(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_title() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            await pilot.pause()

            status = app.query_one("#status", tui.Static)
            hints = app.query_one("#footer-hints", tui.Static)
            assert str(status.render()).startswith("Armory  ")
            assert str(hints.render()) == "OPEN enter  CLOSE esc"

            await pilot.press("escape")
            await pilot.pause()
            assert str(status.render()).startswith("Heph  ")
            assert str(hints.render()).startswith(_footer_armory_hint())

    asyncio.run(check_title())


def test_active_materials_menu_title_moves_to_status_bar() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/enabled.pdf",)
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_title() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_materials_inline("/materials")
            await pilot.pause()

            status = app.query_one("#status", tui.Static)
            materials_footer = app.query_one("#materials-footer", tui.Static)
            hints = app.query_one("#footer-hints", tui.Static)
            assert str(status.render()).startswith("Materials  ")
            assert str(materials_footer.render()) == ""
            assert str(hints.render()) == "TOGGLE space/enter  CLOSE esc"

            await pilot.press("escape")
            await pilot.pause()
            assert str(status.render()).startswith("Heph  ")

    asyncio.run(check_title())


def test_active_inline_menu_title_moves_to_status_bar() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_title() -> None:
        async with typed_app.run_test(size=(100, 24)):
            app._open_inline_menu(
                name="models",
                step="menu",
                title="Models",
                options=[("test-model", "current")],
            )
            status = app.query_one("#status", tui.Static)
            assert str(status.render()).startswith("Models  ")

            app._close_inline_flow()
            assert str(status.render()).startswith("Heph  ")

    asyncio.run(check_title())


def test_command_completion_keeps_current_status_title() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_title() -> None:
        async with typed_app.run_test(size=(100, 24)):
            app.action_command_palette()
            status = app.query_one("#status", tui.Static)
            assert str(status.render()).startswith("Heph  ")

            app._hide_completions()
            assert str(status.render()).startswith("Heph  ")

            app._open_inline_menu(
                name="models",
                step="menu",
                title="Models",
                options=[("test-model", "current")],
            )
            app.action_command_palette()
            assert str(status.render()).startswith("Models  ")

    asyncio.run(check_title())


def test_armory_footer_restores_after_exit(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_footer_restore() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            hints = app.query_one("#footer-hints", tui.Static)
            assert str(hints.render()) == "OPEN enter  CLOSE esc"
            await pilot.press("escape")
            await pilot.pause()
            assert _footer_armory_hint() in str(hints.render())

    asyncio.run(check_footer_restore())


def test_armory_inline_app_focus_recovers_composer_control(tmp_path: Path) -> None:
    if tui.Input is None or tui.events is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_app_focus() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")
            composer = app.query_one("#composer", tui.Input)
            app.set_focus(None)
            app.on_app_focus(tui.events.AppFocus())
            assert app.focused is composer

    asyncio.run(check_app_focus())


def test_armory_inline_click_keeps_composer_as_control(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    (tmp_path / "math").mkdir()
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_click_focus() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            composer = app.query_one("#composer", tui.Input)
            await pilot.click("#armory-current-inline", offset=(2, 1))
            await pilot.pause()
            assert app.focused is composer
            assert app._armory_inline_active is True

    asyncio.run(check_click_focus())


def test_armory_inline_transparent_surface_does_not_paint_black(tmp_path: Path) -> None:
    if tui.Input is None or tui.Strip is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_transparency() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            await pilot.pause()
            widgets: tuple[Widget, ...] = (
                cast("Widget", app.query_one("#armory-inline")),  # ty:ignore[redundant-cast]
                cast("Widget", app.query_one("#armory-header")),  # ty:ignore[redundant-cast]
                cast("Widget", app.query_one("#armory-current-inline")),  # ty:ignore[redundant-cast]
                cast("Widget", app.query_one("#armory-preview-inline")),  # ty:ignore[redundant-cast]
            )
            for widget in widgets:
                for line_number in range(widget.size.height):
                    strip = widget.render_line(line_number)
                    assert all("on #000000" not in str(segment.style) for segment in strip)

    asyncio.run(check_transparency())


def test_armory_inline_header_shows_filter_and_no_matches(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_empty_filter() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "no-such-folder"
            await pilot.pause()
            header = app.query_one("#armory-header", tui.Static)
            focus_hint = app.query_one("#armory-pane-hint", tui.Static)
            flow_hint = app.query_one("#armory-flow-hint", tui.Static)
            preview = app.query_one("#armory-preview-inline", tui.Static)
            assert "no-such-folder" not in str(header.render())
            assert str(flow_hint.render()) == ""
            # pane hint is now cleared (empty)
            assert focus_hint is not None
            assert "STATE no matches" in str(preview.render())

    asyncio.run(check_empty_filter())


def test_armory_inline_preserves_selection_across_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    alpha.mkdir()
    beta.mkdir()
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_selection() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")
            current = app.query_one("#armory-current-inline", tui.OptionList)
            current.highlighted = next(
                index for index, entry in enumerate(app._armory_entries) if entry.path == beta
            )
            app._refresh_armory_inline()
            selected = app._armory_highlighted_entry()
            assert selected is not None
            assert selected.path == beta

    asyncio.run(check_selection())


def test_armory_inline_description_column_tracks_visible_rows(tmp_path: Path) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_armory_columns() -> None:
        async with typed_app.run_test(size=(120, 12)) as pilot:
            app._open_armory_inline("manage")
            app._armory_entries = [
                tui._DirEntry("extra-wide-visible-first", path=tmp_path / "wide"),
                tui._DirEntry("aa", path=tmp_path / "aa"),
                tui._DirEntry("bb", path=tmp_path / "bb"),
                tui._DirEntry("cc", path=tmp_path / "cc"),
                tui._DirEntry("dd", path=tmp_path / "dd"),
                tui._DirEntry("ee", path=tmp_path / "ee"),
                tui._DirEntry("ff", path=tmp_path / "ff"),
                tui._DirEntry("gg", path=tmp_path / "gg"),
            ]
            app._render_armory_options(0)
            await pilot.pause()

            columns = _armory_description_columns(app)
            assert len(set(columns[:6])) == 1
            assert columns[0] == len("→ extra-wide-visible-first") + 4

            app._render_armory_options(7)
            await pilot.pause()

            columns = _armory_description_columns(app)
            assert len(set(columns[2:])) == 1
            assert columns[2] == len("  ITEMS 8") + 2

    asyncio.run(check_armory_columns())


def test_armory_inline_rows_show_file_columns_without_duplicate_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory = tmp_path / "biology"
    initialize(armory)
    (armory / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_material_context() -> None:
        async with typed_app.run_test(size=(120, 12)) as pilot:
            app._open_armory_inline("manage")
            await pilot.pause()

            current = app.query_one("#armory-current-inline", tui.OptionList)
            index = next(
                index for index, entry in enumerate(app._armory_entries) if entry.path == armory
            )
            prompt = _option_prompt_plain(current, index)
            header = app.query_one("#armory-header", tui.Static)
            sidebar = app.query_one("#info-panel", tui.Static)

            assert "ITEMS" in str(header.render())
            assert "Armories" not in str(header.render())
            assert "FILES 1" in prompt
            assert "ready" not in prompt
            assert "material file" not in prompt
            assert str(tmp_path) not in prompt
            assert str(tmp_path) not in str(header.render())
            assert "STATE ready" in str(sidebar.render())
            assert "MATERIALS available" in str(sidebar.render())
            assert "1 file(s)" not in str(sidebar.render())
            assert "Enter opens" not in str(sidebar.render())
            assert "biology" not in str(sidebar.render())
            assert "material file" not in str(sidebar.render())

    asyncio.run(check_material_context())


def test_armory_inline_sidebar_avoids_repeating_row_and_footer_details(
    tmp_path: Path,
) -> None:
    initialize(tmp_path)
    (tmp_path / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    entry = tui._DirEntry("biology", path=tmp_path)

    sidebar = tui_armory._armory_sidebar_text(entry)

    assert sidebar == "STATE ready\nMATERIALS available\nMEMORY armory scoped"
    assert "biology" not in sidebar
    assert "1 file(s)" not in sidebar
    assert "Enter opens" not in sidebar


def test_armory_inline_filter_selects_separator_insensitive_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    target = tmp_path / "module-2"
    initialize(target)
    initialize(tmp_path / "module-10")
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_filter_match() -> None:
        async with typed_app.run_test(size=(120, 12)) as pilot:
            app._open_armory_inline("manage")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "module2"
            await pilot.pause()

            selected = app._armory_highlighted_entry()
            assert selected is not None
            assert selected.path == target

    asyncio.run(check_filter_match())


def test_armory_inline_n_filters_instead_of_starting_create() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_filter_key() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")
            await pilot.press("n")
            await pilot.pause()
            composer = app.query_one("#composer", tui.Input)
            assert app._armory_creating is False
            assert composer.value == "n"

    asyncio.run(check_filter_key())


def test_armory_inline_create_entry_uses_composer(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    app._armory_current = tmp_path
    typed_app = cast("TextualApp[None]", app)

    async def check_create_entry() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")
            current = app.query_one("#armory-current-inline", tui.OptionList)
            current.highlighted = next(
                index for index, entry in enumerate(app._armory_entries) if entry.is_create
            )
            app._armory_open_highlighted()
            composer = app.query_one("#composer", tui.Input)
            assert app._armory_creating is True
            assert composer.placeholder == "CREATE armory name"

    asyncio.run(check_create_entry())


def test_handle_armory_browser_cancel_keeps_current_session() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_cancel() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._handle_armory_browser("/armory")
            assert app._armory_inline_active is True
            await pilot.press("escape")
            await pilot.pause()
            assert app.session is session
            assert app._armory_inline_active is False

    asyncio.run(check_cancel())


def test_handle_armory_browser_rejects_invalid_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_invalid_directory() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._handle_armory_browser("/armory open")
            app._open_selected_armory(tmp_path)
            error = app.query_one("#armory-error-inline", tui.Static)
            assert "Not a valid armory" in str(error.render())

    asyncio.run(check_invalid_directory())


def test_armory_inline_enter_opens_highlighted_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "notes"
    initialize(armory_path)
    (armory_path / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_enter_opens_armory() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._handle_armory_browser("/armory")
            labels = [entry.label for entry in app._armory_entries]
            index = next(i for i, label in enumerate(labels) if "notes" in label)
            current = app.query_one("#armory-current-inline", tui.OptionList)
            current.highlighted = index
            await pilot.press("enter")
            await pilot.pause()
            assert app._armory_inline_active is False
            assert app.session.armory_path == armory_path
            assert app.session.source_file_count == 1

    asyncio.run(check_enter_opens_armory())


def test_handle_armory_browser_switches_to_selected_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "notes"
    initialize(armory_path)
    session = _plain_session()
    new_session = _plain_session()
    new_session.armory_path = armory_path
    new_session.source_file_count = 1
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def fake_start_fresh(current: ChatSession, selected: Path | None) -> ChatSession:
        assert current is session
        assert selected == armory_path
        return new_session

    async def check_switch() -> None:
        async with typed_app.run_test(size=(120, 24)):
            monkeypatch.setattr(tui, "start_fresh_session", fake_start_fresh)
            app._handle_armory_browser("/armory open")
            app._open_selected_armory(armory_path)
            assert app.session is new_session
            assert any(entry.content == "Using armory notes" for entry in app.state.transcript)
            composer = app.query_one("#composer", tui.Input)
            assert app.focused is composer

    asyncio.run(check_switch())


def test_busy_turn_allows_switching_armories_and_starting_another_prompt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_a = tmp_path / "alpha"
    armory_b = tmp_path / "beta"
    initialize(armory_a)
    initialize(armory_b)
    session_a = _configured_status_session()
    session_a.armory_path = armory_a
    session_b = _configured_status_session()
    session_b.session_id = "session-beta"
    session_b.armory_path = armory_b
    app = tui.HephTui(
        session_a,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    workers: list[Callable[[], None]] = []

    def fake_start_fresh(current: ChatSession, selected: Path | None) -> ChatSession:
        assert current is session_a
        assert selected == armory_b
        return session_b

    def fake_run_worker(work: Callable[[], None], *, thread: bool) -> None:
        assert thread is True
        workers.append(work)

    async def check_parallel_armory_turns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(tui, "start_fresh_session", fake_start_fresh)
            monkeypatch.setattr(app, "run_worker", fake_run_worker)
            _mark_active_turn(app, session_a)
            assert app.busy is True

            app._open_selected_armory(armory_b)
            assert app.session is session_b
            assert app.busy is False

            composer = app.query_one("#composer", tui.Input)
            composer.value = "What is in beta?"
            await pilot.press("enter")
            await pilot.pause()

            assert workers
            assert app.busy is True
            assert app._turn_key_for_session(session_a) in app._active_turns
            assert app._turn_key_for_session(session_b) in app._active_turns

            app._open_selected_armory(armory_a)
            assert app.session is session_a
            assert app.busy is True
            app._finish_background_turn(app._turn_key_for_session(session_a), session_a)
            app._finish_background_turn(app._turn_key_for_session(session_b), session_b)

    asyncio.run(check_parallel_armory_turns())


def test_finished_background_turn_is_restored_when_reopening_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory_a = tmp_path / "alpha"
    armory_b = tmp_path / "beta"
    initialize(armory_a)
    initialize(armory_b)
    session_a = _configured_status_session()
    session_a.armory_path = armory_a
    session_b = _configured_status_session()
    session_b.session_id = "session-beta"
    session_b.armory_path = armory_b
    app = tui.HephTui(
        session_b,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def fail_start_fresh(current: ChatSession, selected: Path | None) -> ChatSession:
        raise AssertionError(f"should reuse background session for {selected}")

    async def check_reopen_background_session() -> None:
        async with typed_app.run_test(size=(120, 24)):
            monkeypatch.setattr(tui, "start_fresh_session", fail_start_fresh)
            _mark_active_turn(app, session_a)
            session_a.conversation.add("user", "Alpha prompt")
            session_a.conversation.add("assistant", "Alpha answer")
            app._finish_background_turn(app._turn_key_for_session(session_a), session_a)

            app._open_selected_armory(armory_a)

            assert app.session is session_a
            assert app.busy is False
            assert any("Alpha prompt" in entry.content for entry in app.state.transcript)
            assert any("Alpha answer" in entry.content for entry in app.state.transcript)

    asyncio.run(check_reopen_background_session())


def test_armory_inline_marks_armories_with_running_turns(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HARNESS_ARMORY_HOME", str(tmp_path))
    armory = tmp_path / "notes"
    initialize(armory)
    session = _plain_session()
    session.armory_path = armory
    app = tui.HephTui(
        session,
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_running_badge() -> None:
        async with typed_app.run_test(size=(120, 24)):
            _mark_active_turn(app, session)
            app._open_armory_inline("manage")
            current = app.query_one("#armory-current-inline", tui.OptionList)
            index = next(
                index for index, entry in enumerate(app._armory_entries) if entry.path == armory
            )
            current.highlighted = index
            app._render_armory_options(index)
            app._update_armory_preview()

            prompt = current.get_option_at_index(index).prompt
            prompt_text = prompt.plain if isinstance(prompt, Text) else str(prompt)
            preview = app.query_one("#armory-preview-inline", tui.Static)
            assert "working" in prompt_text
            assert "STATE working" in str(preview.render())
            assert str(preview.render()).count("working") == 1

    asyncio.run(check_running_badge())


def test_click_refocuses_composer() -> None:
    if tui.Input is None or tui.Static is None or tui.events is None:
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()
    vertical_class = tui._transparent_vertical_class()
    input_class = tui._transparent_input_class()
    static_class = tui._transparent_static_class()
    rich_log_class = tui._transparent_rich_log_class()

    class ClickStress(tui.App[None]):
        CSS = tui._tui_css()

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with vertical_class(id="shell"):
                yield static_class(
                    tui._status_text(session),
                    id="status",
                )
                yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)
                yield static_class("", id="thinking-indicator")
                with vertical_class(id="composer-frame"):
                    yield input_class(
                        placeholder="Ask...",
                        id="composer",
                    )
                    yield static_class(
                        tui._footer_hints_text(session),
                        id="footer-hints",
                    )

        def on_click(self, event: tui.events.Click) -> None:
            composer = self.query_one("#composer", tui.Input)
            if self.focused is not composer:
                self.call_after_refresh(composer.focus)

    async def check_click_focus() -> None:
        app = ClickStress()
        async with app.run_test(size=(120, 12)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            assert app.focused is composer
            # Click on transcript area
            await pilot.click("#transcript", offset=(5, 2))
            await pilot.pause()
            await pilot.pause()
            # Composer should be re-focused by the on_click handler
            assert app.focused is composer

    asyncio.run(check_click_focus())


def test_completion_menu_auto_highlights_first_item() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()
    vertical_class = tui._transparent_vertical_class()
    horizontal_class = tui._transparent_horizontal_class()
    input_class = tui._transparent_input_class()
    static_class = tui._transparent_static_class()
    rich_log_class = tui._transparent_rich_log_class()
    option_list_class = tui._transparent_option_list_class()

    engine = tui.SlashCompletionEngine()

    class CompletionStress(tui.App[None]):
        CSS = tui._tui_css()

        def __init__(self) -> None:
            super().__init__()
            self.completion_engine = engine
            self.completion_candidates: list[tui.CompletionCandidate] = []

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with horizontal_class(id="main-layout"):
                with vertical_class(id="shell"):
                    yield static_class(
                        tui._status_text(session),
                        id="status",
                    )
                    yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)
                    yield static_class("", id="thinking-indicator")
                    with vertical_class(id="composer-frame"):
                        yield input_class(
                            placeholder="Ask...",
                            id="composer",
                        )
                        yield static_class(
                            tui._footer_hints_text(session),
                            id="footer-hints",
                        )
                yield static_class("", id="info-separator")
                yield static_class(
                    tui._info_panel_default_text(session),
                    id="info-panel",
                )
            yield option_list_class(id="suggestions", classes="hidden", markup=False)

        def on_mount(self) -> None:
            self.query_one("#composer", tui.Input).focus()

        def on_input_changed(self, event: tui.Input.Changed) -> None:
            if event.input.id == "composer":
                self._refresh_completions()

        def _refresh_completions(self) -> None:
            composer = self.query_one("#composer", tui.Input)
            before_cursor = composer.value[: composer.cursor_position]
            self.completion_candidates = self.completion_engine.candidates(
                before_cursor,
                tui._tui_command_suggestions(),
            )
            suggestions = self.query_one("#suggestions", tui.OptionList)
            if not self.completion_candidates:
                suggestions.set_options([])
                suggestions.add_class("hidden")
                return
            suggestions.set_options(
                [f"{c.text:<22} {c.description}" for c in self.completion_candidates]
            )
            suggestions.highlighted = 0
            suggestions.remove_class("hidden")
            self.set_focus(suggestions)
            self.set_focus(composer)

    async def check_highlight() -> None:
        app = CompletionStress()
        async with app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            # Type "/" to trigger completions
            await pilot.press("/")
            await pilot.pause()
            suggestions = app.query_one("#suggestions", tui.OptionList)
            # The suggestion list should be visible with first item highlighted
            assert not suggestions.has_class("hidden")
            assert suggestions.highlighted == 0
            assert suggestions.option_count > 0
            # Composer should retain focus after the brief focus swap
            assert app.focused is composer

    asyncio.run(check_highlight())


def test_plain_composer_typing_does_not_query_slash_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    def fail_command_suggestions() -> list[object]:
        raise AssertionError("plain typing should not query slash commands")

    monkeypatch.setattr(
        "interfaces.tui.composer_controls._tui_command_suggestions",
        fail_command_suggestions,
    )
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_plain_typing() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)

            await pilot.press("h")
            await pilot.press("i")
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            assert composer.value == "hi"
            assert app.completion_candidates == []
            assert not suggestions.has_class("visible")

    asyncio.run(check_plain_typing())


def test_tab_applies_highlighted_completion_in_composer() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_tab_completion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)

            await pilot.press("/")
            await pilot.pause()
            assert composer.value == "/"
            assert app.completion_candidates
            suggestions = app.query_one("#suggestions", tui.OptionList)
            prompt = _option_prompt_plain(suggestions, 0)
            assert prompt.startswith("→ /help")

            await pilot.press("tab")
            await pilot.pause()

            assert composer.value == "/help "
            assert composer.cursor_position == len("/help ")

    asyncio.run(check_tab_completion())


def test_enter_submits_highlighted_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    handled: list[str] = []

    def fake_handle_inline_command(value: str) -> None:
        handled.append(value)

    async def check_enter_completion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "_handle_inline_command", fake_handle_inline_command)
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/model"
            composer.cursor_position = len("/model")
            app._refresh_completions()

            await pilot.press("enter")
            await pilot.pause()

            assert handled == ["/models"]
            assert composer.value == ""

    asyncio.run(check_enter_completion())


def test_clicking_command_completion_executes_command(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    handled: list[str] = []

    def fake_handle_inline_command(value: str) -> None:
        handled.append(value)

    async def check_click_completion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "_handle_inline_command", fake_handle_inline_command)
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/model"
            composer.cursor_position = len("/model")
            app._refresh_completions()
            await pilot.pause()

            await pilot.click("#suggestions", offset=(2, 0))
            await pilot.pause()

            assert handled == ["/models"]
            assert composer.value == ""

    asyncio.run(check_click_completion())


def test_hovering_command_completion_moves_active_row() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_hover_completion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/sta"
            composer.cursor_position = len("/sta")
            app._refresh_completions()
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)
            position = app.query_one("#completion-position", tui.Static)

            assert [candidate.text.strip() for candidate in app.completion_candidates] == [
                "status",
                "stats",
            ]
            assert suggestions.highlighted == 0
            assert str(position.render()) == "  (1/2)"
            assert not suggestions.has_class("mouse-hovering")

            await pilot.hover("#suggestions", offset=(2, 1))
            await pilot.pause()

            assert suggestions.highlighted == 1
            assert suggestions.has_class("mouse-hovering")
            assert str(position.render()) == "  (2/2)"

    asyncio.run(check_hover_completion())


def test_hovering_command_completion_does_not_rebuild_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_hover_completion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/sta"
            composer.cursor_position = len("/sta")
            app._refresh_completions()
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)

            def fail_set_options(_options: object) -> object:
                raise AssertionError("hover should update the active row incrementally")

            monkeypatch.setattr(suggestions, "set_options", fail_set_options)

            await pilot.hover("#suggestions", offset=(2, 1))
            await pilot.pause()

            assert suggestions.highlighted == 1
            assert suggestions.has_class("mouse-hovering")

    asyncio.run(check_hover_completion())


def test_hovering_inline_menu_does_not_rebuild_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_hover_inline_menu() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_inline_menu(
                name="test",
                step="menu",
                title="Choose",
                options=[
                    ("First", "first option"),
                    ("Second", "second option"),
                ],
            )
            await pilot.pause()

            suggestions = app.query_one("#suggestions", tui.OptionList)

            def fail_set_options(_options: object) -> object:
                raise AssertionError("hover should update the active row incrementally")

            monkeypatch.setattr(suggestions, "set_options", fail_set_options)

            await pilot.hover("#suggestions", offset=(2, 1))
            await pilot.pause()

            assert suggestions.highlighted == 1
            assert suggestions.has_class("mouse-hovering")

    asyncio.run(check_hover_inline_menu())


def test_models_completion_menu_uses_readable_columns() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _keyless_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_model_columns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()

            first = app._format_completion_candidate(
                tui.CompletionCandidate(
                    text=" openai ",
                    description="Pollinations",
                    start_position=0,
                    display_provider="OpenAI",
                    display_model="openai",
                    display_source="Pollinations",
                    display_tags="free current",
                )
            )

            assert isinstance(first, str)
            assert first.startswith("  PROVIDER openai  MODEL openai")
            assert "SOURCE pollinations" in first
            assert "STATE free current" in first
            assert "/models" not in first

    asyncio.run(check_model_columns())


def test_models_command_shows_plain_suggestion() -> None:
    """Typing /models shows a regular command suggestion, not inline model picks."""
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _keyless_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_models_suggestion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/models"
            composer.cursor_position = len("/models")
            app._refresh_completions()
            await pilot.pause()

            assert len(app.completion_candidates) == 1
            assert app.completion_candidates[0].text == "models "
            assert app.completion_candidates[0].description == "Pick the active model"
            suggestions = app.query_one("#suggestions", tui.OptionList)
            footer = app.query_one("#footer-hints", tui.Static)
            assert suggestions.has_class("visible")
            assert not suggestions.has_class("model-picker")
            position = app.query_one("#completion-position", tui.Static)
            assert str(position.render()) == "  (1/1)"
            assert str(footer.render()).startswith(_footer_armory_hint())

    asyncio.run(check_models_suggestion())


def test_command_completion_selected_text_uses_brand_without_bold_row() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_completion_styles() -> None:
        async with typed_app.run_test(size=(120, 24)):
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/"
            composer.cursor_position = len("/")
            candidate = tui.CompletionCandidate(
                text="help ",
                description="Show available commands",
                start_position=0,
            )

            selected = app._format_completion_candidate(candidate, selected=True)
            unselected = app._format_completion_candidate(candidate, selected=False)
            palette = tui.current_palette()

            assert not isinstance(selected, str)
            assert not isinstance(unselected, str)
            assert selected.plain.startswith("→ /help")
            assert unselected.plain.startswith("  /help")
            assert "Show available commands" in selected.plain

            selected_styles = [str(span.style) for span in selected.spans]
            unselected_styles = [str(span.style) for span in unselected.spans]
            assert any(palette.brand_primary in style for style in selected_styles)
            assert any(palette.text_muted in style for style in selected_styles)
            assert not any("bold" in style.lower() for style in selected_styles)
            assert any(palette.text_secondary in style for style in unselected_styles)
            assert any(palette.text_muted in style for style in unselected_styles)
            assert not any("bold" in style.lower() for style in unselected_styles)

    asyncio.run(check_completion_styles())


def test_command_completion_column_tracks_visible_commands() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_completion_width() -> None:
        async with typed_app.run_test(size=(120, 24)):
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/"
            composer.cursor_position = len("/")
            app.completion_candidates = [
                tui.CompletionCandidate(text=f"{name} ", description=description, start_position=0)
                for name, description in (
                    ("help", "Show available commands"),
                    ("exit", "Leave Heph"),
                    ("login", "Authenticate"),
                    ("logout", "Clear credentials"),
                    ("status", "Show status"),
                    ("new", "Start a new chat"),
                    ("armory", "Browse armories"),
                    ("much-longer-command", "Visible after scrolling"),
                )
            ]

            suggestions = app.query_one("#suggestions", tui.OptionList)
            app._set_completion_options(highlighted=0)
            first_visible = suggestions.get_option_at_index(0).prompt
            assert str(first_visible).startswith("→ /help      Show available commands")

            app._set_completion_options(highlighted=7)
            scrolled_visible = suggestions.get_option_at_index(0).prompt
            assert str(scrolled_visible).startswith(
                "  /help                   Show available commands"
            )

    asyncio.run(check_completion_width())


def test_command_completion_column_ignores_stale_filtered_height() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_stale_height() -> None:
        async with typed_app.run_test(size=(120, 24)):
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/"
            composer.cursor_position = len("/")
            app.completion_candidates = [
                tui.CompletionCandidate(text=f"{name} ", description=description, start_position=0)
                for name, description in (
                    ("help", "Show available commands"),
                    ("exit", "Leave Heph"),
                    ("login", "Authenticate"),
                    ("logout", "Clear credentials"),
                    ("status", "Show status"),
                    ("new", "Start a new chat"),
                    ("armory", "Browse armories"),
                )
            ]

            assert app._completion_command_width(0, 1) == len("/help")

    asyncio.run(check_stale_height())


def test_visible_option_height_ignores_stale_full_list_height() -> None:
    assert (
        visible_option_height(
            next_option_count=0,
            current_option_count=26,
            rendered_height=1,
            max_visible_rows=7,
        )
        == 0
    )
    assert (
        visible_option_height(
            next_option_count=26,
            current_option_count=26,
            rendered_height=1,
            max_visible_rows=7,
        )
        == 7
    )


@pytest.mark.parametrize(
    ("next_option_count", "current_option_count", "rendered_height", "max_visible_rows", "height"),
    [
        (4, 0, 0, 7, 4),
        (4, 2, 2, 7, 4),
        (26, 26, 1, 7, 7),
        (3, 5, 3, 7, 3),
        (3, 5, 4, 7, 4),
    ],
)
def test_visible_option_height_preserves_stable_rows(
    next_option_count: int,
    current_option_count: int,
    rendered_height: int,
    max_visible_rows: int,
    height: int,
) -> None:
    assert (
        visible_option_height(
            next_option_count=next_option_count,
            current_option_count=current_option_count,
            rendered_height=rendered_height,
            max_visible_rows=max_visible_rows,
        )
        == height
    )


def test_command_completion_columns_restore_after_filter_reset() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_filter_reset_columns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/a"
            composer.cursor_position = len("/a")
            app._refresh_completions()
            await pilot.pause()
            assert [candidate.text.strip() for candidate in app.completion_candidates] == [
                "armory"
            ]

            composer.value = "/"
            composer.cursor_position = len("/")
            app._refresh_completions()
            await pilot.pause()

            columns = _completion_description_columns(app)[:7]
            assert columns
            assert len(set(columns)) == 1
            assert columns[0] == len("→ /armory") + 4

    asyncio.run(check_filter_reset_columns())


def test_busy_footer_keeps_exit_hint_with_completion_menu_visible() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_busy_footer() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/"
            composer.cursor_position = 1
            app._refresh_completions()
            app.busy = True
            app._refresh_footer_hints()
            await pilot.pause()

            footer = app.query_one("#footer-hints", tui.Static)
            position = app.query_one("#completion-position", tui.Static)
            assert str(footer.render()) == "STOP esc  EXIT ctrl+c"
            assert str(position.render()) == f"  (1/{len(app.completion_candidates)})"

    asyncio.run(check_busy_footer())


def test_escape_cancels_busy_turn() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_escape_cancel() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app.busy = True
            await pilot.press("escape")
            await pilot.press("escape")
            await pilot.pause()

            assert app.abort_event.is_set()
            interrupt_notices = [
                entry
                for entry in app.state.transcript
                if entry.kind == "notice" and entry.content == "Interrupt requested."
            ]
            assert len(interrupt_notices) == 1

    asyncio.run(check_escape_cancel())


def test_escape_clears_active_turn_immediately_and_ignores_late_callbacks() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_active_cancel() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            abort_event = _mark_active_turn(app)
            turn_key = app._current_turn_key()
            turn_token = app._active_turn_tokens[turn_key]
            app._side_panel_progress = "reading"

            await pilot.press("escape")
            await pilot.pause()

            assert abort_event.is_set()
            assert app.busy is False
            assert app._side_panel_progress == ""
            assert turn_key not in app._active_turns
            assert turn_key not in app._active_turn_sessions
            assert turn_key not in app._active_turn_tokens
            assert turn_token in app._cancelled_turn_tokens
            footer = app.query_one("#footer-hints", tui.Static)
            assert "STOP" not in str(footer.render())

            app._handle_turn_reply(turn_key, turn_token, "late answer")
            app._handle_turn_notice(turn_key, turn_token, "late notice")
            app._handle_turn_error(turn_key, turn_token, "late error")

            assert not any("late" in entry.content for entry in app.state.transcript)

            replacement_event = threading.Event()
            app._next_turn_token += 1
            replacement_token = app._next_turn_token
            app._active_turns[turn_key] = replacement_event
            app._active_turn_sessions[turn_key] = app.session
            app._active_turn_tokens[turn_key] = replacement_token
            app._sync_busy_to_current_session()

            app._finish_background_turn(turn_key, app.session, turn_token)

            assert turn_token not in app._cancelled_turn_tokens
            assert app._active_turns[turn_key] is replacement_event
            assert app._active_turn_tokens[turn_key] == replacement_token
            assert app.busy is True

    asyncio.run(check_active_cancel())


def test_slash_on_empty_composer_preserves_cursor_after_focus_swap() -> None:
    """Pressing / must show completions without selecting/highlighting the / character.

    Regression test: the focus swap in _refresh_completions (set_focus(suggestions)
    then set_focus(composer)) was causing Textual's Input to select its text, so the
    next keypress would replace the / instead of appending to it.
    """
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()
    vertical_class = tui._transparent_vertical_class()
    horizontal_class = tui._transparent_horizontal_class()
    input_class = tui._transparent_input_class()
    static_class = tui._transparent_static_class()
    rich_log_class = tui._transparent_rich_log_class()
    option_list_class = tui._transparent_option_list_class()

    engine = tui.SlashCompletionEngine()

    class SlashStress(tui.App[None]):
        CSS = tui._tui_css()

        def __init__(self) -> None:
            super().__init__()
            self.completion_engine = engine
            self.completion_candidates: list[tui.CompletionCandidate] = []

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with horizontal_class(id="main-layout"):
                with vertical_class(id="shell"):
                    yield static_class(
                        tui._status_text(session),
                        id="status",
                    )
                    yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)
                    yield static_class("", id="thinking-indicator")
                    with vertical_class(id="composer-frame"):
                        yield input_class(
                            placeholder="Ask...",
                            id="composer",
                        )
                        yield static_class(
                            tui._footer_hints_text(session),
                            id="footer-hints",
                        )
                yield static_class("", id="info-separator")
                yield static_class(
                    tui._info_panel_default_text(session),
                    id="info-panel",
                )
            yield option_list_class(id="suggestions", classes="hidden", markup=False)

        def on_mount(self) -> None:
            composer = self.query_one("#composer", tui.Input)
            composer.select_on_focus = False
            composer.focus()

        def on_input_changed(self, event: tui.Input.Changed) -> None:
            if event.input.id == "composer":
                self._refresh_completions()

        def _refresh_completions(self) -> None:
            composer = self.query_one("#composer", tui.Input)
            before_cursor = composer.value[: composer.cursor_position]
            self.completion_candidates = self.completion_engine.candidates(
                before_cursor,
                tui._tui_command_suggestions(),
            )
            suggestions = self.query_one("#suggestions", tui.OptionList)
            if not self.completion_candidates:
                suggestions.set_options([])
                suggestions.add_class("hidden")
                return
            suggestions.set_options(
                [f"{c.text:<22} {c.description}" for c in self.completion_candidates]
            )
            suggestions.highlighted = 0
            suggestions.remove_class("hidden")
            self.set_focus(suggestions)
            self.set_focus(composer)

    async def check_cursor_preserved() -> None:
        app = SlashStress()
        async with app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            # Type "/" to trigger completions
            await pilot.press("/")
            await pilot.pause()
            # Composer value should be "/" and cursor should be at the end
            assert composer.value == "/"
            assert composer.cursor_position == 1
            # Typing another character should append, not replace
            await pilot.press("h")
            await pilot.pause()
            assert composer.value == "/h"
            assert composer.cursor_position == 2

    asyncio.run(check_cursor_preserved())


def test_completion_menu_scrolls_after_highlight_reaches_center() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scroll_policy() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("/")
            await pilot.pause()

            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),
            )  # ty:ignore[redundant-cast]
            footer = app.query_one("#footer-hints", tui.Static)

            assert suggestions.highlighted == 0
            assert suggestions.scroll_y == 0
            assert [c.text.strip() for c in app.completion_candidates[:7]] == [
                "help",
                "exit",
                "login",
                "local",
                "logout",
                "status",
                "new",
            ]

            expected = (
                (1, 0),
                (2, 0),
                (3, 0),
                (4, 1),
                (5, 2),
            )
            for highlighted, scroll_y in expected:
                await pilot.press("down")
                await pilot.pause()

                assert suggestions.highlighted == highlighted
                assert suggestions.scroll_y == scroll_y
                position = app.query_one("#completion-position", tui.Static)
                expected_position = f"  ({highlighted + 1}/{suggestions.option_count})"
                assert str(position.render()) == expected_position
                assert str(footer.render()).startswith(_footer_armory_hint())

    asyncio.run(check_scroll_policy())


def test_completion_menu_highlight_moves_down_at_bottom() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_bottom_policy() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("/")
            await pilot.pause()

            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),
            )  # ty:ignore[redundant-cast]
            visible_rows = min(
                suggestions.option_count,
                suggestions.size.height,
                7,
            )
            last_index = suggestions.option_count - 1
            last_scroll_y = suggestions.option_count - visible_rows

            for _ in range(last_index):
                await pilot.press("down")
            await pilot.pause()

            assert suggestions.highlighted == last_index
            assert suggestions.scroll_y == last_scroll_y
            highlighted = suggestions.highlighted
            assert highlighted is not None
            assert highlighted - suggestions.scroll_y == visible_rows - 1

    asyncio.run(check_bottom_policy())


def test_tui_runs_external_commands_in_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    calls: list[str] = []

    def fake_refresh_status() -> None:
        calls.append("status")

    def fake_run_worker(work: object, *, thread: bool = False) -> object:
        calls.append(f"worker:{thread}")
        return work

    monkeypatch.setattr(app, "_refresh_status", fake_refresh_status)
    monkeypatch.setattr(app, "run_worker", fake_run_worker)

    app._handle_external_input("/priority")

    assert app.busy is True
    assert app._thinking_label == "working"
    assert calls == ["status", "worker:True"]


def test_external_command_collects_plain_output_for_compact_append(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    calls: list[tuple[str, tuple[object, ...]]] = []

    def fake_call_from_thread(fn: object, *args: object) -> None:
        name = getattr(fn, "__name__", fn.__class__.__name__)
        calls.append((name, args))

    def fake_handle_input(session: ChatSession, _value: str, _history: object):
        print("phase 1")
        print("phase 2", end="")
        return session, True

    monkeypatch.setattr(app, "call_from_thread", fake_call_from_thread)
    monkeypatch.setattr("interfaces.terminal.input.handle_input", fake_handle_input)

    app._run_external_command("/priority")

    streamed = [args[0] for name, args in calls if name == "_append_notice"]
    assert streamed == []
    finish = [args for name, args in calls if name == "_finish_external_command"]
    assert finish
    assert finish[0][2] == "phase 1\nphase 2"


def test_status_command_output_is_not_streamed_line_by_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    calls: list[tuple[str, tuple[object, ...]]] = []

    def fake_call_from_thread(fn: object, *args: object) -> None:
        name = getattr(fn, "__name__", fn.__class__.__name__)
        calls.append((name, args))

    monkeypatch.setattr(app, "call_from_thread", fake_call_from_thread)

    app._run_external_command("/status")

    streamed = [args[0] for name, args in calls if name == "_append_notice"]
    assert streamed == []
    finish = [args for name, args in calls if name == "_finish_external_command"]
    assert finish
    finish_output = cast("str", finish[0][2])
    assert "Model:" in finish_output
    assert "Runtime:" in finish_output


def test_external_command_indents_streamed_activity_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)
    settings_store.save_setting("activity_trace_mode", settings_store.ACTIVITY_TRACE_TOOL_CALLS)

    app = tui.HephTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    calls: list[tuple[str, tuple[object, ...]]] = []

    def fake_call_from_thread(fn: object, *args: object) -> None:
        name = getattr(fn, "__name__", fn.__class__.__name__)
        calls.append((name, args))

    def fake_handle_input(session: ChatSession, _value: str, _history: object):
        print("info: Ran model request gpt-5.4-mini (turn 1, 4 message(s)).")
        print(
            "info: Read complete model response from gpt-5.4-mini: "
            "142 character(s), 0 tool call(s) in 3.3s."
        )
        return session, True

    monkeypatch.setattr(app, "call_from_thread", fake_call_from_thread)
    monkeypatch.setattr("interfaces.terminal.input.handle_input", fake_handle_input)

    app._run_external_command("/priority")

    streamed = [args[0] for name, args in calls if name == "_append_notice"]
    assert streamed == [
        "    Ran model request gpt-5.4-mini (turn 1, 4 message(s)).",
        (
            "    Read complete model response from gpt-5.4-mini: "
            "142 character(s), 0 tool call(s) in 3.3s."
        ),
    ]
