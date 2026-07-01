<p align="center">
  <img alt="Heph" src="https://raw.githubusercontent.com/gildrb/heph/main/assets/logo-auto.svg" width="320">
</p>

# Extensions

Extensions is the contract package for behavior that should be open to user or
third-party extension without changing Heph or harness internals.

Use this package for:

- stable protocols, dataclasses, and helper contracts that extension code can
  target;
- small context hooks shared by Heph and the harness;
- generic extension-facing boundaries.

Do not put concrete tools, provider access, retrieval, validation, command
handlers, terminal rendering, or TUI widgets here.

## Source Layout

```text
src/
  extensions/
    contracts.py
```

Keep this package small. It should define the shape of extension points, not
implement the system around them.

## Boundaries

Extensions must not import AI, Heph, harness, or Interfaces modules. Higher
packages depend on these contracts; contracts do not depend upward.

## Development

```bash
uv run pytest --no-cov packages/extensions/test
uv run python -m scripts.check_repo_policies
```

## Related Docs

- [Root architecture guide](../../docs/architecture.md)
