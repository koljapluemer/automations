from __future__ import annotations

from .automations import (
    GitHubRepoCountAutomation,
    ObsidianMarkdownCountAutomation,
    PublishPortfolioFromObsAutomation,
    WallpaperFromReportAutomation,
)
from .automations.base import Automation


def load_automations() -> list[Automation]:
    return [
        GitHubRepoCountAutomation(),
        ObsidianMarkdownCountAutomation(),
        PublishPortfolioFromObsAutomation(),
        WallpaperFromReportAutomation(),
    ]
