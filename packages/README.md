# Packages

This source root separates stable product ownership from extension surfaces.

- `heph/`: model-facing identity, prompt contracts, and self-knowledge target.
- `hephaion/`: correctness harness, validation loops, retrieval, runtime, and persistence.
- `interfaces/`: user-facing shells and integrations that compose the stable packages.
- `extensions/`: user-extensible packages and plugin-style additions.

The architecture goal is a closed kernel with an open extension plane. Heph and
Hephaion should know themselves well enough to help the user add, remove, or
adapt behavior through stable extension points instead of waiting for every
possible feature to be built into the core.

The importable `hephaion` package currently lives directly under `packages/hephaion`.
The `heph`, `interfaces`, and `extensions` roots are tracked as migration targets so future
work can move behavior into the right owner without reintroducing god modules.
