# Security Policy

## Supported Versions

Currently only the latest version from the `main` branch is supported.

## Reporting a Vulnerability

If you discover a security vulnerability in Heph, please report it privately.

**Do not** open a public issue.

Instead, send an email to: hi@gildrb.com

Please include:
- A description of the vulnerability
- Steps to reproduce the issue
- Any potential impact you've identified
- If possible, a suggested fix

I will acknowledge receipt within 48 hours and provide a timeline for addressing the issue.

## Security Features

Heph is designed with security and privacy in mind:

- **Local-first**: Your documents and chats stay on your machine
- **No telemetry by default**: Analytics and crash reporting are opt-in only
- **Scoped memory**: Each armory's memory is isolated from others
- **No default terminal access**: Model-generated commands are not exposed as a default agent tool
- **Secret protection**: API keys are stored in OS keyring or environment variables, never in config files

## Security Best Practices for Users

1. **Review armory plugins**: Only use armory plugins from sources you trust
2. **Use terminal escapes carefully**: The `!` command escape should only be used in armories you trust
3. **Keep dependencies updated**: Run `uv tool upgrade heph` regularly
4. **Check diagnostics settings**: Review what analytics/crash reporting is enabled in `/settings`

## Dependency Security

The default dependency profile is deliberately minimal. Heavy ML and document
backends are opt-in extras because they add substantial native code, model
assets, and transitive dependencies that increase supply-chain attack surface.
Install only the capability groups you need, such as `heph[documents]` or
`heph[embeddings]`.

Pre-commit runs `gitleaks` and Bandit. Dependency changes require reviewed
`pyproject.toml`, `uv.lock`, and source-only sdist allowlist changes.
