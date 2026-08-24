"""Small deterministic plans for grounded chat and material answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.chat.product_context import product_context as heph_product_context
from harness.documents.state import DocumentAction

_SAME_LANGUAGE_RULE = (
    "- Answer in the same language as the user's request when clear; preserve source terms.\n"
)
_OVERVIEW_RULES = (
    "- Write 1-2 short cited sentences in the user's language, or the requested table/list.",
    "- Honor requested shape exactly; tables need meaningful headers and a markdown separator.",
    "- State only topics, methods, examples, tasks, or problem types visible in the excerpts.",
    "- Cite factual claims next to their support; omit unsupported specifics.",
    "- Do not add unsolicited menus, plans, or next-step questions.",
)
_SOURCE_RULES = (
    "- Use only retrieved armory material for factual claims.",
    "- Cite evidence IDs whenever you state a source-backed claim.",
    "- If the evidence does not answer the request, say so plainly.",
)


@dataclass(frozen=True, slots=True)
class DocumentTurnPlan:
    action: DocumentAction
    prompt: str
    phase: Any = None  # retained only for loading older session/test payloads
    original_user_input: str = ""
    retrieval_query: str | None = None
    retrieval_strategy: str = ""
    evidence_refs: tuple[str, ...] = ()
    requires_direct_evidence: bool = False
    use_expected_source_refs: bool = False
    uses_overview_sampling: bool = False
    allow_tools: bool = True
    allowed_tool_names: tuple[str, ...] | None = None
    buffer_response: bool = False


def _prompt_frame(execute_line: str, *context_lines: str, rules: tuple[str, ...]) -> str:
    lines = [execute_line, *[line for line in context_lines if line]]
    return "\n".join([*lines, "Rules:", *rules]).strip()


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def material_overview_plan(user_request: str, *, retrieval_query: str | None = None) -> DocumentTurnPlan:
    return DocumentTurnPlan(
        action=DocumentAction.PRESENT,
        prompt=_prompt_frame(
            "Execute MATERIAL_OVERVIEW.",
            f"User request: {user_request}",
            rules=(_SAME_LANGUAGE_RULE, *_OVERVIEW_RULES),
        ),
        original_user_input=user_request,
        retrieval_query=retrieval_query or _normalize(user_request) or None,
        retrieval_strategy="overview",
        uses_overview_sampling=True,
        buffer_response=True,
    )


def material_topic_presentation_plan(user_request: str, *, retrieval_query: str) -> DocumentTurnPlan:
    query = _normalize(retrieval_query) or _normalize(user_request)
    return DocumentTurnPlan(
        action=DocumentAction.PRESENT,
        prompt=_prompt_frame(
            "Answer from the retrieved material.",
            f"User request: {user_request}",
            f"Material query: {query}",
            rules=(_SAME_LANGUAGE_RULE, *_SOURCE_RULES),
        ),
        original_user_input=user_request,
        retrieval_query=query,
        retrieval_strategy="retrieve",
        allow_tools=True,
        allowed_tool_names=("search_materials", "open_material"),
    )


def material_source_qa_plan(user_request: str, *, retrieval_query: str) -> DocumentTurnPlan:
    query = _normalize(retrieval_query) or _normalize(user_request)
    return DocumentTurnPlan(
        action=DocumentAction.SOURCE_QA,
        prompt=_prompt_frame(
            "Answer the source question.",
            f"User request: {user_request}",
            f"Material query: {query}",
            rules=(_SAME_LANGUAGE_RULE, *_SOURCE_RULES),
        ),
        original_user_input=user_request,
        retrieval_query=query,
        retrieval_strategy="retrieve",
        requires_direct_evidence=True,
        allow_tools=True,
        allowed_tool_names=("search_materials", "open_material"),
    )


def plain_chat_plan(user_request: str) -> DocumentTurnPlan:
    return DocumentTurnPlan(
        action=DocumentAction.CHAT,
        prompt=_prompt_frame(
            "Answer the user's request directly.",
            f"User request: {user_request}",
            rules=(heph_product_context(), "- Do not invent local material evidence."),
        ),
        original_user_input=user_request,
        allow_tools=True,
    )


def heph_help_plan(user_request: str) -> DocumentTurnPlan:
    return DocumentTurnPlan(
        action=DocumentAction.CHAT,
        prompt=_prompt_frame(
            "Execute HEPH_HELP.",
            f"User request: {user_request}",
            rules=(heph_product_context(),),
        ),
        original_user_input=user_request,
        allow_tools=False,
    )


def heph_action_plan(user_request: str) -> DocumentTurnPlan:
    return DocumentTurnPlan(
        action=DocumentAction.CHAT,
        prompt=_prompt_frame(
            "Execute HEPH_ACTION.",
            f"User request: {user_request}",
            rules=(heph_product_context(),),
        ),
        original_user_input=user_request,
        retrieval_strategy="none",
        allow_tools=True,
        allowed_tool_names=("create_named_armory", "import_materials", "validate_armory", "list_files"),
    )


def _open_material_plan_for_intent(user_request: str, intent: str) -> DocumentTurnPlan:
    query = _normalize(user_request)
    if intent == "source_qa":
        return material_source_qa_plan(user_request, retrieval_query=query)
    if intent == "material_overview":
        return material_overview_plan(user_request, retrieval_query=query)
    return material_topic_presentation_plan(user_request, retrieval_query=query)
