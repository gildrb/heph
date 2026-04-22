## Telemetry

Hephaistos keeps telemetry optional and maintainer-facing.

- `hephaistos.analytics` sends anonymous PostHog events only when a backend is
  configured and the user explicitly opts in.
- `hephaistos.observability` sends redacted Sentry crash reports only when a
  backend is configured and the user explicitly opts in.
- `hephaistos/_telemetry_release.py` is committed as a safe stub in the public
  repository. Official release and edge workflows overwrite it in CI before
  building artifacts.
- Source, editable, and Git installs stay bare by default. Forks and custom
  builds can wire their own endpoints with `HEPHAISTOS_POSTHOG_PROJECT_TOKEN`,
  `HEPHAISTOS_POSTHOG_HOST`, and `HEPHAISTOS_SENTRY_DSN`.
- Agents and contributors should preserve this split: telemetry exists only for
  opt-in maintainer visibility into usage/errors and is never a required product
  dependency.
