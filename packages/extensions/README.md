<p align="center">
  <img alt="Hephaion" src="https://gildrb.github.io/heph/logo-auto.svg" width="128">
</p>

# heph-extensions

`heph-extensions` is the stable contract plane for user-extensible behavior. It
defines the smallest shared APIs that core code, interface code, and future
extension packages can depend on without reaching into each other's internals.

This package is deliberately thin. It should make extension points possible, not
become another product or harness implementation.

## Package Role

Use `heph-extensions` when a change is about:

- a stable protocol, dataclass, or helper that third-party or armory-local
  extension code should be able to target;
- product self-knowledge hooks that Heph can read without importing app or TUI
  modules;
- routing context that helps the harness distinguish product questions from
  user-material questions without phrase-catching architecture;
- cross-package contracts that must stay independent of providers, armories, and
  UI adapters.

Do not put concrete tool execution, provider logic, RAG behavior, TUI widgets,
or command handlers here. Those belong in implementation packages that depend on
these contracts.

## Import Surface

The current public module is:

```text
src/
  extension_contracts.py
```

It exposes product-context helpers used by Heph and the harness:

```python
from extension_contracts import heph_product_context, heph_product_routing_context
```

As extension work grows, prefer adding narrow named contracts here before adding
new imports from core packages into user-owned behavior.

## Boundaries

`heph-extensions` must not import concrete product, harness, AI, or interface
modules. In practice, that means no imports from `agent`, `chat`, `runtime`,
`providers`, `commands`, `terminal`, `tui`, or any armory/materials package.

The package may read repo documentation at runtime for product context, but
those reads should stay generic and optional. It must not bake in user-private
corpus terms or local paths.

## Development

Run the focused package tests:

```bash
uv run pytest --no-cov packages/extensions/test
```

Run the policy checker after changing contracts:

```bash
uv run python -m scripts.check_repo_policies
```

When a requested feature sounds personal, project-specific, or workflow-specific,
look here first for the contract shape, then implement the concrete behavior in
the package that actually owns the runtime decision.

## Related Docs

- [Contracts](docs/contracts.md)
- [Workspace package map](../README.md)
- [Root architecture guide](../../docs/architecture.md)
