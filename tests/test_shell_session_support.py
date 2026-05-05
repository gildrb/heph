from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import create_plain_session
from hephaistos.shell import session_support


def _config() -> ChatConfig:
    return ChatConfig(base_url="https://api.example.com", model="test-model")


def test_prompt_module_name_returns_none_on_eof(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)

    assert session_support._prompt_module_name() is None  # type: ignore[reportPrivateUsage]


def test_onboard_new_armory_returns_none_for_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "cancel")

    assert session_support.onboard_new_armory(_config()) is None


def test_onboard_new_armory_reports_initialize_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(session_support, "_DEFAULT_ARMORY_HOME", tmp_path)  # type: ignore[reportPrivateUsage]
    monkeypatch.setattr("builtins.input", lambda _prompt: "demo")
    monkeypatch.setattr(
        session_support,
        "initialize",
        lambda _path: (_ for _ in ()).throw(OSError("boom")),
    )
    errors: list[str] = []
    monkeypatch.setattr(session_support, "print_error", errors.append)

    assert session_support.onboard_new_armory(_config()) is None
    assert errors == ["boom"]


def test_onboard_new_armory_returns_none_when_user_skips_materials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(session_support, "_DEFAULT_ARMORY_HOME", tmp_path)  # type: ignore[reportPrivateUsage]
    monkeypatch.setattr(session_support, "add_known_armory", lambda _path: [])
    answers = iter(["demo", "skip"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert session_support.onboard_new_armory(_config()) is None
    assert (tmp_path / "demo" / "materials").is_dir()


def test_onboard_new_armory_returns_none_when_material_prompt_is_interrupted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(session_support, "_DEFAULT_ARMORY_HOME", tmp_path)  # type: ignore[reportPrivateUsage]
    monkeypatch.setattr(session_support, "add_known_armory", lambda _path: [])

    def _input(prompt: str) -> str:
        if prompt == "Module name: ":
            return "demo"
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", _input)

    assert session_support.onboard_new_armory(_config()) is None


def test_recover_empty_armory_session_returns_none_on_skip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = tmp_path / "demo"
    initialize(armory)
    monkeypatch.setattr("builtins.input", lambda _prompt: "skip")

    assert session_support.recover_empty_armory_session(_config(), armory) is None


def test_recover_empty_armory_session_returns_none_on_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = tmp_path / "demo"
    initialize(armory)

    def _raise_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)

    assert session_support.recover_empty_armory_session(_config(), armory) is None


def test_recover_empty_armory_session_returns_session_after_materials_added(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = tmp_path / "demo"
    initialize(armory)
    prompts: list[str] = []

    def _input(_prompt: str) -> str:
        prompts.append(_prompt)
        (armory / "materials" / "notes.md").write_text("# Notes\ncontent\n", encoding="utf-8")
        return ""

    monkeypatch.setattr("builtins.input", _input)

    session = session_support.recover_empty_armory_session(_config(), armory)

    assert session is not None
    assert session.armory_path == armory.resolve()
    assert len(prompts) == 1


def test_save_on_exit_saves_dirty_armory_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(_config())
    session.dirty = True
    session.armory_path = tmp_path  # type: ignore[assignment]
    session.trace = MagicMock()  # type: ignore[assignment]
    saved = tmp_path / "chat.json"
    success: list[str] = []

    monkeypatch.setattr(session_support, "session_has_messages", lambda _session: True)
    monkeypatch.setattr(session_support, "save_session", lambda _session: saved)
    monkeypatch.setattr(session_support, "print_success", success.append)

    session_support.save_on_exit(session)

    assert success == [f"Saved chat to {saved}"]
    session.trace.close.assert_called_once()


def test_save_on_exit_reports_storage_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(_config())
    session.dirty = True
    session.armory_path = tmp_path  # type: ignore[assignment]
    session.trace = MagicMock()  # type: ignore[assignment]
    errors: list[str] = []

    monkeypatch.setattr(session_support, "session_has_messages", lambda _session: True)
    monkeypatch.setattr(
        session_support,
        "save_session",
        lambda _session: (_ for _ in ()).throw(chat_storage.ChatStorageError("boom")),
    )
    monkeypatch.setattr(session_support, "print_error", errors.append)

    session_support.save_on_exit(session)

    assert errors == ["boom"]
    session.trace.close.assert_called_once()
