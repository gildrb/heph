"""Tests for the optional Textual shell wrapper."""

# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from hephaistos.app import tui
from hephaistos.app.armory_browser import armory_detail, build_entries
from hephaistos.app.search_index import KnownArmory
from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession
from hephaistos.providers import catalog
from hephaistos.providers.catalog import LiveProviderCatalog
from hephaistos.providers.config import default_config
from hephaistos.providers.registry import ModelInfo

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


def test_footer_hints_show_idle_shortcuts() -> None:
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


def test_footer_hints_show_api_missing_when_unconfigured() -> None:
    session = _plain_session()
    session.config.api_key = None
    hints = tui._footer_hints_text(session)  # type: ignore[reportPrivateUsage]
    plain = hints.plain

    assert "api missing" in plain


def test_tui_config_error_allows_pollinations_without_api_key() -> None:
    assert tui._config_error(_keyless_session()) is None  # type: ignore[reportPrivateUsage]


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
    session.source_files = ("materials/binary-search.md", "materials/calculus.md")
    session.source_file_count = 2

    listing = tui._source_listing(session, "binary")  # type: ignore[reportPrivateUsage]

    assert listing.splitlines()[0] == "@materials/binary-search.md"


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
    assert tui._is_armory_command("/armory detach")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("  /armory  ")  # type: ignore[reportPrivateUsage]
    assert tui._is_armory_command("/ARMORY OPEN")  # type: ignore[reportPrivateUsage]

    assert not tui._is_armory_command("/model")  # type: ignore[reportPrivateUsage]
    assert not tui._is_armory_command("hello")  # type: ignore[reportPrivateUsage]


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
    existing = tmp_path / "exam-prep"
    initialize(existing)
    missing = tmp_path / "missing"
    monkeypatch.setattr(
        "hephaistos.app.armory_browser.load_known_armory_entries",
        lambda: [
            KnownArmory(existing, exists=True, valid=True),
            KnownArmory(missing, exists=False, valid=False),
        ],
    )

    entries = build_entries(tmp_path, allow_create=True)
    labels = [entry.label for entry in entries]

    assert labels[0].startswith("recent  exam-prep")
    assert labels[1].startswith("recent  missing")
    assert "missing" in labels[1]


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
            )

            assert composer.value == "/"  # type: ignore[reportUnknownMemberType]
            assert composer.cursor_position == 1  # type: ignore[reportUnknownMemberType]
            assert suggestions.has_class("visible")
            assert app.completion_candidates

    asyncio.run(check_command_palette())


def test_armory_home_text_includes_recent_armories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    known = [tmp_path / "linear-algebra", tmp_path / "algorithms"]
    monkeypatch.setattr(tui, "load_known_armories", lambda: known)

    text = tui._armory_home_text()  # type: ignore[reportPrivateUsage]

    assert "No armory attached." in text
    assert "ctrl+a" in text
    assert "materials/" in text
    assert "Recent armories:" in text
    assert "linear-algebra" in text
    assert "algorithms" in text


def test_plain_tui_shows_armory_home_notice() -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

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


def test_armory_inline_composer_filters_without_chat_transcript(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

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


def test_armory_inline_new_armory_uses_composer_without_chat_transcript(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

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


def test_armory_inline_escape_cancels_create_then_exits(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

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
                cast("Widget", app.query_one("#armory-inline")),  # type: ignore[reportUnknownMemberType]
                cast("Widget", app.query_one("#armory-header")),  # type: ignore[reportUnknownMemberType]
                cast("Widget", app.query_one("#armory-current-inline")),  # type: ignore[reportUnknownMemberType]
                cast("Widget", app.query_one("#armory-preview-inline")),  # type: ignore[reportUnknownMemberType]
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
            preview = app.query_one("#armory-preview-inline", tui.Static)  # type: ignore[reportPrivateUsage]
            assert "filter: no-such-folder" in str(header.render())  # type: ignore[reportUnknownMemberType]
            assert "No matches" in str(preview.render())  # type: ignore[reportUnknownMemberType]

    asyncio.run(check_empty_filter())


def test_armory_inline_preserves_selection_across_refresh(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

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
            assert composer.placeholder == "New armory name..."  # type: ignore[reportUnknownMemberType]

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


def test_handle_armory_browser_rejects_invalid_directory(tmp_path: Path) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

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


def test_handle_armory_browser_switches_to_selected_armory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if tui.Input is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

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


def test_models_completion_menu_includes_live_openrouter_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if tui.Input is None or tui.OptionList is None:  # type: ignore[reportUnnecessaryComparison]
        pytest.skip("Textual is not installed")

    monkeypatch.delenv("HEPHAISTOS_DISABLE_LIVE_MODELS", raising=False)
    catalog.invalidate_catalog_cache()
    config = default_config()
    config.set_active("openrouter")

    def fake_fetch(_endpoint: str) -> LiveProviderCatalog:
        return LiveProviderCatalog(
            models=[
                "anthropic/claude-sonnet-latest",
                "poolside/laguna-m.1:free",
            ],
            metadata=[
                ModelInfo(
                    "anthropic/claude-sonnet-latest",
                    "openrouter",
                    "Anthropic Claude Sonnet Latest",
                    1_000_000,
                    128_000,
                    0.003,
                    0.015,
                ),
                ModelInfo(
                    "poolside/laguna-m.1:free",
                    "openrouter",
                    "Poolside Laguna M.1 (free)",
                    131_072,
                    8_192,
                    0.0,
                    0.0,
                    tags=("free",),
                ),
            ],
        )

    monkeypatch.setattr(catalog, "_fetch_openrouter_catalog", fake_fetch)
    app = tui.HephaistosTui(
        _configured_status_session(),
        tui._TuiRuntimeState(),  # type: ignore[reportPrivateUsage]
        tui.current_palette(),
    )
    app.completion_engine = tui.SlashCompletionEngine(provider_config_loader=lambda: config)
    typed_app = cast("TextualApp[None]", app)

    async def check_live_models_visible() -> None:
        async with typed_app.run_test(size=(140, 28)) as pilot:
            composer = app.query_one("#composer", tui.Input)  # type: ignore[reportPrivateUsage]
            composer.value = "/models"
            composer.cursor_position = len("/models")  # type: ignore[reportUnknownMemberType]
            app._refresh_completions()  # type: ignore[reportPrivateUsage]
            await pilot.pause()

            suggestions = cast(
                "TextualOptionList",
                app.query_one("#suggestions", tui.OptionList),  # type: ignore[reportPrivateUsage]
            )
            visible_models = [candidate.text.strip() for candidate in app.completion_candidates]

            assert suggestions.option_count == len(app.completion_candidates)
            assert visible_models[:2] == [
                "poolside/laguna-m.1:free",
                "anthropic/claude-sonnet-latest",
            ]
            assert suggestions.has_class("visible")
            assert suggestions.has_class("model-picker")

    asyncio.run(check_live_models_visible())


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
            )

            assert suggestions.highlighted == 0
            assert suggestions.scroll_y == 0
            assert [c.text.strip() for c in app.completion_candidates[:6]] == [
                "help",
                "exit",
                "login",
                "logout",
                "status",
                "save",
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
            )
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
