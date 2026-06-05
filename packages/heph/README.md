# Heph

Target package for the thing the user talks to: identity, self-knowledge, prompt
contracts, and model-facing behavior.

Heph should be open for extension through prompt/state files, not modified by TUI,
keybinding, provider, or harness details.

Heph should know the system well enough to help extend it through documented
extension points. Self-knowledge belongs here; correctness loops and protected
runtime machinery belong in `packages/hephaion`.
