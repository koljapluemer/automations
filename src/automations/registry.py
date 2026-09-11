from __future__ import annotations

from .automations import (
    GitCommitTrackerAutomation,
    ObsidianMarkdownCountAutomation,
    ObsidianEditTrackerAutomation,
    ProjectCommandCenterAutomation,
    RandomArtAutomation,
    UneditedKindleNotesAutomation,
    WallpaperFromReportAutomation,
)
from .automations.base import Automation


def load_automations() -> list[Automation]:
    return [
        GitCommitTrackerAutomation(),
        ObsidianMarkdownCountAutomation(),
        ObsidianEditTrackerAutomation(),
        ProjectCommandCenterAutomation(),
        RandomArtAutomation(),
        UneditedKindleNotesAutomation(),
        WallpaperFromReportAutomation(),
    ]
