# Contributing to Hephaistos

Thanks for your interest. Hephaistos is a personal learning project, and
suggestions, fixes, and careful feature work are welcome.

The product promise is simple: **a local-first study agent that works with your
files and any LLM.** Changes should protect that shape. Keep armories portable,
answers source-grounded, citations verifiable, memory scoped to the armory, and
provider/model choices swappable.

## Setup

```bash
uv sync --group dev
```

Optional extras:

```bash
uv sync --group rag       # embeddings, hybrid retrieval, re-ranking
uv sync --group docling   # PDF/DOCX/PPTX/XLSX-style document conversion
uv sync --group docs      # documentation site tooling
```

## Development Workflow

1. Create a feature branch from `main`.
2. Make a focused change.
3. Add or update tests for behavior that could break.
4. Update user-facing docs when commands, armory behavior, retrieval, citation
   checks, memory, or provider setup changes.
5. Run the relevant checks.
6. Commit with a clear message and open a pull request.

## Checks

Run the full set before opening a larger PR:

```bash
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run pytest
```

For a narrow change, run the closest focused test first:

```bash
uv run pytest tests/test_citation.py
uv run pytest tests/test_memory.py
uv run pytest tests/test_rag_retrieve.py
uv run pytest -k "provider"
```

## Code Style

- Prefer readable code over clever or overly optimized code.
- Follow the existing module boundaries and local helper APIs.
- Use Python 3.13+ and `from __future__ import annotations` in every module.
- Keep line length at 99 characters.
- Use double quotes and LF line endings.
- Keep comments sparse and useful. Explain why a non-obvious block exists.

Naming is enforced by Ruff:

- Classes: PascalCase, for example `ChatConfig`.
- Functions and methods: snake_case, for example `build_system_prompt()`.
- Variables: snake_case, for example `source_file_count`.
- Constants: UPPER_SNAKE_CASE, for example `_RAG_MIN_SCORE`.
- Private names: underscore prefix, for example `_resolve_turn_evidence()`.

## Product And Docs Style

User-facing copy should sound like Hephaistos: practical, local-first,
study-focused, and grounded in the user's files.

- Lead with armories, source files, RAG, citation verification, study memory,
  recall practice, and model freedom.
- Do not market bare-minimum plumbing as a feature.
- Keep vendor-specific behavior optional unless the code truly requires it.
- Avoid putting internal operations or maintainer-only details in user-facing
  docs.
- Prefer concrete examples over abstract claims.

## Testing Guidance

Tests use `pytest`. Aim to cover the behavior, not implementation trivia.

Good places to add tests:

- Citation parsing and verification when evidence is missing, invalid, or
  correctly cited.
- Armory-scoped memory extraction, deduplication, and prompt context.
- Retrieval behavior for source/library files and stale indexes.
- Provider/model switching without tying an armory to one vendor.
- Study-loop state transitions for present, recall, assess, hint, and resume.

Test naming conventions:

- Test files: `test_<module>.py`.
- Test classes: `Test<FeatureOrComponent>`.
- Test functions: `test_<verb>_<object>_<condition_or_expectation>`.
- Parametrize with tuple names, list values, and tuple rows:

```python
@pytest.mark.parametrize(("key", "value"), [("model", "glm-5"), ("max_tokens", "1024")])
```

- Use `match=` when asserting broad exceptions:

```python
with pytest.raises(ValueError, match="expected"):
    ...
```

## Commit Messages

Use short, imperative commit messages:

```text
Clarify armory memory in README
Fix citation warning for uncited source answers
Add retrieval test for library files
```

## Reporting Issues

Open a GitHub issue with:

- What you expected to happen.
- What actually happened.
- Steps to reproduce, including commands and relevant config.
- Relevant command output or error text.
