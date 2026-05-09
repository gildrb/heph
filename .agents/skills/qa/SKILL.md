---
name: qa
description: >
  Run manual/functional QA for Hephaistos. Analyzes git diff, runs the current
  CLI/TUI regression matrix with tuistory, validates chat/RAG with available
  subscription auth, and writes a concise QA report.
---

# QA Orchestrator

**SCOPE: This skill performs manual/functional QA only -- verifying that the application actually works by interacting with it as a real user would (TUI interactions, keystrokes, output verification). Do NOT run or report on CI checks, linting, ruff, ty, pytest, unit tests, or any static analysis. Those are handled by separate workflows.**

## Step 1: Load Configuration

Read `.agents/skills/qa/config.yaml` for environment URLs, credentials, personas, integrations, cleanup rules, and app definitions.

## Step 2: Determine Target Environment

This is a local CLI tool. There is no remote environment. QA always runs against the local checkout.

## Step 3: Analyze Git Diff

Run `git diff` to determine what changed. Map changed files to apps using the path_patterns in config.yaml.

This project has a SINGLE app (the CLI/TUI). If ANY file under `hephaistos/**` or `tests/**` changed, the CLI app IS affected and the FULL current regression matrix in `.agents/skills/qa-cli/SKILL.md` MUST run.

Files that don't match ANY app's path_patterns (e.g., `.agents/skills/**`, `docs/**`, `.github/**`, `scripts/**`) are NOT associated with any app. However, since this is a single-app project, even docs-only changes can benefit from a regression check. Use judgment:

- If `hephaistos/**` or `tests/**` changed: run the FULL current regression matrix from the qa-cli skill.
- If ONLY docs/CI/config changed: report INCONCLUSIVE ("No app code changed") but still run the first-time launch, `/status`, `/help`, autocomplete, and one armory launch smoke test.

## Step 4: Pre-flight Checks

Always run pre-flight checks when app code is affected:

- **CLI binary**: Run `uv sync --frozen` to ensure dependencies are installed.
- **tuistory**: Verify tuistory is available (`tuistory --version`; install with `npm install -g tuistory` only if missing).
- **Test armory**: Create a named QA armory under `~/.armories/<qa-run-id>` and write study files into `materials/` (see qa-cli "Pre-test Setup"). Armories cannot be initialized under `/tmp`.
- **LLM auth for chat/RAG**: Prefer Hephaistos OpenAI Codex/ChatGPT auth. Do not print tokens or raw secrets. Check availability in this order:
  1. Existing Hephaistos OpenAI Codex OAuth (`~/.config/hephaistos/auth.json` may contain an `openai-codex` entry; inspect only provider names/presence, never token values).
  2. `OPENAI_API_KEY` or `HEPHAISTOS_API_KEY` if already present in the environment.
  3. `OPENROUTER_API_KEY` if already present.
  4. Interactive `/login` -> `OpenAI Codex` in the TUI. If browser/user action is required, pause and ask the user to complete it.
  5. Pollinations keyless provider may be used only for non-critical smoke chat when subscription auth is unavailable; do not count it as sufficient for full chat/RAG coverage if it is unstable or rate-limited.

If a pre-flight check fails, report it as BLOCKED with the specific error and remediation steps -- but still proceed with other flows that don't depend on the failed check.

## Step 5: Execute Full Regression Matrix

Read `.agents/skills/qa-cli/SKILL.md` and execute every flow in the current regression matrix in sequence. The matrix is intentionally aligned with the live command surface from `/help`; do not resurrect removed commands such as `/provider`, `/model`, `/history`, `/clear`, `/resume`, or `/chats` unless they are reintroduced in the app.

Additionally:

1. Read the diff carefully to identify any NEW or CHANGED features not covered by existing flows.
2. If the diff adds a new slash command, write an ADDITIONAL ad-hoc manual flow for it.
3. If the diff changes the behavior of an existing command, pay extra attention to that flow and add targeted assertions.
4. Do NOT skip flows just because they seem unrelated to the diff -- run the full current matrix every time to catch regressions.
5. Do NOT run unit tests, lint, typecheck, or any automated test suite. This is manual/functional QA only.

## Step 6: TUI Interaction Discipline

Use tuistory for all TUI interactions. Avoid false failures caused by stale input state:

- Use separate tuistory sessions for first-time/plain-chat, armory/RAG, and terminal-interactive flows when practical.
- After every command, wait for relevant text or a visible UI state change before snapshotting.
- Ensure the composer is empty before typing the next command. If uncertain, press `Esc`, then `Ctrl+U` if supported, or restart a fresh tuistory session.
- After autocomplete or inline menus, press `Esc` until the normal composer returns before continuing.
- For terminal-interactive commands (`/edit`, `/persona` without args, `/vocab` drill), complete or cancel the prompt before sending another slash command.
- Never batch many keystrokes without intermediate snapshots and state checks.

## Step 7: Evidence Capture

After each significant test step, capture evidence. Use **text snapshots as primary evidence**.

For CLI/TUI apps (tuistory):

- Capture terminal snapshots via `tuistory snapshot --trim --no-cursor` as text evidence.
- Embed snapshots directly in the report as fenced code blocks with descriptive labels.
- Each snapshot MUST show something DIFFERENT. Wait for the UI to change before capturing again.

Evidence quality rules:

- Focus on the RELEVANT content. Trim snapshots to the meaningful part.
- Label each snapshot clearly: what it shows and why it matters for the test.
- NEVER embed broken image links.
- Never include raw API keys, access tokens, refresh tokens, or credential file contents.

## Step 8: Test Quality Gate

TEST QUALITY REQUIREMENTS:

1. FULL REGRESSION. Run every current flow in the qa-cli skill. Do not skip flows.
2. DIFF-TARGETED EXTRA. After the regression matrix, add ad-hoc tests for any new/changed features in the diff that aren't covered by existing flows.
3. NO AUTOMATED TEST SUITES. Do NOT run pytest, ruff, ty, or any CI-style checks. This is manual/functional QA only.
4. NEGATIVE TESTS. Invalid commands and invalid subcommands must produce user-friendly errors and never Python tracebacks.
5. INTERACTIVE TESTING. Test by actually interacting with the TUI as a real user would. Every current slash command must be exercised directly or via its current inline flow.
6. CHAT/RAG PRIORITY. Full QA is BLOCKED, not PASS, if subscription-backed chat/RAG cannot be exercised. Ask the user to complete `/login` rather than silently falling back to Z.AI or skipping RAG.
7. INCONCLUSIVE IF UNSURE. If you cannot articulate what the PR changes, still run the full current matrix but mark the diff analysis as INCONCLUSIVE.

## Step 9: Handle Failures

**Never silently skip a flow.** If a flow cannot complete, report it as BLOCKED with what was tried and how the user can fix it. Then continue to the next flow -- never abort the entire run for a single failure.

## Step 10: Generate Report

Generate the report at `./qa-results/report.md` using `.agents/skills/qa/REPORT-TEMPLATE.md`.

The report MUST follow the template. Key rules:

- Start with `## QA Report` heading followed by the test results table.
- Result column MUST use emojis: :white_check_mark: PASS, :x: FAIL, :no_entry: BLOCKED, :warning: FLAKY, :grey_question: INCONCLUSIVE.
- Keep it CONCISE. The table + a short "Action Required" section (if any) + collapsed snapshots = the entire report.
- Do NOT include: "Behavioral Change Summary", "Blocked Flows" prose, "Info" metadata table, or verbose explanations of what the diff does. The reviewer already knows that.
- Do NOT report setup/prerequisite steps (building, startup, launching) as test rows. Those are means to an end, not test cases. Only report rows that verify actual user-facing behavior or the specific behavioral change from the diff.
- Put ALL evidence in a single collapsed `<details>` block.
- For TUI evidence: embed text snapshots as labeled fenced code blocks.

## Step 11: Suggested Skill Updates (Failure Learning)

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
