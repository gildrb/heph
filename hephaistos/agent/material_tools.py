"""Handlers for study-material search tools used by the agent harness."""

from __future__ import annotations

from pathlib import Path

from hephaistos.agent.tool_schema import ToolResult
from hephaistos.rag import load_or_build, retrieve

_MAX_MATERIAL_TOOL_CHARS = 18_000


def run_search_materials(
    query: str,
    *,
    workspace: Path,
    top_k: int | None = None,
    **_kwargs: object,
) -> ToolResult:
    """Search the persisted armory material index."""
    if not query.strip():
        return ToolResult(success=False, content="Error: query is required.", error="empty_query")
    try:
        index = load_or_build(workspace)
    except Exception as exc:
        return ToolResult(
            success=False,
            content=f"Error preparing material index: {exc}",
            error="index_error",
        )
    if index.chunk_count <= 0:
        return ToolResult(
            success=False,
            content="No searchable material text is indexed for this armory.",
            metadata={"chunks": 0},
            error="empty_index",
        )

    limit = max(1, min(top_k or 8, 20))
    results = retrieve(query, index, top_k=limit)
    if not results:
        return ToolResult(
            success=True,
            content=f"No indexed material excerpts matched: {query}",
            metadata={"matches": 0, "chunks": index.chunk_count},
        )

    lines = [f"Material search results for: {query}"]
    metadata_items: list[dict[str, object]] = []
    for result_index, scored in enumerate(results, 1):
        chunk = scored.chunk
        heading = f" under {chunk.heading}" if chunk.heading else ""
        excerpt = _material_tool_excerpt(chunk.text)
        lines.extend(
            [
                "",
                f"[M{result_index}] {chunk.source}#chunk={chunk.index}{heading}",
                f"score: {scored.score:.3f}",
                excerpt,
            ]
        )
        metadata_items.append(
            {
                "id": f"M{result_index}",
                "source": chunk.source,
                "chunk": chunk.index,
                "score": scored.score,
                "heading": chunk.heading,
            }
        )

    return ToolResult(
        success=True,
        content=_trim_tool_content("\n".join(lines)),
        metadata={"matches": len(results), "items": metadata_items},
    )


def run_open_material(
    source: str,
    *,
    workspace: Path,
    chunk: int | None = None,
    context: int | None = None,
    **_kwargs: object,
) -> ToolResult:
    """Open a window of indexed material text."""
    source = source.strip()
    if not source:
        return ToolResult(
            success=False,
            content="Error: source is required.",
            error="empty_source",
        )
    try:
        index = load_or_build(workspace)
    except Exception as exc:
        return ToolResult(
            success=False,
            content=f"Error preparing material index: {exc}",
            error="index_error",
        )

    document = next((doc for doc in index.documents if doc.source == source), None)
    if document is None:
        available = ", ".join(doc.source for doc in index.documents[:8])
        suffix = "..." if len(index.documents) > 8 else ""
        return ToolResult(
            success=False,
            content=f"Indexed source not found: {source}. Available sources: {available}{suffix}",
            metadata={"sources": [doc.source for doc in index.documents]},
            error="source_not_found",
        )
    if not document.chunks:
        return ToolResult(
            success=False,
            content=f"Indexed source has no readable chunks: {source}",
            error="empty_source",
        )

    requested_chunk = chunk if chunk is not None and chunk >= 0 else 0
    center = min(requested_chunk, len(document.chunks) - 1)
    radius = max(0, min(context or 1, 5))
    start = max(0, center - radius)
    end = min(len(document.chunks), center + radius + 1)
    lines = [f"Opened indexed material: {source} chunks {start}-{end - 1}"]
    for material_chunk in document.chunks[start:end]:
        heading = f" under {material_chunk.heading}" if material_chunk.heading else ""
        lines.extend(
            [
                "",
                f"[{source}#chunk={material_chunk.index}{heading}]",
                material_chunk.text.strip(),
            ]
        )

    return ToolResult(
        success=True,
        content=_trim_tool_content("\n".join(lines)),
        metadata={"source": source, "start_chunk": start, "end_chunk": end - 1},
    )


def _material_tool_excerpt(text: str, *, limit: int = 900) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."


def _trim_tool_content(content: str) -> str:
    if len(content) <= _MAX_MATERIAL_TOOL_CHARS:
        return content
    return content[: _MAX_MATERIAL_TOOL_CHARS - 16].rstrip() + "\n... [truncated]"
