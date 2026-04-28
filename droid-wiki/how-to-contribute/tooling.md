# Tooling

## Package manager

The project uses [uv](https://docs.astral.sh/uv/) as its package manager and build tool. Configuration is in `pyproject.toml` with the `uv_build` backend.

```bash
uv sync --frozen       # install runtime deps (reproducible lockfile)
uv sync --group dev    # install dev tools (lint, type-check, test)
uv sync --group docs   # install doc-building tools
```

## Linting

[ruff](https://docs.astral.sh/ruff/) handles both linting and formatting. The configuration is in `pyproject.toml` under `[tool.ruff]`.

Enabled rule sets: E, W, F, I, UP, B, SIM, RUF, A, C4, DTZ, EM, EXE, ISC, ICN, LOG, G, PIE, PYI, PT, Q, R, RET, SLOT, T10, TCH, INT, ARG, PTH, TD, FIX, ERA, PGH, PL, TRY, FURB, PERF, N.

Key ignored rules:
- `PLR0913` (too many arguments) — fine for config/data classes
- `PLR2004` (magic numbers) — tests are full of them
- `TC001`/`TC002`/`TC003` (type-checking block imports) — we use top-level imports with `from __future__ import annotations`
- `ERA001` (commented-out code) — too aggressive in tests

```bash
uv run ruff check .           # lint
uv run ruff check --fix .     # lint with auto-fix
uv run ruff format .          # format
uv run ruff format --check .  # format check (CI mode)
```

## Type checking

[basedpyright](https://github.com/DetachHead/basedpyright) in strict mode. Configuration in `pyproject.toml` under `[tool.basedpyright]`:

```toml
typeCheckingMode = "strict"
pythonVersion = "3.13"
```

```bash
uv run basedpyright
```

## Dead code detection

[vulture](https://github.com/jendrikseipp/vulture) detects unused code. A whitelist file at `vulture-whitelist.py` marks known false positives.

```bash
uv run vulture hephaistos tests vulture-whitelist.py
```

## Import boundaries

[import-linter](https://import-linter.readthedocs.io/) enforces package architecture. Contracts are defined in `pyproject.toml` under `[tool.importlinter]`:

- `logging` must not import `app`
- Non-app packages must not import `app`
- `app.commands` must not import `app.shell`
- `chat.session` and `chat.orchestrator` are independent

```bash
uv run lint-imports
```

## Duplicate code

[pylint](https://pylint.readthedocs.io/) runs only the duplicate-code checker:

```bash
uv run pylint --persistent=no --score=no --disable=all --enable=duplicate-code hephaistos
```

## Security

[bandit](https://bandit.readthedocs.io/) scans for common security issues. Configuration in `pyproject.toml` under `[tool.bandit]`:

```bash
uv run bandit -r hephaistos -c pyproject.toml
```

## Dependency checking

[deptry](https://deptry.readthedocs.io/) finds unused, missing, and transitive dependencies:

```bash
uv run deptry hephaistos
```

Per-rule ignores handle optional RAG deps (`sentence-transformers`, `scikit-learn`, `docling`) that are imported conditionally.

## Complexity

[radon](https://radon.readthedocs.io/) measures cyclomatic complexity:

```bash
uv run radon cc hephaistos -a -nc --total-average
```

## Pre-commit hooks

Defined in `.pre-commit-config.yaml`. Runs on every commit:

1. ruff check
2. ruff-format
3. basedpyright
4. check-repo-policies
5. check-large-files
6. vulture
7. pylint
8. lint-imports

```bash
uv run pre-commit install    # install hooks
uv run pre-commit run --all  # run all checks manually
```

## CI workflows

All workflows are in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | push to `main`, PRs to `main` | Full check suite: lint, typecheck, test, security, dead-code, duplicates, architecture, unused-deps, complexity, build, feature-flags, docs-sync, tech-debt, agents-md-validation, metrics |
| `deploy.yml` | manual | Publish edge builds |
| `release.yml` | `v*` tags | Build and publish release to PyPI |
| `docs.yml` | push to `main` | Build and deploy docs |
| `qa.yml` | PRs | Run QA tests |
| `pr-review.yml` | PRs | Automated code review |
| `auto-approve.yml` | PRs | Auto-approve specific PR types |
| `ci-failure-issue.yml` | CI failure on `main` | Auto-create issue for CI failures |

## Scripts

Utility scripts in `scripts/`:

| Script | Purpose |
|--------|---------|
| `sync_docs.py` | Keep README, docs, AGENTS.md in sync |
| `check_repo_policies.py` | Enforce no `Any`, no deferred imports |
| `check_feature_flags.py` | Validate feature flag usage |
| `check_tech_debt.py` | Check TODO/FIXME have issue links |
| `detect_co_author.py` | Detect AI agent co-authorship in PRs |
| `record_metrics.py` | Record build and test metrics |
| `sync_labels.py` | Sync GitHub labels from `.github/labels.yml` |
| `validate_agents_md.py` | Validate commands in AGENTS.md |

## Repo policy checks

`scripts/check_repo_policies.py` enforces two rules:

1. **No explicit `Any`** — use concrete types, `TypedDict`, dataclasses, or protocols.
2. **No deferred imports** — except for module-scope optional extras and armory plugin loading.

```bash
uv run python -m scripts.check_repo_policies
```
