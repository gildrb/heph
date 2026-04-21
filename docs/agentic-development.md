# Agentic Development

This document describes how AI coding agents are used in the Hephaistos project.

## Shared Project Skills

Hephaistos keeps the shared, repo-level agent context in vendor-neutral skill folders:

| Location | Purpose |
|---|---|
| `.factory/skills/hephaistos/SKILL.md` | Shared Factory skill with commands, conventions, and architecture |
| `.codex/skills/hephaistos/SKILL.md` | Shared Codex skill with the same project context |
| personal agent home directories | Personal prompts, helpers, or local agent config that should not be committed |

## Why This Split

- Shared skills belong in the repository when they help contributors and agents understand the project.
- Personal agent config belongs outside the repository.
- Maintainer-only telemetry or vendor-specific setup should stay out of shared skills.

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
4. **Keep repo skills current** — update `.factory` and `.codex` skills when commands or architecture change
5. **Document decisions** — if an agent made an architectural choice, note it in the PR
