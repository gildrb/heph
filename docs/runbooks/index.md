# Runbooks

Operational playbooks for diagnosing and resolving issues in Hephaistos.

## Available Runbooks

| Runbook | When to use |
|---------|-------------|
| [CI Failure](ci-failure.md) | CI pipeline fails on `main` branch |
| [Sentry Errors](sentry-errors.md) | Investigating error reports from Sentry |
| [Slow LLM Response](slow-llm-response.md) | Debugging slow or unresponsive LLM interactions |
| [Deployment Rollback](deployment-rollback.md) | Reverting a bad release or edge deploy |
| [RAG Retrieval Issues](rag-retrieval-issues.md) | Debugging poor RAG search quality or index problems |

## Quick Reference

**Where to check deploy impact:**
- [Sentry Releases](https://sentry.io) — filter by release tag `hephaistos@{version}`
- [GitHub Deployments](https://github.com/gildrb/hephaistos/deployments) — deployment history and status

**Alerting channels:**
- Critical errors: Sentry → webhook (configure `ALERT_WEBHOOK_URL`)
- CI failures on main: auto-created GitHub Issue (via `ci-failure-issue.yml`)
- Deploy notifications: configure `DEPLOY_WEBHOOK_URL` in repository secrets

**Monitoring:**
- Sentry dashboard for error tracking
- OpenTelemetry backend (configure via `OTEL_EXPORTER_OTLP_ENDPOINT`) for traces and metrics
- GitHub Actions Step Summary for CI performance trends
