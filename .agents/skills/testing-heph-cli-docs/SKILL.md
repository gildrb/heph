---
name: testing-heph-cli-docs
description: Test Heph CLI entrypoints and generated documentation locally. Use when verifying command, install, README, docs sync, or product naming changes in the Heph repo.
---

# Testing Heph CLI and Docs Surfaces

Use this skill for changes that affect public CLI commands, install/start copy, generated README/docs, or product naming.

## Devin Secrets Needed

None for local CLI/docs validation. Provider keys such as `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `ZAI_API_KEY`, or `CUSTOM_API_KEY` are only needed when testing model-backed chat flows.

## Setup

1. Work from the branch or merged commit under test.
2. Confirm dependencies are available:
   ```bash
   uv sync --group dev
   ```
3. Do not record the desktop if all testing is shell-only. Capture command output as text evidence instead.

## Core Checks

Run the command surfaces directly through `uv`:

```bash
uv run heph --help
uv run hephaion --help
uv run heph --version
uv run hephaion --version
uv run python -m scripts.sync_docs --check
```

For CLI naming changes, verify the help output includes the exact expected usage for each invoked command and does not silently fall back to the wrong program name.

## Useful Programmatic Assertions

Use a small Python assertion script when validating docs/model synchronization:

```python
from pathlib import Path

from hephaion.cli.main import build_parser
from scripts import sync_docs

root = Path.cwd()
model = sync_docs.collect_docs_model(root)
scripts = sync_docs.load_project_scripts(root / "pyproject.toml")

assert model.short_command == "heph"
assert model.long_command == "hephaion"
assert scripts["heph"] == scripts["hephaion"]

for prog in ("heph", "hephaion"):
    parser = build_parser()
    parser.prog = prog
    help_text = parser.format_help()
    assert f"Usage: {prog} [options] [command] [path]" in help_text
```

Adapt the expected command names and copy to the change being tested.

## CI Caveat

GitHub Actions may occasionally fail before any workflow step executes. If every job fails in a few seconds with empty steps and logs only show hosted-runner startup lines, treat that as a CI/runner issue until proven otherwise; rely on local command evidence only when the user explicitly approves proceeding despite red CI.
