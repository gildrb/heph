"""Milestone tracking for study priorities and exam sessions."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from hephaistos._types import is_string_mapping
from hephaistos.study.exam_session import (
    EXAM_SESSION_ACTIVE,
    EXAM_SESSION_COMPLETED_STATUSES,
    EXAM_SESSION_CORRECT,
    EXAM_SESSION_PARTIAL,
    EXAM_SESSION_WRONG,
    ExamSession,
)
from hephaistos.study.priority import PriorityAnalysis

MILESTONE_NOT_STARTED = "not_started"
MILESTONE_IN_PROGRESS = "in_progress"
MILESTONE_PASSED = "passed"
MILESTONE_FAILED = "failed"
_MILESTONE_STATUSES = frozenset(
    {MILESTONE_NOT_STARTED, MILESTONE_IN_PROGRESS, MILESTONE_PASSED, MILESTONE_FAILED}
)


@dataclass(slots=True)
class Milestone:
    """A visible progress item in the right-hand study sidebar."""

    name: str
    status: str = MILESTONE_NOT_STARTED
    subtasks: list[str] = field(default_factory=list)
    progress: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "subtasks": list(self.subtasks),
            "progress": self.progress,
        }

    @classmethod
    def from_dict(cls, data: object) -> Milestone | None:
        if not is_string_mapping(data):
            return None
        raw_name = data.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            return None
        raw_status = data.get("status")
        status = raw_status if isinstance(raw_status, str) else MILESTONE_NOT_STARTED
        if status not in _MILESTONE_STATUSES:
            status = MILESTONE_NOT_STARTED
        raw_subtasks = data.get("subtasks")
        subtasks = (
            [item for item in raw_subtasks if isinstance(item, str)]
            if isinstance(raw_subtasks, list)
            else []
        )
        raw_progress = data.get("progress")
        progress = raw_progress if isinstance(raw_progress, float | int) else 0.0
        return cls(
            name=raw_name,
            status=status,
            subtasks=subtasks,
            progress=_clamp_progress(float(progress)),
        )


@dataclass(slots=True)
class MilestoneTracker:
    """Persistent milestone list for priority and autopilot sessions."""

    milestones: list[Milestone] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"milestones": [milestone.to_dict() for milestone in self.milestones]}

    @classmethod
    def from_dict(cls, data: object) -> MilestoneTracker | None:
        if not is_string_mapping(data):
            return None
        raw_milestones = data.get("milestones")
        milestones: list[Milestone] = []
        if isinstance(raw_milestones, list):
            for raw_milestone in raw_milestones:
                milestone = Milestone.from_dict(raw_milestone)
                if milestone is not None:
                    milestones.append(milestone)
        return cls(milestones=milestones)

    def update_for_assessment(self, topic: str, status: str) -> MilestoneTracker:
        """Return a copy with the milestone matching the assessed topic updated."""
        index = _matching_milestone_index(self.milestones, topic)
        if index is None:
            return self
        milestones = [
            replace(milestone, subtasks=list(milestone.subtasks)) for milestone in self.milestones
        ]
        milestone = milestones[index]
        if status == MILESTONE_PASSED:
            milestone.status = MILESTONE_PASSED
            milestone.progress = 1.0
        elif status == MILESTONE_FAILED:
            milestone.status = MILESTONE_FAILED
            milestone.progress = max(milestone.progress, 0.25)
        else:
            milestone.status = MILESTONE_IN_PROGRESS
            milestone.progress = max(milestone.progress, 0.5)
        return MilestoneTracker(milestones=milestones)


def milestones_from_priority(analysis: PriorityAnalysis) -> list[Milestone]:
    """Convert deterministic priority topics into visible milestones."""
    milestones: list[Milestone] = []
    for topic in analysis.topics:
        subtasks = list(topic.prerequisites[:3])
        if not subtasks:
            subtasks = list(topic.sources[:3])
        milestones.append(
            Milestone(
                name=topic.topic,
                status=MILESTONE_NOT_STARTED,
                subtasks=subtasks,
                progress=0.0,
            )
        )
    return milestones


def milestones_from_exam_session(session: ExamSession) -> list[Milestone]:
    """Convert exam-session questions into milestone rows."""
    milestones: list[Milestone] = []
    for index, item in enumerate(session.items, start=1):
        status = _milestone_status_from_exam_item(item.status)
        progress = _milestone_progress_from_exam_item(item.status)
        subtasks = [item.source_ref]
        if item.marks is not None:
            subtasks.append(f"{item.marks} mark(s)")
        milestones.append(
            Milestone(
                name=f"Q{index}: {_short_question(item.question)}",
                status=status,
                subtasks=subtasks,
                progress=progress,
            )
        )
    return milestones


def _milestone_status_from_exam_item(status: str) -> str:
    if status == EXAM_SESSION_CORRECT:
        return MILESTONE_PASSED
    if status == EXAM_SESSION_WRONG:
        return MILESTONE_FAILED
    if status in {EXAM_SESSION_ACTIVE, EXAM_SESSION_PARTIAL}:
        return MILESTONE_IN_PROGRESS
    return MILESTONE_NOT_STARTED


def _milestone_progress_from_exam_item(status: str) -> float:
    if status == EXAM_SESSION_CORRECT:
        return 1.0
    if status in EXAM_SESSION_COMPLETED_STATUSES:
        return 0.5
    if status == EXAM_SESSION_ACTIVE:
        return 0.25
    return 0.0


def _matching_milestone_index(milestones: list[Milestone], topic: str) -> int | None:
    normalized_topic = topic.casefold()
    for index, milestone in enumerate(milestones):
        normalized_name = milestone.name.casefold()
        if normalized_name in normalized_topic or normalized_topic in normalized_name:
            return index
    return None


def _short_question(question: str, *, width: int = 36) -> str:
    clean = " ".join(question.split())
    if len(clean) <= width:
        return clean
    return f"{clean[: width - 1]}…"


def _clamp_progress(value: float) -> float:
    return min(1.0, max(0.0, value))
