# Plan 002: Enforce coverage in CI pytest

> **Executor instructions**: Follow this plan step by step. Run every verification command and
> confirm the expected result before moving on. If a STOP condition occurs, stop and report.
>
> **Drift check (run first)**:
> `git diff --stat 57b55b0..HEAD -- .github/workflows/ci.yml pyproject.toml AGENTS.md`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW/MED
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `57b55b0`, 2026-06-11
- **Completed**: 2026-06-11

## Why this matters

`pyproject.toml` configures pytest with package coverage and `--cov-fail-under=46`, and AGENTS.md
documents that baseline. CI currently bypasses it with `--no-cov`, so a PR can pass while lowering
coverage below the project floor.

## Current State

- `.github/workflows/ci.yml:303` runs `uv run pytest --no-cov --junitxml=.artifacts/pytest-junit.xml`.
- `pyproject.toml:293` sets pytest `addopts` with coverage reports and `--cov-fail-under=46`.

## Commands You Will Need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Static check | `rtk rg -n "pytest --no-cov" .github/workflows/ci.yml` | no matches |
| Static check | `rtk rg -n "junitxml=.artifacts/pytest-junit.xml" .github/workflows/ci.yml` | one pytest line remains |
| Format/lint | `rtk uv run ruff check .` | exit 0 |

## Scope

**In scope**
- `.github/workflows/ci.yml`

**Out of scope**
- Changing the coverage threshold.
- Reworking the whole CI workflow.
- Editing `pyproject.toml` unless the pytest config has drifted.

## Steps

1. Remove the `--no-cov` override from the CI pytest command while preserving the JUnit artifact.
2. Run the static checks above.

## Done Criteria

- [x] CI pytest no longer includes `--no-cov`.
- [x] CI still writes `.artifacts/pytest-junit.xml`.

## STOP Conditions

- CI has added a separate coverage-enforcing job since this plan was written.
- Removing `--no-cov` requires unrelated workflow restructuring.

## Maintenance Notes

If CI runtime becomes too high, add a dedicated coverage job rather than silently bypassing the
configured baseline.
