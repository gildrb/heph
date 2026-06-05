# Packages

This source root separates stable product ownership from extension surfaces.

- `ai/`: provider, model, runtime, logging, diagnostics, and palette primitives.
- `extensions/`: stable contracts for user-extensible prompts, tools, and workflows.
- `hephaion/`: correctness harness, retrieval, citations, memory, study state, armories,
  and persistence.
- `interfaces/`: terminal and Textual adapters over the harness.
- `heph/`: app package, command entrypoint, slash commands, product identity, and
  composition.

The architecture goal is a closed kernel with an open extension plane. Heph and
Hephaion should know themselves well enough to help the user add, remove, or
adapt behavior through stable extension points instead of waiting for every
possible feature to be built into the core.

Each package has its own `README.md`, `docs/`, `src/`, and `test/` tree. The
source roots stay flat by import concern rather than wrapping everything in a
duplicate package-name directory.

Dependency direction is intentional:

```text
heph app -> heph-interfaces
heph app -> hephaion harness
heph app -> heph-ai
heph app -> heph-extensions

heph-interfaces -> hephaion harness
heph-interfaces -> heph-ai

hephaion harness -> heph-ai
hephaion harness -> heph-extensions
```

The important rule is that low-level packages do not reach upward. `heph-ai`
and `heph-extensions` are foundation packages; `hephaion` is the protected
harness; `heph-interfaces` adapts presentation; and `heph` composes the product.
