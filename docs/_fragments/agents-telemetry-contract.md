- Telemetry rule: PostHog is anonymous opt-in maintainer visibility only; Sentry
  is redacted opt-in crash reporting only.
- Preserve the public safe-stub split in `hephaistos/_telemetry_release.py`.
  Official release builds inject telemetry values in CI; source, editable, and
  Git installs must stay bare by default.
- When CLI commands, telemetry surfaces, or README-adjacent docs change, run
  `uv run python -m scripts.sync_docs` and keep `README.md`, `docs/index.md`,
  `docs/cli-reference.md`, `AGENTS.md`, and the architecture telemetry section
  aligned.
