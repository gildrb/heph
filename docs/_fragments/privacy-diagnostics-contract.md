PostHog is used only for anonymous, opt-in usage/error visibility for the
maintainer. Sentry is used only for redacted, opt-in crash reporting. The
public repository ships `packages/hephaion/privacy/release.py` as a safe stub;
official release builds inject privacy and diagnostics backend values during CI, and forks or custom
builds can provide `HEPHAION_POSTHOG_PROJECT_TOKEN`,
`HEPHAION_POSTHOG_HOST`, and `HEPHAION_SENTRY_DSN`.
