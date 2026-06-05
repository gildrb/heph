"""Small, deterministic retrieval audit helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

QUERY_AUDIT_SCHEMA_VERSION = "query-classification-v2"
QUERY_EXCERPT_LIMIT = 180

_QUERY_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./:-]*")
_QUOTED_QUERY_RE = re.compile(r'"[^"]+"|`[^`]+`')
_PATH_OR_REF_TOKEN_RE = re.compile(r"(?:[/\\#]|[.][A-Za-z0-9]{1,8}$)")
_MULTI_PART_QUERY_RE = re.compile("[;\n]|\\s[-\\u2013\\u2014]\\s")


@dataclass(frozen=True, slots=True)
class RetrievalAuditConfig:
    retrieval_mode: str
    transform_strategy: str
    top_k: int
    candidate_multiplier: int = 1
    repair_max_passes: int = 1
    rerank_requested: bool = False

    @property
    def candidate_budget(self) -> int:
        return self.top_k * max(1, self.candidate_multiplier)


def query_class(query: str) -> str:
    normalized = " ".join(query.split())
    if not normalized:
        return "empty"
    tokens = _QUERY_TOKEN_RE.findall(normalized)
    if _QUOTED_QUERY_RE.search(normalized):
        return "quoted"
    if any(_PATH_OR_REF_TOKEN_RE.search(token) for token in tokens):
        return "path_or_ref"
    if _MULTI_PART_QUERY_RE.search(normalized):
        return "multi_part"
    if len(tokens) <= 3:
        return "short"
    return "plain"


def transformed_query_count(transform_strategy: str) -> int:
    if transform_strategy == "identity":
        return 1
    if transform_strategy == "multi_query":
        return 4
    return 2


def retrieval_strategy_payload(config: RetrievalAuditConfig) -> dict[str, object]:
    return {
        "retrieval_mode": config.retrieval_mode,
        "transform_strategy": config.transform_strategy,
        "top_k": config.top_k,
        "candidate_multiplier": config.candidate_multiplier,
        "candidate_budget": config.candidate_budget,
        "repair_max_passes": config.repair_max_passes,
        "rerank_requested": config.rerank_requested,
    }


def query_classification_payload(
    query: str,
    config: RetrievalAuditConfig,
) -> dict[str, object]:
    return {
        "schema_version": QUERY_AUDIT_SCHEMA_VERSION,
        "query_class": query_class(query),
        "decision_basis": "query-shape-and-fixed-retrieval-parameters",
        "fallback": {"used": False, "reason": None},
        "transformed_query_count": transformed_query_count(config.transform_strategy),
        "retrieval_strategy": retrieval_strategy_payload(config),
    }


def query_excerpt(query: str | None, *, limit: int = QUERY_EXCERPT_LIMIT) -> str:
    if query is None:
        return ""
    normalized = " ".join(query.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."


__all__ = [
    "QUERY_AUDIT_SCHEMA_VERSION",
    "QUERY_EXCERPT_LIMIT",
    "RetrievalAuditConfig",
    "query_class",
    "query_classification_payload",
    "query_excerpt",
    "retrieval_strategy_payload",
    "transformed_query_count",
]
