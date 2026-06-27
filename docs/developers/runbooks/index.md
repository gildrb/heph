# Runbooks

Operational playbooks for diagnosing and resolving issues in Heph.

## Available Runbooks

| Runbook | When to use |
|---------|-------------|
| [CI Failure](ci-failure.md) | CI pipeline fails on `main` branch |
| [Stable Release](stable-release.md) | Publishing a reviewed `heph` release to PyPI and GitHub |
| [Slow LLM Response](slow-llm-response.md) | Debugging slow or unresponsive LLM interactions |
| [Deployment Rollback](deployment-rollback.md) | Reverting a bad release or edge deploy |
| [RAG Retrieval Issues](rag-retrieval-issues.md) | Debugging poor RAG search quality or index problems |

## Quick Reference

**Where to check deploy impact:**
- [GitHub Deployments](https://github.com/gildrb/heph/deployments) — history for manual edge publishes and releases

**Primary diagnostics:**
- Structured logs via `HEPHAION_LOG_*`
- Per-armory trace files in `.hephaion/traces/`
- CPU and memory profiles in `~/.cache/hephaion/profiles/`

**Monitoring:**
- CI failures on main: auto-created GitHub Issue (via `ci-failure-issue.yml`)
- GitHub Actions Step Summary for CI performance trends
