from .base import Automation
from .github_repo_count import GitHubRepoCountAutomation
from .obsidian_md_count import ObsidianMarkdownCountAutomation
from .wallpaper_from_report import WallpaperFromReportAutomation

__all__ = [
    "Automation",
    "GitHubRepoCountAutomation",
    "ObsidianMarkdownCountAutomation",
    "WallpaperFromReportAutomation",
]
