# Interfaces Architecture

Interfaces owns terminal and TUI adapter behavior built on Textual and terminal
rendering primitives. It adapts user input and presentation into the harness;
it does not own reusable harness or agent decisions.

## Ownership

The package owns:

- `palette`: theme and ANSI color tokens;
- `terminal`: terminal styling, direct input/output, menu helpers, source
  opening, input history, and theme state;
- `tui`: Textual app composition, widgets, inline flows, keymaps, transcript
  rendering, model/auth flows, resize behavior, and chat-stream adaptation.

## Dependency Direction

Allowed direction:

```text
interfaces -> ai
interfaces -> hephaion
interfaces -> extensions
heph -> interfaces
```

Interface modules may compose broadly, but ownership still matters. Rendering,
keyboard, and session-adapter code belongs here. Retrieval, citation checks,
memory extraction, provider behavior, and command business logic belong below or
beside the interface.

## Migration Pressure

When TUI code accumulates reusable decisions, promote those decisions into
Hephaion, AI, or Heph. When command behavior is needed, inject the command
registry from Heph rather than making Interfaces the command owner.
