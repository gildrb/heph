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
- **No hosted telemetry**: Heph does not send analytics or crash reports
- **Scoped memory**: Each armory's memory is isolated from others
- **No default terminal access**: Shell execution is disabled unless an armory is explicitly trusted
- **Secret protection**: API keys are stored in OS keyring or environment variables, never in config files

## Security Best Practices for Users

1. **Review armory plugins**: Only use armory plugins from sources you trust
2. **Enable shell execution only for trusted armories**: Set
   `HARNESS_TRUST_ARMORY_SHELL=/path/to/armory` only when you accept that the agent
   can run argv-style commands on that machine. Shell execution is disabled by
   default and does not provide a sandbox.
3. **Keep dependencies updated**: Run `uv tool upgrade heph` regularly
4. **Review provider traffic**: Use a local model or a trusted provider for sensitive prompts

## Dependency Security

The default dependency profile is deliberately minimal: one install, with no
optional extras, ML runtime, or model downloads. Retrieval is lexical and
document extraction uses native XML parsing plus bundled PDFium.

Dependency changes require review of `pyproject.toml` and `uv.lock`.
