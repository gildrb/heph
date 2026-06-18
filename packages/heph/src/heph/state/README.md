# State

Target home for declarative Heph state contracts.

JSON and Markdown state should be owned here when it describes Heph behavior,
self-knowledge, or prompt-program inputs rather than harness persistence.

`release.toml` is the official stable user-facing release pointer. It lets
maintainers keep developing on `main` while preserving a clear in-repo record of
the version intended for PyPI and `uv tool install heph@latest`.
