---
name: qa
description: >
  Run QA tests for Hephaistos. Analyzes git diff to determine affected areas,
  runs configured test flows with multiple personas, and generates diff-targeted tests.
  Uses tuistory for interactive TUI testing of the CLI.
  Use when testing PRs, releases, or smoke testing environments.
---

# QA Orchestrator

**SCOPE: This skill performs manual/functional QA only -- verifying that the application actually works by interacting with it as a real user would (TUI interactions, keystrokes, output verification). Do NOT run or report on CI checks, linting, ruff, basedpyright, pytest, unit tests, or any static analysis. Those are handled by separate workflows.**

## Step 1: Load Configuration

Read `.factory/skills/qa/config.yaml` for environment URLs, credentials, personas, and app definitions.

## Step 2: Determine Target Environment

This is a local CLI tool. There is no remote environment. QA always runs against the local checkout.

## Step 3: Analyze Git Diff

Run `git diff` to determine what changed. Map changed files to apps using the path_patterns in config.yaml.

This project has a SINGLE app (the CLI/TUI). If ANY file under `hephaistos/**` or `tests/**` changed, the CLI app IS affected and the FULL regression suite MUST run.

Files that don't match ANY app's path_patterns (e.g., `.factory/skills/**`, `docs/**`, `.github/**`, `scripts/**`) are NOT associated with any app. However, since this is a single-app project, even docs-only changes can benefit from a regression check. Use judgment:

- If `hephaistos/**` or `tests/**` changed: run the FULL regression suite (all 40 flows)
- If ONLY docs/CI/config changed: report INCONCLUSIVE ("No app code changed") but still run Flows 1-4 (launch, /status, /help, autocomplete) as a quick smoke test to verify the app still starts

## Step 4: Pre-flight Checks

Always run pre-flight checks when app code is affected:

- **CLI binary**: Run `uv sync --frozen` to ensure dependencies are installed
- **Test armory**: Create the test armory with source files (see qa-cli SKILL.md "Pre-test Setup")
- **API key**: Verify `ZAI_API_KEY` is available in the environment
- **tuistory**: Verify tuistory is available (`npm install -g tuistory` if needed)

If a pre-flight check fails, report it as BLOCKED with the specific error and remediation steps -- but still proceed with other flows that don't depend on the failed check.

## Step 5: Execute Full Regression Suite

Read the sub-skill from `.factory/skills/qa-cli/SKILL.md`.

The sub-skill contains a full regression test suite with 40 flows covering every slash command in the application. Execute ALL 40 flows in sequence as documented.

Additionally:

1. Read the diff carefully to identify any NEW or CHANGED features not covered by existing flows
2. If the diff adds a new slash command, write an ADDITIONAL ad-hoc test flow for it
3. If the diff changes the behavior of an existing command, pay extra attention to that flow and add targeted assertions
4. Do NOT skip flows just because they seem unrelated to the diff -- run the full suite every time to catch regressions
5. Do NOT run unit tests, lint, typecheck, or any automated test suite. This is manual/functional QA only.

## Step 6: Evidence Capture

After each significant test step, capture evidence. Use **text snapshots as primary evidence**.

For CLI/TUI apps (tuistory):

- Use the `tuistory` skill for all TUI interactions
- Capture terminal snapshots via `tuistory snapshot` as text evidence
- Embed the snapshot directly in the report as a fenced code block with a descriptive label
- Each snapshot MUST show something DIFFERENT. Wait for the UI to change before capturing again.

Evidence quality rules:

- Focus on the RELEVANT content. Trim snapshots to the meaningful part.
- Label each snapshot clearly: what it shows and why it matters for the test.
- NEVER embed broken image links.

## Step 7: Test Quality Gate

TEST QUALITY REQUIREMENTS:

1. FULL REGRESSION. Run ALL 40 flows in the qa-cli sub-skill. Do not skip flows.
2. DIFF-TARGETED EXTRA. After the regression suite, add ad-hoc tests for any new/changed features in the diff that aren't covered by existing flows.
3. NO AUTOMATED TEST SUITES. Do NOT run pytest, ruff, basedpyright, or any CI-style checks. This is manual/functional QA only.
4. NEGATIVE TESTS. Flow 39 covers error handling -- ensure it passes (invalid commands produce user-friendly errors, never crashes).
5. INTERACTIVE TESTING. Test by actually interacting with the TUI as a real user would. Every slash command must be exercised.
6. INCONCLUSIVE IF UNSURE. If you cannot articulate what the PR changes, still run the full regression but mark the diff analysis as INCONCLUSIVE.

## Step 8: Handle Failures

**Never silently skip a flow.** If a flow cannot complete, report it as BLOCKED with what was tried and how the user can fix it. Then continue to the next flow -- never abort the entire run for a single failure.

## Step 9: Generate Report

Generate the report at `./qa-results/report.md` using `.factory/skills/qa/REPORT-TEMPLATE.md`.

The report MUST follow the template. Key rules:

- Start with `## QA Report` heading followed by the test results table
- Result column MUST use emojis: :white_check_mark: PASS, :x: FAIL, :no_entry: BLOCKED, :warning: FLAKY, :grey_question: INCONCLUSIVE
- Keep it CONCISE. The table + a short "Action Required" section (if any) + collapsed snapshots = the entire report.
- Do NOT include: "Behavioral Change Summary", "Blocked Flows" prose, "Info" metadata table, or verbose explanations of what the diff does. The reviewer already knows that.
- Do NOT report setup/prerequisite steps (building, startup, launching) as test rows. Those are means to an end, not test cases. Only report rows that verify actual user-facing behavior or the specific behavioral change from the diff.
- Put ALL evidence in a single collapsed `<details>` block
- For TUI evidence: embed text snapshots as labeled fenced code blocks.

## Step 10: Suggest Skill Updates (Failure Learning)

After generating the report, check if any BLOCKED or FAIL results revealed a **testing environment insight** that would help future QA runs succeed. This is about learning how the testing environment works, NOT about fixing bad selectors or skill typos.

Format as a table with severity, collapsible fix prompts, and a count in the heading:

## Suggested Skill Updates (N issues found)

| #   | Severity        | File     | Issue               | Fix Prompt                                                                           |
| --- | --------------- | -------- | ------------------- | ------------------------------------------------------------------------------------ |
| 1   | <emoji> <level> | `<file>` | <short description> | <details><summary>Copy</summary><br>`<full droid prompt to fix the issue>`</details> |

**Severity levels:**

- :red_circle: Breaking -- Causes test failures every run
- :yellow_circle: Degraded -- Causes intermittent failures or suboptimal behavior
- :large_blue_circle: Info -- New knowledge that improves future runs

Read the `failure_learning` field from config.yaml. Current setting: `suggest_in_report` -- include the table in the PR comment report only. Do NOT write `skill-updates.json`.

Do NOT suggest updates for failures already covered in Known Failure Modes, bad selectors, or expected behavior changes from the PR. If no genuinely new environment insights were discovered, omit this section entirely.
