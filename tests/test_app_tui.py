"""Tests for the optional Textual shell wrapper."""

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


def _pollinations_session() -> ChatSession:
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


def test_composer_meta_keeps_input_hints_below_composer() -> None:
    meta = tui._composer_meta(_plain_session())  # type: ignore[reportPrivateUsage]

    assert "enter send" in meta
    assert "tab complete" in meta
    assert "/help commands" in meta
    assert "ctrl+c interrupt" in meta
    assert "ctrl+d exit" in meta
    assert "armory" not in meta
    assert "test-model" not in meta


def test_tui_config_error_allows_pollinations_without_api_key() -> None:
    assert tui._config_error(_pollinations_session()) is None  # type: ignore[reportPrivateUsage]


def test_tui_css_keeps_surface_transparent() -> None:
    css = tui._TUI_CSS  # type: ignore[reportPrivateUsage]

    assert "App {\n    background: transparent;" in css
    assert "Screen {\n    layout: vertical;\n    background: transparent;" in css
    assert "#status {\n    height: 2;\n    width: auto;" in css
    assert ("#composer-meta {\n    height: 1;\n    width: auto;\n    max-width: 100%;") in css
    assert "#transcript:focus" in css
    assert "background-tint: transparent;" in css
    assert "background: ansi_default;" not in css
    assert "border-bottom: tall" not in css


def test_tui_css_prevents_full_width_status_and_composer_bars() -> None:
    css = tui._TUI_CSS  # type: ignore[reportPrivateUsage]

    for selector in ("#status", "#composer-frame", "#composer", "#composer-meta"):
        block_start = css.index(f"{selector} {{")
        block_end = css.index("}", block_start)
        block = css[block_start:block_end]

        assert "width: auto;" in block
        assert "max-width: 100%;" in block


def test_status_and_composer_meta_segments_do_not_paint_black_background() -> None:
    if tui.Static is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    class Smoke(tui.App[None]):  # type: ignore[index]
        CSS = tui._TUI_CSS  # type: ignore[reportPrivateUsage]

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            status_text = tui._status_text(session)  # type: ignore[reportPrivateUsage]
            meta_text = tui._composer_meta_text(session)  # type: ignore[reportPrivateUsage]
            with tui.Vertical(id="shell"):  # type: ignore[operator, reportCallIssue]
                yield tui.Static(status_text, id="status")  # type: ignore[operator]
                yield tui.Static(meta_text, id="composer-meta")  # type: ignore[operator]

    async def check_segments() -> None:
        app = Smoke()
        async with app.run_test(size=(120, 12)) as pilot:
            await pilot.pause()
            for selector in ("#status", "#composer-meta"):
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
        CSS = tui._TUI_CSS  # type: ignore[reportPrivateUsage]

        def get_default_screen(self) -> Screen[object]:
            return screen_class(id="_default")

        def compose(self) -> tui.ComposeResult:
            session = _plain_session()
            with vertical_class(id="shell"):  # type: ignore[operator, reportCallIssue]
                yield static_class(tui._status_text(session), id="status")  # type: ignore[operator, reportPrivateUsage]
                yield rich_log_class(id="transcript", markup=True, wrap=True, highlight=True)  # type: ignore[operator]
                with vertical_class(id="composer-frame"):  # type: ignore[operator, reportCallIssue]
                    yield input_class(  # type: ignore[operator]
                        placeholder='Ask anything... "What do I need to study next?"',
                        id="composer",
                    )
                    yield static_class(  # type: ignore[operator]
                        tui._composer_meta_text(session),  # type: ignore[reportPrivateUsage]
                        id="composer-meta",
                    )

    async def check_layout_blanks() -> None:
        app = Smoke()
        async with app.run_test(size=(120, 12)) as pilot:
            await pilot.pause()
            widgets: tuple[Widget, ...] = (
                cast("Widget", app.screen),
                app.query_one("#shell"),
                app.query_one("#status"),
                app.query_one("#transcript"),
                app.query_one("#composer-frame"),
                app.query_one("#composer"),
                app.query_one("#composer-meta"),
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
        CSS = tui._TUI_CSS  # type: ignore[reportPrivateUsage]

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
