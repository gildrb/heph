# Contributing

Hephaistos is a single-author project (Gil, @gildrb) but contributions are welcome. This section covers the process from branch to merge.

## Quick checklist

Every PR should pass all of these before merging:

- [ ] `uv run ruff check .` — lint clean
- [ ] `uv run ruff format --check .` — formatting clean
- [ ] `uv run basedpyright` — type check clean
- [ ] `uv run pytest` — all tests pass with ≥75% coverage
- [ ] `uv run python -m scripts.check_repo_policies` — no forbidden `Any`, no deferred imports outside allowed sites
- [ ] No secrets or API keys in the diff

## PR process

1. **Branch** from `main` with a descriptive name (`feat/rag-hybrid`, `fix/shell-crash`).
2. **Code** — follow the patterns in [patterns-and-conventions.md](patterns-and-conventions.md).
3. **Test** — write tests. The coverage gate is 75% and actual coverage is ~77%. See [testing.md](testing.md).
4. **Push** and open a pull request against `main`.
5. **CI runs** — lint, type-check, tests, coverage, dead code, import boundaries, security scan, and more. See [tooling.md](tooling.md) for the full list.
6. **Review** — `.github/CODEOWNERS` assigns reviewers. Currently all paths map to `@gildrb`.
7. **Merge** once CI is green and review is approved.

## PR template

The template at `.github/pull_request_template.md` asks for:

- **Description** — what and why
- **Type of change** — bug fix, feature, refactor, docs, or chore
- **Testing done** — checklist of which checks you ran locally
- **Context** — related issues, screenshots, notes

Fill it out. Link the issue it closes (`Closes #123`).

## Review expectations

Reviews focus on correctness, test coverage, and adherence to project conventions. The reviewer checks:

- Does the change follow the import boundary rules? (See [../overview/architecture.md](../overview/architecture.md).)
- Are there any `Any` types? Those are forbidden — use concrete types, `TypedDict`, or protocols instead.
- Is error handling consistent with the patterns in [patterns-and-conventions.md](patterns-and-conventions.md)?
- Are new public APIs documented clearly?

## Definition of done

A PR is ready to merge when:

1. All CI jobs pass (lint, type-check, test, build, architecture, security, dead code, duplicates).
2. At least one approving review.
3. No unresolved conversations.
4. The branch is up to date with `main`.

## Pre-commit hooks

Install them once:

```bash
uv run pre-commit install
```

The hooks run ruff, ruff-format, basedpyright, check-repo-policies, check-large-files, vulture, pylint, and lint-imports on every commit. If a hook fails, the commit is blocked. Fix the issue and try again.
