# Contributing

## Setup

```sh
uv sync --frozen
uv run heph --help
```

## Checks

```sh
uv run ruff check packages tests
uv run pytest
uv lock --check
```

Keep armories portable. Keep answers grounded in local materials with source citations. Keep shell execution opt-in. Prefer deleting layers over adding wrappers, and add a focused test for changed behavior.
