"""Shared test fixtures for Hephaistos tests."""

from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path
from types import SimpleNamespace

import pytest

from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import create_session


@pytest.fixture(autouse=True)
def _isolate_global_state() -> Generator[None]:
    """Reset mutable module-level globals between tests."""
    import hephaistos.logging as _log_mod
    import hephaistos.providers.keyring_store as _ks

    _ks._volatile.clear()
    _log_mod._root_initialised = False
    root = logging.getLogger("hephaistos")
    root.handlers.clear()
    root.setLevel(logging.WARNING)

    yield

    _ks._volatile.clear()
    _log_mod._root_initialised = False
    root.handlers.clear()
    root.setLevel(logging.WARNING)


@pytest.fixture
def isolated_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Redirect user-config paths to a temp directory."""
    config_dir = tmp_path / "hephaistos_config"
    config_file = config_dir / "config.json"
    defaults_file = tmp_path / "default.toml"
    monkeypatch.setattr("hephaistos.parameters.cli._USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr("hephaistos.parameters.cli._USER_CONFIG_FILE", config_file)
    monkeypatch.setattr("hephaistos.parameters.cli._DEFAULTS_FILE", defaults_file)
    return SimpleNamespace(
        config_dir=config_dir, config_file=config_file, defaults_file=defaults_file
    )


@pytest.fixture
def isolated_auth_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Redirect auth paths to a temp directory."""
    auth_dir = tmp_path / "auth_test"
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "auth.json"
    monkeypatch.setattr("hephaistos.providers.oauth._AUTH_DIR", auth_dir)
    monkeypatch.setattr("hephaistos.providers.oauth._AUTH_FILE", auth_file)
    return SimpleNamespace(auth_dir=auth_dir, auth_file=auth_file)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with sample files for tool tests."""
    (tmp_path / "hello.py").write_text('print("hello")\n')
    (tmp_path / "README.md").write_text("# Test\n")
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "main.py").write_text("def main(): pass\n")
    return tmp_path


@pytest.fixture
def armory(tmp_path: Path) -> Path:
    """Create a minimal armory with source files."""
    arm = tmp_path / "test-armory"
    (arm / "source").mkdir(parents=True)
    (arm / "library").mkdir(parents=True)
    (arm / ".hephaistos").mkdir(parents=True)

    (arm / "source" / "python.md").write_text(
        "# Python Basics\n\n"
        "Python is a high-level programming language.\n\n"
        "Variables are dynamically typed.\n\n"
        "Functions use the `def` keyword.\n"
    )
    (arm / "source" / "rust.md").write_text(
        "# Rust Basics\n\n"
        "Rust is a systems programming language.\n\n"
        "Ownership and borrowing are core concepts.\n\n"
        "Cargo is the build tool.\n"
    )
    (arm / "library" / "algorithms.md").write_text(
        "# Algorithms\n\n"
        "Binary search runs in O(log n) time.\n\n"
        "Quick sort has average O(n log n) complexity.\n\n"
        "Merge sort is stable and runs in O(n log n).\n"
    )
    return arm


@pytest.fixture
def chat_session(tmp_path: Path):
    """Create a session attached to a valid armory."""
    armory_path = tmp_path / "test-armory"
    initialize(armory_path)
    (armory_path / "source").mkdir(exist_ok=True)
    (armory_path / "source" / "exam.md").write_text(
        "# Past Exam\n## Q1\nWhat is 2+2?\n\nAnswer: 4\n"
    )
    return create_session(
        ChatConfig(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        ),
        armory_path,
    )


@pytest.fixture
def providers_toml(tmp_path: Path) -> Path:
    """Create a minimal providers.toml for testing."""
    path = tmp_path / "providers.toml"
    path.write_text(
        """
[zai]
display_name = "Z.AI"
endpoint = "https://api.z.ai/api/paas/v4/"
api_key_env = "ZAI_API_KEY"
active = true
current_model = "glm-5"
models = ["glm-5", "glm-5-plus"]

[openrouter]
display_name = "OpenRouter"
endpoint = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
active = false
current_model = ""
models = ["openai/gpt-5.4", "google/gemini-3-flash-preview"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path
