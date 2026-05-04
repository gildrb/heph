# Agentic Development

This document describes how AI coding agents are used in the Hephaistos project.

## Shared Project Skills

Hephaistos keeps shared, repo-level agent context in a single vendor-neutral directory:

| Location | Purpose |
|---|---|
| `.agents/skills/hephaistos/SKILL.md` | Thin pointer back to the repo-native docs |
| `.agents/skills/qa/` | QA orchestrator skill and config |
| `.agents/skills/qa-cli/` | Full regression test suite for TUI |
| personal agent home directories | Personal prompts, helpers, or local agent config that should not be committed |

## Conventions

- Shared skills belong in the repository when they help contributors and agents understand the project.
- Personal agent config belongs outside the repository.
- Maintainer-only diagnostics or vendor-specific setup should stay out of shared skills.
- `AGENTS.md` and `docs/architecture.md` are the authoritative agent-facing surfaces.
- Repo-local skill files should stay thin and point back to those repo-native docs.
- When CLI or privacy/diagnostics docs change, run `uv run python -m scripts.sync_docs`.
- Before opening a PR, run `uv run python -m scripts.check_repo_policies` to catch explicit `Any` usage and deferred imports.

## Agent Co-Authorship

When code is authored or co-authored by an AI agent, commits should include a
`Co-authored-by` trailer:

```
Co-authored-by: Droid <droid@factory.ai>
```

The CI pipeline automatically detects agent-authored commits on PRs and posts an
annotation comment.

### Detection

The `scripts/detect_co_author.py` script checks for agent signatures:

- `Co-authored-by:` trailers referencing known agent identities
- Commit messages containing `[agent]` or `ai:` prefixes
- Factory/Droid metadata in commit footers

## Conventions

1. **Always review** agent-generated code before merging
2. **Tag agent commits** with co-authorship trailers
3. **Test thoroughly** — agent code follows the same quality gates
4. **Keep repo-native docs current** — update `AGENTS.md` and `docs/architecture.md`, then run `uv run python -m scripts.sync_docs`
5. **Document decisions** — if an agent made an architectural choice, note it in the PR
