PostHog is used only for anonymous, opt-in usage/error visibility for the
maintainer. Sentry is used only for redacted, opt-in crash reporting. The
public repository ships `packages/harness/src/harness/privacy/release.py` as a safe stub;
official release builds inject privacy and diagnostics backend values during CI, and forks or custom
builds can provide `HARNESS_POSTHOG_PROJECT_TOKEN`,
`HARNESS_POSTHOG_HOST`, and `HARNESS_SENTRY_DSN`.
