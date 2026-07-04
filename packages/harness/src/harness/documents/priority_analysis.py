from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from harness.documents.priority_types import PriorityChunk, PriorityExamQuestion, PriorityTopic


@dataclass(frozen=True, slots=True)
class PriorityAnalysis:
    topics: tuple[PriorityTopic, ...]
    past_exam_sources: tuple[str, ...]
    material_sources: tuple[str, ...]
    chunks: tuple[PriorityChunk, ...] = ()
    exam_questions: tuple[PriorityExamQuestion, ...] = ()

    def render_for_prompt(self, *, limit: int = 6) -> str:
        return _render_priority_analysis_for_prompt(self, limit=limit)


def _render_priority_analysis_for_prompt(analysis: PriorityAnalysis, *, limit: int) -> str:
    if not analysis.topics:
        return "Local priority scan: no recurring indexed topics were found."

    lines = ["Local priority scan from indexed materials:"]
    lines.extend(_priority_source_summary_lines(analysis))
    lines.append("- Candidate priorities:")
    lines.extend(_priority_prompt_topic_line(topic) for topic in analysis.topics[:limit])
    return "\n".join(lines)


def _priority_source_summary_lines(analysis: PriorityAnalysis) -> Iterator[str]:
    if analysis.past_exam_sources:
        yield f"- Past exams scanned: {', '.join(analysis.past_exam_sources[:5])}"
    if analysis.material_sources:
        yield f"- Supporting materials scanned: {', '.join(analysis.material_sources[:5])}"


def _priority_prompt_topic_line(topic: PriorityTopic) -> str:
    return (
        f"  - {topic.topic}: {priority_tier(topic)}; "
        f"{_priority_prompt_exam_signal(topic)}; "
        f"sources: {', '.join(topic.sources[:3])}{_priority_prompt_prerequisites(topic)}"
    )


def _priority_prompt_exam_signal(topic: PriorityTopic) -> str:
    if topic.exam_marks:
        return f"{topic.exam_hits} exam hit(s), {topic.exam_marks} visible mark(s)"
    if topic.exam_hits:
        return f"{topic.exam_hits} exam hit(s), no explicit marks found"
    return "No past-exam hit found"


def _priority_prompt_prerequisites(topic: PriorityTopic) -> str:
    if topic.prerequisites:
        return f"; prerequisites to check: {', '.join(topic.prerequisites[:3])}"
    if topic.web_prerequisites:
        terms = ", ".join(item.term for item in topic.web_prerequisites[:3])
        return f"; web-backed prerequisite hints: {terms}"
    return ""


def priority_tier(topic: PriorityTopic) -> str:
    for predicate, tier in _PRIORITY_TIER_RULES:
        if predicate(topic):
            return tier
    return "Supporting"


def _exam_core_topic(topic: PriorityTopic) -> bool:
    return topic.exam_marks >= 12 or topic.exam_hits >= 3


def _high_yield_topic(topic: PriorityTopic) -> bool:
    return topic.exam_marks >= 6 or topic.exam_hits >= 2


def _foundation_topic(topic: PriorityTopic) -> bool:
    return bool(topic.exam_hits)


def _prerequisite_topic(topic: PriorityTopic) -> bool:
    return topic.supporting_material_coverage >= 2 or topic.material_hits >= 3


_PRIORITY_TIER_RULES: tuple[tuple[Callable[[PriorityTopic], bool], str], ...] = (
    (_exam_core_topic, "Exam core"),
    (_high_yield_topic, "High-yield"),
    (_foundation_topic, "Foundation"),
    (_prerequisite_topic, "Prerequisite"),
)
