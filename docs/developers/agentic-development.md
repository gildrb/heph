# Agentic Development

This document describes how AI coding agents are used in the Heph project.

## Shared Project Skills

Heph keeps shared, repo-level agent context in vendor-neutral committed docs and
local ignored agent directories:

| Location | Purpose |
|---|---|
| `AGENTS.md` | Canonical agent guide with commands, conventions, validation, and safety policy |
| `docs/architecture.md` | Package boundaries, data flow, armory layout, and diagnostics design |
| `.factory/skills/` | Local Factory/Droid skills; keep ignored and install/update outside Git |
| personal agent home directories | Personal prompts, helpers, or local agent config that should not be committed |

## Conventions

- Shared agent readiness belongs in committed docs, not in checked-in vendor skill folders.
- Personal or vendor-specific agent config belongs outside the repository or in ignored local folders.
- Maintainer-only diagnostics or vendor-specific setup should stay out of shared skills.
- `AGENTS.md` and `docs/architecture.md` are the authoritative agent-facing surfaces.
- Local skill files should stay thin and point back to those repo-native docs.
- When CLI or privacy/diagnostics docs change, run `uv run python -m scripts.sync_docs`.
- Before opening a PR, run `uv run python -m scripts.check_repo_policies` to catch explicit `Any` usage and unapproved deferred imports.

## Review Conventions

1. **Always review** agent-generated code before merging
2. **Keep vendor metadata local** — personal attribution, setup, or diagnostics should stay outside tracked project scripts
3. **Test thoroughly** — agent code follows the same quality gates
4. **Keep repo-native docs current** — update `AGENTS.md` and `docs/architecture.md`, then run `uv run python -m scripts.sync_docs`
5. **Document decisions** — if an agent made an architectural choice, note it in the PR
