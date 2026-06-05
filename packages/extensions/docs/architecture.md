# Extensions Architecture

Extensions is the smallest layer in the workspace. It exists so
extension-oriented code can target stable contracts without importing concrete
app, harness, AI, or interface modules.

## Ownership

The package owns:

- stable extension protocols and dataclasses;
- context hooks that are safe to read from app and harness code;
- narrow routing context that helps Heph distinguish system behavior from
  user-material behavior.

It does not own concrete tool execution, provider access, retrieval, UI, or
command behavior.

## Dependency Direction

Allowed direction:

```text
heph / interfaces / hephaion -> extensions
```

Forbidden direction:

```text
extensions -> heph
extensions -> hephaion
extensions -> ai
extensions -> interfaces
```

Contracts should be boring and stable. If a contract needs implementation
details from another package, the contract is probably too large.

## Migration Pressure

When a feature should be user-owned, start by defining the smallest generic
contract here. Then implement concrete behavior in the owning package or in a
future extension package.
