# Contributing

Thanks for helping improve Heph.

## Setup

```bash
git clone https://github.com/gildrb/heph
cd heph
uv sync --frozen --group dev
```

Run the app from source:

```bash
uv run heph
```

## Checks

Run the narrowest useful tests for your change, then the relevant gates:

```bash
uv run pytest -s --no-cov
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run python -m scripts.check_repo_policies
uv lock --check
uv run python -m scripts.check_dependency_pinning
uv run python -m scripts.check_dependency_sdist_allowlist
uv audit --frozen
```

When README, CLI, privacy, diagnostics, or docs-adjacent behavior changes:

```bash
uv run python -m scripts.sync_docs
```

## Guidelines

- Treat dependency changes as reviewed code changes; set `HEPH_ALLOW_LOCKFILE_CHANGE=1` only after reviewing `pyproject.toml`, `uv.lock`, and the source-only sdist allowlist.
- Keep armories portable normal directories.
- Keep answers grounded in user materials with verifiable citations.
- Keep memory scoped to the armory unless the user explicitly opts into a shared service.
- Keep providers and models swappable.
- Prefer deleting duplication and simplifying control flow over adding new abstractions.
- Add focused tests for behavior that could break.
- Update user-facing docs in `docs/` when changing commands, armory behavior, retrieval, citation checks, memory, provider setup, privacy, or diagnostics. See `docs/getting-started.md` and related user guides.
- Update developer docs in `docs/developers/` when changing internal architecture, agent conventions, or operational procedures.

Before opening a pull request, make sure generated docs are synced and the worktree has no unrelated churn.
