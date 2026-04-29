"""Tests for the optional Textual shell wrapper."""

# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from hephaistos.app import tui
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession

if TYPE_CHECKING:
    from textual.screen import Screen
    from textual.widget import Widget


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


def test_footer_hints_show_idle_shortcuts() -> None:
    hints = tui._footer_hints_text(_plain_session())  # type: ignore[reportPrivateUsage]
    plain = hints.plain

    assert "enter" in plain
    assert "tab" in plain
    assert "/help" in plain
    assert "ctrl+d" in plain
    assert "armory" not in plain
    assert "test-model" not in plain


def test_footer_hints_show_cancel_when_busy() -> None:
    hints = tui._footer_hints_text(_plain_session(), busy=True)  # type: ignore[reportPrivateUsage]
    plain = hints.plain

    assert "ctrl+c" in plain
    assert "cancel" in plain
    assert "enter" not in plain
    assert "/help" not in plain


def test_footer_hints_show_api_missing_when_unconfigured() -> None:
    session = _plain_session()
    session.config.api_key = None
    hints = tui._footer_hints_text(session)  # type: ignore[reportPrivateUsage]
    plain = hints.plain

    assert "api missing" in plain


def test_tui_css_keeps_surface_transparent() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    assert "App {\n    background: transparent;" in css
    assert "Screen {\n    layout: vertical;\n    background: transparent;" in css
    assert "#status {\n    height: 1;\n    width: auto;" in css
    assert ("#footer-hints {\n    height: 1;\n    width: auto;\n    max-width: 100%;") in css
    assert "#transcript:focus" in css
    assert "background-tint: transparent;" in css
    assert "background: ansi_default;" not in css
    assert "border-bottom: tall" not in css


def test_tui_css_has_info_panel_layout() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    assert "#info-panel" in css
    assert "#info-separator" in css
    assert "#shell" in css


def test_tui_css_prevents_full_width_status_and_composer_bars() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    for selector in ("#status", "#composer-frame", "#composer", "#footer-hints"):
        block_start = css.index(f"{selector} {{")
        block_end = css.index("}", block_start)
        block = css[block_start:block_end]

        assert "width: auto;" in block
        assert "max-width: 100%;" in block


def test_tui_css_positions_suggestions_above_composer_spacer() -> None:
    css = tui._tui_css()  # type: ignore[reportPrivateUsage]

    composer_start = css.index("#composer-frame {")
    composer_end = css.index("}", composer_start)
    composer_block = css[composer_start:composer_end]
    suggestions_start = css.index("#suggestions {")
    suggestions_end = css.index("}", suggestions_start)
    suggestions_block = css[suggestions_start:suggestions_end]
    footer_start = css.index("#footer-hints {")
    footer_end = css.index("}", footer_start)
    footer_block = css[footer_start:footer_end]

    assert "margin-top: 1;" in composer_block
    assert "margin-bottom: 3;" in suggestions_block
    assert "margin-top: 1;" in footer_block


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
    assert "/provider" in help_text
    assert "/sources" in help_text
    assert "/status" in help_text


def test_tui_slash_suggestion_uses_shared_registry() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/sta")  # type: ignore[reportPrivateUsage]

    assert suggestion == "/status "


def test_tui_slash_suggestion_includes_tui_source_command() -> None:
    engine = tui.SlashCompletionEngine()

    suggestion = tui._slash_suggestion(engine, "/sou")  # type: ignore[reportPrivateUsage]

    assert suggestion == "/sources "


def test_source_listing_filters_with_fuzzy_match() -> None:
    session = _plain_session()
    session.source_files = ("source/binary-search.md", "library/calculus.md")
    session.source_file_count = 2

    listing = tui._source_listing(session, "binary")  # type: ignore[reportPrivateUsage]

    assert listing.splitlines()[0] == "@source/binary-search.md"


def test_run_tui_reports_missing_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tui, "Markdown", None)

    with pytest.raises(tui.TuiDependencyError) as exc_info:
        tui.run_tui(_plain_session())

    message = str(exc_info.value)
    assert "repository root" in message
    assert "uv sync --frozen" in message
    assert "uv run --project" not in message
    assert "-m pip install -e ." in message


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
    assert tui._is_armory_command("  /armory  ")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("/ARMORY OPEN")  # type: ignore[reportPrivateUsage]

    assert not tui._is_armory_command("/armory detach")  # type: ignore[reportPrivateUsage]
    assert not tui._is_armory_command("/model")  # type: ignore[reportPrivateUsage]
    assert not tui._is_armory_command("hello")  # type: ignore[reportPrivateUsage]


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
