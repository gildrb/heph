"""Tests for the optional Textual shell wrapper."""

from __future__ import annotations

import asyncio
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from rich.segment import Segment
from textual.strip import Strip

from hephaistos import tui
from hephaistos.armory.search import KnownArmory, add_known_armory
from hephaistos.armory.storage import initialize
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession
from hephaistos.parameters import settings as settings_store
from hephaistos.providers.config import ProviderConfig, default_config
from hephaistos.study import StudyAutonomyMode
from hephaistos.terminal import current_theme_name, set_theme
from hephaistos.tui import keymap
from hephaistos.tui.armory_browser import armory_detail, build_entries, default_armory_home
from hephaistos.tui.inline_flows import (
    _dedupe_inline_options,
    _duplicate_model_names,
    _inline_menu_option_text,
    _model_choice_from_label,
    _model_choice_label,
    overview_topic_menu,
    overview_topic_options,
)
from hephaistos.tui.transparent import Region as _Region
from hephaistos.tui.transparent import style_without_black_background

if TYPE_CHECKING:
    from textual.app import App as TextualApp
    from textual.screen import Screen
    from textual.widget import Widget
    from textual.widgets import OptionList as TextualOptionList


class _RichSpanLike(Protocol):
    style: object


class _RichPromptLike(Protocol):
    spans: list[_RichSpanLike]


def _plain_session() -> ChatSession:
    conversation = Conversation()
    conversation.add("system", "test")
    return ChatSession(
        config=ChatConfig(base_url="https://example.test", model="test-model"),
        conversation=conversation,
        session_id="session-test",
    )


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
        "HEPHAISTOS_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ZAI_API_KEY",
        "CUSTOM_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


def test_session_status_for_plain_session() -> None:
    status = tui._status_lines(_plain_session())

    assert "test-model" in status
    assert "armory" in status
    assert "mode guided" in status
    assert "enter" not in status
    assert "/help" not in status


def test_session_status_shows_free_for_keyless_provider() -> None:
    status = tui._status_lines(_keyless_session())

    assert "free" in status
    assert "configured" not in status
    assert "missing" not in status


def test_footer_hints_show_idle_shortcuts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.tui.display_text.armory_shortcut_key", lambda: "ctrl+a")

    hints = tui._footer_hints_text(_plain_session())
    plain = hints.plain

    assert "enter" in plain
    assert "tab" in plain
    assert "ctrl+p" in plain
    assert "ctrl+a" in plain
    assert "ctrl+d" in plain
    assert "ctrl+a armory" in plain
    assert "test-model" not in plain


def test_footer_hints_show_cancel_when_busy() -> None:
    hints = tui._footer_hints_text(_plain_session(), busy=True)
    plain = hints.plain

    assert "esc" in plain
    assert "stop" in plain
    assert "ctrl+c" in plain
    assert "cancel" in plain
    assert "enter" not in plain
    assert "/help" not in plain


def test_armory_shortcut_uses_tmux_fallback_for_ctrl_a_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        args: tuple[str, ...],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        assert args == ("tmux", "show-options", "-gqv", "prefix")
        assert capture_output is True
        assert check is False
        assert text is True
        assert timeout > 0
        return subprocess.CompletedProcess(args, 0, stdout="C-a\n", stderr="")

    monkeypatch.setenv("TMUX", "/tmp/tmux-session")
    monkeypatch.setattr(keymap.subprocess, "run", fake_run)
    keymap.tmux_uses_ctrl_a_prefix.cache_clear()
    try:
        assert keymap.armory_shortcut_key() == "ctrl+o"
    finally:
        keymap.tmux_uses_ctrl_a_prefix.cache_clear()


def test_footer_hints_show_api_missing_when_unconfigured() -> None:
    session = _plain_session()
    session.config.api_key = None  # ty:ignore[invalid-assignment]
    hints = tui._footer_hints_text(session)
    plain = hints.plain

    assert "api missing" in plain


def test_footer_command_shortcuts_share_neutral_shortcut_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("hephaistos.tui.display_text.armory_shortcut_key", lambda: "ctrl+a")

    hints = tui._footer_hints_text(_plain_session())
    palette = tui.current_palette()
    dim_label_style = f"dim {palette.dim}"
    shortcut_style = f"dim {palette.shortcut}"
    labels = ("enter", "tab", "ctrl+p", "ctrl+a", "ctrl+d")
    shortcut_styles: dict[str, list[str]] = {}
    for label in labels:
        start = hints.plain.index(label)
        end = start + len(label)
        shortcut_styles[label] = [
            str(span.style) for span in hints.spans if span.start <= start and span.end >= end
        ]

    assert str(hints.style) == dim_label_style
    for styles in shortcut_styles.values():
        assert styles == [shortcut_style]
        assert not any(palette.brand in style for style in styles)
        assert not any(palette.emphasis in style for style in styles)
        assert not any("bold" in style.lower() for style in styles)


def test_high_contrast_routine_labels_use_neutral_emphasis() -> None:
    set_theme("high_contrast")
    try:
        session = _plain_session()
        status = tui._status_text(session)
        hints = tui._footer_hints_text(session)
        panel = tui._info_panel_default_text(session)
        palette = tui.current_palette()

        assert palette.emphasis != palette.accent

        mode_start = status.plain.index("guided")
        mode_styles = [
            str(span.style)
            for span in status.spans
            if span.start <= mode_start and span.end >= mode_start + len("guided")
        ]
        shortcut_start = hints.plain.index("ctrl+p")
        shortcut_styles = [
            str(span.style)
            for span in hints.spans
            if span.start <= shortcut_start and span.end >= shortcut_start + len("ctrl+p")
        ]
        title_start = panel.plain.index("Study session")
        title_styles = [
            str(span.style)
            for span in panel.spans
            if span.start <= title_start and span.end >= title_start + len("Study session")
        ]

        for styles in (mode_styles, title_styles):
            assert any(palette.emphasis in style for style in styles)
            assert not any(palette.accent in style for style in styles)
        assert str(hints.style) == f"dim {palette.dim}"
        assert shortcut_styles == [f"dim {palette.shortcut}"]
        assert not any(palette.emphasis in style for style in shortcut_styles)
        assert not any(palette.accent in style for style in shortcut_styles)
    finally:
        set_theme("forge")


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
        "hephaistos.runtime.engine.load_credentials",
        lambda _provider, **_kwargs: object(),
    )

    assert "api configured" in tui._status_lines(session)
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
        "hephaistos.runtime.engine.load_credentials",
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
    assert "#status {\n    height: auto;\n    max-height: 2;\n    width: auto;" in css
    assert ("#footer-hints {\n    height: 1;\n    width: auto;\n    max-width: 100%;") in css
    assert "#completion-stack {\n    height: 9;" in css
    assert "#transcript-spacer {\n    height: 1;" in css
    assert "#transcript:focus" in css
    assert "background-tint: transparent;" in css
    suggestions_start = css.index("#suggestions {")
    suggestions_end = css.index("}", suggestions_start)
    suggestions_block = css[suggestions_start:suggestions_end]

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
    assert f"background: {tui.current_palette().panel};" in composer_frame_block
    assert f"background: {tui.current_palette().panel};" in prompt_block
    assert f"background: {tui.current_palette().panel};" in composer_block
    assert "scrollbar-size: 0 0;" in suggestions_block
    assert "scrollbar-size-vertical" not in suggestions_block
    assert "padding: 0 2;" in option_block
    assert "border-bottom: tall" not in css
    assert "background: #FFFFFF;" not in css
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


def test_non_default_themes_do_not_paint_terminal_background() -> None:
    try:
        for theme in ("light", "high_contrast"):
            set_theme(theme)
            palette = tui.current_palette()
            css = tui._tui_css()

            assert palette.is_transparent is True
            assert palette.background == "transparent"
            assert "background: transparent;" in css
            assert palette.background in css
    finally:
        set_theme("forge")


def test_runtime_theme_switch_keeps_core_tui_backgrounds_transparent() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
                or segment.style.bgcolor.name == palette.panel.lower()
                for segment in strip
            )

    async def check_runtime_switch() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_settings_flow()
            app._handle_inline_menu_choice("Appearance")
            app._handle_appearance_choice("light")
            await pilot.pause()

            assert app.styles.background is not None
            assert app.styles.background.a == 0.0
            assert app.screen.styles.background is not None
            assert app.screen.styles.background.a == 0.0

            assert_core_widgets_are_transparent()

            app._handle_appearance_choice("high_contrast")
            await pilot.pause()

            assert app.styles.background is not None
            assert app.styles.background.a == 0.0
            assert app.screen.styles.background is not None
            assert app.screen.styles.background.a == 0.0
            assert_core_widgets_are_transparent()

    asyncio.run(check_runtime_switch())


def test_tui_uses_transparent_widgets_for_all_palettes() -> None:
    if tui.RichLog is None:
        pytest.skip("Textual is not installed")

    palette = tui.ThemePalette(
        name="opaque-test",
        brand="#ff6600",
        panel="#000000",
        stone="#111111",
        text="#ffffff",
        dim="#999999",
        accent="#ffffff",
        emphasis="#ffffff",
        shortcut="#999999",
        ember="#ff6600",
        configured="#00ff00",
        error="#ff0000",
        success="#00ff00",
        highlight="#222222",
        selection_background="#bbbbbb",
        selection_text="#000000",
        material_enabled="#00ff00",
        material_disabled="#ff6600",
        is_transparent=False,
        background="#000000",
    )

    widgets = tui._WidgetClasses.from_palette(palette)

    assert widgets.screen.__name__ == "BlankBackgroundWidget"
    assert widgets.vertical.__name__ == "TransparentWidget"
    assert widgets.horizontal.__name__ == "TransparentWidget"
    assert issubclass(widgets.rich_log, tui.RichLog)
    assert widgets.rich_log.can_focus is False


def test_tui_css_has_info_panel_layout() -> None:
    css = tui._tui_css()

    assert "#info-panel" in css
    assert "#info-separator" not in css
    assert "#shell" in css
    shell_start = css.index("#shell {")
    shell_end = css.index("}", shell_start)
    shell_block = css[shell_start:shell_end]
    assert "min-width: 0;" in shell_block
    info_start = css.index("#info-panel {")
    info_end = css.index("}", info_start)
    info_block = css[info_start:info_end]
    assert "padding: 0 1;" in info_block


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

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_transcript_backgrounds() -> None:
        async with typed_app.run_test(size=(100, 18)) as pilot:
            app._append_user("User prompt", mark_working=False)
            app._append_assistant_reply("Assistant reply")
            await pilot.pause()

            transcript = app.query_one("#transcript")
            panel = tui.current_palette().panel.lower()
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
    app = tui.HephaistosTui(
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
    app = tui.HephaistosTui(
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
            assert any(palette.dim.lower() in style for style in activity_styles)
            assert any(palette.dim.lower() in style for style in notice_styles)

    asyncio.run(check_activity_style())


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


def test_tui_css_materials_highlight_uses_state_colours() -> None:
    css = tui._tui_css()
    palette = tui.current_palette()

    assert "#materials-list > .option-list--option-highlighted" not in css
    assert "#materials-list.material-enabled > .option-list--option-highlighted" in css
    assert f"background: {palette.material_enabled};" in css
    assert "#materials-list.material-disabled > .option-list--option-highlighted" in css
    assert f"background: {palette.material_disabled};" in css
    disabled_start = css.index(
        "#materials-list.material-disabled > .option-list--option-highlighted"
    )
    disabled_end = css.index("}", disabled_start)
    disabled_block = css[disabled_start:disabled_end]
    assert f"color: {palette.selection_text};" in disabled_block


def test_tui_css_completion_highlight_avoids_brand_strip() -> None:
    css = tui._tui_css()
    palette = tui.current_palette()
    block_start = css.index("#suggestions > .option-list--option-highlighted")
    block_end = css.index("}", block_start)
    block = css[block_start:block_end]

    assert "background: transparent;" in block
    assert f"color: {palette.text};" in block
    assert f"background: {palette.selection_background};" not in block
    assert f"color: {palette.selection_text};" not in block


def test_tui_css_inline_menu_highlight_has_no_brand_stripe() -> None:
    css = tui._tui_css()

    assert "#suggestions.inline-menu > .option-list--option-highlighted" not in css


def test_inline_menu_selected_label_uses_brand_without_recoloring_description() -> None:
    selected = _inline_menu_option_text("Folgen", "study this topic", selected=True)
    unselected = _inline_menu_option_text("Folgen", "study this topic", selected=False)
    palette = tui.current_palette()

    assert not isinstance(selected, str)
    assert not isinstance(unselected, str)
    selected_styles = [str(span.style) for span in selected.spans]
    unselected_styles = [str(span.style) for span in unselected.spans]
    assert any(palette.brand in style and "bold" in style for style in selected_styles)
    assert any(palette.dim in style for style in selected_styles)
    assert not any(palette.brand in style for style in unselected_styles)


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
        assert f"background: {palette.selection_background};" in block
        assert f"color: {palette.selection_text};" in block


def test_info_panel_material_colours_match_materials_picker() -> None:
    session = _plain_session()
    session.source_files = ("materials/enabled.pdf", "materials/disabled.pdf")
    session.disabled_source_files.add("materials/disabled.pdf")

    panel = tui._info_panel_default_text(session)
    spans = {(span.start, span.end, str(span.style)) for span in panel.spans}
    palette = tui.current_palette()

    enabled_start = panel.plain.index("@enabled.pdf")
    disabled_start = panel.plain.index("@disabled.pdf")
    assert (enabled_start, enabled_start + len("@enabled.pdf"), palette.material_enabled) in spans
    assert (
        disabled_start,
        disabled_start + len("@disabled.pdf"),
        palette.material_disabled,
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
    panel = tui.current_palette().panel

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

    assert "height: 3;" in frame_block
    assert "width: 100%;" in frame_block
    assert "layout: horizontal;" in frame_block
    assert "padding: 1 0;" in frame_block
    assert f"background: {panel};" in frame_block
    assert "width: 2;" in prompt_block
    assert "padding: 0 0;" in prompt_block
    assert f"background: {panel};" in prompt_block
    assert "width: 100%;" in composer_block
    assert "padding: 0 0;" in composer_block
    assert "padding: 0 0;" in input_block


def test_composer_text_is_inset_inside_full_width_chatbox() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert str(prompt.render()) == "▸"
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
    assert "min-height: 9;" in stack_block
    assert "max-height: 9;" in stack_block
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

    app = tui.HephaistosTui(
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
            assert str(footer.render()).startswith("enter send")
            assert suggestions.size.width == stack.size.width
            assert suggestions.has_class("visible")
            assert suggestions.size.height <= 7
            assert position.region.y == suggestions.region.y + suggestions.size.height
            assert footer.region.y == position.region.y + 1

    asyncio.run(check_inline_menu_layout())


def test_transcript_overflow_scrolls_without_moving_composer() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
                    "then add study materials so I can answer from your sources."
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

    class Smoke(tui.App[None]):
        CSS = tui._tui_css()

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            status_text = tui._status_text(session)
            hints_text = tui._footer_hints_text(session)
            with tui.Vertical(id="main-layout"):
                yield tui.Static(status_text, id="status")
                yield tui.Static(hints_text, id="footer-hints")

    async def check_segments() -> None:
        app = Smoke()
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

    class Smoke(tui.App[None]):
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
                        placeholder='Ask anything... "What do I need to study next?"',
                        id="composer",
                    )
                    yield static_class(
                        tui._footer_hints_text(session),
                        id="footer-hints",
                    )

    async def check_layout_blanks() -> None:
        app = Smoke()
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

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_separator_absent() -> None:
        async with typed_app.run_test(size=(160, 24)) as pilot:
            await pilot.pause()
            assert list(app.query("#info-separator")) == []

            # The seam between #shell and #info-panel must also be free of any
            # synthetic ``rgb(0,0,0)`` cells. Textual's styles cache pads
            # widget content with the resolved background style, which
            # collapses the ``Color(0,0,0,a=0)`` produced by
            # ``background: transparent`` into opaque black -- exactly the
            # stripe the user sees at the shell/info-panel boundary.
            shell = app.query_one("#shell")
            info_panel = app.query_one("#info-panel")
            for sibling in (shell, info_panel):
                crop = _Region(0, 0, sibling.size.width, sibling.size.height)
                strips = sibling.render_lines(crop)
                for strip in strips:
                    for segment in strip:
                        assert "on #000000" not in str(segment.style)

    asyncio.run(check_separator_absent())


def test_shell_info_panel_seam_has_no_black_background() -> None:
    if tui.Input is None or tui.Static is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            info_panel = app.query_one("#info-panel")
            # Sanity: the sidebar must actually be visible for this test to
            # exercise the seam between two siblings.
            assert info_panel.styles.display != "none"
            assert shell.size.width > 0
            assert info_panel.size.width > 0

            # Inspect the actual composited frame via the screen's
            # compositor: the boundary column is at shell.size.width, and the
            # chop covering the info-panel starts there. Any segment in that
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
            for sibling in (shell, info_panel):
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

    class Smoke(tui.App[None]):
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
        app = Smoke()
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


def test_tui_slash_suggestion_uses_shared_registry() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/sta")

    assert suggestion == "/status "


def test_tui_slash_suggestion_uses_canonical_materials_command() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/mat")

    assert suggestion == "/materials "


def test_info_panel_shows_session_duration_and_material_names() -> None:
    session = _plain_session()
    long_pdf = "materials/very-important-full-pdf-name-for-exam-review.pdf"
    session.source_files = (long_pdf, "materials/calculus.md")
    session.source_file_count = 2

    panel = tui._info_panel_default_text(
        session,
        session_seconds=125,
    )

    lines = panel.plain.splitlines()
    assert lines[0].startswith("  Study session")
    assert lines[1].startswith("  \u2500")
    assert all(line.startswith("  ") for line in lines if line)
    assert "time 2m 05s" in panel.plain
    assert "materials" in panel.plain
    assert "/exam active recall" in panel.plain
    assert "/priority plan focus" in panel.plain
    assert "/remind due review" in panel.plain
    assert "@very-important-full-pdf-name-for-exam-review.pdf" in panel.plain
    assert "@calculus.md" in panel.plain
    assert "☑" not in panel.plain
    assert "☐" not in panel.plain
    assert "..." not in panel.plain
    assert "model" not in panel.plain
    assert "armory" not in panel.plain
    assert "evidence" not in panel.plain


def test_info_panel_message_text_is_indented_from_sidebar_edge() -> None:
    session = _plain_session()
    entry = tui.TuiTranscriptEntry("How do I prepare for the exam?", kind="user")

    panel = tui._info_panel_message_text(entry, session)

    lines = panel.plain.splitlines()
    assert lines[0].startswith("  You message")
    assert lines[1].startswith("  \u2500")
    assert all(line.startswith("  ") for line in lines if line)


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
        ("/help", "Commands"),
        ("/status", "Model:"),
        ("!echo shell-ok", "shell-ok"),
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
            _palette: tui.ThemePalette,
        ) -> None:
            nonlocal captured_state
            captured_state = state

        def run(self, *, mouse: bool = True) -> None:
            nonlocal run_count
            assert mouse is False
            run_count += 1
            assert captured_state is not None
            if run_count == 1:
                captured_state.pending_input = pending_input

    def fake_save_on_exit(_session: ChatSession) -> None:
        return

    def fake_load_history(_cls: type[tui.InputHistory], _path: Path) -> tui.InputHistory:
        return tui.InputHistory()

    monkeypatch.setattr(tui, "HephaistosTui", FakeTui)
    monkeypatch.setattr(tui, "save_on_exit", fake_save_on_exit)
    monkeypatch.setattr(tui.InputHistory, "load", classmethod(fake_load_history))

    tui.run_tui(_plain_session())

    assert captured_state is not None
    assert run_count == 2
    assert any(expected_output in entry.content for entry in captured_state.transcript)


def test_run_tui_applies_saved_theme_on_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_palette: tui.ThemePalette | None = None

    class FakeTui:
        def __init__(
            self,
            _session: ChatSession,
            _state: tui._TuiRuntimeState,
            palette: tui.ThemePalette,
        ) -> None:
            nonlocal captured_palette
            captured_palette = palette

        def run(self, *, mouse: bool = True) -> None:
            assert mouse is False

    def fake_save_on_exit(_session: ChatSession) -> None:
        return

    def fake_load_history(_cls: type[tui.InputHistory], _path: Path) -> tui.InputHistory:
        return tui.InputHistory()

    monkeypatch.setattr(tui, "HephaistosTui", FakeTui)
    monkeypatch.setattr(tui, "save_on_exit", fake_save_on_exit)
    monkeypatch.setattr(tui.InputHistory, "load", classmethod(fake_load_history))
    monkeypatch.setattr(
        tui,
        "load_app_settings",
        lambda: settings_store.AppSettings(theme="high_contrast"),
    )

    try:
        set_theme("forge")
        tui.run_tui(_plain_session())
        assert captured_palette is not None
        assert captured_palette.name == "high_contrast"
        assert current_theme_name() == "high_contrast"
    finally:
        set_theme("forge")


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


def test_status_lines_shows_armory_path() -> None:
    """Status bar text includes the armory path when session has one."""
    session = _plain_session()
    session.armory_path = Path("/tmp/my-armory")

    status = tui._status_lines(session)

    assert "armory /tmp/my-armory" in status


def test_status_lines_shows_none_when_no_armory() -> None:
    """Status bar shows 'none' for armory when no armory is attached."""
    session = _plain_session()

    status = tui._status_lines(session)

    assert "armory none" in status


def test_status_lines_shows_active_study_mode() -> None:
    session = _plain_session()
    session.study_state.autonomy_mode = StudyAutonomyMode.AUTOPILOT

    status = tui._status_lines(session)

    assert "mode autopilot" in status


@pytest.mark.parametrize(
    ("mode", "expected_color", "expected_weight"),
    [
        (StudyAutonomyMode.MANUAL, "#808080", ""),
        (StudyAutonomyMode.GUIDED, "#C8C8C8", ""),
        (StudyAutonomyMode.AUTOPILOT, "#CC3333", "bold"),
    ],
)
def test_status_text_colours_active_study_mode(
    mode: StudyAutonomyMode,
    expected_color: str,
    expected_weight: str,
) -> None:
    session = _plain_session()
    session.study_state.autonomy_mode = mode

    status = tui._status_text(session)
    start = status.plain.index(mode.value, status.plain.index("mode "))
    end = start + len(mode.value)
    mode_styles = [
        str(span.style).lower() for span in status.spans if span.start <= start and span.end >= end
    ]

    assert any(expected_color.lower() in style for style in mode_styles)
    if expected_weight:
        assert any(expected_weight in style for style in mode_styles)


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
        ("/sessions", tui._TuiInputRoute.SESSIONS),
        ("/sessions list", tui._TuiInputRoute.SESSIONS),
        ("/history browse", tui._TuiInputRoute.EXTERNAL),
        ("/history stats", tui._TuiInputRoute.EXTERNAL),
        ("/new", tui._TuiInputRoute.NEW),
        ("/armory", tui._TuiInputRoute.ARMORY),
        ("/armory open", tui._TuiInputRoute.ARMORY),
        ("/help", tui._TuiInputRoute.EXTERNAL),
        ("!echo hi", tui._TuiInputRoute.EXTERNAL),
    ],
)
def test_tui_input_route_classifies_submissions(
    value: str,
    route: tui._TuiInputRoute,
) -> None:
    assert tui._tui_input_route(value) == route


def test_pending_terminal_commands_are_registered() -> None:
    registered = {cmd.name for cmd in tui.get_registry().commands}

    assert registered >= tui._TERMINAL_INTERACTIVE_COMMANDS


def test_tui_input_route_covers_visible_command_suggestions() -> None:
    routes = {
        f"/{suggestion.name}": tui._tui_input_route(f"/{suggestion.name}")
        for suggestion in tui._tui_command_suggestions()
    }

    assert routes["/models"] is tui._TuiInputRoute.EXTERNAL
    assert "/sources" not in routes
    assert "/history" not in routes
    assert routes["/materials"] is tui._TuiInputRoute.MATERIALS
    assert routes["/sessions"] is tui._TuiInputRoute.SESSIONS
    assert routes["/new"] is tui._TuiInputRoute.NEW
    assert routes["/armory"] is tui._TuiInputRoute.ARMORY
    assert all(
        route is tui._TuiInputRoute.EXTERNAL
        for command, route in routes.items()
        if command not in {"/materials", "/sessions", "/new", "/armory"}
    )


def test_armory_command_mode_validates_supported_subcommands() -> None:
    assert tui._armory_command_mode("/armory") == "manage"
    assert tui._armory_command_mode("/armory menu") == "manage"
    assert tui._armory_command_mode("/armory open") == "open"
    assert tui._armory_command_mode("/armory create") == "create"
    assert tui._armory_command_mode("/armory new") == "create"

    assert tui._armory_command_mode("/armory detach") is None
    assert "Usage: /armory" in tui._armory_usage_message()


def test_armory_browser_entries_include_recent_and_missing_armories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    existing = armory_home / "exam-prep"
    initialize(existing)
    missing = armory_home / "missing"
    monkeypatch.setattr(
        "hephaistos.tui.armory_browser.load_known_armory_entries",
        lambda: [
            KnownArmory(existing, exists=True, valid=True),
            KnownArmory(missing, exists=False, valid=False),
        ],
    )

    entries = build_entries(armory_home, allow_create=True)
    recent_labels = [entry.label for entry in entries if entry.is_recent]

    assert len(recent_labels) == 1
    assert "exam-prep" in recent_labels[0]
    assert "recent  " not in recent_labels[0]


def test_armory_browser_detail_describes_material_layout(tmp_path: Path) -> None:
    armory = tmp_path / "exam-prep"
    initialize(armory)
    (armory / "materials" / "exam.md").write_text("# Exam\n", encoding="utf-8")

    detail = armory_detail(armory)

    assert "valid armory" in detail
    assert "1 material file" in detail
    assert "User files: materials/" in detail
    assert "Internal state: .hephaistos/" in detail


def test_ctrl_p_opens_command_palette() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_command_palette() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("ctrl+p")
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


def test_settings_inline_menu_exposes_privacy_and_appearance() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert "Login" in labels
            assert "Logout" in labels

    asyncio.run(check_settings_menu())


def test_overview_topic_reply_opens_arrow_key_study_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    submitted: list[str] = []

    async def check_topic_flow() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._append_assistant_reply(
                "These are the study topics I found in the material:\n"
                "- Enzyme Kinetics [E1]\n"
                "- Protein Folding [E2]\n\n"
                "Choose a topic to study next. In the shell, use ↑/↓ and press Enter.\n\n"
                "Recommended options:\n"
                "- Start with a guided explanation of Enzyme Kinetics [E1].\n"
                "- Practice one exam-style or exercise question on Protein Folding [E2].\n"
                "- Turn the selected topic into a quick recall drill."
            )
            app._open_study_topic_flow(
                [
                    ("Enzyme Kinetics", "study this topic"),
                    ("Protein Folding", "study this topic"),
                ]
            )
            await pilot.pause()

            assert app._inline_flow.name == "study_topic"
            assert app._inline_flow.step == "topic"
            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),
            )  # ty:ignore[redundant-cast]
            assert suggestions.has_class("visible")
            assert suggestions.has_class("inline-menu")
            palette = tui.current_palette()

            def option_styles(index: int) -> list[str]:
                prompt = cast("_RichPromptLike", suggestions.get_option_at_index(index).prompt)
                return [str(span.style) for span in prompt.spans]

            first_styles = option_styles(0)
            second_styles = option_styles(1)
            assert any(palette.brand in style and "bold" in style for style in first_styles)
            assert not any(palette.brand in style for style in second_styles)

            await pilot.press("down")
            await pilot.pause()
            first_styles = option_styles(0)
            second_styles = option_styles(1)
            assert not any(palette.brand in style for style in first_styles)
            assert any(palette.brand in style and "bold" in style for style in second_styles)
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.step == "action"
            assert app._inline_flow.slug == "Protein Folding"
            action_labels = [label for label, _description in app._inline_flow.options]
            assert action_labels == ["Explain it", "Practice it", "Recall drill"]

            monkeypatch.setattr(app, "_submit_inline_chat_value", submitted.append)
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()

            assert submitted == [
                "Give me one source-grounded practice question about Protein Folding."
            ]
            assert app._inline_flow.active is False

    asyncio.run(check_topic_flow())


def test_overview_recommended_option_submits_direct_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    submitted: list[str] = []
    typed_app = cast("TextualApp[None]", app)

    async def check_recommendation_flow() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "_submit_inline_chat_value", submitted.append)
            app._open_study_topic_flow(
                [
                    ("Folgen", "study this topic"),
                    ("Compare Folgen and Grenzwerte", "recommended"),
                ],
                {
                    "Compare Folgen and Grenzwerte": (
                        "Compare Folgen and Grenzwerte so you can separate the ideas [E13]."
                    )
                },
            )
            await pilot.pause()

            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()

            assert submitted == [
                "Compare Folgen and Grenzwerte so you can separate the ideas [E13]."
            ]
            assert app._inline_flow.active is False

    asyncio.run(check_recommendation_flow())


def test_overview_topic_options_parse_only_actual_topic_section() -> None:
    reply = (
        "These are the study topics I found in the material [E1][E2].\n"
        "- Ableitungen [E1].\n"
        "- Grenzwerte [E2].\n\n"
        "Choose a topic to study next. In the shell, use ↑/↓ and press Enter.\n\n"
        "Recommended options:\n"
        "- Start with a guided explanation of Ableitungen [E1]."
    )

    assert overview_topic_options(reply) == [
        ("Ableitungen", "study this topic"),
        ("Grenzwerte", "study this topic"),
        ("Explain Ableitungen", "recommended"),
    ]


def test_overview_topic_menu_adds_recommended_options_as_direct_prompts() -> None:
    reply = (
        "These are the study topics I found in the material:\n"
        "- Folgen [E11]\n"
        "- Grenzwerte [E13]\n\n"
        "Choose a topic to study next. In the shell, use ↑/↓ and press Enter.\n\n"
        "Recommended options:\n"
        "- Start with a guided explanation of Folgen [E11].\n"
        "- Practice one exam-style or exercise question on Grenzwerte [E13].\n"
        "- Compare Folgen and Grenzwerte so you can separate the ideas [E13]."
    )

    menu = overview_topic_menu(reply)

    assert menu is not None
    assert menu.options == [
        ("Folgen", "study this topic"),
        ("Grenzwerte", "study this topic"),
        ("Explain Folgen", "recommended"),
        ("Practice Grenzwerte", "recommended"),
        ("Compare Folgen and Grenzwerte", "recommended"),
    ]
    assert menu.prompts["Compare Folgen and Grenzwerte"] == (
        "Compare Folgen and Grenzwerte so you can separate the ideas [E13]."
    )


def test_overview_topic_options_limits_to_seven_topics() -> None:
    topics = "\n".join(f"- Topic {index} [E1]" for index in range(1, 9))
    reply = (
        "These are the study topics I found in the material:\n"
        f"{topics}\n\n"
        "Choose a topic to study next. In the shell, use ↑/↓ and press Enter."
    )

    assert [label for label, _description in overview_topic_options(reply)] == [
        "Topic 1",
        "Topic 2",
        "Topic 3",
        "Topic 4",
        "Topic 5",
        "Topic 6",
        "Topic 7",
    ]


def test_settings_inline_submenus_expose_theme_and_telemetry() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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

            app._open_settings_flow()
            app._handle_inline_menu_choice("Appearance")
            appearance_labels = [label for label, _description in app._inline_flow.options]

            assert app._inline_flow.step == "appearance"
            assert "forge" in appearance_labels
            assert "light" in appearance_labels
            assert "high_contrast" in appearance_labels
            assert "Back" not in appearance_labels

            app._open_settings_flow()
            app._handle_inline_menu_choice("Activity trace")
            activity_labels = [label for label, _description in app._inline_flow.options]

            assert app._inline_flow.step == "activity_trace"
            assert "Tool calls" in activity_labels
            assert "Minimal tool calls" in activity_labels
            assert "Hidden tool calls" in activity_labels

    asyncio.run(check_settings_submenus())


def test_settings_inline_escape_returns_from_submenu() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_escape_back_navigation() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_settings_flow()
            app._handle_inline_menu_choice("Appearance")

            await pilot.press("escape")

            assert app._inline_flow.active is True
            assert app._inline_flow.name == "settings"
            assert app._inline_flow.step == "menu"

            await pilot.press("escape")

            assert app._inline_flow.active is False

    asyncio.run(check_escape_back_navigation())


def test_settings_inline_toggles_privacy_and_theme(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)
    settings_store.invalidate_settings_cache()

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_changes() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()
            app._submit_inline_flow("Privacy & Diagnostics")
            app._submit_inline_flow("Usage analytics")

            assert settings_store.load_app_settings().analytics_enabled is True

            app._open_settings_flow()
            app._submit_inline_flow("Appearance")
            app._submit_inline_flow("light")

            assert settings_store.load_app_settings().theme == "light"
            assert "#2C241B" in app.CSS

            app._open_settings_flow()
            app._submit_inline_flow("Activity trace")
            app._submit_inline_flow("Hidden tool calls")

            assert settings_store.load_app_settings().activity_trace_mode == (
                settings_store.ACTIVITY_TRACE_HIDDEN_TOOL_CALLS
            )

    try:
        asyncio.run(check_settings_changes())
    finally:
        set_theme("forge")
        settings_store.invalidate_settings_cache()


def test_logout_inline_menu_lists_only_clearable_stored_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    _clear_credential_env(monkeypatch)
    monkeypatch.setenv("HEPHAISTOS_API_KEY", "sk-global")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-env")
    monkeypatch.setattr(ProviderConfig, "load", classmethod(lambda _cls: default_config()))
    monkeypatch.setattr(
        "hephaistos.tui.inline_flows.oauth.list_providers",
        lambda: ["openai-codex"],
    )

    def fake_retrieve_key(slug: str) -> str | None:
        return "sk-keychain" if slug == "openai" else None

    def fake_get_volatile(slug: str) -> str | None:
        return "sk-session" if slug == "zai" else None

    monkeypatch.setattr("hephaistos.tui.inline_flows.retrieve_key", fake_retrieve_key)
    monkeypatch.setattr("hephaistos.tui.inline_flows.get_volatile", fake_get_volatile)

    app = tui.HephaistosTui(
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
                "ChatGPT Plus/Pro",
                "OpenAI API",
                "Z.AI",
                "All",
            ]
            assert descriptions["ChatGPT Plus/Pro"] == "configured"
            assert descriptions["OpenAI API"] == "configured"
            assert descriptions["Z.AI"] == "configured"
            assert descriptions["All"] == "clear shown"
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
                "HEPHAISTOS_API_KEY global override" in entry.content
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
    monkeypatch.setattr("hephaistos.tui.inline_flows.oauth.list_providers", list)
    monkeypatch.setattr("hephaistos.tui.inline_flows.retrieve_key", lambda _slug: None)
    monkeypatch.setattr("hephaistos.tui.inline_flows.get_volatile", lambda _slug: None)

    app = tui.HephaistosTui(
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
                "Environment credentials cannot be cleared inside Hephaistos" in entry.content
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
        "hephaistos.tui.inline_flows.oauth.list_providers",
        lambda: ["openai-codex"],
    )
    monkeypatch.setattr(
        "hephaistos.tui.inline_flows.retrieve_key",
        lambda slug: "sk-keychain" if slug == "openai-codex" else None,
    )
    monkeypatch.setattr("hephaistos.tui.inline_flows.get_volatile", lambda _slug: None)
    cleared_oauth: list[str] = []
    cleared_keys: list[str] = []
    monkeypatch.setattr(
        "hephaistos.tui.inline_flows.oauth.clear_credentials",
        cleared_oauth.append,
    )
    monkeypatch.setattr("hephaistos.tui.inline_flows.clear_key", cleared_keys.append)

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_selected_kind() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_logout_flow()

            labels = [label for label, _description in app._inline_flow.options]
            assert "ChatGPT Plus/Pro" in labels
            assert "OpenAI Codex API key" in labels

            app._submit_inline_flow("OpenAI Codex API key")

            assert cleared_keys == ["openai-codex"]
            assert cleared_oauth == []

    asyncio.run(check_selected_kind())


def test_armory_home_text_includes_recent_armories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    known = [tmp_path / "linear-algebra", tmp_path / "algorithms"]
    monkeypatch.setattr("hephaistos.tui.display_text.load_known_armories", lambda: known)
    monkeypatch.setattr("hephaistos.tui.display_text.armory_shortcut_key", lambda: "ctrl+a")

    text = tui._armory_home_text()

    assert "No armory attached." in text
    assert "Existing armories found." in text
    assert "What module or topic" not in text
    assert "ctrl+a" in text
    assert "materials/" in text
    assert "Recent armories:" in text
    assert "linear-algebra" in text
    assert "algorithms" in text


def test_plain_tui_shows_armory_home_notice(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    monkeypatch.setattr("hephaistos.tui.display_text.armory_shortcut_key", lambda: "ctrl+a")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_home_notice() -> None:
        async with typed_app.run_test(size=(120, 24)):
            assert app.state.armory_home_shown is True
            assert any("No armory attached" in entry.content for entry in app.state.transcript)
            assert any("materials/" in entry.content for entry in app.state.transcript)
            assert any("ctrl+a" in entry.content for entry in app.state.transcript)

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
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    add_known_armory(armory)

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_armory_menu() -> None:
        async with typed_app.run_test(size=(120, 24)):
            assert app.state.armory_home_shown is True
            assert app._armory_inline_active is False
            assert any("No armory attached" in entry.content for entry in app.state.transcript)
            assert any(
                "Existing armories found" in entry.content for entry in app.state.transcript
            )
            assert any(str(armory.resolve()) in entry.content for entry in app.state.transcript)

    asyncio.run(check_armory_menu())


def test_plain_tui_no_armory_question_uses_local_guardrail() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_guardrail() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)
            composer.value = "What is 2+2?"
            await pilot.press("enter")
            await pilot.pause()

            assert app.busy is False
            assert any("No armory is attached" in entry.content for entry in app.state.transcript)

    asyncio.run(check_guardrail())


def test_handle_armory_browser_invalid_subcommand_shows_usage() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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

    app = tui.HephaistosTui(
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


def test_sessions_command_lists_saved_sessions_inline(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    armory = tmp_path / "module"
    initialize(armory)
    saved_conversation = Conversation()
    saved_conversation.add("user", "What did I study?")
    chat_storage.save(armory, "abc123", saved_conversation, title="Study recap")

    session = _plain_session()
    session.armory_path = armory
    app = tui.HephaistosTui(
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

            assert any("Saved sessions for" in entry.content for entry in app.state.transcript)
            assert any("abc123" in entry.content for entry in app.state.transcript)
            assert any("Study recap" in entry.content for entry in app.state.transcript)
            assert app.state.pending_input is None

    asyncio.run(check_sessions_listing())


def test_sessions_command_defaults_to_filtered_resume_menu(tmp_path: Path) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    armory = tmp_path / "module"
    initialize(armory)
    first_conversation = Conversation()
    first_conversation.add("user", "What did I study?")
    first_conversation.add("assistant", "You reviewed modal logic.")
    chat_storage.save(armory, "logic123", first_conversation, title="Modal logic recap")
    second_conversation = Conversation()
    second_conversation.add("user", "What about calculus?")
    chat_storage.save(armory, "calc456", second_conversation, title="Calculus notes")

    session = _plain_session()
    session.armory_path = armory
    app = tui.HephaistosTui(
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


def test_sessions_command_browses_and_resumes_saved_session_inline(tmp_path: Path) -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    armory = tmp_path / "module"
    initialize(armory)
    saved_conversation = Conversation()
    saved_conversation.add("user", "What did I study?")
    saved_conversation.add("assistant", "You reviewed modal logic.")
    chat_storage.save(armory, "abc123", saved_conversation, title="Study recap")

    session = _plain_session()
    session.armory_path = armory
    app = tui.HephaistosTui(
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
            assert any("What did I study?" in entry.content for entry in app.state.transcript)
            assert any(
                "You reviewed modal logic." in entry.content for entry in app.state.transcript
            )
            assert any("resumed session abc123" in entry.content for entry in app.state.transcript)

    asyncio.run(check_sessions_resume())


def test_ctrl_a_opens_armory_without_input_home_conflict() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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

            assert app._armory_inline_active is True
            assert composer.cursor_position == len(composer.value)

    asyncio.run(check_ctrl_a())


def test_ctrl_o_opens_armory_as_tmux_safe_fallback() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_ctrl_o() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("ctrl+o")
            await pilot.pause()

            assert app._armory_inline_active is True

    asyncio.run(check_ctrl_o())


def test_composer_input_does_not_retain_ctrl_a_home_binding() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_composer_bindings() -> None:
        async with typed_app.run_test(size=(120, 24)):
            composer = app.query_one("#composer", tui.Input)
            key_to_bindings = composer._bindings.key_to_bindings

            assert "ctrl+a" not in key_to_bindings
            assert "home" in key_to_bindings

    asyncio.run(check_composer_bindings())


@pytest.mark.parametrize(
    "command_input",
    [
        *(f"/{suggestion.name}" for suggestion in tui._tui_command_suggestions()),
        "!echo shell",
    ],
)
def test_command_input_executes_without_user_transcript(
    monkeypatch: pytest.MonkeyPatch,
    command_input: str,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert not any("You:" in entry.content for entry in app.state.transcript)
            if command_input == "/armory":
                assert app._armory_inline_active is True
            elif command_input == "/materials":
                assert app._materials_inline_active is True
            elif command_input == "/new":
                assert any("New chat started" in entry.content for entry in app.state.transcript)
            elif command_input.startswith(("/models", "/help", "/status", "!")):
                assert app.state.pending_input is None
                assert app.state.transcript
            elif tui._pending_input_requires_terminal(command_input):
                assert app.state.pending_input == command_input
            else:
                assert app.state.pending_input is None

    asyncio.run(check_command_input())


def test_inline_command_output_has_command_boundary() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_command_boundary() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._append_notice("Previous action finished.")
            composer = app.query_one("#composer", tui.Input)
            composer.value = "/settings"
            await pilot.press("enter")
            await pilot.pause()

            previous_index = next(
                index
                for index, entry in enumerate(app.state.transcript)
                if entry.content == "Previous action finished."
            )
            command_entry = app.state.transcript[previous_index + 1]

            assert command_entry.kind == "user"
            assert command_entry.content == "/settings"
            assert app._inline_flow.active is True

    asyncio.run(check_command_boundary())


def test_materials_inline_toggles_rag_sources() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/biology.pdf", "materials/calculus.md")
    session.source_file_count = 2
    app = tui.HephaistosTui(
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


def test_transcript_reflows_when_resize_crosses_sidebar_threshold() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.armory_path = Path.home()
    app = tui.HephaistosTui(
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


def test_transcript_scrolls_to_latest_entry_after_long_output() -> None:
    if tui.Input is None or tui.RichLog is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephaistosTui(
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
    app = tui.HephaistosTui(
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
    app = tui.HephaistosTui(
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
    app = tui.HephaistosTui(
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
                "Hephaistos will reconnect automatically when connectivity returns."
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

    app = tui.HephaistosTui(
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
            assert any("Commands" in entry.content for entry in app.state.transcript)

    asyncio.run(check_inline_help())


def test_armory_inline_composer_filters_without_chat_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    _make_child = tmp_path / "biology"
    _make_child.mkdir()
    app = tui.HephaistosTui(
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
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    app = tui.HephaistosTui(
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


def test_armory_inline_create_starts_in_default_armory_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    default_home = Path.home() / ".armories"
    monkeypatch.delenv("HEPHAISTOS_ARMORY_HOME", raising=False)
    app = tui.HephaistosTui(
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
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path / ".armory-home"))
    assert default_armory_home() == (tmp_path / ".armory-home").resolve()


def test_default_armory_home_falls_back_to_dot_armory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEPHAISTOS_ARMORY_HOME", raising=False)
    assert default_armory_home() == (Path.home() / ".armories").resolve()


def test_armory_inline_place_entries_stay_inside_armory_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    app = tui.HephaistosTui(
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
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    app = tui.HephaistosTui(
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
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    app = tui.HephaistosTui(
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
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    (tmp_path / "existing").mkdir()
    app = tui.HephaistosTui(
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
            assert not (tmp_path / "existing" / ".hephaistos").exists()
            assert app._armory_inline_active is True

    asyncio.run(check_reject_existing())


def test_armory_inline_create_rejects_path_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    app = tui.HephaistosTui(
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

    app = tui.HephaistosTui(
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
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    app = tui.HephaistosTui(
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

    assert "type filter" in normal.plain
    assert "esc clear" in filtering.plain
    assert "enter create" in creating.plain


def test_armory_footer_restores_after_exit(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert "armory" in str(hints.render())
            await pilot.press("escape")
            await pilot.pause()
            assert "enter send" in str(hints.render())

    asyncio.run(check_footer_restore())


def test_armory_inline_app_focus_recovers_composer_control(tmp_path: Path) -> None:
    if tui.Input is None or tui.events is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
    app = tui.HephaistosTui(
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

    app = tui.HephaistosTui(
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

    app = tui.HephaistosTui(
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
            mode_hint = app.query_one("#armory-mode-hint", tui.Static)
            preview = app.query_one("#armory-preview-inline", tui.Static)
            assert "no-such-folder" in str(header.render())
            assert "enter open" in str(mode_hint.render())
            # pane hint is now cleared (empty)
            assert focus_hint is not None
            assert "No matches" in str(preview.render())

    asyncio.run(check_empty_filter())


def test_armory_inline_preserves_selection_across_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    alpha.mkdir()
    beta.mkdir()
    app = tui.HephaistosTui(
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


def test_armory_inline_open_mode_disables_new_shortcut() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_open_mode() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("open")
            await pilot.press("n")
            await pilot.pause()
            assert app._armory_creating is False

    asyncio.run(check_open_mode())


def test_armory_inline_create_entry_uses_composer(tmp_path: Path) -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert composer.placeholder == "Module or topic name..."

    asyncio.run(check_create_entry())


def test_handle_armory_browser_cancel_keeps_current_session() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephaistosTui(
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

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    app = tui.HephaistosTui(
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

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "study"
    initialize(armory_path)
    (armory_path / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_enter_opens_armory() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._handle_armory_browser("/armory")
            labels = [entry.label for entry in app._armory_entries]
            index = next(i for i, label in enumerate(labels) if "study" in label)
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

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "study"
    initialize(armory_path)
    session = _plain_session()
    new_session = _plain_session()
    new_session.armory_path = armory_path
    new_session.source_file_count = 1
    app = tui.HephaistosTui(
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
            assert any("Using armory" in entry.content for entry in app.state.transcript)
            composer = app.query_one("#composer", tui.Input)
            assert app.focused is composer

    asyncio.run(check_switch())


def test_click_refocuses_composer() -> None:
    if tui.Input is None or tui.Static is None or tui.events is None:
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()
    vertical_class = tui._transparent_vertical_class()
    input_class = tui._transparent_input_class()
    static_class = tui._transparent_static_class()
    rich_log_class = tui._transparent_rich_log_class()

    class ClickSmoke(tui.App[None]):
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
        app = ClickSmoke()
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

    class CompletionSmoke(tui.App[None]):
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
        app = CompletionSmoke()
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


def test_tab_applies_highlighted_completion_in_composer() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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

            await pilot.press("tab")
            await pilot.pause()

            assert composer.value == "/help "
            assert composer.cursor_position == len("/help ")

    asyncio.run(check_tab_completion())


def test_enter_submits_highlighted_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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


def test_models_completion_menu_uses_readable_columns() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert first.startswith("OpenAI         openai")
            assert "Pollinations" in first
            assert "free current" in first
            assert "/models" not in first

    asyncio.run(check_model_columns())


def test_models_command_shows_plain_suggestion() -> None:
    """Typing /models shows a regular command suggestion, not inline model picks."""
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert str(footer.render()).startswith("enter send")

    asyncio.run(check_models_suggestion())


def test_command_completion_selected_text_uses_brand_without_recoloring_description() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert selected.plain.startswith("/help")
            assert "Show available commands" in selected.plain

            selected_styles = [str(span.style) for span in selected.spans]
            unselected_styles = [str(span.style) for span in unselected.spans]
            assert any(palette.brand in style and "bold" in style for style in selected_styles)
            assert any(palette.dim in style for style in selected_styles)
            assert any(palette.text in style for style in unselected_styles)
            assert not any(palette.brand in style for style in unselected_styles)

    asyncio.run(check_completion_styles())


def test_busy_footer_keeps_cancel_hint_with_completion_menu_visible() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
            assert str(footer.render()) == "esc stop  ctrl+c cancel"
            assert str(position.render()) == f"  (1/{len(app.completion_candidates)})"

    asyncio.run(check_busy_footer())


def test_escape_cancels_busy_turn() -> None:
    if tui.Input is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_escape_cancel() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app.busy = True
            await pilot.press("escape")
            await pilot.pause()

            assert app.abort_event.is_set()
            assert any("Interrupt requested." in entry.content for entry in app.state.transcript)

    asyncio.run(check_escape_cancel())


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

    class SlashSmoke(tui.App[None]):
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
        app = SlashSmoke()
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

    app = tui.HephaistosTui(
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
                "logout",
                "status",
                "new",
                "armory",
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
                assert str(footer.render()).startswith("enter send")

    asyncio.run(check_scroll_policy())


def test_completion_menu_highlight_moves_down_at_bottom() -> None:
    if tui.Input is None or tui.OptionList is None:
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
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
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),
        tui.current_palette(),
    )
    calls: list[str] = []

    def fake_append_user(value: str, mark_working: bool = True) -> None:
        calls.append(f"user:{value}:{mark_working}")

    def fake_refresh_status(state: str = "ready") -> None:
        calls.append(f"status:{state}")

    def fake_run_worker(work: object, *, thread: bool = False) -> object:
        calls.append(f"worker:{thread}")
        return work

    monkeypatch.setattr(app, "_append_user", fake_append_user)
    monkeypatch.setattr(app, "_refresh_status", fake_refresh_status)
    monkeypatch.setattr(app, "run_worker", fake_run_worker)

    app._handle_external_input("/priority")

    assert app.busy is True
    assert app._thinking_label == "working"
    assert calls == ["user:/priority:True", "status:command working", "worker:True"]


def test_external_command_streams_notice_lines_live(monkeypatch: pytest.MonkeyPatch) -> None:
    app = tui.HephaistosTui(
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
    monkeypatch.setattr("hephaistos.terminal.input.handle_input", fake_handle_input)

    app._run_external_command("/priority")

    streamed = [args[0] for name, args in calls if name == "_append_notice"]
    assert streamed == ["phase 1", "phase 2"]
    finish = [args for name, args in calls if name == "_finish_external_command"]
    assert finish
    assert finish[0][2] == ""


def test_external_command_indents_streamed_activity_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = tui.HephaistosTui(
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
    monkeypatch.setattr("hephaistos.terminal.input.handle_input", fake_handle_input)

    app._run_external_command("/priority")

    streamed = [args[0] for name, args in calls if name == "_append_notice"]
    assert streamed == [
        "    Ran model request gpt-5.4-mini (turn 1, 4 message(s)).",
        (
            "    Read complete model response from gpt-5.4-mini: "
            "142 character(s), 0 tool call(s) in 3.3s."
        ),
    ]


def test_autopilot_command_resend_renders_reply_as_assistant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = tmp_path / "study"
    initialize(armory)
    session = _configured_status_session()
    session.armory_path = armory
    app = tui.HephaistosTui(
        session,
        tui._TuiRuntimeState(history=["/autopilot"]),
        tui.current_palette(),
    )
    calls: list[tuple[str, tuple[object, ...]]] = []
    seen: dict[str, str] = {}

    def fake_call_from_thread(fn: object, *args: object) -> None:
        name = getattr(fn, "__name__", fn.__class__.__name__)
        calls.append((name, args))

    def fake_run_tui_turn(
        _session: ChatSession,
        user_input: str,
        _abort_event: object,
        *,
        on_reply: Callable[[str], None],
        on_notice: Callable[[str], None],
        on_error: Callable[[str], None],
        on_finish: Callable[[], None],
        on_progress: Callable[[str], None] | None = None,
        on_activity: Callable[[str], None] | None = None,
    ) -> None:
        del on_notice, on_error, on_progress, on_activity
        seen["user_input"] = user_input
        on_reply("State the definition of a sequence.")
        on_finish()

    monkeypatch.setattr(app, "call_from_thread", fake_call_from_thread)
    monkeypatch.setattr(tui, "run_tui_turn", fake_run_tui_turn)

    app._run_external_command("/autopilot")

    notices = [args[0] for name, args in calls if name == "_append_notice"]
    replies = [args[0] for name, args in calls if name == "_append_assistant_reply"]
    assert any("Autopilot general session started" in str(notice) for notice in notices)
    assert replies == ["State the definition of a sequence."]
    assert seen["user_input"].startswith("Start an autopilot study session")
    assert all("Hephaistos:" not in str(args) for _, args in calls)
