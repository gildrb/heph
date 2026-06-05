"""Shared test fixtures for Heph tests."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Generator
from pathlib import Path
from types import SimpleNamespace

import pytest

# Avoid writing .pyc files during test runs
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import ai.logging as _log_mod
import ai.providers.catalog as _provider_catalog_mod
import ai.providers.config as _provider_config_mod
import ai.providers.keyring_store as _ks
import ai.providers.oauth as _oauth_mod
import ai.runtime.engine as _engine_mod
import ai.runtime.resilience as _res_mod
import chat.turn_finalization as _turn_finalization_mod
import commands as _commands_mod
import diagnostics.crashes as _obs_mod
import parameters.settings as _settings_mod
import privacy.consent as _privacy_mod
import rag.chunker as _rag_chunker_mod
import rag.optional_backends as _rag_optional_mod
import tui.command_access as _tui_command_access
from agent.tools import ToolHandlerResult, ToolSpec
from ai.runtime import ApiMessage, ChatConfig
from armory.storage import initialize
from chat.session import create_session
from terminal import set_theme

# Cache noop diagnostics objects to avoid recreating per test
_NOOP_TRACER = _obs_mod._NoopTracer()
_NOOP_METER = _obs_mod._NoopMeter()
_NOOP_HISTOGRAM = _obs_mod._NoopHistogram()
_NOOP_COUNTER = _obs_mod._NoopCounter()
_NOOP_GAUGE = _obs_mod._NoopGauge()


def _reset_diagnostics_module_objects() -> None:
    """Replace module-level diagnostics objects with no-ops to isolate tests."""
    _noop_tracer = _NOOP_TRACER
    _noop_meter = _NOOP_METER

    # engine.py
    _engine_mod._tracer = _noop_tracer  # ty:ignore[invalid-assignment]
    _engine_mod._meter = _noop_meter
    _engine_mod._llm_duration_hist = _NOOP_HISTOGRAM
    _engine_mod._llm_token_counter = _NOOP_COUNTER

    # resilience.py
    _res_mod._meter = _noop_meter
    _res_mod._state_gauge = _NOOP_GAUGE

    # turn_finalization.py
    _turn_finalization_mod._tracer = _noop_tracer
    _turn_finalization_mod._meter = _noop_meter
    _turn_finalization_mod._rag_duration_hist = _NOOP_HISTOGRAM


def _pin_optional_rag_backends_off() -> None:
    """Keep tests deterministic when optional retrieval extras are installed."""
    _rag_optional_mod.HAS_SKLEARN = False
    _rag_optional_mod.SKLEARN_TFIDF_VECTORIZER = None
    _rag_optional_mod.BM25_CLASS = None
    _rag_optional_mod.SENTENCE_TRANSFORMER = None
    _rag_optional_mod.CROSS_ENCODER = None
    _rag_optional_mod._sentence_transformers_available = False
    _rag_chunker_mod._SentenceTransformer = None


@pytest.fixture(autouse=True)
def _isolate_global_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Reset mutable module-level globals between tests."""
    config_dir = tmp_path / "hephaion_config"
    config_file = config_dir / "config.json"
    providers_file = config_dir / "providers.toml"
    auth_dir = tmp_path / "hephaion_auth"
    auth_file = auth_dir / "auth.json"
    _ks._volatile.clear()
    _log_mod._hephaion_logger_initialised = False
    _engine_mod._circuit_breaker.reset()
    _provider_config_mod.invalidate_provider_cache()
    _provider_catalog_mod.invalidate_catalog_cache()
    _oauth_mod._creds_cache.clear()
    _reset_diagnostics_module_objects()
    _pin_optional_rag_backends_off()
    _obs_mod.reset_state()
    _tui_command_access.set_command_registry_fn(_commands_mod.get_registry)
    set_theme("dark")
    monkeypatch.setattr(_settings_mod, "_USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(_settings_mod, "_USER_CONFIG_FILE", config_file)
    monkeypatch.setattr(_provider_config_mod, "_CONFIG_DIR", config_dir)
    monkeypatch.setattr(_provider_config_mod, "_PROVIDERS_FILE", providers_file)
    monkeypatch.setattr(_oauth_mod, "_AUTH_DIR", auth_dir)
    monkeypatch.setattr(_oauth_mod, "_AUTH_FILE", auth_file)
    monkeypatch.setattr(
        _privacy_mod,
        "_INSTALL_ID_PATH",
        config_dir / "install_id.json",
    )
    monkeypatch.setenv("HEPHAION_DISABLE_LIVE_MODELS", "1")
    root = logging.getLogger("hephaion")
    root.handlers.clear()
    root.setLevel(logging.WARNING)

    yield

    _ks._volatile.clear()
    _log_mod._hephaion_logger_initialised = False
    _engine_mod._circuit_breaker.reset()
    _provider_config_mod.invalidate_provider_cache()
    _provider_catalog_mod.invalidate_catalog_cache()
    _oauth_mod._creds_cache.clear()
    _reset_diagnostics_module_objects()
    _pin_optional_rag_backends_off()
    _obs_mod.reset_state()
    _tui_command_access.set_command_registry_fn(_commands_mod.get_registry)
    set_theme("dark")
    root.handlers.clear()
    root.setLevel(logging.WARNING)


@pytest.fixture
def isolated_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Redirect user-config paths to a temp directory."""
    config_dir = tmp_path / "hephaion_config"
    config_file = config_dir / "config.json"
    defaults_file = tmp_path / "default.toml"
    monkeypatch.setattr("parameters.settings._USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr("parameters.settings._USER_CONFIG_FILE", config_file)
    monkeypatch.setattr("parameters.settings._DEFAULTS_FILE", defaults_file)
    return SimpleNamespace(
        config_dir=config_dir, config_file=config_file, defaults_file=defaults_file
    )


@pytest.fixture
def isolated_auth_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Redirect auth paths to a temp directory."""
    auth_dir = tmp_path / "auth_test"
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "auth.json"
    monkeypatch.setattr("ai.providers.oauth._AUTH_DIR", auth_dir)
    monkeypatch.setattr("ai.providers.oauth._AUTH_FILE", auth_file)
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


def message_text(message: ApiMessage) -> str:
    """Extract string content from an API-like message."""
    content = message["content"]
    return content if isinstance(content, str) else ""


def default_tool_handler(**_kw: object) -> str:
    return ""


def make_tool_spec(
    name: str,
    handler: Callable[..., ToolHandlerResult] | None = None,
    description: str = "",
) -> ToolSpec:
    """Create a minimal ToolSpec for tests."""
    return ToolSpec(
        schema={
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        handler=handler if handler is not None else default_tool_handler,
    )


@pytest.fixture
def armory(tmp_path: Path) -> Path:
    """Create a minimal armory with material files."""
    arm = tmp_path / "test-armory"
    (arm / "materials").mkdir(parents=True)
    (arm / ".hephaion").mkdir(parents=True)

    (arm / "materials" / "python.md").write_text(
        "# Python Basics\n\n"
        "Python is a high-level programming language.\n\n"
        "Variables are dynamically typed.\n\n"
        "Functions use the `def` keyword.\n"
    )
    (arm / "materials" / "rust.md").write_text(
        "# Rust Basics\n\n"
        "Rust is a systems programming language.\n\n"
        "Ownership and borrowing are core concepts.\n\n"
        "Cargo is the build tool.\n"
    )
    (arm / "materials" / "algorithms.md").write_text(
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
    (armory_path / "materials").mkdir(exist_ok=True)
    (armory_path / "materials" / "exam.md").write_text(
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
