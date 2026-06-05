# Extensions

Target package root for user-extensible behavior.

Extension packages can add workflows, tools, prompts, or UI integrations through
stable contracts without modifying Heph identity or Hephaion harness internals.

This is the user-owned plane. When a requested behavior is not part of the
correctness harness or Heph identity, prefer adding an extension point or
extension package so Heph can implement the user-specific feature without making
the core more coupled.
