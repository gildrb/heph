# Heph Interfaces

Interfaces owns CLI/TUI adapter behavior built on Textual and terminal
rendering primitives. It adapts user input and presentation into the harness;
it does not own reusable product decisions.

## Ownership

The package owns:

- `terminal`: terminal styling, direct input/output, menu helpers, source
  opening, input history, and theme state;
- `tui`: Textual app composition, widgets, inline flows, keymaps, transcript
  rendering, model/auth flows, resize behavior, and chat-stream adaptation.

## Dependency Direction

Allowed direction:

```text
heph-interfaces -> heph-ai
heph-interfaces -> hephaion
heph-interfaces -> heph-extensions
heph app -> heph-interfaces
```

Interface modules may compose broadly, but ownership still matters. Rendering,
keyboard, and session-adapter code belongs here. Retrieval, citation checks,
memory extraction, provider behavior, and command business logic belong below or
beside the interface.

## Migration Pressure

When TUI code accumulates reusable decisions, promote those decisions into
`hephaion` or `heph-ai`. When command behavior is needed, inject the command
registry from the app package rather than making the interface package the
command owner.
