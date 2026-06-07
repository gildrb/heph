<p align="center">
  <img alt="Hephaion" src="https://gildrb.github.io/heph/logo-auto.svg" width="128">
</p>

# Heph

Heph is the agent brain the user talks to.

It owns the user-facing agent identity, research/talking orchestration, the
command entrypoint, slash-command coordination, and the composition needed to
connect the harness, AI runtime, interfaces, and extension contracts.

Heph is not the validation harness. That is Hephaion.

## Source Layout

```text
src/
  heph/
    cli/       Console entrypoint and top-level command routing
    commands/  Slash-command registry and command coordinators
    sdk/       Programmatic runtime/session surface for native apps and automation
    product/   Temporary bridge for Heph self-knowledge context
    identity/  Stable agent identity target
    prompts/   Prompt-program target for Heph-facing behavior
    state/     Declarative state contract target
```

The `product/` bridge exists for current self-knowledge routing. It should stay
thin and should not become a second harness or a place for domain behavior.

## Boundaries

Heph is protected as the brain and composition layer. Lower packages must not
import it, and optional behavior should extend Heph through contracts or
composition instead of modifying harness or AI internals:

- Heph calls Hephaion for grounded answering, validation, citations, retrieval,
  memory, and armory workflows.
- Heph calls AI for provider/model runtime.
- Heph calls Interfaces for terminal and TUI presentation.
- Heph calls Extensions for stable extension contracts.
- Heph exposes SDK wrappers for non-terminal clients; those wrappers must stay
  UI-neutral and must not import `interfaces.*`.

Reusable validation behavior should move to Hephaion. Provider/API behavior
should move to AI. Conversational strategy, research orchestration, and
Heph-facing identity should stay here or move here as the migration continues.

## Development

```bash
uv run pytest --no-cov packages/heph/test
uv run heph --help
uv run python -m scripts.check_repo_policies
uv run lint-imports
```

## Related Docs

- [Root architecture guide](../../docs/architecture.md)
