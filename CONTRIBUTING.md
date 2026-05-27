# Contributing

Thanks for helping improve Hephaion and the Heph agent.

## Setup

```bash
git clone https://github.com/gildrb/heph
cd heph
uv sync --group dev
```

Optional extras:

```bash
uv sync --group rag      # BM25, embeddings, reranking
uv sync --group docling  # document extraction extras
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
```

When README, CLI, privacy, diagnostics, or docs-adjacent behavior changes:

```bash
uv run python -m scripts.sync_docs
```

## Guidelines

- Keep armories portable normal directories.
- Keep answers grounded in user materials with verifiable citations.
- Keep memory scoped to the armory unless the user explicitly opts into a shared service.
- Keep providers and models swappable.
- Prefer deleting duplication and simplifying control flow over adding new abstractions.
- Add focused tests for behavior that could break.

Before opening a pull request, make sure generated docs are synced and the worktree has no unrelated churn.
