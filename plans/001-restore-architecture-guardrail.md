# Plan 001: Restore the architecture guardrail baseline

> **Executor instructions**: Follow this plan step by step. Run every verification command and
> confirm the expected result before moving on. If a STOP condition occurs, stop and report.
>
> **Drift check (run first)**:
> `git diff --stat 57b55b0..HEAD -- packages/hephaion/src/hephaion/chat/intent_resolution.py packages/hephaion/test/test_chat_routing.py packages/hephaion/test/test_chat_orchestrator.py`
> If any in-scope file changed since this plan was written, compare the excerpts below against
> the live code before proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: MED
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `57b55b0`, 2026-06-11
- **Completed**: 2026-06-11

## Why this matters

The repository has an explicit architecture guardrail that prevents new complexity from growing
past the current refactor baseline. The current checkout fails that gate because
`_stabilized_intent_for_default_material_plan` grew from complexity 14 to 15. Restoring the
baseline keeps intent-routing work shippable without weakening the guardrail.

## Current State

- `packages/hephaion/src/hephaion/chat/intent_resolution.py` contains the failing helper.
- `scripts/check_architecture_guardrails.py` sets `COMPLEXITY_THRESHOLD = 11` and has a
  baseline of 14 for `chat/intent_resolution.py:_stabilized_intent_for_default_material_plan`.
- The current failing command reports:
  `chat/intent_resolution.py:_stabilized_intent_for_default_material_plan: cyclomatic complexity grew from 14 to 15`.

Current excerpt:

```python
# packages/hephaion/src/hephaion/chat/intent_resolution.py:204
def _stabilized_intent_for_default_material_plan(...):
    if (...):
        return TurnIntentResolution(...)
    if (...):
        return resolution
    if not resolution.direct_evidence_required:
        return resolution
    if _direct_source_resolution_should_keep_source_route(...):
        return resolution
    if index is not None and _source_lookup_preserves_user_terms(resolution, index):
        return resolution
    return TurnIntentResolution(...)
```

## Commands You Will Need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Guardrail | `rtk uv run python scripts/check_architecture_guardrails.py` | exit 0 |
| Focused tests | `rtk uv run pytest packages/hephaion/test/test_chat_routing.py packages/hephaion/test/test_chat_orchestrator.py -q --no-cov` | all pass |
| Policy | `rtk uv run python -m scripts.check_repo_policies` | exit 0 |

## Scope

**In scope**
- `packages/hephaion/src/hephaion/chat/intent_resolution.py`
- Existing focused chat routing/orchestrator tests if a behavior regression test is needed.

**Out of scope**
- Raising architecture baselines.
- Rewriting broader chat routing or changing public intent semantics.

## Steps

1. Split one or more conditions out of `_stabilized_intent_for_default_material_plan` into
   small named helpers, preserving current behavior exactly.
2. Run the architecture guardrail command and confirm the complexity regression is gone.
3. Run focused chat routing/orchestrator tests.

## Done Criteria

- [x] `rtk uv run python scripts/check_architecture_guardrails.py` exits 0.
- [x] Focused chat tests pass.
- [x] No architecture baseline is raised.

## STOP Conditions

- The function no longer matches the current-state shape above.
- Reducing complexity appears to require changing intent-routing behavior rather than extracting
  readable helpers.

## Maintenance Notes

Future changes to direct-source, material-overview, or follow-up routing should add a helper or
small policy object before increasing this already-baselined function.
