"""Fail when architecture debt grows beyond the current refactor baseline."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

from radon.complexity import cc_visit

ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "packages" / "harness" / "src" / "harness"

MODULE_LINE_THRESHOLD = 1_200
CLASS_LINE_THRESHOLD = 500
FUNCTION_LINE_THRESHOLD = 80
COMPLEXITY_THRESHOLD = 11
SUPPORT_FACADE_MODULES = {"_types", "version"}

MODULE_LINE_BASELINE: dict[str, int] = {}

CLASS_LINE_BASELINE = {
    "rag/index.py:ArmoryIndex": 628,
}

FUNCTION_LINE_BASELINE = {
    "agent/dispatch.py:_tool_turn_events": 96,
    "agent/dispatch.py:iter_agent_events": 109,
    "chat/intent_resolution.py:_stabilized_followup_intent_resolution": 119,
    "chat/turn_planning.py:_apply_turn_contract_to_plan": 197,
    "chat/turn_planning.py:_stabilized_followup_retrieval": 114,
    "rag/retrieve.py:retrieve": 111,
}

COMPLEXITY_BASELINE = {
    "agent/dispatch.py:iter_agent_events": 11,
    "chat/evidence.py:_expanded_prior_query_evidence": 11,
    "chat/intent_resolution.py:_stabilized_followup_intent_resolution": 33,
    "chat/intent_resolution.py:_stabilized_intent_for_default_material_plan": 14,
    "chat/intent_resolution.py:_transform_resolution_points_at_prior_answer": 11,
    "chat/document_reply.py:_deterministic_document_reply": 13,
    "chat/overview_reply.py:_overview_answer_has_bad_shape": 26,
    "chat/overview_reply.py:_overview_cue_looks_like_byline": 12,
    "chat/overview_reply.py:_overview_fallback_cue_is_substantive": 11,
    "chat/overview_reply.py:_overview_heading_is_sparse_title_block": 13,
    "chat/overview_reply.py:_overview_lead_prefix_within_budget": 16,
    "chat/overview_reply.py:_overview_model_fallback_candidates": 12,
    "chat/overview_reply.py:_overview_pipe_table_line_rows": 11,
    "chat/prior_answer.py:_prior_answer_position_absence_reply": 15,
    "chat/prior_answer.py:_prior_answer_prompt_context": 12,
    "chat/prior_answer.py:_prior_answer_single_citation_reply": 13,
    "chat/prior_answer.py:_prior_answer_target_phrase_reply": 11,
    "chat/reply_repair.py:_deterministic_evidence_pointer_repair": 11,
    "chat/reply_repair.py:_evidence_output_needs_model_repair": 11,
    "chat/reply_repair.py:_repair_structurally_invalid_evidence_output": 13,
    "chat/turn_planning.py:_apply_turn_contract_to_plan": 50,
    "chat/turn_planning.py:_contract_with_default_material_scope": 15,
    "chat/turn_planning.py:_expanded_prior_followup_query": 11,
    "chat/turn_planning.py:_stabilized_current_topic_query": 13,
    "chat/turn_planning.py:_stabilized_followup_retrieval": 62,
    "documents/controller.py:_plan_recall_phase_intent": 14,
    "documents/controller.py:_plan_waiting_intent": 11,
}

FACADE_IMPORT_BASELINE = {
    "agent/compact.py": 1,
    "agent/dispatch.py": 2,
    "agent/material_tools.py": 1,
    "agent/model_stream.py": 1,
    "agent/prompt.py": 1,
    "agent/runtime_notes.py": 1,
    "agent/tool_execution.py": 1,
    "agent/tools.py": 1,
    "armory/search.py": 1,
    "chat/compaction.py": 1,
    "chat/evidence.py": 3,
    "chat/session.py": 6,
    "chat/storage.py": 1,
    "chat/titles.py": 1,
    "chat/turn_history.py": 3,
    "chat/usage.py": 1,
    "memory/extract.py": 2,
    "memory/workflow.py": 2,
    "parameters/cli.py": 2,
    "rag/hybrid.py": 1,
    "rag/index.py": 1,
    "rag/retrieve.py": 1,
    "rag/semantic.py": 1,
    "rag/sparse.py": 1,
    "documents/priority.py": 1,
    "vocab/parser.py": 1,
}


@dataclass(frozen=True, slots=True)
class Finding:
    key: str
    metric: str
    current: int
    baseline: int | None

    def render(self) -> str:
        if self.baseline is None:
            return f"{self.key}: new {self.metric} debt ({self.current})"
        return f"{self.key}: {self.metric} grew from {self.baseline} to {self.current}"


def python_files() -> list[Path]:
    return sorted(SOURCE_ROOT.rglob("*.py"))


def rel_path(path: Path) -> str:
    if path.is_relative_to(SOURCE_ROOT):
        return path.relative_to(SOURCE_ROOT).as_posix()
    return path.relative_to(ROOT).as_posix()


def node_length(node: ast.AST) -> int:
    lineno = getattr(node, "lineno", 0)
    end_lineno = getattr(node, "end_lineno", lineno)
    return end_lineno - lineno + 1


def parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def qualname(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    names = (
        [node.name]
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        else []
    )
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            names.append(parent.name)
        parent = parents.get(parent)
    return ".".join(reversed(names))


def package_names() -> set[str]:
    return {
        path.name
        for path in SOURCE_ROOT.iterdir()
        if (path / "__init__.py").exists() and path.name not in SUPPORT_FACADE_MODULES
    }


def facade_import_count(tree: ast.AST, packages: set[str]) -> int:
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            count += _facade_module_count(node.module, packages)
        elif isinstance(node, ast.Import):
            count += sum(_facade_module_count(alias.name, packages) for alias in node.names)
    return count


def _facade_module_count(module: str, packages: set[str]) -> int:
    parts = module.split(".")
    if len(parts) == 1 and parts[0] in packages:
        return 1
    return 0


def changed_baseline(
    *,
    key: str,
    metric: str,
    current: int,
    threshold: int,
    baseline: dict[str, int],
) -> Finding | None:
    if current < threshold:
        return None
    allowed = baseline.get(key)
    if allowed is None or current > allowed:
        return Finding(key=key, metric=metric, current=current, baseline=allowed)
    return None


def collect_size_findings(path: Path, tree: ast.AST) -> list[Finding]:
    rel = rel_path(path)
    findings: list[Finding] = []
    lines = len(path.read_text(encoding="utf-8").splitlines())
    finding = changed_baseline(
        key=rel,
        metric="module lines",
        current=lines,
        threshold=MODULE_LINE_THRESHOLD + 1,
        baseline=MODULE_LINE_BASELINE,
    )
    if finding is not None:
        findings.append(finding)
    findings.extend(collect_node_size_findings(rel, tree))
    return findings


def collect_node_size_findings(rel: str, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []
    parents = parent_map(tree)
    for node in ast.walk(tree):
        key = f"{rel}:{qualname(node, parents)}"
        if isinstance(node, ast.ClassDef):
            finding = changed_baseline(
                key=key,
                metric="class lines",
                current=node_length(node),
                threshold=CLASS_LINE_THRESHOLD + 1,
                baseline=CLASS_LINE_BASELINE,
            )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            finding = changed_baseline(
                key=key,
                metric="function lines",
                current=node_length(node),
                threshold=FUNCTION_LINE_THRESHOLD + 1,
                baseline=FUNCTION_LINE_BASELINE,
            )
        else:
            finding = None
        if finding is not None:
            findings.append(finding)
    return findings


def collect_complexity_findings(path: Path) -> list[Finding]:
    rel = rel_path(path)
    findings: list[Finding] = []
    for block in cc_visit(path.read_text(encoding="utf-8")):
        key = f"{rel}:{block.fullname}"
        finding = changed_baseline(
            key=key,
            metric="cyclomatic complexity",
            current=block.complexity,
            threshold=COMPLEXITY_THRESHOLD,
            baseline=COMPLEXITY_BASELINE,
        )
        if finding is not None:
            findings.append(finding)
    return findings


def collect_facade_import_findings(path: Path, tree: ast.AST, packages: set[str]) -> list[Finding]:
    rel = rel_path(path)
    count = facade_import_count(tree, packages)
    if count == 0:
        return []
    allowed = FACADE_IMPORT_BASELINE.get(rel)
    if allowed is None or count > allowed:
        return [
            Finding(
                key=rel,
                metric="package-facade imports",
                current=count,
                baseline=allowed,
            )
        ]
    return []


def collect_findings() -> list[Finding]:
    packages = package_names()
    findings: list[Finding] = []
    for path in python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        findings.extend(collect_size_findings(path, tree))
        findings.extend(collect_complexity_findings(path))
        findings.extend(collect_facade_import_findings(path, tree, packages))
    return findings


def main() -> None:
    findings = collect_findings()
    if not findings:
        return
    print("Architecture guardrail regressions:")
    for finding in findings:
        print(f"  {finding.render()}")
    sys.exit(1)


if __name__ == "__main__":
    main()
