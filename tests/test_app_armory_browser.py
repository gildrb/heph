"""Tests for the inline Textual armory browser screen."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from hephaion.armory.search import KnownArmory
from hephaion.armory.storage import MARKER_FILE, initialize
from hephaion.tui import armory_browser

# Skip the entire module if Textual is not installed.
pytestmark = pytest.mark.skipif(
    armory_browser.ModalScreen is object,
    reason="Textual is not installed",
)

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Input, OptionList, Static
except ImportError:
    App = None  # ty:ignore[invalid-assignment]
    ComposeResult = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]


class _ShellApp(App[None]):
    """Minimal Textual app used to host screens under test."""

    def compose(self) -> ComposeResult:
        yield Static("test", id="placeholder")


class _SubmissionCountingApp(_ShellApp):
    """Host app that records bubbled input submissions."""

    def __init__(self) -> None:
        super().__init__()
        self.submission_count = 0

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.submission_count += 1


def _make_dirs(parent: Path, *names: str) -> list[Path]:
    """Create child directories under *parent* and return them."""
    dirs: list[Path] = []
    for name in names:
        d = parent / name
        d.mkdir(parents=True, exist_ok=True)
        dirs.append(d)
    return dirs


def _make_armory(parent: Path, name: str) -> Path:
    """Create an initialized armory under *parent*."""
    path = parent / name
    initialize(path)
    return path


def test_list_entries_skips_hidden_and_files_by_default(tmp_path: Path) -> None:
    _make_dirs(tmp_path, "visible", ".hidden")
    (tmp_path / "a-file.txt").touch()

    dirs = armory_browser._list_entries(tmp_path)

    names = [d.name for d in dirs]
    assert "visible" in names
    assert ".hidden" not in names
    assert "a-file.txt" not in names


def test_is_armory_detects_marker(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path, "my-armory")
    plain = tmp_path / "plain-dir"
    plain.mkdir()

    assert armory_browser._is_armory(armory)
    assert not armory_browser._is_armory(plain)


def test_build_entries_include_recent_all_and_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    entries = armory_browser.build_entries(allow_create=True)

    assert entries[0].is_section
    assert entries[0].label == armory_browser._RECENT_HEADING
    assert any(
        entry.is_create and entry.label == armory_browser._NEW_ARMORY_LABEL for entry in entries
    )
    assert any(
        entry.is_section and entry.label == armory_browser._ALL_HEADING for entry in entries
    )


def test_build_entries_without_create_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    _make_dirs(armory_home, "alpha", "beta")
    entries = armory_browser.build_entries(allow_create=False)

    labels = [e.label for e in entries]
    assert not any(e.is_create for e in entries)
    assert any("alpha" in label for label in labels)
    assert any("beta" in label for label in labels)


def test_build_entries_can_include_common_places(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    entries = armory_browser.build_entries(allow_create=True, show_places=True)

    place_entries = [entry for entry in entries if entry.is_place]
    assert any(entry.path == armory_home for entry in place_entries)
    assert all(
        entry.path is not None and armory_browser._is_within_armory_home(entry.path)
        for entry in place_entries
    )
    assert not any(entry.path == Path("/") for entry in place_entries)


def test_build_entries_filters_outside_recent_armories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    inside = _make_armory(armory_home, "inside")
    outside = _make_armory(tmp_path / "outside", "external")
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    monkeypatch.setattr(
        armory_browser,
        "load_known_armory_entries",
        lambda: [
            KnownArmory(outside, exists=True, valid=True),
            KnownArmory(inside, exists=True, valid=True),
        ],
    )

    entries = armory_browser.build_entries(allow_create=True)

    recent_paths = [entry.path for entry in entries if entry.is_recent]
    assert recent_paths == [inside]


def test_build_entries_discovers_armories_in_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    first = _make_armory(armory_home, "alpha")
    second = _make_armory(armory_home, "beta")
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    entries = armory_browser.build_entries(allow_create=True)

    all_paths = {entry.path for entry in entries if entry.path is not None}
    assert first.resolve() in all_paths
    assert second.resolve() in all_paths


def test_build_entries_filters_symlink_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    outside = tmp_path / "outside"
    armory_home.mkdir()
    outside.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    (armory_home / "outside-link").symlink_to(outside, target_is_directory=True)

    entries = armory_browser.build_entries(allow_create=True)

    assert not any(entry.path == armory_home / "outside-link" for entry in entries)


def test_default_start_path_rejects_outside_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    screen = armory_browser.ArmoryBrowserScreen(start=outside)

    assert screen._current == armory_home


def test_build_entries_returns_sectioned_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    alpha, beta = _make_dirs(armory_home, "alpha", "beta")
    entries = armory_browser.build_entries(allow_create=True)

    assert any(
        entry.is_section and entry.label == armory_browser._RECENT_HEADING for entry in entries
    )
    assert any(entry.is_create for entry in entries)
    assert any(
        entry.is_section and entry.label == armory_browser._ALL_HEADING for entry in entries
    )
    assert alpha in {entry.path for entry in entries}
    assert beta in {entry.path for entry in entries}


def test_browser_screen_compose_and_mount(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    _make_dirs(armory_home, "docs")

    async def run_screen() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            path_widget = screen.query_one("#armory-path", armory_browser.Static)
            rendered = path_widget.render()
            assert str(tmp_path.name) in str(rendered)

    asyncio.run(run_screen())


def test_browser_css_uses_borderless_transparent_surface() -> None:
    css = armory_browser._armory_browser_css(armory_browser.current_palette())

    dialog_start = css.index("#armory-dialog {")
    dialog_end = css.index("}", dialog_start)
    dialog_block = css[dialog_start:dialog_end]
    assert "border: none" in dialog_block
    assert "background-tint: transparent" in dialog_block
    assert "border: round" not in css


def test_browser_arrow_keys_move_highlight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    _make_dirs(armory_home, "alpha", "beta")

    async def run_keys() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(100, 28)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            assert ol.highlighted is not None
            first_highlight = ol.highlighted

            await pilot.press("down")
            await pilot.pause()
            assert ol.highlighted is not None
            assert ol.highlighted != first_highlight

            await pilot.press("up")
            await pilot.pause()
            assert ol.highlighted == first_highlight

    asyncio.run(run_keys())


def test_browser_enter_dismisses_with_selected_armory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    child = _make_dirs(armory_home, "child")[0]
    result_path: Path | None = None

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            ol.highlighted = next(
                index for index, entry in enumerate(screen._entries) if entry.path == child
            )
            await pilot.pause()
            screen.action_activate()
            await pilot.pause()
            assert result_path == child

    asyncio.run(run_nav())


def test_browser_right_arrow_does_not_navigate_into_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    child = _make_dirs(armory_home, "child")[0]

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(100, 28)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            ol.highlighted = next(
                index for index, entry in enumerate(screen._entries) if entry.path == child
            )
            await pilot.press("right")
            await pilot.pause()
            assert screen._current == armory_home

    asyncio.run(run_nav())


def test_browser_left_does_not_navigate_above_armory_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    async def run_nav() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            await pilot.press("left")
            await pilot.pause()
            assert screen._current == armory_home

    asyncio.run(run_nav())


def test_browser_enter_dismisses_with_current_armory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    armory = _make_armory(armory_home, "selected")
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    result_path: Path | None = None

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_choose() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            ol = screen.query_one("#armory-current-col", armory_browser.OptionList)
            ol.highlighted = next(
                index for index, entry in enumerate(screen._entries) if entry.path == armory
            )
            screen.action_activate()
            await pilot.pause()

    asyncio.run(run_choose())
    assert result_path == armory


def test_browser_cancel_dismisses_with_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    result_path: Path | None = "NOT_NONE"  # sentinel  # ty:ignore[invalid-assignment]

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_cancel() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            screen.action_cancel()
            await pilot.pause()

    asyncio.run(run_cancel())
    assert result_path is None


def test_browser_escape_key_dismisses_with_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    result_path: Path | None = "NOT_NONE"  # sentinel  # ty:ignore[invalid-assignment]

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_cancel() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

    asyncio.run(run_cancel())
    assert result_path is None


def test_browser_new_armory_creates_and_dismisses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))
    result_path: Path | None = None

    def on_result(path: Path | None) -> None:
        nonlocal result_path
        result_path = path

    async def run_new() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen, on_result)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "test-armory"
            screen.on_input_submitted(
                armory_browser.Input.Submitted(inp, "test-armory", "test-armory")  # ty:ignore[invalid-argument-type]
            )
            await pilot.pause()

    asyncio.run(run_new())
    assert result_path is not None
    assert result_path.name == "test-armory"
    assert (result_path / MARKER_FILE).exists()


def test_browser_new_armory_submission_does_not_bubble_to_chat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    async def run_new() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _SubmissionCountingApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "maths"
            await pilot.press("enter")
            await pilot.pause()
            assert app.submission_count == 0

    asyncio.run(run_new())


def test_new_armory_path_rejects_escape_names(tmp_path: Path) -> None:
    bad_names = ("../outside", "/tmp/outside", "nested/armory")

    for name in bad_names:
        path, error = armory_browser.new_armory_path(tmp_path, name)
        assert path is None
        assert error is not None


def test_new_armory_path_rejects_existing_folder(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()

    path, error = armory_browser.new_armory_path(tmp_path, "existing")

    assert path is None
    assert error is not None
    assert "already exists" in error


def test_browser_new_armory_refuses_unwritable_parent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    def not_writable(_path: Path) -> bool:
        return False

    monkeypatch.setattr(armory_browser, "_is_writable_directory", not_writable)

    async def run_error() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "blocked"
            await pilot.press("enter")
            await pilot.pause()
            error = screen.query_one("#armory-error", armory_browser.Static)
            assert "read-only folder" in str(error.render())
            assert not (armory_home / "blocked").exists()

    asyncio.run(run_error())


def test_browser_new_armory_surfaces_creation_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    def fail_initialize(_path: Path) -> None:
        raise OSError("permission denied")

    monkeypatch.setattr(armory_browser, "initialize", fail_initialize)

    async def run_error() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            screen.on_input_submitted(
                armory_browser.Input.Submitted(inp, "blocked", "blocked")  # ty:ignore[invalid-argument-type]
            )
            await pilot.pause()
            error = screen.query_one("#armory-error", armory_browser.Static)
            assert "Could not create armory" in str(error.render())
            assert screen._creating is True
            assert not (armory_home / "blocked").exists()

    asyncio.run(run_error())


def test_browser_new_armory_empty_name_cancels_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    async def run_empty() -> None:
        screen = armory_browser.ArmoryBrowserScreen(start=armory_home)
        app = _ShellApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await app.push_screen(screen)
            await pilot.pause()
            screen._start_new_armory()
            await pilot.pause()
            assert screen._creating is True
            inp = screen.query_one("#armory-new-input", armory_browser.Input)
            inp.value = "   "
            screen.on_input_submitted(
                armory_browser.Input.Submitted(inp, "   ", "   ")  # ty:ignore[invalid-argument-type]
            )
            await pilot.pause()
            assert screen._creating is False

    asyncio.run(run_empty())


def test_creation_parent_error_rejects_outside_armories_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    outside = tmp_path / "outside" / "armory"
    outside.mkdir(parents=True)

    error = armory_browser._creation_parent_error(outside)
    assert error is not None
    assert "Armories can only be created in the armories directory" in error
    assert str(armory_home) in error


def test_creation_parent_error_allows_inside_armories_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    armory_home = tmp_path / ".armories"
    armory_home.mkdir()
    monkeypatch.setenv("HEPHAION_ARMORY_HOME", str(armory_home))

    inside = armory_home / "new-armory"

    error = armory_browser._creation_parent_error(inside)
    assert error is None
