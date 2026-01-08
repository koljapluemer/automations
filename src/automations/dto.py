from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DashboardDTO:
    """Data Transfer Object for dashboard rendering."""

    generated_at: datetime
    artwork_image_path: str
    artwork_filename: str
    active_repos: int
    vault_notes: int
    zk_percentage: float
    leaf_percentage: float
    commit_heatmap: list[int]  # 14 days of commit counts
    obs_edits_heatmap: list[int]  # 14 days of obsidian edit counts

    def to_dict(self) -> dict:
        """Convert to dict for Jinja2 template."""
        # Calculate colors for commit heatmap
        max_commits = max(self.commit_heatmap) if self.commit_heatmap else 1
        heatmap_colors = [self._get_color(count, max_commits) for count in self.commit_heatmap]

        # Calculate colors for obs edits heatmap
        max_obs_edits = max(self.obs_edits_heatmap) if self.obs_edits_heatmap else 1
        obs_edits_colors = [self._get_color(count, max_obs_edits) for count in self.obs_edits_heatmap]

        return {
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M"),
            "artwork_image_path": self.artwork_image_path,
            "artwork_filename": self.artwork_filename,
            "active_repos": self.active_repos,
            "vault_notes": self.vault_notes,
            "zk_percentage": f"{self.zk_percentage:.1f}%",
            "leaf_percentage": f"{self.leaf_percentage:.1f}%",
            "commit_heatmap": self.commit_heatmap,
            "heatmap_colors": heatmap_colors,
            "obs_edits_heatmap": self.obs_edits_heatmap,
            "obs_edits_colors": obs_edits_colors,
        }

    def _get_color(self, commit_count: int, max_commits: int) -> str:
        """Map commit count to GitHub-style green gradient."""
        if commit_count == 0:
            return "transparent"
        if max_commits == 0:
            return "transparent"

        ratio = commit_count / max_commits

        if ratio <= 0.25:
            return "#c6e48b"  # Lightest green
        elif ratio <= 0.50:
            return "#7bc96f"  # Light green
        elif ratio <= 0.75:
            return "#239a3b"  # Medium green
        else:
            return "#196c2f"  # Dark green
