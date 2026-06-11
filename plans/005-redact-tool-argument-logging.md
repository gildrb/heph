# Plan 005: Redact tool argument logging by default

> **Executor instructions**: Follow this plan step by step. Run every verification command and
> confirm the expected result before moving on. If a STOP condition occurs, stop and report.
>
> **Drift check (run first)**:
> `git diff --stat 57b55b0..HEAD -- packages/hephaion/src/hephaion/agent/tool_execution.py packages/hephaion/test`

## Status

- **Priority**: P2
- **Effort**: S/M
- **Risk**: LOW
- **Depends on**: none
- **Category**: privacy
- **Planned at**: commit `57b55b0`, 2026-06-11
- **Completed**: 2026-06-11

## Why this matters

Structured tool logs currently include argument values for most tools, truncating long strings to
100 characters. That can put memory entries, search queries, edit snippets, URLs, or user text into
local logs when logging is enabled. Logs should preserve operational value while avoiding private
content by default.

## Current State

- `packages/hephaion/src/hephaion/agent/tool_execution.py:268` logs `"args"` for every completed
  tool call.
- `_tool_args_summary` special-cases only `bash` and `write_file`; every other tool falls back to
  raw argument values with string truncation.

## Commands You Will Need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Focused tests | `rtk uv run pytest packages/hephaion/test/test_tool_registry.py packages/hephaion/test/test_harness.py -q --no-cov` | all pass |
| Lint | `rtk uv run ruff check packages/hephaion/src/hephaion/agent/tool_execution.py packages/hephaion/test` | exit 0 |
| Policy | `rtk uv run python -m scripts.check_repo_policies` | exit 0 |

## Scope

**In scope**
- `packages/hephaion/src/hephaion/agent/tool_execution.py`
- Existing hephaion agent/tool tests, or a small new focused test file.

**Out of scope**
- Changing trace contents, tool result messages, or model-visible tool output.
- Reworking `ai.logging` redaction.

## Steps

1. Replace the fallback argument summary with per-tool structural summaries that keep paths,
   counts, booleans, and lengths, but not content-like strings.
2. Ensure errors do not log raw argument dictionaries.
3. Add tests for representative sensitive tools: `memory`, `search_files`, `web_fetch`, and
   `edit_file`.
4. Run focused tests, lint, and policy checks.

## Done Criteria

- [x] Successful and failed tool logs avoid raw content-like argument values.
- [x] Tests prove sensitive arguments are summarized structurally.
- [x] Focused tests and policy checks pass.

## STOP Conditions

- Debuggability requires raw argument logging for a specific tool and there is no safe structural
  alternative.
- A required change would alter tool behavior or model-visible tool results.

## Maintenance Notes

When adding a new tool, reviewers should check whether `_tool_args_summary` needs a structural
summary for its arguments.
