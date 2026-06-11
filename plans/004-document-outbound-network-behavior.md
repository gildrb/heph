# Plan 004: Document outbound network behavior accurately

> **Executor instructions**: Follow this plan step by step. Run every verification command and
> confirm the expected result before moving on. If a STOP condition occurs, stop and report.
>
> **Drift check (run first)**:
> `git diff --stat 57b55b0..HEAD -- docs/privacy.md docs/architecture.md AGENTS.md README.md docs/index.md docs/cli-reference.md`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: plans/003-preserve-https-host-identity-in-web-fetch.md
- **Category**: docs
- **Planned at**: commit `57b55b0`, 2026-06-11
- **Completed**: 2026-06-11

## Why this matters

The privacy docs promise local-first behavior and list outbound connections, but omit two real
network paths: the default `web_fetch` tool and optional DuckDuckGo prerequisite hints. Accurate
privacy docs are part of the product promise.

## Current State

- `docs/privacy.md:159` lists model providers, model downloads, package managers, and diagnostics.
- `packages/hephaion/src/hephaion/agent/tools.py:258` exposes `web_fetch` as a default tool.
- `packages/hephaion/src/hephaion/study/priority_web.py:31` uses
  `https://duckduckgo.com/html/` when optional web prerequisite hints are enabled.
- AGENTS.md requires running `uv run python -m scripts.sync_docs` when privacy or diagnostics
  surfaces change.

## Commands You Will Need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Docs sync | `rtk uv run python -m scripts.sync_docs` | exit 0 |
| Docs sync check | `rtk uv run python -m scripts.sync_docs --check` | exit 0 |
| Policy | `rtk uv run python -m scripts.check_repo_policies` | exit 0 |

## Scope

**In scope**
- `docs/privacy.md`
- Managed docs touched by `scripts.sync_docs`, if any.

**Out of scope**
- Changing telemetry consent behavior.
- Adding new network controls.

## Steps

1. Update `docs/privacy.md` under Network Activity to include user/model-triggered `web_fetch`
   and optional DuckDuckGo prerequisite searches.
2. Run docs sync and keep any managed files it updates.
3. Run docs sync check and repo policy checks.

## Done Criteria

- [x] Privacy docs name `web_fetch`.
- [x] Privacy docs name optional DuckDuckGo prerequisite searches and their enablement path.
- [x] Docs sync check passes.

## STOP Conditions

- The implementation has changed so `web_fetch` is no longer a default tool.
- `scripts.sync_docs` rewrites unrelated content unexpectedly.

## Maintenance Notes

Future network-facing features should update this section in the same change as the feature.
