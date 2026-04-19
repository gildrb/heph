from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from hephaistos.app.cli import build_parser, run_argv
from hephaistos.chat.engine import ChatConfig
from hephaistos.parameters import cli as params_cli


def test_config_show_uses_registered_handler(monkeypatch, capsys) -> None:
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

    run_argv(build_parser(), ["config", "show"])

    out = capsys.readouterr().out
    assert "Current configuration:" in out
    assert "base_url: https://example.com/v1" in out
    assert "model: test-model" in out
    assert "max_tokens: 1234" in out
    assert "rag_context_budget: 4321" in out


def test_config_set_persists_override(isolated_config_dir, capsys) -> None:
    run_argv(build_parser(), ["config", "set", "model", "gpt-test"])

    out = capsys.readouterr().out
    assert "Set model = gpt-test" in out
    saved = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert saved == {"model": "gpt-test"}


def test_load_config_precedence(monkeypatch, isolated_config_dir) -> None:
    isolated_config_dir.defaults_file.write_text(
        "\n".join(
            [
                'base_url = "https://defaults.example/v1"',
                'model_id = "default-model"',
                "max_tokens = 1000",
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
        "hephaistos.providers.config.ProviderConfig.load",
        classmethod(lambda cls: _FakeProviderConfig()),
    )
    monkeypatch.setenv("HEPHAISTOS_BASE_URL", "https://env.example/v1")
    monkeypatch.setenv("HEPHAISTOS_MODEL", "env-model")
    monkeypatch.setenv("HEPHAISTOS_MAX_TOKENS", "4000")
    monkeypatch.setenv("HEPHAISTOS_RAG_CONTEXT_BUDGET", "5000")

    config = params_cli.load_config()

    assert config.base_url == "https://env.example/v1"
    assert config.model == "env-model"
    assert config.max_tokens == 4000
    assert config.rag_context_budget == 5000


def test_load_config_falls_back_to_user_overrides_when_env_is_missing(
    monkeypatch, isolated_config_dir
) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"model": "user-model", "rag_context_budget": "2500"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "hephaistos.providers.config.ProviderConfig.load",
        classmethod(lambda cls: SimpleNamespace(apply_to_config=lambda _config: None)),
    )

    config = params_cli.load_config()

    assert config.model == "user-model"
    assert config.rag_context_budget == 2500


def test_parse_toml_simple_handles_comments_and_literals(isolated_config_dir) -> None:
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

    assert params_cli._parse_toml_simple(isolated_config_dir.defaults_file) == {
        "base_url": "https://example.com/v1",
        "max_tokens": "2048",
        "enabled": "true",
        "temperature": "0.5",
    }


def test_load_user_overrides_returns_empty_for_invalid_json(isolated_config_dir) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text("{", encoding="utf-8")

    assert params_cli._load_user_overrides() == {}


def test_load_user_overrides_filters_unknown_keys(isolated_config_dir) -> None:
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
    monkeypatch, isolated_config_dir, capsys
) -> None:
    isolated_config_dir.defaults_file.write_text("", encoding="utf-8")

    def _raise(cls) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr("hephaistos.providers.config.ProviderConfig.load", classmethod(_raise))

    config = params_cli.load_config()

    assert isinstance(config, ChatConfig)
    assert "warning: could not load provider config: boom" in capsys.readouterr().err


def test_invalid_integer_overrides_are_ignored(monkeypatch, isolated_config_dir) -> None:
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
        "hephaistos.providers.config.ProviderConfig.load",
        classmethod(lambda cls: SimpleNamespace(apply_to_config=lambda _config: None)),
    )
    monkeypatch.setenv("HEPHAISTOS_MAX_TOKENS", "not-an-int")
    monkeypatch.setenv("HEPHAISTOS_RAG_CONTEXT_BUDGET", "still-not-an-int")

    config = params_cli.load_config()

    assert config.model == "default-model"
    assert config.max_tokens == 1234
    assert config.rag_context_budget == 2000


def test_config_set_unknown_key_exits_with_code_1(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        run_argv(build_parser(), ["config", "set", "unknown", "value"])

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "error: unknown config key 'unknown'." in err
    assert "valid keys:" in err


def test_parse_feature_flags_normalizes() -> None:
    assert params_cli._parse_feature_flags("alpha, Beta , ,GAMMA") == frozenset(
        {"alpha", "beta", "gamma"}
    )


def test_parse_feature_flags_empty_string() -> None:
    assert params_cli._parse_feature_flags("") == frozenset()


def test_config_set_feature_flags_persists(isolated_config_dir, capsys) -> None:
    run_argv(build_parser(), ["config", "set", "feature_flags", "alpha,beta"])

    out = capsys.readouterr().out
    assert "Set feature_flags = alpha,beta" in out
    data = json.loads(isolated_config_dir.config_file.read_text(encoding="utf-8"))
    assert data["feature_flags"] == "alpha,beta"


def test_config_show_displays_feature_flags(monkeypatch, capsys) -> None:
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

    run_argv(build_parser(), ["config", "show"])

    out = capsys.readouterr().out
    assert "feature_flags: alpha, beta" in out


def test_config_show_displays_no_feature_flags(monkeypatch, capsys) -> None:
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

    run_argv(build_parser(), ["config", "show"])

    out = capsys.readouterr().out
    assert "feature_flags: (none)" in out


def test_load_config_feature_flags_env_overrides_user(monkeypatch, isolated_config_dir) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"feature_flags": "user_flag"}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "hephaistos.providers.config.ProviderConfig.load",
        classmethod(lambda cls: SimpleNamespace(apply_to_config=lambda _config: None)),
    )
    monkeypatch.setenv("HEPHAISTOS_FEATURE_FLAGS", "env_flag")

    config = params_cli.load_config()

    assert config.feature_flags == frozenset({"env_flag"})


def test_load_config_feature_flags_from_user_overrides(isolated_config_dir) -> None:
    isolated_config_dir.config_dir.mkdir(parents=True, exist_ok=True)
    isolated_config_dir.config_file.write_text(
        json.dumps({"feature_flags": "alpha,beta"}), encoding="utf-8"
    )

    config = params_cli.load_config()

    assert config.feature_flags == frozenset({"alpha", "beta"})
