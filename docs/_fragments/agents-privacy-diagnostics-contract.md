- Privacy and diagnostics rule: PostHog is anonymous opt-in maintainer visibility only; Sentry
  is redacted opt-in crash reporting only.
- Preserve the public safe-stub split in `packages/hephaion/privacy/release.py`.
  Official release builds inject privacy and diagnostics backend values in CI; source, editable, and
  Git installs must stay bare by default.
- When CLI commands, privacy or diagnostics surfaces, or README-adjacent docs change, run
  `uv run python -m scripts.sync_docs` and keep `README.md`, `docs/index.md`,
  `docs/cli-reference.md`, `AGENTS.md`, and the architecture privacy and diagnostics section
  aligned.
