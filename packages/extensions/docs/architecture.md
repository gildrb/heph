# heph-extensions Architecture

`heph-extensions` is the smallest layer in the workspace. It exists so
extension-oriented code can target stable contracts without importing concrete
app, harness, AI, or interface modules.

## Ownership

The package owns:

- stable extension protocols and dataclasses;
- product context hooks that are safe to read from app and harness code;
- narrow routing context that helps Heph distinguish product behavior from
  user-material behavior.

It does not own concrete tool execution, provider access, retrieval, UI, or
command behavior.

## Dependency Direction

Allowed direction:

```text
heph / interfaces / hephaion -> heph-extensions
```

Forbidden direction:

```text
heph-extensions -> heph
heph-extensions -> hephaion
heph-extensions -> heph-ai
heph-extensions -> heph-interfaces
```

Contracts should be boring and stable. If a contract needs implementation
details from another package, the contract is probably too large.

## Migration Pressure

When a feature should be user-owned, start by defining the smallest generic
contract here. Then implement concrete behavior in the owning package or in a
future extension package.
