# Agentic Development

This document describes how AI coding agents are used in the Hephaistos project.

## Factory Configuration

The project uses [Factory](https://factory.ai) for AI-assisted development. Configuration
lives in two locations:

| Location | Purpose |
|---|---|
| `.factory/skills/SKILL.md` | Project-specific skill manifest with commands, conventions, and architecture |
| `~/.factory/droids/` | Personal agent configurations (shared across all projects) |

### Skills

The `.factory/skills/` directory contains a `SKILL.md` that teaches agents about project
conventions, commands, and architecture. This is automatically discovered by Factory agents.

### Droids

Custom droids (if any) are stored in `~/.factory/droids/` for personal use. Project-level
droids can be added to `.factory/droids/` for team-shared agent configurations.

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
4. **Document decisions** — if an agent made an architectural choice, note it in the PR
