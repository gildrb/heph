# Development workflow

## Set up

```bash
git clone https://github.com/gildrb/hephaistos.git
cd hephaistos
uv sync --frozen          # install runtime dependencies
uv sync --group dev       # install lint, type-check, test tools
```

See [../overview/getting-started.md](../overview/getting-started.md) for first-time setup details.

## Branch

Create a feature branch from `main`:

```bash
git checkout main
git pull
git checkout -b feat/my-feature
```

Branch naming conventions:

- `feat/` — new features
- `fix/` — bug fixes
- `refactor/` — code reorganization
- `docs/` — documentation changes
- `chore/` — maintenance tasks

## Code

Follow the conventions in [patterns-and-conventions.md](patterns-and-conventions.md). Key points:

- 99-char line limit, double quotes, LF endings
- No `Any` types — use concrete types, `TypedDict`, or protocols
- Standard top-level imports only (no deferred imports except for optional extras)
- Respect import boundaries — only `app` may import from other packages

## Test

Write tests for every change. The project requires ≥75% coverage:

```bash
uv run pytest                              # run all tests
uv run pytest tests/test_chat_engine.py    # single file
uv run pytest -k "test_stream_recovery"    # by keyword
```

See [testing.md](testing.md) for the full testing guide.

## Local checks

Before pushing, run the same checks CI runs:

```bash
uv run ruff check .                        # lint
uv run ruff format --check .               # format check
uv run basedpyright                        # type check
uv run pytest --cov --cov-fail-under=75    # tests with coverage
uv run python -m scripts.check_repo_policies  # no Any / no deferred imports
uv run vulture hephaistos tests vulture-whitelist.py  # dead code
uv run lint-imports                        # import boundaries
```

Or install pre-commit hooks to run them automatically:

```bash
uv run pre-commit install
```

## Push and PR

```bash
git push -u origin feat/my-feature
```

Open a pull request against `main`. Fill in the PR template (see [index.md](index.md)).

## CI

CI runs on every push to `main` and every PR via `.github/workflows/ci.yml`. It includes these jobs:

| Job | What it checks |
|-----|----------------|
| lint | ruff check + repo policies + ruff format |
| typecheck | basedpyright strict |
| test | pytest with coverage gate (75%) |
| security | bandit scan |
| dead-code | vulture |
| duplicate-code | pylint duplicate-code |
| architecture | import-linter |
| unused-deps | deptry |
| complexity | radon |
| build | `uv build` (sdist + wheel) |
| feature-flags | check_feature_flags.py |
| docs-sync | sync_docs.py --check |
| tech-debt | check_tech_debt.py |
| agents-md-validation | validate_agents_md.py |

CI also posts security scan findings as PR comments and detects agent co-authorship.

See [tooling.md](tooling.md) for details on each tool.

## Merge

After CI is green and review is approved, merge via GitHub's "Squash and merge" or "Merge commit". The project doesn't enforce a specific merge strategy.

## Deploy

- **Edge deploys** are published manually via `.github/workflows/deploy.yml`.
- **Releases** are automated via `.github/workflows/release.yml` on `v*` tags.

```bash
git tag v0.2.0
git push origin v0.2.0
```

The release workflow builds, signs, and publishes to PyPI.
