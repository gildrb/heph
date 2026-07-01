## Privacy & Diagnostics

Heph keeps privacy-impacting diagnostics optional and maintainer-facing.
User-facing data, cache, prompt, and compute ownership terms live in
`docs/trust.md` and `docs/privacy.md`.

- `diagnostics.events` sends anonymous PostHog events only when a backend is
  configured and the user explicitly opts in.
- `diagnostics.crashes` sends redacted Sentry crash reports only when a
  backend is configured and the user explicitly opts in.
- `packages/harness/src/harness/privacy/release.py` is committed as a safe stub in the public
  repository. Official release and edge workflows overwrite it in CI before
  building artifacts.
- Source, editable, and Git installs stay bare by default. Forks and custom
  builds can wire their own endpoints with `HARNESS_POSTHOG_PROJECT_TOKEN`,
  `HARNESS_POSTHOG_HOST`, and `HARNESS_SENTRY_DSN`.
- Agents and contributors should preserve this split: diagnostics exist only for
  opt-in maintainer visibility into usage/errors and is never a required product
  dependency.
