from __future__ import annotations

from .automations import (
    BlogDisplayAutomation,
    GitCommitTrackerAutomation,
    GraphirstStatsAutomation,
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
        BlogDisplayAutomation(),
        GitCommitTrackerAutomation(),
        GraphirstStatsAutomation(),
        ObsidianMarkdownCountAutomation(),
        ObsidianEditTrackerAutomation(),
        ProjectCommandCenterAutomation(),
        RandomArtAutomation(),
        UneditedKindleNotesAutomation(),
        WallpaperFromReportAutomation(),
    ]
