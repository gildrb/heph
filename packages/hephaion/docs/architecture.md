# Hephaion Harness

Hephaion owns the correctness-critical harness:

`intent -> planning -> evidence -> generation/repair -> verification/finalization`

It may depend on AI primitives from `runtime`, `providers`, `ai_logging`, and
related `packages/ai/src` concerns, plus extension contracts, but it does not
import the app package or interface adapters.
