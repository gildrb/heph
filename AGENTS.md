# Agent Instructions — Hephaistos

## 1) Project overview

Hephaistos is an armory-first study CLI built in Python (3.13+). It provides an interactive terminal shell (`hephaistos` / `heph`) backed by LLM providers, with RAG support, session management, and structured study workflows.

- **Entry point**: `hephaistos.app.cli:main`
- **Build system**: `uv` with `uv_build` backend
- **Package manager**: `uv` (use `uv run` for all commands, never bare `python`/`pytest`)

## 2) Engineering Principles (Normative)

These principles are mandatory — they are implementation constraints, not suggestions.

### 2.1 KISS (Keep It Simple, Stupid)
- Prefer straightforward control flow over meta-programming.
- Prefer explicit branches and typed structs over hidden dynamic behavior.
- Keep error paths obvious and localized.

### 2.2 YAGNI (You Aren't Gonna Need It)
- Do not add config features, CLI arguments, or other features without a concrete caller/use.
- Do not introduce speculative abstractions.
- Keep unsupported paths explicit (raise or return clear error) rather than silent no-ops.

### 2.3 DRY + Rule of Three
- Duplicate small local logic when it preserves clarity.
- Extract shared helpers only after repeated, stable patterns (rule-of-three).
- When extracting, preserve module boundaries and avoid hidden coupling.

### 2.4 Fail fast + Explicit errors
- Prefer explicit errors for unsupported or unsafe states.
- Never silently broaden permissions or capabilities.

## 3) Agent Workflow (Required)

1. **Read before write** — inspect existing implementation before editing.
2. **Define scope boundary** — one concern per change; avoid mixed feature + refactor + infra patches.
3. **Implement minimal patch** — apply KISS/YAGNI/DRY rule-of-three explicitly.
4. **Test** — Write tests for new features or changes.
5. **Incremental** — Keep the program working at each step.

## 4) Code style and conventions

- **Formatter/linter**: `ruff` (config in `pyproject.toml`), line length 99.
- **Type checker**: `basedpyright` in strict mode (`typeCheckingMode = "strict"`).
- **Target Python**: 3.13+.
- **Required header**: `from __future__ import annotations` at the top of every module.
- **Quote style**: double quotes, spaces for indentation, LF line endings.

### Naming (enforced by ruff N rules)
- Classes: PascalCase (`ChatConfig`, `EngineError`)
- Functions/methods/variables: snake_case (`build_parser()`, `api_key`)
- Constants: UPPER_SNAKE_CASE (`_VERSION`, `_RETRYABLE_TYPES`)
- Private: underscore prefix (`_tools`, `_registry`)

### Commit messages
Short, imperative mood: `Add --version flag to CLI`, `Fix citation verification for empty sources`.

## 5) Architecture and import rules

The codebase has strict import boundaries enforced by `import-linter`:

```
hephaistos/
  app/          # CLI shell, commands, workspace, display — the top layer
  chat/         # Engine, orchestrator, session, storage — no app imports
  harness/      # Prompt building, persona, citation — no app imports
  providers/    # LLM provider registry, config, auth — no app imports
  armory/       # Armory data and commands — no app imports
  study/        # Study controller — no app imports
  memory/       # Memory extraction and storage — no app imports
  parameters/   # Parameter management CLI — no app imports
  source/       # Source management — no app imports
  logging.py    # Shared logging — must NOT import app
  palette.py    # ANSI color primitives — must NOT import app
```

**Key constraints**:
- Only `app` may import from other packages. All other packages are forbidden from importing `app`.
- `app.commands` must not import `app.shell`.
- `chat.session` and `chat.orchestrator` are independent at runtime.

## 6) Development commands

```bash
# Install
uv sync --group dev          # core dev deps
uv sync --group rag          # optional RAG extras

# Lint and format
uv run ruff check .
uv run ruff format --check .

# Type check
uv run basedpyright

# Test
uv run pytest                # full suite (coverage >= 75%)
uv run pytest tests/test_foo.py  # single file

# Dead code
uv run vulture hephaistos tests vulture-whitelist.py

# Import architecture
uv run lint-imports

# All checks (pre-commit runs these)
uv run ruff check . && uv run ruff format --check . && uv run basedpyright && uv run pytest
```

## 7) Test conventions

- Framework: `pytest` with `pytest-cov`.
- Coverage threshold: 75% (enforced via `--cov-fail-under=75`).
- Test files: `tests/test_<module>.py`.
- Shared fixtures: `tests/conftest.py`.
- Aim to cover new code with tests; do not lower the coverage threshold.

## 8) Things to avoid

- Do not use bare `python` or `pytest`; always use `uv run`.
- Do not add dependencies without checking `pyproject.toml` first.
- Do not bypass import-linter contracts — they encode real architectural boundaries.
- Do not remove or weaken ruff rules to silence warnings; fix the code instead.
- Do not commit `.env` files or secrets.
