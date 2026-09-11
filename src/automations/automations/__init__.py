from .base import Automation
from .blog_display import BlogDisplayAutomation
from .git_commit_tracker import GitCommitTrackerAutomation
from .obsidian_md_count import ObsidianMarkdownCountAutomation
from .obsidian_edit_tracker import ObsidianEditTrackerAutomation
from .random_art import RandomArtAutomation
from .unedited_kindle_notes import UneditedKindleNotesAutomation
from .wallpaper_from_report import WallpaperFromReportAutomation
from .project_command_center import ProjectCommandCenterAutomation

__all__ = [
    "Automation",
    "BlogDisplayAutomation",
    "GitCommitTrackerAutomation",
    "ObsidianMarkdownCountAutomation",
    "ObsidianEditTrackerAutomation",
    "ProjectCommandCenterAutomation",
    "RandomArtAutomation",
    "UneditedKindleNotesAutomation",
    "WallpaperFromReportAutomation",
]
