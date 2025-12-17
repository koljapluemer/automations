from .base import Automation
from .github_repo_count import GitHubRepoCountAutomation
from .obsidian_md_count import ObsidianMarkdownCountAutomation
from .publish_portfolio_from_obs import PublishPortfolioFromObsAutomation
from .wallpaper_from_report import WallpaperFromReportAutomation

__all__ = [
    "Automation",
    "GitHubRepoCountAutomation",
    "ObsidianMarkdownCountAutomation",
    "PublishPortfolioFromObsAutomation",
    "WallpaperFromReportAutomation",
]
