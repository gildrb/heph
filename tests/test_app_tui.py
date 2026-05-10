"""Tests for the optional Textual shell wrapper."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, cast

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
from hephaistos.terminal import current_theme_name, set_theme
from hephaistos.tui import keymap
from hephaistos.tui.armory_browser import armory_detail, build_entries, default_armory_home
from hephaistos.tui.inline_flows import _dedupe_inline_options
from hephaistos.tui.transparent import Region as _Region
from hephaistos.tui.transparent import style_without_black_background

if TYPE_CHECKING:
    from textual.app import App as TextualApp
    from textual.screen import Screen
    from textual.widget import Widget
    from textual.widgets import OptionList as TextualOptionList


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


def test_session_status_for_plain_session() -> None:
    status = tui._status_lines(_plain_session())  # type: ignore[reportPrivateUsage]

    assert "test-model" in status
    assert "armory" in status
    assert "enter" not in status
    assert "/help" not in status


def test_session_status_shows_free_for_keyless_provider() -> None:
    status = tui._status_lines(_keyless_session())  # type: ignore[reportPrivateUsage]

    assert "free" in status
    assert "configured" not in status
    assert "missing" not in status


def test_footer_hints_show_idle_shortcuts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.tui.display_text.armory_shortcut_key", lambda: "ctrl+a")

    hints = tui._footer_hints_text(_plain_session())  # type: ignore[reportPrivateUsage]
    plain = hints.plain

    assert "enter" in plain
    assert "tab" in plain
    assert "ctrl+p" in plain
    assert "ctrl+a" in plain
    assert "ctrl+d" in plain
    assert "ctrl+a armory" in plain
    assert "test-model" not in plain


def test_footer_hints_show_cancel_when_busy() -> None:
    hints = tui._footer_hints_text(_plain_session(), busy=True)  # type: ignore[reportPrivateUsage]
    plain = hints.plain

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
    hints = tui._footer_hints_text(session)  # type: ignore[reportPrivateUsage]
    plain = hints.plain

    assert "api missing" in plain


def test_tui_config_error_allows_pollinations_without_api_key() -> None:
    assert tui._config_error(_keyless_session()) is None  # type: ignore[reportPrivateUsage]


def test_tui_css_keeps_surface_transparent() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    assert "App {\n    background: transparent;" in css
    assert "Screen {\n    layout: vertical;\n    background: transparent;" in css
    assert "#status {\n    height: auto;\n    max-height: 2;\n    width: auto;" in css
    assert ("#footer-hints {\n    height: 1;\n    width: auto;\n    max-width: 100%;") in css
    assert "#completion-stack {\n    height: 9;" in css
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
    assert "background: transparent;" in transcript_block
    assert f"background: {tui.current_palette().panel};" in composer_frame_block
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


def test_non_default_themes_do_not_paint_terminal_background() -> None:
    try:
        for theme in ("light", "high_contrast"):
            set_theme(theme)
            palette = tui.current_palette()
            css = tui._tui_css()  # type: ignore[reportPrivateUsage]

            assert palette.is_transparent is True
            assert palette.background == "transparent"
            assert "background: transparent;" in css
            assert palette.background in css
    finally:
        set_theme("forge")


def test_runtime_theme_switch_keeps_core_tui_backgrounds_transparent() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
            app._open_settings_flow()  # type: ignore[reportPrivateUsage]
            app._handle_inline_menu_choice("Appearance")  # type: ignore[reportPrivateUsage]
            app._handle_appearance_choice("light")  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            assert app.styles.background is not None
            assert app.styles.background.a == 0.0
            assert app.screen.styles.background is not None
            assert app.screen.styles.background.a == 0.0

            assert_core_widgets_are_transparent()

            app._handle_appearance_choice("high_contrast")  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            assert app.styles.background is not None
            assert app.styles.background.a == 0.0
            assert app.screen.styles.background is not None
            assert app.screen.styles.background.a == 0.0
            assert_core_widgets_are_transparent()

    asyncio.run(check_runtime_switch())


def test_tui_uses_transparent_widgets_for_all_palettes() -> None:
    if tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    palette = tui.ThemePalette(
        name="opaque-test",
        panel="#000000",
        stone="#111111",
        text="#ffffff",
        dim="#999999",
        accent="#ffffff",
        ember="#ff6600",
        configured="#00ff00",
        error="#ff0000",
        success="#00ff00",
        highlight="#222222",
        is_transparent=False,
        background="#000000",
    )

    widgets = tui._WidgetClasses.from_palette(palette)  # type: ignore[reportPrivateUsage]

    assert widgets.screen.__name__ == "BlankBackgroundWidget"
    assert widgets.vertical.__name__ == "TransparentWidget"
    assert widgets.horizontal.__name__ == "TransparentWidget"
    assert issubclass(widgets.rich_log, tui.RichLog)
    assert widgets.rich_log.can_focus is False


def test_tui_css_has_info_panel_layout() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

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
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    assert "Horizontal,\nVertical,\nStatic,\nRichLog {" in css
    container_start = css.index("Horizontal,\nVertical,\nStatic,\nRichLog {")
    container_end = css.index("}", container_start)
    container_block = css[container_start:container_end]

    assert "background: transparent;" in container_block
    assert "background-tint: transparent;" in container_block


def test_transcript_panel_background_only_paints_user_entries() -> None:
    if tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_transcript_backgrounds() -> None:
        async with typed_app.run_test(size=(100, 16)) as pilot:
            app._append_user("User prompt", mark_working=False)  # type: ignore[reportPrivateUsage]
            app._append_assistant_reply("Assistant reply")  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            transcript = app.query_one("#transcript")
            panel = tui.current_palette().panel.lower()
            user_segments: list[str] = []
            assistant_segments: list[str] = []
            panel_scroll_y = -1
            panel_line_index = -1
            for scroll_y in range(int(transcript.max_scroll_y) + 1):  # type: ignore[attr-defined]
                transcript.scroll_y = scroll_y  # type: ignore[attr-defined]
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
            transcript.scroll_y = panel_scroll_y  # type: ignore[attr-defined]
            await pilot.pause(0)
            assert _strip_is_panel_filled(transcript.render_line(panel_line_index - 1), panel)
            assert _strip_is_panel_filled(transcript.render_line(panel_line_index), panel)
            assert _strip_is_panel_filled(transcript.render_line(panel_line_index + 1), panel)

    asyncio.run(check_transcript_backgrounds())


def _strip_is_panel_filled(strip: Strip, panel: str) -> bool:
    segments: list[Segment] = list(strip)
    return all(
        segment.text == "" or f"on {panel}" in str(segment.style).lower() for segment in segments
    )


def test_transparent_style_strips_standard_and_truecolor_black_backgrounds() -> None:
    if tui._RichStyle is None:  # type: ignore[attr-defined, reportPrivateUsage]
        pytest.skip("Rich is not installed")

    standard = style_without_black_background(tui._RichStyle.parse("red on black"))  # type: ignore[attr-defined, reportPrivateUsage]
    truecolor = style_without_black_background(tui._RichStyle.parse("red on #000000"))  # type: ignore[attr-defined, reportPrivateUsage]
    nonblack = style_without_black_background(tui._RichStyle.parse("red on #111111"))  # type: ignore[attr-defined, reportPrivateUsage]

    assert standard.bgcolor is None
    assert truecolor.bgcolor is None
    assert nonblack.bgcolor is not None


def test_tui_css_suggestion_scrollbar_is_hidden() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]
    suggestions_start = css.index("#suggestions {")
    suggestions_end = css.index("}", suggestions_start)
    suggestions_block = css[suggestions_start:suggestions_end]
    assert "scrollbar-size: 0 0;" in suggestions_block
    assert "scrollbar-background:" not in suggestions_block
    assert "scrollbar-background: #1C1C1C;" not in suggestions_block


def test_tui_css_materials_highlight_uses_state_colours() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    assert "#materials-list > .option-list--option-highlighted" not in css
    assert "#materials-list.material-enabled > .option-list--option-highlighted" in css
    assert "background: #7F9A6A;" in css
    assert "#materials-list.material-disabled > .option-list--option-highlighted" in css
    assert "background: #9B4A2E;" in css


def test_info_panel_material_colours_match_materials_picker() -> None:
    session = _plain_session()
    session.source_files = ("materials/enabled.pdf", "materials/disabled.pdf")
    session.disabled_source_files.add("materials/disabled.pdf")

    panel = tui._info_panel_default_text(session)  # type: ignore[reportPrivateUsage]
    spans = {(span.start, span.end, str(span.style)) for span in panel.spans}

    enabled_start = panel.plain.index("@enabled.pdf")
    disabled_start = panel.plain.index("@disabled.pdf")
    assert (enabled_start, enabled_start + len("@enabled.pdf"), "#7F9A6A") in spans
    assert (disabled_start, disabled_start + len("@disabled.pdf"), "#9B4A2E") in spans


def test_tui_css_prevents_full_width_status_and_footer_bars() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    for selector in ("#status", "#footer-hints"):
        block_start = css.index(f"{selector} {{")
        block_end = css.index("}", block_start)
        block = css[block_start:block_end]

        assert "width: auto;" in block
        assert "max-width: 100%;" in block


def test_tui_css_pads_composer_as_full_width_user_block() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]
    panel = tui.current_palette().panel

    frame_start = css.index("#composer-frame {")
    frame_end = css.index("}", frame_start)
    frame_block = css[frame_start:frame_end]
    composer_start = css.index("#composer {")
    composer_end = css.index("}", composer_start)
    composer_block = css[composer_start:composer_end]
    input_start = css.index("Input {")
    input_end = css.index("}", input_start)
    input_block = css[input_start:input_end]

    assert "height: 3;" in frame_block
    assert "width: 100%;" in frame_block
    assert "padding: 1 0;" in frame_block
    assert f"background: {panel};" in frame_block
    assert "width: 100%;" in composer_block
    assert "padding: 0 1;" in composer_block
    assert "padding: 0 1;" in input_block


def test_tui_css_reserves_inline_completion_stack_below_composer() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

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

    assert "margin-top: 1;" not in composer_block
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
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
                app.query_one("#suggestions", tui.OptionList),  # type: ignore[reportPrivateUsage]
            )  # ty:ignore[redundant-cast]
            position = app.query_one("#completion-position", tui.Static)  # type: ignore[reportPrivateUsage]
            footer = app.query_one("#footer-hints", tui.Static)  # type: ignore[reportPrivateUsage]
            assert frame.region.y == frame_y
            assert stack.region.y == stack_y
            assert frame.size.width == stack.size.width
            assert str(position.render()) == f"(1/{suggestions.option_count})"
            assert str(footer.render()).startswith("enter send")
            assert suggestions.size.width == stack.size.width
            assert suggestions.has_class("visible")
            assert suggestions.size.height <= 7
            assert position.region.y == suggestions.region.y + suggestions.size.height
            assert footer.region.y == position.region.y + 1

    asyncio.run(check_inline_menu_layout())


def test_transcript_overflow_scrolls_without_moving_composer() -> None:
    if tui.Input is None or tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
                app._append_user(f"stress history message {index}", mark_working=False)  # type: ignore[reportPrivateUsage]
                app._append_assistant_reply(
                    "No armory is attached. Open or create an armory with /armory, "
                    "then add study materials so I can answer from your sources."
                )  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            transcript = app.query_one("#transcript", tui.RichLog)  # type: ignore[reportPrivateUsage]
            assert transcript.max_scroll_y > 0
            assert frame.region.y == baseline_y
            assert stack.region.y - frame.region.y == baseline_stack_gap
            assert baseline_stack_gap > 0
            assert frame.region.y < 30

    asyncio.run(check_transcript_overflow())


def test_status_and_footer_hints_segments_do_not_paint_black_background() -> None:
    if tui.Static is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    class Smoke(tui.App[None]):  # type: ignore[index]
        CSS = tui._tui_css()  # type: ignore[reportPrivateUsage]

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            status_text = tui._status_text(session)  # type: ignore[reportPrivateUsage]
            hints_text = tui._footer_hints_text(session)  # type: ignore[reportPrivateUsage]
            with tui.Vertical(id="main-layout"):  # type: ignore[operator, reportCallIssue]
                yield tui.Static(status_text, id="status")  # type: ignore[operator]
                yield tui.Static(hints_text, id="footer-hints")  # type: ignore[operator]

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
    if tui.Static is None or tui.Strip is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()  # type: ignore[reportPrivateUsage]
    vertical_class = tui._transparent_vertical_class()  # type: ignore[reportPrivateUsage]
    static_class = tui._transparent_static_class()  # type: ignore[reportPrivateUsage]
    rich_log_class = tui._transparent_rich_log_class()  # type: ignore[reportPrivateUsage]
    input_class = tui._transparent_input_class()  # type: ignore[reportPrivateUsage]

    class Smoke(tui.App[None]):  # type: ignore[index]
        CSS = tui._tui_css()  # type: ignore[reportPrivateUsage]

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with vertical_class(id="main-layout"):  # type: ignore[operator, reportCallIssue]
                yield static_class(tui._status_text(session), id="status")  # type: ignore[operator, reportPrivateUsage]
                yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)  # type: ignore[operator]
                yield static_class("", id="thinking-indicator")  # type: ignore[operator]
                with vertical_class(id="composer-frame"):  # type: ignore[operator, reportCallIssue]
                    yield input_class(  # type: ignore[operator]
                        placeholder='Ask anything... "What do I need to study next?"',
                        id="composer",
                    )
                    yield static_class(  # type: ignore[operator]
                        tui._footer_hints_text(session),  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None or tui.Static is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None or tui.Static is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
            compositor = screen._compositor  # type: ignore[reportPrivateUsage]
            chops = compositor._render_chops(  # type: ignore[reportPrivateUsage]
                compositor.size.region, lambda y: True
            )
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
    if tui.Static is None or tui.Strip is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()  # type: ignore[reportPrivateUsage]
    vertical_class = tui._transparent_vertical_class()  # type: ignore[reportPrivateUsage]
    static_class = tui._transparent_static_class()  # type: ignore[reportPrivateUsage]

    class Smoke(tui.App[None]):  # type: ignore[index]
        CSS = tui._tui_css()  # type: ignore[reportPrivateUsage]

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            with vertical_class(id="shell"):  # type: ignore[operator, reportCallIssue]
                yield static_class(  # type: ignore[operator]
                    tui._status_text(_configured_status_session()),  # type: ignore[reportPrivateUsage]
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
    help_text = tui._command_help()  # type: ignore[reportPrivateUsage]

    assert "/help" in help_text
    assert "/models" in help_text
    assert "/materials" in help_text
    assert "/sessions" in help_text
    assert "/status" in help_text
    assert "/sources" not in help_text
    assert "/history" not in help_text


def test_tui_slash_suggestion_uses_shared_registry() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/sta")  # type: ignore[reportPrivateUsage]

    assert suggestion == "/status "


def test_tui_slash_suggestion_uses_canonical_materials_command() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/mat")  # type: ignore[reportPrivateUsage]

    assert suggestion == "/materials "


def test_info_panel_shows_session_duration_and_material_names() -> None:
    session = _plain_session()
    long_pdf = "materials/very-important-full-pdf-name-for-exam-review.pdf"
    session.source_files = (long_pdf, "materials/calculus.md")
    session.source_file_count = 2

    panel = tui._info_panel_default_text(  # type: ignore[reportPrivateUsage]
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

    panel = tui._info_panel_message_text(entry, session)  # type: ignore[reportPrivateUsage]

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
    captured_state: tui._TuiRuntimeState | None = None  # type: ignore[reportPrivateUsage]
    run_count = 0

    class FakeTui:
        def __init__(
            self,
            _session: ChatSession,
            state: tui._TuiRuntimeState,  # type: ignore[reportPrivateUsage]
            _palette: tui.ThemePalette,
        ) -> None:
            nonlocal captured_state
            captured_state = state

        def run(self) -> None:
            nonlocal run_count
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
            _state: tui._TuiRuntimeState,  # type: ignore[reportPrivateUsage]
            palette: tui.ThemePalette,
        ) -> None:
            nonlocal captured_palette
            captured_palette = palette

        def run(self) -> None:
            return

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

    status = tui._status_lines(session)  # type: ignore[reportPrivateUsage]

    assert "armory /tmp/my-armory" in status


def test_status_lines_shows_none_when_no_armory() -> None:
    """Status bar shows 'none' for armory when no armory is attached."""
    session = _plain_session()

    status = tui._status_lines(session)  # type: ignore[reportPrivateUsage]

    assert "armory none" in status


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
    assert tui._is_armory_command("/armory")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("/armory open")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("/armory create")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("/armory detach")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("  /armory  ")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("/ARMORY OPEN")  # type: ignore[reportPrivateUsage]

    assert not tui._is_armory_command("/model")  # type: ignore[reportPrivateUsage]
    assert not tui._is_armory_command("hello")  # type: ignore[reportPrivateUsage]


@pytest.mark.parametrize(
    ("value", "route"),
    [
        ("", tui._TuiInputRoute.EMPTY),  # type: ignore[reportPrivateUsage]
        ("   ", tui._TuiInputRoute.EMPTY),  # type: ignore[reportPrivateUsage]
        ("hello", tui._TuiInputRoute.CHAT),  # type: ignore[reportPrivateUsage]
        ("/models", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
        ("/models openai", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
        ("/sources", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
        ("/sources notes", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
        ("/materials", tui._TuiInputRoute.MATERIALS),  # type: ignore[reportPrivateUsage]
        ("/materials notes", tui._TuiInputRoute.MATERIALS),  # type: ignore[reportPrivateUsage]
        ("/sessions", tui._TuiInputRoute.SESSIONS),  # type: ignore[reportPrivateUsage]
        ("/sessions list", tui._TuiInputRoute.SESSIONS),  # type: ignore[reportPrivateUsage]
        ("/history browse", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
        ("/history stats", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
        ("/new", tui._TuiInputRoute.NEW),  # type: ignore[reportPrivateUsage]
        ("/armory", tui._TuiInputRoute.ARMORY),  # type: ignore[reportPrivateUsage]
        ("/armory open", tui._TuiInputRoute.ARMORY),  # type: ignore[reportPrivateUsage]
        ("/help", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
        ("!echo hi", tui._TuiInputRoute.EXTERNAL),  # type: ignore[reportPrivateUsage]
    ],
)
def test_tui_input_route_classifies_submissions(
    value: str,
    route: tui._TuiInputRoute,  # type: ignore[reportPrivateUsage]
) -> None:
    assert tui._tui_input_route(value) == route  # type: ignore[reportPrivateUsage]


def test_pending_terminal_commands_are_registered() -> None:
    registered = {cmd.name for cmd in tui.get_registry().commands}

    assert registered >= tui._TERMINAL_INTERACTIVE_COMMANDS  # type: ignore[reportPrivateUsage]


def test_tui_input_route_covers_visible_command_suggestions() -> None:
    routes = {
        f"/{suggestion.name}": tui._tui_input_route(f"/{suggestion.name}")  # type: ignore[reportPrivateUsage]
        for suggestion in tui._tui_command_suggestions()  # type: ignore[reportPrivateUsage]
    }

    assert routes["/models"] is tui._TuiInputRoute.EXTERNAL  # type: ignore[reportPrivateUsage]
    assert "/sources" not in routes
    assert "/history" not in routes
    assert routes["/materials"] is tui._TuiInputRoute.MATERIALS  # type: ignore[reportPrivateUsage]
    assert routes["/sessions"] is tui._TuiInputRoute.SESSIONS  # type: ignore[reportPrivateUsage]
    assert routes["/new"] is tui._TuiInputRoute.NEW  # type: ignore[reportPrivateUsage]
    assert routes["/armory"] is tui._TuiInputRoute.ARMORY  # type: ignore[reportPrivateUsage]
    assert all(
        route is tui._TuiInputRoute.EXTERNAL  # type: ignore[reportPrivateUsage]
        for command, route in routes.items()
        if command not in {"/materials", "/sessions", "/new", "/armory"}
    )


def test_armory_command_mode_validates_supported_subcommands() -> None:
    assert tui._armory_command_mode("/armory") == "manage"  # type: ignore[reportPrivateUsage]
    assert tui._armory_command_mode("/armory menu") == "manage"  # type: ignore[reportPrivateUsage]
    assert tui._armory_command_mode("/armory open") == "open"  # type: ignore[reportPrivateUsage]
    assert tui._armory_command_mode("/armory create") == "create"  # type: ignore[reportPrivateUsage]
    assert tui._armory_command_mode("/armory new") == "create"  # type: ignore[reportPrivateUsage]

    assert tui._armory_command_mode("/armory detach") is None  # type: ignore[reportPrivateUsage]
    assert "Usage: /armory" in tui._armory_usage_message()  # type: ignore[reportPrivateUsage]


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
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_command_palette() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("ctrl+p")
            await pilot.pause()
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),  # type: ignore[reportPrivateUsage]
            )  # ty:ignore[redundant-cast]

            assert composer.value == "/"  # type: ignore[reportUnknownMemberType]
            assert composer.cursor_position == 1  # type: ignore[reportUnknownMemberType]
            assert suggestions.has_class("visible")
            assert app.completion_candidates

    asyncio.run(check_command_palette())


def test_settings_inline_menu_exposes_privacy_and_appearance() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_menu() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()  # type: ignore[reportPrivateUsage]
            labels = [label for label, _description in app._inline_flow.options]

            assert app._inline_flow.name == "settings"
            assert app._inline_flow.step == "menu"
            assert "Privacy & Diagnostics" in labels
            assert "Appearance" in labels
            assert "Login" in labels
            assert "Logout" in labels

    asyncio.run(check_settings_menu())


def test_settings_inline_submenus_expose_theme_and_telemetry() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_submenus() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()  # type: ignore[reportPrivateUsage]
            app._handle_inline_menu_choice("Privacy & Diagnostics")  # type: ignore[reportPrivateUsage]
            privacy_labels = [label for label, _description in app._inline_flow.options]

            assert app._inline_flow.step == "privacy"
            assert "Usage analytics" in privacy_labels
            assert "Crash reports" in privacy_labels
            assert "Back" not in privacy_labels

            app._open_settings_flow()  # type: ignore[reportPrivateUsage]
            app._handle_inline_menu_choice("Appearance")  # type: ignore[reportPrivateUsage]
            appearance_labels = [label for label, _description in app._inline_flow.options]

            assert app._inline_flow.step == "appearance"
            assert "forge" in appearance_labels
            assert "light" in appearance_labels
            assert "high_contrast" in appearance_labels
            assert "Back" not in appearance_labels

    asyncio.run(check_settings_submenus())


def test_settings_inline_escape_returns_from_submenu() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_escape_back_navigation() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_settings_flow()  # type: ignore[reportPrivateUsage]
            app._handle_inline_menu_choice("Appearance")  # type: ignore[reportPrivateUsage]

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
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_store, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_store, "_USER_CONFIG_FILE", config_file)
    settings_store.invalidate_settings_cache()

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_settings_changes() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_settings_flow()  # type: ignore[reportPrivateUsage]
            app._submit_inline_flow("Privacy & Diagnostics")  # type: ignore[reportPrivateUsage]
            app._submit_inline_flow("Usage analytics")  # type: ignore[reportPrivateUsage]

            assert settings_store.load_app_settings().analytics_enabled is True

            app._open_settings_flow()  # type: ignore[reportPrivateUsage]
            app._submit_inline_flow("Appearance")  # type: ignore[reportPrivateUsage]
            app._submit_inline_flow("light")  # type: ignore[reportPrivateUsage]

            assert settings_store.load_app_settings().theme == "light"
            assert "#2C241B" in app.CSS

    try:
        asyncio.run(check_settings_changes())
    finally:
        set_theme("forge")
        settings_store.invalidate_settings_cache()


def test_armory_home_text_includes_recent_armories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    known = [tmp_path / "linear-algebra", tmp_path / "algorithms"]
    monkeypatch.setattr(tui, "load_known_armories", lambda: known)
    monkeypatch.setattr(tui, "armory_shortcut_key", lambda: "ctrl+a")

    text = tui._armory_home_text()  # type: ignore[reportPrivateUsage]

    assert "No armory attached." in text
    assert "Existing armories found." in text
    assert "What module or topic" not in text
    assert "ctrl+a" in text
    assert "materials/" in text
    assert "Recent armories:" in text
    assert "linear-algebra" in text
    assert "algorithms" in text


def test_plain_tui_shows_armory_home_notice(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")
    monkeypatch.setattr(tui, "armory_shortcut_key", lambda: "ctrl+a")
    monkeypatch.setattr("hephaistos.tui.display_text.armory_shortcut_key", lambda: "ctrl+a")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    armory = armory_home / "known"
    initialize(armory)
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    add_known_armory(armory)

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_armory_menu() -> None:
        async with typed_app.run_test(size=(120, 24)):
            assert app.state.armory_home_shown is True
            assert app._armory_inline_active is False  # type: ignore[reportPrivateUsage]
            assert any("No armory attached" in entry.content for entry in app.state.transcript)
            assert any(
                "Existing armories found" in entry.content for entry in app.state.transcript
            )
            assert any(str(armory.resolve()) in entry.content for entry in app.state.transcript)

    asyncio.run(check_armory_menu())


def test_plain_tui_no_armory_question_uses_local_guardrail() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_invalid_usage() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._handle_armory_browser("/armory detach")  # type: ignore[reportPrivateUsage]
            assert any("Usage: /armory" in entry.content for entry in app.state.transcript)
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            assert app.focused is composer  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_invalid_usage())


def test_armory_input_executes_without_user_transcript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    def fake_handle_armory_browser(value: str) -> None:
        assert value == "/armory"
        app._append_notice("opened armory browser")  # type: ignore[reportPrivateUsage]

    async def check_inline_command() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "_handle_armory_browser", fake_handle_armory_browser)
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/armory"
            await pilot.press("enter")
            await pilot.pause()
            assert not any("You:" in entry.content for entry in app.state.transcript)
            assert any("opened armory browser" in entry.content for entry in app.state.transcript)

    asyncio.run(check_inline_command())


def test_sessions_command_lists_saved_sessions_inline(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
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
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sessions_listing() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/sessions list"
            await pilot.press("enter")
            await pilot.pause()

            assert any("Saved sessions for" in entry.content for entry in app.state.transcript)
            assert any("abc123" in entry.content for entry in app.state.transcript)
            assert any("Study recap" in entry.content for entry in app.state.transcript)
            assert app.state.pending_input is None

    asyncio.run(check_sessions_listing())


def test_sessions_command_defaults_to_filtered_resume_menu(tmp_path: Path) -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
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
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sessions_menu() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/sessions"
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.name == "sessions"  # type: ignore[reportPrivateUsage]
            assert app._inline_flow.all_options  # type: ignore[reportPrivateUsage]
            composer.value = "logic"
            await pilot.pause()

            session_labels = [
                label
                for label, _description in app._inline_flow.options  # type: ignore[reportPrivateUsage]
            ]
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
    if tui.Input is None or tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
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
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_sessions_resume() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/sessions browse"
            await pilot.press("enter")
            await pilot.pause()

            assert app._inline_flow.name == "sessions"  # type: ignore[reportPrivateUsage]
            app._submit_inline_flow("abc123")  # type: ignore[reportPrivateUsage]

            assert app.session.session_id == "abc123"
            assert any("What did I study?" in entry.content for entry in app.state.transcript)
            assert any(
                "You reviewed modal logic." in entry.content for entry in app.state.transcript
            )
            assert any("resumed session abc123" in entry.content for entry in app.state.transcript)

    asyncio.run(check_sessions_resume())


def test_ctrl_a_opens_armory_without_input_home_conflict() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_ctrl_a() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "draft"
            composer.cursor_position = len(composer.value)
            await pilot.press("ctrl+a")
            await pilot.pause()

            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]
            assert composer.cursor_position == len(composer.value)

    asyncio.run(check_ctrl_a())


def test_ctrl_o_opens_armory_as_tmux_safe_fallback() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_ctrl_o() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("ctrl+o")
            await pilot.pause()

            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]

    asyncio.run(check_ctrl_o())


def test_composer_input_does_not_retain_ctrl_a_home_binding() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_composer_bindings() -> None:
        async with typed_app.run_test(size=(120, 24)):
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            key_to_bindings = composer._bindings.key_to_bindings  # type: ignore[reportPrivateUsage]

            assert "ctrl+a" not in key_to_bindings
            assert "home" in key_to_bindings

    asyncio.run(check_composer_bindings())


@pytest.mark.parametrize(
    "command_input",
    [
        *(f"/{suggestion.name}" for suggestion in tui._tui_command_suggestions()),  # type: ignore[reportPrivateUsage]
        "!echo shell",
    ],
)
def test_command_input_executes_without_user_transcript(
    monkeypatch: pytest.MonkeyPatch,
    command_input: str,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_command_input() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "exit", lambda: None)
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = command_input
            await pilot.press("enter")
            await pilot.pause()
            assert not any("You:" in entry.content for entry in app.state.transcript)
            if command_input == "/armory":
                assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]
            elif command_input == "/materials":
                assert app._materials_inline_active is True  # type: ignore[reportPrivateUsage]
            elif command_input == "/new":
                assert any("New chat started" in entry.content for entry in app.state.transcript)
            elif command_input.startswith(("/models", "/help", "/status", "!")):
                assert app.state.pending_input is None
                assert app.state.transcript
            elif tui._pending_input_requires_terminal(command_input):  # type: ignore[reportPrivateUsage]
                assert app.state.pending_input == command_input
            else:
                assert app.state.pending_input is None

    asyncio.run(check_command_input())


def test_materials_inline_toggles_rag_sources() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.source_files = ("materials/biology.pdf", "materials/calculus.md")
    session.source_file_count = 2
    app = tui.HephaistosTui(
        session,
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_materials_toggle() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/materials"
            await pilot.press("enter")
            await pilot.pause()
            assert app._materials_inline_active is True  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None or tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    session = _plain_session()
    session.armory_path = Path.home()
    app = tui.HephaistosTui(
        session,
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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

            app._append_plain(long_line)  # type: ignore[reportPrivateUsage]
            await pilot.pause()
            log = app.query_one("#transcript", tui.RichLog)  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None or tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephaistosTui(
        session,
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scroll() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            await pilot.pause()
            app._append_plain("\n".join(f"old line {i}" for i in range(60)))  # type: ignore[reportPrivateUsage]
            app._append_plain("latest exam question line")  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            log = app.query_one("#transcript", tui.RichLog)
            assert log.scroll_y > 0
            assert "latest exam question line" in str(log.lines[-1])

    asyncio.run(check_scroll())


def test_transcript_scrolls_to_final_line_of_multiline_command_output() -> None:
    if tui.Input is None or tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephaistosTui(
        session,
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scroll() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            await pilot.pause()
            app._append_plain("\n".join(f"old line {i}" for i in range(60)))  # type: ignore[reportPrivateUsage]
            app._append_entry(  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None or tui.RichLog is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephaistosTui(
        session,
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_notice() -> None:
        async with typed_app.run_test(size=(80, 16)) as pilot:
            await pilot.pause()
            app._append_notice(  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    _make_child = tmp_path / "biology"
    _make_child.mkdir()
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_filter() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "bio"
            await pilot.pause()
            labels = [entry.label for entry in app._armory_entries]  # type: ignore[reportPrivateUsage]
            assert any("biology" in label for label in labels)
            assert not any("You:" in entry.content for entry in app.state.transcript)

    asyncio.run(check_filter())


def test_armory_inline_new_armory_uses_composer_without_chat_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_create() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "maths"
            await pilot.press("enter")
            await pilot.pause()
            assert (tmp_path / "maths").exists()
            assert not any("You:" in entry.content for entry in app.state.transcript)

    asyncio.run(check_create())


def test_armory_inline_create_starts_in_default_armory_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    default_home = Path.home() / ".armories"
    monkeypatch.delenv("HEPHAISTOS_ARMORY_HOME", raising=False)
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_default_home() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("create")  # type: ignore[reportPrivateUsage]
            assert app._armory_current == default_home.resolve()  # type: ignore[reportPrivateUsage]

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
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_places() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            place_entries = [
                entry
                for entry in app._armory_entries
                if entry.is_place  # type: ignore[reportPrivateUsage]
            ]
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
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    armory_home = tmp_path / ".armories"
    child = armory_home / "child"
    child.mkdir(parents=True)
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_left_navigation() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            app._armory_current = child  # type: ignore[reportPrivateUsage]
            app._refresh_armory_inline()  # type: ignore[reportPrivateUsage]
            await pilot.press("left")
            await pilot.pause()
            assert app._armory_current == child  # type: ignore[reportPrivateUsage]
            await pilot.press("left")
            await pilot.pause()
            assert app._armory_current == child  # type: ignore[reportPrivateUsage]

    asyncio.run(check_left_navigation())


def test_armory_inline_rejects_open_outside_armory_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    armory_home = tmp_path / ".armories"
    outside = tmp_path / "outside"
    armory_home.mkdir()
    initialize(outside)
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(armory_home))
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_rejected_open() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            app._open_selected_armory(outside)  # type: ignore[reportPrivateUsage]
            error = app.query_one("#armory-error-inline", tui.Static)  # type: ignore[reportPrivateUsage]
            assert "outside armory home" in str(error.render())  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_rejected_open())


def test_armory_inline_create_rejects_existing_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    (tmp_path / "existing").mkdir()
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_reject_existing() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "existing"
            await pilot.press("enter")
            await pilot.pause()
            error = app.query_one("#armory-error-inline", tui.Static)  # type: ignore[reportPrivateUsage]
            assert "already exists" in str(error.render())  # type: ignore[reportUnknownMemberType]
            assert not (tmp_path / "existing" / ".hephaistos").exists()
            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]

    asyncio.run(check_reject_existing())


def test_armory_inline_create_rejects_path_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_reject_escape() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "../outside"
            await pilot.press("enter")
            await pilot.pause()
            error = app.query_one("#armory-error-inline", tui.Static)  # type: ignore[reportPrivateUsage]
            assert "inside the selected folder" in str(error.render())  # type: ignore[reportUnknownMemberType]
            assert not (tmp_path.parent / "outside").exists()
            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]

    asyncio.run(check_reject_escape())


def test_armory_inline_escape_clears_filter_then_exits(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_escape_flow() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "math"
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]
            assert composer.value == ""
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is False  # type: ignore[reportPrivateUsage]

    asyncio.run(check_escape_flow())


def test_armory_inline_escape_cancels_create_then_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")
    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_create_escape() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("create")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "math"
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]
            assert app._armory_creating is False  # type: ignore[reportPrivateUsage]
            assert composer.value == ""
            await pilot.press("escape")
            await pilot.pause()
            assert app._armory_inline_active is False  # type: ignore[reportPrivateUsage]
            assert not (tmp_path / "math").exists()

    asyncio.run(check_create_escape())


def test_armory_footer_hints_follow_mode() -> None:
    normal = tui._armory_footer_hints_text()  # type: ignore[reportPrivateUsage]
    filtering = tui._armory_footer_hints_text(filtering=True)  # type: ignore[reportPrivateUsage]
    creating = tui._armory_footer_hints_text(creating=True)  # type: ignore[reportPrivateUsage]

    assert "type filter" in normal.plain
    assert "esc clear" in filtering.plain
    assert "enter create" in creating.plain


def test_armory_footer_restores_after_exit(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_footer_restore() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            hints = app.query_one("#footer-hints", tui.Static)  # type: ignore[reportPrivateUsage]
            assert "armory" in str(hints.render())  # type: ignore[reportUnknownMemberType]
            await pilot.press("escape")
            await pilot.pause()
            assert "enter send" in str(hints.render())  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_footer_restore())


def test_armory_inline_app_focus_recovers_composer_control(tmp_path: Path) -> None:
    if tui.Input is None or tui.events is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_app_focus() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            app.set_focus(None)  # type: ignore[reportUnknownMemberType]
            app.on_app_focus(tui.events.AppFocus())  # type: ignore[reportPrivateUsage]
            assert app.focused is composer  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_app_focus())


def test_armory_inline_click_keeps_composer_as_control(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    (tmp_path / "math").mkdir()
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_click_focus() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            await pilot.click("#armory-current-inline", offset=(2, 1))
            await pilot.pause()
            assert app.focused is composer  # type: ignore[reportUnknownMemberType]
            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]

    asyncio.run(check_click_focus())


def test_armory_inline_transparent_surface_does_not_paint_black(tmp_path: Path) -> None:
    if tui.Input is None or tui.Strip is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_transparency() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            await pilot.pause()
            widgets: tuple[Widget, ...] = (
                cast("Widget", app.query_one("#armory-inline")),  # type: ignore[reportUnknownMemberType]  # ty:ignore[redundant-cast]
                cast("Widget", app.query_one("#armory-header")),  # type: ignore[reportUnknownMemberType]  # ty:ignore[redundant-cast]
                cast("Widget", app.query_one("#armory-current-inline")),  # type: ignore[reportUnknownMemberType]  # ty:ignore[redundant-cast]
                cast("Widget", app.query_one("#armory-preview-inline")),  # type: ignore[reportUnknownMemberType]  # ty:ignore[redundant-cast]
            )
            for widget in widgets:
                for line_number in range(widget.size.height):
                    strip = widget.render_line(line_number)
                    assert all("on #000000" not in str(segment.style) for segment in strip)

    asyncio.run(check_transparency())


def test_armory_inline_header_shows_filter_and_no_matches(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_empty_filter() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "no-such-folder"
            await pilot.pause()
            header = app.query_one("#armory-header", tui.Static)  # type: ignore[reportPrivateUsage]
            focus_hint = app.query_one("#armory-pane-hint", tui.Static)  # type: ignore[reportPrivateUsage]
            mode_hint = app.query_one("#armory-mode-hint", tui.Static)  # type: ignore[reportPrivateUsage]
            preview = app.query_one("#armory-preview-inline", tui.Static)  # type: ignore[reportPrivateUsage]
            assert "no-such-folder" in str(header.render())  # type: ignore[reportUnknownMemberType]
            assert "enter open" in str(mode_hint.render())  # type: ignore[reportUnknownMemberType]
            # pane hint is now cleared (empty)
            assert focus_hint is not None
            assert "No matches" in str(preview.render())  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_empty_filter())


def test_armory_inline_preserves_selection_across_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    alpha.mkdir()
    beta.mkdir()
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_selection() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            current = app.query_one("#armory-current-inline", tui.OptionList)  # type: ignore[reportPrivateUsage]
            current.highlighted = next(
                index
                for index, entry in enumerate(app._armory_entries)  # type: ignore[reportPrivateUsage]
                if entry.path == beta
            )
            app._refresh_armory_inline()  # type: ignore[reportPrivateUsage]
            selected = app._armory_highlighted_entry()  # type: ignore[reportPrivateUsage]
            assert selected is not None
            assert selected.path == beta

    asyncio.run(check_selection())


def test_armory_inline_open_mode_disables_new_shortcut() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_open_mode() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._open_armory_inline("open")  # type: ignore[reportPrivateUsage]
            await pilot.press("n")
            await pilot.pause()
            assert app._armory_creating is False  # type: ignore[reportPrivateUsage]

    asyncio.run(check_open_mode())


def test_armory_inline_create_entry_uses_composer(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app._armory_current = tmp_path  # type: ignore[reportPrivateUsage]
    typed_app = cast("TextualApp[None]", app)

    async def check_create_entry() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._open_armory_inline("manage")  # type: ignore[reportPrivateUsage]
            current = app.query_one("#armory-current-inline", tui.OptionList)  # type: ignore[reportPrivateUsage]
            current.highlighted = next(
                index
                for index, entry in enumerate(app._armory_entries)  # type: ignore[reportPrivateUsage]
                if entry.is_create
            )
            app._armory_open_highlighted()  # type: ignore[reportPrivateUsage]
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            assert app._armory_creating is True  # type: ignore[reportPrivateUsage]
            assert composer.placeholder == "Module or topic name..."  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_create_entry())


def test_handle_armory_browser_cancel_keeps_current_session() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    session = _plain_session()
    app = tui.HephaistosTui(
        session,
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_cancel() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._handle_armory_browser("/armory")  # type: ignore[reportPrivateUsage]
            assert app._armory_inline_active is True  # type: ignore[reportPrivateUsage]
            await pilot.press("escape")
            await pilot.pause()
            assert app.session is session
            assert app._armory_inline_active is False  # type: ignore[reportPrivateUsage]

    asyncio.run(check_cancel())


def test_handle_armory_browser_rejects_invalid_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_invalid_directory() -> None:
        async with typed_app.run_test(size=(120, 24)):
            app._handle_armory_browser("/armory open")  # type: ignore[reportPrivateUsage]
            app._open_selected_armory(tmp_path)  # type: ignore[reportPrivateUsage]
            error = app.query_one("#armory-error-inline", tui.Static)  # type: ignore[reportPrivateUsage]
            assert "Not a valid armory" in str(error.render())  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_invalid_directory())


def test_armory_inline_enter_opens_highlighted_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    monkeypatch.setenv("HEPHAISTOS_ARMORY_HOME", str(tmp_path))
    armory_path = tmp_path / "study"
    initialize(armory_path)
    (armory_path / "materials" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_enter_opens_armory() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            app._handle_armory_browser("/armory")  # type: ignore[reportPrivateUsage]
            labels = [entry.label for entry in app._armory_entries]  # type: ignore[reportPrivateUsage]
            index = next(i for i, label in enumerate(labels) if "study" in label)
            current = app.query_one("#armory-current-inline", tui.OptionList)  # type: ignore[reportPrivateUsage]
            current.highlighted = index
            await pilot.press("enter")
            await pilot.pause()
            assert app._armory_inline_active is False  # type: ignore[reportPrivateUsage]
            assert app.session.armory_path == armory_path
            assert app.session.source_file_count == 1

    asyncio.run(check_enter_opens_armory())


def test_handle_armory_browser_switches_to_selected_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
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
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
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
            app._handle_armory_browser("/armory open")  # type: ignore[reportPrivateUsage]
            app._open_selected_armory(armory_path)  # type: ignore[reportPrivateUsage]
            assert app.session is new_session
            assert any("Using armory" in entry.content for entry in app.state.transcript)
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            assert app.focused is composer  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_switch())


def test_click_refocuses_composer() -> None:
    if tui.Input is None or tui.Static is None or tui.events is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()  # type: ignore[reportPrivateUsage]
    vertical_class = tui._transparent_vertical_class()  # type: ignore[reportPrivateUsage]
    input_class = tui._transparent_input_class()  # type: ignore[reportPrivateUsage]
    static_class = tui._transparent_static_class()  # type: ignore[reportPrivateUsage]
    rich_log_class = tui._transparent_rich_log_class()  # type: ignore[reportPrivateUsage]

    class ClickSmoke(tui.App[None]):  # type: ignore[index]
        CSS = tui._tui_css()  # type: ignore[reportPrivateUsage]

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with vertical_class(id="shell"):  # type: ignore[operator, reportCallIssue]
                yield static_class(  # type: ignore[operator]
                    tui._status_text(session),  # type: ignore[reportPrivateUsage]
                    id="status",
                )
                yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)  # type: ignore[operator]
                yield static_class("", id="thinking-indicator")  # type: ignore[operator]
                with vertical_class(id="composer-frame"):  # type: ignore[operator, reportCallIssue]
                    yield input_class(  # type: ignore[operator]
                        placeholder="Ask...",
                        id="composer",
                    )
                    yield static_class(  # type: ignore[operator]
                        tui._footer_hints_text(session),  # type: ignore[reportPrivateUsage]
                        id="footer-hints",
                    )

        def on_click(self, event: tui.events.Click) -> None:  # type: ignore[reportPrivateUsage]
            composer = self.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            if self.focused is not composer:
                self.call_after_refresh(composer.focus)

    async def check_click_focus() -> None:
        app = ClickSmoke()
        async with app.run_test(size=(120, 12)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            assert app.focused is composer
            # Click on transcript area
            await pilot.click("#transcript", offset=(5, 2))
            await pilot.pause()
            await pilot.pause()
            # Composer should be re-focused by the on_click handler
            assert app.focused is composer

    asyncio.run(check_click_focus())


def test_completion_menu_auto_highlights_first_item() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()  # type: ignore[reportPrivateUsage]
    vertical_class = tui._transparent_vertical_class()  # type: ignore[reportPrivateUsage]
    horizontal_class = tui._transparent_horizontal_class()  # type: ignore[reportPrivateUsage]
    input_class = tui._transparent_input_class()  # type: ignore[reportPrivateUsage]
    static_class = tui._transparent_static_class()  # type: ignore[reportPrivateUsage]
    rich_log_class = tui._transparent_rich_log_class()  # type: ignore[reportPrivateUsage]
    option_list_class = tui._transparent_option_list_class()  # type: ignore[reportPrivateUsage]

    engine = tui.SlashCompletionEngine()

    class CompletionSmoke(tui.App[None]):  # type: ignore[index]
        CSS = tui._tui_css()  # type: ignore[reportPrivateUsage]

        def __init__(self) -> None:
            super().__init__()
            self.completion_engine = engine
            self.completion_candidates: list[tui.CompletionCandidate] = []

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with horizontal_class(id="main-layout"):  # type: ignore[operator, reportCallIssue]
                with vertical_class(id="shell"):  # type: ignore[operator, reportCallIssue]
                    yield static_class(  # type: ignore[operator]
                        tui._status_text(session),  # type: ignore[reportPrivateUsage]
                        id="status",
                    )
                    yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)  # type: ignore[operator]
                    yield static_class("", id="thinking-indicator")  # type: ignore[operator]
                    with vertical_class(id="composer-frame"):  # type: ignore[operator, reportCallIssue]
                        yield input_class(  # type: ignore[operator]
                            placeholder="Ask...",
                            id="composer",
                        )
                        yield static_class(  # type: ignore[operator]
                            tui._footer_hints_text(session),  # type: ignore[reportPrivateUsage]
                            id="footer-hints",
                        )
                yield static_class("", id="info-separator")  # type: ignore[operator]
                yield static_class(  # type: ignore[operator]
                    tui._info_panel_default_text(session),  # type: ignore[reportPrivateUsage]
                    id="info-panel",
                )
            yield option_list_class(id="suggestions", classes="hidden", markup=False)  # type: ignore[operator]

        def on_mount(self) -> None:
            self.query_one("#composer", tui.Input).focus()  # type: ignore[reportPrivateUsage]

        def on_input_changed(self, event: tui.Input.Changed) -> None:  # type: ignore[reportPrivateUsage]
            if event.input.id == "composer":  # type: ignore[reportUnknownMemberType]
                self._refresh_completions()

        def _refresh_completions(self) -> None:
            composer = self.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            before_cursor = composer.value[: composer.cursor_position]
            self.completion_candidates = self.completion_engine.candidates(
                before_cursor,
                tui._tui_command_suggestions(),  # type: ignore[reportPrivateUsage]
            )
            suggestions = self.query_one("#suggestions", tui.OptionList)  # type: ignore[reportPrivateUsage]
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
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            # Type "/" to trigger completions
            await pilot.press("/")
            await pilot.pause()
            suggestions = app.query_one("#suggestions", tui.OptionList)  # type: ignore[reportPrivateUsage]
            # The suggestion list should be visible with first item highlighted
            assert not suggestions.has_class("hidden")
            assert suggestions.highlighted == 0
            assert suggestions.option_count > 0
            # Composer should retain focus after the brief focus swap
            assert app.focused is composer

    asyncio.run(check_highlight())


def test_tab_applies_highlighted_completion_in_composer() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_tab_completion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]

            await pilot.press("/")
            await pilot.pause()
            assert composer.value == "/"  # type: ignore[reportUnknownMemberType]
            assert app.completion_candidates

            await pilot.press("tab")
            await pilot.pause()

            assert composer.value == "/help "  # type: ignore[reportUnknownMemberType]
            assert composer.cursor_position == len("/help ")  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_tab_completion())


def test_enter_submits_highlighted_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)
    handled: list[str] = []

    def fake_handle_inline_command(value: str) -> None:
        handled.append(value)

    async def check_enter_completion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            monkeypatch.setattr(app, "_handle_inline_command", fake_handle_inline_command)
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/model"
            composer.cursor_position = len("/model")  # type: ignore[reportUnknownMemberType]
            app._refresh_completions()  # type: ignore[reportPrivateUsage]

            await pilot.press("enter")
            await pilot.pause()

            assert handled == ["/models"]
            assert composer.value == ""  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_enter_completion())


def test_models_completion_menu_uses_readable_columns() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _keyless_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_model_columns() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()

            first = app._format_completion_candidate(  # type: ignore[reportPrivateUsage]
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

            assert first.startswith("OpenAI         openai")
            assert "Pollinations" in first
            assert "free current" in first
            assert "/models" not in first

    asyncio.run(check_model_columns())


def test_models_command_shows_plain_suggestion() -> None:
    """Typing /models shows a regular command suggestion, not inline model picks."""
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _keyless_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_models_suggestion() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/models"
            composer.cursor_position = len("/models")  # type: ignore[reportUnknownMemberType]
            app._refresh_completions()  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            assert len(app.completion_candidates) == 1
            assert app.completion_candidates[0].text == "models "
            assert app.completion_candidates[0].description == "Pick the active model"
            suggestions = app.query_one("#suggestions", tui.OptionList)  # type: ignore[reportPrivateUsage]
            footer = app.query_one("#footer-hints", tui.Static)  # type: ignore[reportPrivateUsage]
            assert suggestions.has_class("visible")
            assert not suggestions.has_class("model-picker")
            position = app.query_one("#completion-position", tui.Static)  # type: ignore[reportPrivateUsage]
            assert str(position.render()) == "(1/1)"
            assert str(footer.render()).startswith("enter send")

    asyncio.run(check_models_suggestion())


def test_busy_footer_keeps_cancel_hint_with_completion_menu_visible() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_busy_footer() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/"
            composer.cursor_position = 1  # type: ignore[reportUnknownMemberType]
            app._refresh_completions()  # type: ignore[reportPrivateUsage]
            app.busy = True
            app._refresh_footer_hints()  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            footer = app.query_one("#footer-hints", tui.Static)  # type: ignore[reportPrivateUsage]
            position = app.query_one("#completion-position", tui.Static)  # type: ignore[reportPrivateUsage]
            assert str(footer.render()) == "ctrl+c cancel"
            assert str(position.render()) == "(1/28)"

    asyncio.run(check_busy_footer())


def test_slash_on_empty_composer_preserves_cursor_after_focus_swap() -> None:
    """Pressing / must show completions without selecting/highlighting the / character.

    Regression test: the focus swap in _refresh_completions (set_focus(suggestions)
    then set_focus(composer)) was causing Textual's Input to select its text, so the
    next keypress would replace the / instead of appending to it.
    """
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    screen_class = tui._transparent_screen_class()  # type: ignore[reportPrivateUsage]
    vertical_class = tui._transparent_vertical_class()  # type: ignore[reportPrivateUsage]
    horizontal_class = tui._transparent_horizontal_class()  # type: ignore[reportPrivateUsage]
    input_class = tui._transparent_input_class()  # type: ignore[reportPrivateUsage]
    static_class = tui._transparent_static_class()  # type: ignore[reportPrivateUsage]
    rich_log_class = tui._transparent_rich_log_class()  # type: ignore[reportPrivateUsage]
    option_list_class = tui._transparent_option_list_class()  # type: ignore[reportPrivateUsage]

    engine = tui.SlashCompletionEngine()

    class SlashSmoke(tui.App[None]):  # type: ignore[index]
        CSS = tui._tui_css()  # type: ignore[reportPrivateUsage]

        def __init__(self) -> None:
            super().__init__()
            self.completion_engine = engine
            self.completion_candidates: list[tui.CompletionCandidate] = []

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with horizontal_class(id="main-layout"):  # type: ignore[operator, reportCallIssue]
                with vertical_class(id="shell"):  # type: ignore[operator, reportCallIssue]
                    yield static_class(  # type: ignore[operator]
                        tui._status_text(session),  # type: ignore[reportPrivateUsage]
                        id="status",
                    )
                    yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)  # type: ignore[operator]
                    yield static_class("", id="thinking-indicator")  # type: ignore[operator]
                    with vertical_class(id="composer-frame"):  # type: ignore[operator, reportCallIssue]
                        yield input_class(  # type: ignore[operator]
                            placeholder="Ask...",
                            id="composer",
                        )
                        yield static_class(  # type: ignore[operator]
                            tui._footer_hints_text(session),  # type: ignore[reportPrivateUsage]
                            id="footer-hints",
                        )
                yield static_class("", id="info-separator")  # type: ignore[operator]
                yield static_class(  # type: ignore[operator]
                    tui._info_panel_default_text(session),  # type: ignore[reportPrivateUsage]
                    id="info-panel",
                )
            yield option_list_class(id="suggestions", classes="hidden", markup=False)  # type: ignore[operator]

        def on_mount(self) -> None:
            composer = self.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.select_on_focus = False
            composer.focus()

        def on_input_changed(self, event: tui.Input.Changed) -> None:  # type: ignore[reportPrivateUsage]
            if event.input.id == "composer":  # type: ignore[reportUnknownMemberType]
                self._refresh_completions()

        def _refresh_completions(self) -> None:
            composer = self.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            before_cursor = composer.value[: composer.cursor_position]
            self.completion_candidates = self.completion_engine.candidates(
                before_cursor,
                tui._tui_command_suggestions(),  # type: ignore[reportPrivateUsage]
            )
            suggestions = self.query_one("#suggestions", tui.OptionList)  # type: ignore[reportPrivateUsage]
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
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
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
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_scroll_policy() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("/")
            await pilot.pause()

            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),  # type: ignore[reportPrivateUsage]
            )  # ty:ignore[redundant-cast]
            footer = app.query_one("#footer-hints", tui.Static)  # type: ignore[reportPrivateUsage]

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
                position = app.query_one("#completion-position", tui.Static)  # type: ignore[reportPrivateUsage]
                assert str(position.render()) == f"({highlighted + 1}/{suggestions.option_count})"
                assert str(footer.render()).startswith("enter send")

    asyncio.run(check_scroll_policy())


def test_completion_menu_highlight_moves_down_at_bottom() -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    app = tui.HephaistosTui(
        _plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    typed_app = cast("TextualApp[None]", app)

    async def check_bottom_policy() -> None:
        async with typed_app.run_test(size=(120, 24)) as pilot:
            await pilot.press("/")
            await pilot.pause()

            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),  # type: ignore[reportPrivateUsage]
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
