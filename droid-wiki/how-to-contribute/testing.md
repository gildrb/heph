# Testing

## Test framework and configuration

Tests use pytest with a coverage gate at 75% (actual coverage is ~77%). Configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
addopts = "--tb=short -q --durations=10 --strict-markers --cov=hephaistos --cov-report=term-missing --cov-fail-under=75"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
```

## Running tests

```bash
uv run pytest                              # all tests
uv run pytest --cov --cov-fail-under=75    # with coverage gate
uv run pytest tests/test_chat_engine.py    # single file
uv run pytest -k "test_stream_recovery"    # by keyword
uv run pytest -m flaky                     # flaky-marked tests only
uv run pytest tests/test_app_tui.py -x     # stop on first failure
```

## Test file organization

All tests live in `tests/`. Files follow `test_<module>.py` naming. Integration tests are in `tests/integration/`.

The largest test files:

| File | Lines | What it tests |
|------|-------|---------------|
| `tests/test_app_tui.py` | 1,409 | TUI widget rendering, events, keybindings |
| `tests/test_app_shell.py` | 1,001 | prompt-toolkit shell, command dispatch |
| `tests/test_rag_retrieve.py` | 1,132 | RAG retrieval, ranking, filtering |
| `tests/test_rag_chunker.py` | 485 | document chunking |
| `tests/test_harness.py` | 479 | agent loop, tool dispatch |

## Shared fixtures

`tests/conftest.py` (282 lines) provides fixtures used across all tests:

- **`_isolate_global_state`** (autouse) — resets module-level globals, caches, logging, and diagnostics between every test. Redirects config paths to `tmp_path`. This is the most important fixture — it ensures tests don't leak state into each other.
- **`isolated_config_dir`** — redirects `~/.config/hephaistos/` to a temp directory.
- **`isolated_auth_dir`** — redirects auth paths to a temp directory.
- **`workspace`** — creates a temp workspace with sample `.py` and `.md` files.
- **`armory`** — creates a minimal armory with `source/`, `library/`, and `.hephaistos/` directories plus sample markdown files.
- **`chat_session`** — creates a `ChatSession` attached to a valid armory.
- **`providers_toml`** — creates a minimal `providers.toml` with Z.AI and OpenRouter entries.

The autouse fixture also:
- Clears the volatile keyring store
- Resets the circuit breaker
- Invalidates settings and provider caches
- Replaces diagnostics objects with no-ops
- Resets the theme to "forge"
- Clears and resets logging handlers

## Flaky tests

Mark unreliable tests with the `flaky` marker:

```python
@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_network_call():
    ...
```

The marker is configured in `pyproject.toml` and causes pytest to rerun the test up to 2 times with a 1-second delay between attempts. The project uses `pytest-rerunfailures` for this.

## Mocking

The project uses standard library tools for mocking — no external mock library beyond `unittest.mock`:

- **`monkeypatch`** — preferred for patching environment variables, module attributes, and config paths. Used heavily in `conftest.py`.
- **`tmp_path`** — pytest's built-in fixture for temporary directories. Used for armory isolation, config file tests, and file operations.
- **`unittest.mock.patch`** — used when monkeypatch isn't enough (mocking context managers, async code, or complex objects).
- **Fixture-based** — shared mock objects are defined as fixtures in `conftest.py` rather than inline patches.

Common patterns:

```python
# Redirect config to temp dir
def test_something(self, isolated_config_dir):
    ...

# Create a temp armory
def test_armory(self, armory):
    ...

# Patch an environment variable
def test_api_key(self, monkeypatch):
    monkeypatch.setenv("HEPHAISTOS_API_KEY", "test-key")
```

## Coverage

Coverage is measured on `hephaistos/` only (not tests). The threshold is 75% in CI, but actual coverage runs around 77%. Coverage reports show missing lines per file:

```bash
uv run pytest --cov --cov-report=term-missing
```

## Writing new tests

When adding a new module, create a corresponding `tests/test_<module>.py`. Follow these conventions:

- One test class per logical group: `TestChatEngine`, `TestRAGRetrieve`, etc.
- Use `conftest.py` fixtures for isolation — don't create real config files or armories on disk.
- Mark network-dependent tests with `@pytest.mark.flaky`.
- Keep tests focused — one assertion per test when practical.
- Use descriptive test names: `test_session_exits_on_ctrl_d`, not `test_exit`.
