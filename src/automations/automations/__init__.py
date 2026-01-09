from .base import Automation
from .git_commit_tracker import GitCommitTrackerAutomation
from .github_repo_count import GitHubRepoCountAutomation
from .obsidian_md_count import ObsidianMarkdownCountAutomation
from .obsidian_edit_tracker import ObsidianEditTrackerAutomation
from .obsidian_essay_to_website import ObsidianEssayToWebsiteAutomation
from .publish_portfolio_from_obs import PublishPortfolioFromObsAutomation
from .random_art import RandomArtAutomation
from .unedited_kindle_notes import UneditedKindleNotesAutomation
from .wallpaper_from_report import WallpaperFromReportAutomation
from .weekly_commit_tracker import WeeklyCommitTrackerAutomation

__all__ = [
    "Automation",
    "GitCommitTrackerAutomation",
    "GitHubRepoCountAutomation",
    "ObsidianMarkdownCountAutomation",
    "ObsidianEditTrackerAutomation",
    "ObsidianEssayToWebsiteAutomation",
    "PublishPortfolioFromObsAutomation",
    "RandomArtAutomation",
    "UneditedKindleNotesAutomation",
    "WallpaperFromReportAutomation",
    "WeeklyCommitTrackerAutomation",
]
