# Plan 003: Preserve HTTPS host identity in web_fetch

> **Executor instructions**: Follow this plan step by step. Run every verification command and
> confirm the expected result before moving on. If a STOP condition occurs, stop and report.
>
> **Drift check (run first)**:
> `git diff --stat 57b55b0..HEAD -- packages/hephaion/src/hephaion/agent/web_tools.py packages/hephaion/test/test_tools.py`

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED/HIGH
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `57b55b0`, 2026-06-11
- **Completed**: 2026-06-11

## Why this matters

`web_fetch` is a default agent tool for fetching a web page when armory material is insufficient.
The current SSRF hardening rewrites the URL host to a resolved IP address, then sets the original
host only as an HTTP `Host` header. That keeps an IP decision stable, but for HTTPS it means TLS
certificate validation and SNI see the IP literal instead of the original hostname.

## Current State

- `packages/hephaion/src/hephaion/agent/web_tools.py:192` validates the URL, resolves hostname
  IPs, blocks private/internal addresses, then builds `safe_url` with the resolved IP.
- `_fetch_request` sends `target.safe_url` and optionally adds a `Host` header.
- `packages/hephaion/test/test_tools.py` covers validation, SSRF blocking, content type checks,
  and redirects, but mocks `_open_without_redirect` and does not assert HTTPS host identity.

## Commands You Will Need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Focused tests | `rtk uv run pytest packages/hephaion/test/test_tools.py -q --no-cov` | all pass |
| Security scan | `rtk uv run bandit -q -c pyproject.toml packages/hephaion/src/hephaion/agent/web_tools.py` | exit 0 or only accepted existing warnings |
| Policy | `rtk uv run python -m scripts.check_repo_policies` | exit 0 |

## Scope

**In scope**
- `packages/hephaion/src/hephaion/agent/web_tools.py`
- `packages/hephaion/test/test_tools.py`

**Out of scope**
- Adding a broad browser or HTTP client dependency.
- Weakening private/internal IP blocking.
- Allowing redirects to bypass host validation.

## Steps

1. Replace IP-in-URL HTTPS behavior with a small connection/opening path that connects to the
   validated IP while preserving the original hostname for TLS SNI and certificate verification.
   HTTP may continue using a `Host` header with the validated IP connection target.
2. Keep redirect validation exactly as strict as the initial URL validation.
3. Add regression tests that inspect the constructed HTTPS connection/request behavior without
   making real network calls.
4. Run focused tests, bandit for the changed module, and policy checks.

## Done Criteria

- [x] HTTPS fetches preserve the original hostname for TLS identity.
- [x] Initial and redirected hosts are still resolved and blocked when any resolved IP is not global.
- [x] Focused tests pass and include HTTPS host-identity coverage.

## STOP Conditions

- The fix requires disabling TLS certificate verification.
- The fix requires accepting DNS rebinding between validation and connection without an explicit
  reviewer decision.

## Maintenance Notes

Reviewers should scrutinize this change for SSRF regressions first, then HTTPS compatibility.
