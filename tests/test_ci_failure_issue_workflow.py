from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci-failure-issue.yml"


def test_ci_failure_issue_workflow_ignores_stale_main_runs() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    current_sha_lookup = (
        "CURRENT_MAIN_SHA=$(gh api \"repos/$REPO/git/ref/heads/main\" --jq '.object.sha'"
    )
    missing_sha_guard = 'if [ -z "$CURRENT_MAIN_SHA" ]; then'
    stale_sha_guard = 'if [ "$SHA" != "$CURRENT_MAIN_SHA" ]; then'
    failure_branch = 'if [ "$CONCLUSION" = "failure" ]; then'
    success_branch = 'elif [ "$CONCLUSION" = "success" ]; then'

    assert current_sha_lookup in text
    assert missing_sha_guard in text
    assert stale_sha_guard in text
    assert (
        text.index(current_sha_lookup)
        < text.index(missing_sha_guard)
        < text.index(stale_sha_guard)
        < text.index(failure_branch)
        < text.index(success_branch)
    )
