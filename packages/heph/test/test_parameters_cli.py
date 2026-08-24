from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from ai.runtime import ChatConfig
from harness.parameters import cli as params_cli
from harness.parameters import settings as settings_store
from heph.cli.main import build_parser, run_argv


def test_config_show_uses_registered_handler(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        params_cli,
        "load_config",
        lambda _armory_path=None: ChatConfig(
            base_url="https://example.com/v1",
            model="test-model",
            max_tokens=1234,
            rag_context_budget=4321,
            temperature=0.2,
        ),
    )
    monkeypatch.setattr(
        params_cli,
        "_effective_setting_value",
        lambda key: {
            "theme": "dark",
            "default_armory_path": "(not set)",
            "activity_trace_mode": "tool_calls",
            "thinking_visibility": "off",
            "live_tokens_visible": "false",
            "live_cost_visible": "false",
        }[key],
    )

    run_argv(build_parser(), ["config", "show"])

    out = capsys.readouterr().out
    assert "Current configuration:" in out
    assert "base_url: https://example.com/v1" in out
    assert "model: test-model" in out
    assert "max_tokens: 1234" in out
    assert "rag_context_budget: 4321" in out
    assert "temperature: 0.2" in out
    assert "theme: dark" in out
    assert "thinking_visibility: off" in out
    assert "live_tokens_visible: false" in out
    assert "live_cost_visible: false" in out




def test_config_set_persists_override(
    isolated_config_dir: SimpleNamespace, capsys: pytest.CaptureFixture[str]
) -> None:
    run_argv(build_parser(), ["config", "set", "model", "gpt-test"])

    out = capsys.readouterr().out
    assert "Set model = gpt-test" in out
    saved = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert saved == {"model": "gpt-test"}


def test_load_config_precedence(
    monkeypatch: pytest.MonkeyPatch, isolated_config_dir: SimpleNamespace
) -> None:
    isolated_config_dir.defaults_file.write_text(
        "\n".join(
            [
                'base_url = "https://defaults.example/v1"',
                'model_id = "default-model"',
                "max_tokens = 1000",
                "temperature = 0.4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps(
            {
                "base_url": "https://user.example/v1",
                "model": "user-model",
                "max_tokens": "2000",
                "rag_context_budget": "3000",
                "temperature": "0.3",
                "thinking_visibility": "minimal",
            }
        ),
        encoding="utf-8",
    )

    class _FakeProviderConfig:
        def apply_to_config(self, config: ChatConfig) -> None:
            config.base_url = "https://provider.example/v1"
            config.model = "provider-model"
            config.max_tokens = 1500

    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(lambda _cls: _FakeProviderConfig()),
    )
    monkeypatch.setenv("HARNESS_BASE_URL", "https://env.example/v1")
    monkeypatch.setenv("HARNESS_MODEL", "env-model")
    monkeypatch.setenv("HARNESS_MAX_TOKENS", "4000")
    monkeypatch.setenv("HARNESS_RAG_CONTEXT_BUDGET", "5000")
    monkeypatch.setenv("HARNESS_TEMPERATURE", "0")

    config = params_cli.load_config()

    assert config.base_url == "https://env.example/v1"
    assert config.model == "env-model"
    assert config.max_tokens == 4000
    assert config.rag_context_budget == 5000
    assert config.temperature == 0.0
    assert config.thinking_visibility == "minimal"


def test_load_config_falls_back_to_user_overrides_when_env_is_missing(
    monkeypatch: pytest.MonkeyPatch, isolated_config_dir: SimpleNamespace
) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"model": "user-model", "rag_context_budget": "2500", "temperature": "0.1"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(
            lambda _cls: SimpleNamespace(
                apply_to_config=lambda _config: None,
            )
        ),
    )

    config = params_cli.load_config()

    assert config.model == "user-model"
    assert config.rag_context_budget == 2500
    assert config.temperature == 0.1


def test_parse_toml_simple_handles_comments_and_literals(
    isolated_config_dir: SimpleNamespace,
) -> None:
    isolated_config_dir.defaults_file.write_text(
        "\n".join(
            [
                "# comment",
                'base_url = "https://example.com/v1"',
                "max_tokens = 2048 # trailing comment",
                "enabled = true",
                "temperature = 0.5",
                "[ignored]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert settings_store.parse_toml_simple(isolated_config_dir.defaults_file) == {
        "base_url": "https://example.com/v1",
        "max_tokens": "2048",
        "enabled": "true",
        "temperature": "0.5",
    }


def test_load_user_overrides_returns_empty_for_invalid_json(
    isolated_config_dir: SimpleNamespace,
) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text("{", encoding="utf-8")

    assert params_cli._load_user_overrides() == {}


def test_load_user_overrides_filters_unknown_keys(
    isolated_config_dir: SimpleNamespace,
) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"model": "user-model", "unknown": "value", "max_tokens": 1234}),
        encoding="utf-8",
    )

    assert params_cli._load_user_overrides() == {
        "model": "user-model",
        "max_tokens": "1234",
    }


def test_load_config_warns_when_provider_config_load_fails(
    monkeypatch: pytest.MonkeyPatch,
    isolated_config_dir: SimpleNamespace,
    capsys: pytest.CaptureFixture[str],
) -> None:
    isolated_config_dir.defaults_file.write_text("", encoding="utf-8")

    def _raise(_cls: type) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(_raise),
    )

    config = params_cli.load_config()

    assert isinstance(config, ChatConfig)
    assert "warning: could not load provider config: boom" in capsys.readouterr().err


def test_invalid_integer_overrides_are_ignored(
    monkeypatch: pytest.MonkeyPatch, isolated_config_dir: SimpleNamespace
) -> None:
    isolated_config_dir.defaults_file.write_text(
        "\n".join(['model_id = "default-model"', "max_tokens = 1234"]) + "\n",
        encoding="utf-8",
    )
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"max_tokens": "invalid", "rag_context_budget": "also-invalid"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(
            lambda _cls: SimpleNamespace(
                apply_to_config=lambda _config: None,
            )
        ),
    )
    monkeypatch.setenv("HARNESS_MAX_TOKENS", "not-an-int")
    monkeypatch.setenv("HARNESS_RAG_CONTEXT_BUDGET", "still-not-an-int")

    config = params_cli.load_config()

    assert config.model == "default-model"
    assert config.max_tokens == 1234
    assert config.rag_context_budget == 2000


def test_config_set_unknown_key_exits_with_code_1(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        run_argv(build_parser(), ["config", "set", "unknown", "value"])

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "error: unknown config key 'unknown'." in err
    assert "valid keys:" in err


def test_parse_feature_flags_normalizes() -> None:
    assert settings_store.parse_feature_flags("alpha, Beta , ,GAMMA") == frozenset(
        {"alpha", "beta", "gamma"}
    )


def test_parse_feature_flags_empty_string() -> None:
    assert settings_store.parse_feature_flags("") == frozenset()


def test_config_set_feature_flags_persists(
    isolated_config_dir: SimpleNamespace, capsys: pytest.CaptureFixture[str]
) -> None:
    run_argv(build_parser(), ["config", "set", "feature_flags", "alpha,beta"])

    out = capsys.readouterr().out
    assert "Set feature_flags = alpha,beta" in out
    data = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert data["feature_flags"] == "alpha,beta"


def test_config_set_temperature_persists_float(
    isolated_config_dir: SimpleNamespace, capsys: pytest.CaptureFixture[str]
) -> None:
    run_argv(build_parser(), ["config", "set", "temperature", "0.25"])

    out = capsys.readouterr().out
    assert "Set temperature = 0.25" in out
    data = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert data["temperature"] == 0.25


def test_config_show_displays_feature_flags(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        params_cli,
        "load_config",
        lambda _armory_path=None: ChatConfig(
            base_url="https://example.com/v1",
            model="test-model",
            max_tokens=1234,
            rag_context_budget=4321,
            feature_flags=frozenset({"alpha", "beta"}),
        ),
    )
    monkeypatch.setattr(
        params_cli,
        "_effective_setting_value",
        lambda key: {
            "theme": "dark",
            "default_armory_path": "(not set)",
            "activity_trace_mode": "tool_calls",
            "thinking_visibility": "off",
            "live_tokens_visible": "false",
            "live_cost_visible": "false",
        }[key],
    )

    run_argv(build_parser(), ["config", "show"])

    out = capsys.readouterr().out
    assert "feature_flags: alpha, beta" in out


def test_config_show_displays_no_feature_flags(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        params_cli,
        "load_config",
        lambda _armory_path=None: ChatConfig(
            base_url="https://example.com/v1",
            model="test-model",
            max_tokens=1234,
            rag_context_budget=4321,
        ),
    )
    monkeypatch.setattr(
        params_cli,
        "_effective_setting_value",
        lambda key: {
            "theme": "dark",
            "default_armory_path": "(not set)",
            "activity_trace_mode": "tool_calls",
            "thinking_visibility": "off",
            "live_tokens_visible": "false",
            "live_cost_visible": "false",
        }[key],
    )

    run_argv(build_parser(), ["config", "show"])

    out = capsys.readouterr().out
    assert "feature_flags: (none)" in out


def test_config_set_live_usage_visibility_persists_boolean(
    isolated_config_dir: SimpleNamespace, capsys: pytest.CaptureFixture[str]
) -> None:
    run_argv(build_parser(), ["config", "set", "live_tokens_visible", "true"])

    out = capsys.readouterr().out
    assert "Set live_tokens_visible = true" in out
    saved = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert saved["live_tokens_visible"] is True


def test_config_set_thinking_visibility_persists_string(
    isolated_config_dir: SimpleNamespace, capsys: pytest.CaptureFixture[str]
) -> None:
    run_argv(build_parser(), ["config", "set", "thinking_visibility", "minimal"])

    out = capsys.readouterr().out
    assert "Set thinking_visibility = minimal" in out
    saved = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert saved["thinking_visibility"] == "minimal"


def test_config_path_prints_persistent_config_file(
    isolated_config_dir: SimpleNamespace, capsys: pytest.CaptureFixture[str]
) -> None:
    run_argv(build_parser(), ["config", "path"])

    out = capsys.readouterr().out.strip()
    assert out == str(isolated_config_dir.config_file)


def test_config_list_includes_persistent_preferences(
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_argv(build_parser(), ["config", "list"])

    out = capsys.readouterr().out
    assert "theme: TUI theme preset" in out
    assert "thinking_visibility: Model thinking visibility: off, minimal, or all" in out
    assert "live_tokens_visible: Show token estimates in the TUI status bar" in out


def test_config_unset_removes_persisted_setting(
    isolated_config_dir: SimpleNamespace, capsys: pytest.CaptureFixture[str]
) -> None:
    run_argv(build_parser(), ["config", "set", "theme", "light"])
    run_argv(build_parser(), ["config", "unset", "theme"])

    out = capsys.readouterr().out
    assert "Unset theme" in out
    saved = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert "theme" not in saved


def test_load_config_feature_flags_env_overrides_user(
    monkeypatch: pytest.MonkeyPatch, isolated_config_dir: SimpleNamespace
) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"feature_flags": "user_flag"}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(
            lambda _cls: SimpleNamespace(
                apply_to_config=lambda _config: None,
            )
        ),
    )
    monkeypatch.setenv("HARNESS_FEATURE_FLAGS", "env_flag")

    config = params_cli.load_config()

    assert config.feature_flags == frozenset({"env_flag"})


def test_load_config_feature_flags_from_user_overrides(
    isolated_config_dir: SimpleNamespace,
) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"feature_flags": "alpha,beta"}), encoding="utf-8"
    )

    config = params_cli.load_config()

    assert config.feature_flags == frozenset({"alpha", "beta"})


def test_load_config_falls_back_when_active_provider_has_no_key(
    monkeypatch: pytest.MonkeyPatch,
    isolated_config_dir: SimpleNamespace,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When active provider needs a key but none is configured, fall back to Pollinations."""
    isolated_config_dir.defaults_file.write_text("", encoding="utf-8")

    class _FakeProviderConfig:
        def apply_to_config(self, config: ChatConfig) -> None:
            config.base_url = "https://openrouter.ai/api/v1"
            config.model = "qwen/test"
            config.apply_provider_reference("openrouter", "OPENROUTER_API_KEY")

    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(lambda _cls: _FakeProviderConfig()),
    )
    # Ensure no key is resolved for openrouter.
    monkeypatch.setattr(
        "ai.runtime.engine.resolve_key",
        lambda _slug, _env="": "",
    )

    config = params_cli.load_config()

    assert config.base_url == "https://text.pollinations.ai/openai"
    assert config.model == "openai"
    assert config._provider_slug == "pollinations"
    err = capsys.readouterr().err
    assert "falling back to Pollinations AI" in err


def test_load_config_no_fallback_when_keyless(
    monkeypatch: pytest.MonkeyPatch,
    isolated_config_dir: SimpleNamespace,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When active provider is keyless (Pollinations), no fallback should occur."""
    isolated_config_dir.defaults_file.write_text("", encoding="utf-8")

    class _FakeProviderConfig:
        def apply_to_config(self, config: ChatConfig) -> None:
            config.base_url = "https://text.pollinations.ai/openai"
            config.model = "openai"
            config.apply_provider_reference("pollinations", "")

    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(lambda _cls: _FakeProviderConfig()),
    )

    config = params_cli.load_config()

    assert config.base_url == "https://text.pollinations.ai/openai"
    assert config._provider_slug == "pollinations"
    err = capsys.readouterr().err
    assert "falling back" not in err


def test_load_config_no_fallback_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
    isolated_config_dir: SimpleNamespace,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When active provider has an API key, no fallback should occur."""
    isolated_config_dir.defaults_file.write_text("", encoding="utf-8")

    class _FakeProviderConfig:
        def apply_to_config(self, config: ChatConfig) -> None:
            config.base_url = "https://api.openai.com/v1"
            config.model = "gpt-test"
            config.apply_provider_reference("openai", "OPENAI_API_KEY")

    monkeypatch.setattr(
        "ai.providers.config.ProviderConfig.load",
        classmethod(lambda _cls: _FakeProviderConfig()),
    )
    monkeypatch.setattr(
        "ai.runtime.engine.resolve_key",
        lambda _slug, _env="": "sk-test-key",
    )

    config = params_cli.load_config()

    assert config.base_url == "https://api.openai.com/v1"
    assert config._provider_slug == "openai"
    err = capsys.readouterr().err
    assert "falling back" not in err
