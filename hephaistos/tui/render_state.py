from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class DirtyRegion(StrEnum):
    STATUS = "status"
    TRANSCRIPT = "transcript"
    COMPOSER = "composer"
    COMPLETIONS = "completions"
    FOOTER = "footer"
    SIDE_PANEL = "side_panel"
    OVERLAY = "overlay"
    THINKING = "thinking"


@dataclass(slots=True)
class TuiRenderCache:
    snapshots: dict[DirtyRegion, str] = field(default_factory=dict)
    dirty_regions: set[DirtyRegion] = field(default_factory=set)

    def mark(self, *regions: DirtyRegion) -> None:
        self.dirty_regions.update(regions)

    def should_update(self, region: DirtyRegion, snapshot: str) -> bool:
        previous = self.snapshots.get(region)
        if previous == snapshot and region not in self.dirty_regions:
            return False
        self.snapshots[region] = snapshot
        self.dirty_regions.discard(region)
        return True

    def forget(self, *regions: DirtyRegion) -> None:
        for region in regions:
            self.snapshots.pop(region, None)
            self.dirty_regions.add(region)
