from __future__ import annotations

from .automations import (
    DailyRepoMaintainAutomation,
    GitCommitTrackerAutomation,
    GitHubRepoCountAutomation,
    ObsidianMarkdownCountAutomation,
    ObsidianEditTrackerAutomation,
    ObsidianEssayToWebsiteAutomation,
    PublishPortfolioFromObsAutomation,
    RandomArtAutomation,
    UneditedKindleNotesAutomation,
    WallpaperFromReportAutomation,
    WeeklyCommitTrackerAutomation,
    WeeklyFocusAutomation,
)
from .automations.base import Automation


def load_automations() -> list[Automation]:
    return [
        DailyRepoMaintainAutomation(),
        GitCommitTrackerAutomation(),
        GitHubRepoCountAutomation(),
        ObsidianMarkdownCountAutomation(),
        ObsidianEditTrackerAutomation(),
        ObsidianEssayToWebsiteAutomation(),
        PublishPortfolioFromObsAutomation(),
        RandomArtAutomation(),
        UneditedKindleNotesAutomation(),
        WallpaperFromReportAutomation(),
        WeeklyCommitTrackerAutomation(),
        WeeklyFocusAutomation(),
    ]
