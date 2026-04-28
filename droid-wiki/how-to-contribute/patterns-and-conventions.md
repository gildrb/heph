# Patterns and conventions

## Coding style

- Python 3.13+, `from __future__ import annotations` in every module
- Line length: 99 characters, double quotes, LF line endings
- Naming: PascalCase classes, snake_case functions/variables, UPPER_SNAKE_CASE constants
- Type checking: basedpyright strict mode
- `Explicit Any` is forbidden; use concrete types, `TypedDict`, dataclasses, or protocols
- Standard top-level imports only; deferred imports are reserved for module-scope optional extras and armory plugin loading

## Import boundaries

Import-linter enforces that only `app` may import other packages. All other packages must not import `app`. The contracts are defined in `pyproject.toml` under `[tool.importlinter]`:

- `hephaistos.logging` must not import `hephaistos.app`
- All non-app packages (chat, harness, providers, armory, study, memory, parameters, source, logging, palette, observability) must not import `hephaistos.app`
- `hephaistos.app.commands` must not import `hephaistos.app.shell`
- `hephaistos.chat.session` and `hephaistos.chat.orchestrator` must remain independent (no runtime imports)

## Error handling

- Custom exceptions inherit from a base (e.g., `EngineError`, `SessionError`, `ArmoryError`)
- User-facing errors use descriptive messages; long messages are fine for CLI output
- Streaming errors use `StreamRecoveryError` carrying the partial response
- Network errors are caught and surfaced as user-friendly messages via `is_network_error()` / `offline_message()`

## Logging

- Use `hephaistos.logging.get_logger(name)` for structured logging
- All log output passes through secret redaction (API keys, Bearer tokens)
- Log levels: `DEBUG` for verbose diagnostics, `INFO` for notable events (LLM request, tool call, index build)
- Environment variables: `HEPHAISTOS_LOG_LEVEL`, `HEPHAISTOS_LOG_FILE`, `HEPHAISTOS_LOG_FORMAT`

## Observability and telemetry

- PostHog for anonymous, opt-in usage analytics
- Sentry for redacted, opt-in crash reporting
- The public repo ships a safe stub in `hephaistos/_telemetry_release.py`; official release builds inject telemetry values during CI
- Source, editable, and Git installs stay bare by default

## Configuration pattern

- Cross-session settings: `hephaistos/parameters/settings.py` reads/writes `~/.config/hephaistos/config.json`
- Defaults defined in `hephaistos/parameters/default.toml`
- Provider config: `~/.config/hephaistos/providers.toml`, parsed by `hephaistos/providers/config.py`
- Armory-specific: `.hephaistos/armory.toml` (marker), `.hephaistos/system_prompt.md` (custom study prompt)
- API keys are never written to config files; resolved at runtime from OS keychain → environment variable → in-memory store

## Testing patterns

- pytest with `--cov-fail-under=75` coverage gate
- `@pytest.mark.flaky(reruns=2)` for flaky tests
- `tests/conftest.py` provides shared fixtures
- Test files follow `test_<module>.py` naming
- Integration tests in `tests/integration/`
- Tests use `monkeypatch`, `tmp_path`, and fixture-based mocking

## Pre-commit hooks

Defined in `.pre-commit-config.yaml`: ruff, ruff-format, basedpyright, check-repo-policies, check-large-files, vulture, pylint, lint-imports.

## Deferred imports

Heavy imports (Textual, openai, sentence_transformers, chat modules) are loaded lazily via `importlib.import_module()` to keep CLI startup fast. This pattern is used in:

- `hephaistos/app/cli.py` — defers shell/TUI/chat imports
- `hephaistos/app/shell.py` — defers chat session creation
- `hephaistos/source/cli.py` — defers RAG index module
