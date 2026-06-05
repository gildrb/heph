# Interfaces

Target package root for user-facing shells and integrations.

TUI, CLI, keybindings, browser surfaces, and other interfaces should compose the
stable Heph and Hephaion packages without owning reusable business decisions.

Interfaces should be mode-specific views over the same harness, not separate
brains. The target modes are interactive TUI, print/plain CLI, JSON streaming,
and RPC/process integration for external tools or custom UIs.
