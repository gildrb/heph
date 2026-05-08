<coding_guidelines>
# Hephaistos — Agent Guide

## Setup
```bash
uv sync --frozen           # install all dependencies
uv sync --group dev        # install dev tools (lint, type-check, test)
uv sync --group docs       # install doc-building tools
```

## Run
```bash
uv run heph                # launch interactive shell
uv run heph chat           # start a chat session
uv run heph armory init PATH    # create a new armory
```

## Docs Sync
<!-- sync-docs:privacy-diagnostics-docs-contract:start -->
- Privacy and diagnostics rule: PostHog is anonymous opt-in maintainer visibility only; Sentry
  is redacted opt-in crash reporting only.
- Preserve the public safe-stub split in `hephaistos/privacy/release.py`.
  Official release builds inject privacy and diagnostics backend values in CI; source, editable, and
  Git installs must stay bare by default.
- When CLI commands, privacy or diagnostics surfaces, or README-adjacent docs change, run
  `uv run python -m scripts.sync_docs` and keep `README.md`, `docs/index.md`,
  `docs/cli-reference.md`, `AGENTS.md`, and the architecture privacy and diagnostics section
  aligned.
<!-- sync-docs:privacy-diagnostics-docs-contract:end -->

## Lint & Format
```bash
uv run ruff check .        # lint
uv run ruff check --fix .  # lint with auto-fix
uv run ruff format .       # format
uv run ruff format --check .  # format check (CI mode)
uv run python -m scripts.check_repo_policies  # no Any / unapproved deferred imports
```

## Type Check
```bash
uv run ty check  # type-check the project
```

## Dead Code / Architecture / Duplicates
```bash
uv run vulture hephaistos tests vulture-whitelist.py  # dead-code detection
uv run pylint --persistent=no --score=no --disable=all --enable=duplicate-code hephaistos  # duplicate code
uv run lint-imports        # verify import boundaries
```

## Test
```bash
uv run pytest                              # run all tests
uv run pytest --cov --cov-fail-under=75    # run with coverage gate
uv run pytest tests/test_chat_engine.py    # single file
uv run pytest -k "test_stream_recovery"    # by keyword
uv run pytest -m flaky                     # flaky-marked tests only
```

## Build & Release
```bash
uv build                   # build sdist + wheel
```
Releases are automated via `.github/workflows/release.yml` on `v*` tags.
Edge deploys are published manually via `.github/workflows/deploy.yml`.

## Runbooks

Operational playbooks for incident response:

- `docs/runbooks/ci-failure.md` — CI failure triage
- `docs/runbooks/slow-llm-response.md` — Debug slow LLM responses
- `docs/runbooks/deployment-rollback.md` — Revert bad releases
- `docs/runbooks/rag-retrieval-issues.md` — Debug RAG quality

## Diagnostics

- Structured logging: `HEPHAISTOS_LOG_LEVEL`, `HEPHAISTOS_LOG_FILE`, `HEPHAISTOS_LOG_FORMAT`
- Session traces: per-armory JSONL files under `.hephaistos/traces/`
- Profiling: `--profile` (CPU) or `--profile-memory` (memory) CLI flags

## Project Conventions
- Python ≥3.13, `from __future__ import annotations` in every module
- Line length: 99 chars, double quotes, LF line endings
- Naming: PascalCase classes, snake_case functions/variables, UPPER_SNAKE_CASE constants (enforced by ruff N rules)
- Type checking: ty strict mode
- Explicit `Any` is forbidden; use concrete SDK types, `TypedDict`, dataclasses, or protocols instead
- Standard top-level imports by default; deferred imports require a policy allowlist for optional extras, plugin loading, or measured startup-critical paths
- Import boundaries: only `app` may import other packages; all other packages are forbidden from importing `app` (enforced by import-linter)
- Tests: pytest with `--cov-fail-under=75`, `@pytest.mark.flaky(reruns=2)` for flaky tests
- Pre-commit: ruff, ruff-format, ty, check-repo-policies, check-large-files, vulture, pylint, lint-imports
</coding_guidelines>
