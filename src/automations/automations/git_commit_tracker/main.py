from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec


class GitCommitTrackerAutomation(Automation):
    spec = AutomationSpec(
        id="git_commit_tracker",
        title="Git Commit Tracker",
        description="Track commits across git projects over last 14 days",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        git_project_folder_raw = ctx.config.settings.get("git_project_folder")
        if not git_project_folder_raw:
            raise ValueError(
                "git_commit_tracker requires 'git_project_folder' setting in config.yaml"
            )

        git_project_folder = Path(str(git_project_folder_raw)).expanduser().resolve()

        if not git_project_folder.exists():
            raise FileNotFoundError(
                f"Git project folder does not exist: {git_project_folder}"
            )

        if not git_project_folder.is_dir():
            raise ValueError(
                f"Git project folder path is not a directory: {git_project_folder}"
            )

        repos = _scan_git_repos(git_project_folder)

        if not repos:
            # No repos found - return empty data gracefully
            return {
                "repo_count": 0,
                "daily_commits": {},
                "svg_path": None,
            }

        daily_commits = _aggregate_commits(repos)

        # Generate SVG visualization
        output_dir = Path("/home/brokkoli/GITHUB/automations/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        svg_path = _generate_svg(daily_commits, output_dir)

        return {
            "repo_count": len(repos),
            "daily_commits": daily_commits,
            "svg_path": str(svg_path),
        }


def _scan_git_repos(base_path: Path) -> list[Path]:
    """Find all direct child git repositories."""
    repos = []
    try:
        for child in base_path.iterdir():
            if child.is_dir() and (child / ".git").is_dir():
                repos.append(child)
    except (OSError, PermissionError) as e:
        # Log warning but continue
        pass
    return repos


def _count_commits_by_day(repo_path: Path, days: int = 14) -> dict[str, int]:
    """Count commits per day for last N days in a single repo."""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={days} days ago", "--pretty=format:%ai"],
            cwd=str(repo_path),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {}

        # Parse dates from git log output
        daily_commits: dict[str, int] = {}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Format: "YYYY-MM-DD HH:MM:SS +TZTZ"
            date_str = line.split()[0]  # Extract just YYYY-MM-DD
            daily_commits[date_str] = daily_commits.get(date_str, 0) + 1

        return daily_commits

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {}


def _aggregate_commits(repos: list[Path]) -> dict[str, int]:
    """Aggregate commit counts across all repos by day."""
    aggregated: dict[str, int] = {}

    for repo in repos:
        repo_commits = _count_commits_by_day(repo)
        for date, count in repo_commits.items():
            aggregated[date] = aggregated.get(date, 0) + count

    return aggregated


def _generate_svg(daily_commits: dict[str, int], output_dir: Path) -> Path:
    """Generate GitHub-style contribution graph SVG."""
    # Calculate the last 14 days
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]

    # Get commit counts for each day
    counts = [daily_commits.get(date, 0) for date in dates]

    # Calculate max for color scaling
    max_commits = max(counts) if counts else 1

    # Generate SVG
    svg_parts = ['<svg width="294" height="20" xmlns="http://www.w3.org/2000/svg">']

    for i, count in enumerate(counts):
        color = _get_color(count, max_commits)
        x_pos = i * 22  # 20px width + 2px gap
        svg_parts.append(
            f'<rect x="{x_pos}" y="0" width="20" height="20" fill="{color}"/>'
        )

    svg_parts.append("</svg>")
    svg_content = "\n".join(svg_parts)

    # Save to file
    svg_path = output_dir / "git_commit_tracker.svg"
    svg_path.write_text(svg_content, encoding="utf-8")

    return svg_path


def _get_color(commit_count: int, max_commits: int) -> str:
    """Map commit count to GitHub-style green gradient."""
    if commit_count == 0:
        return "#ebedf0"  # Light gray
    if max_commits == 0:
        return "#ebedf0"

    ratio = commit_count / max_commits

    if ratio <= 0.25:
        return "#c6e48b"  # Lightest green
    elif ratio <= 0.50:
        return "#7bc96f"  # Light green
    elif ratio <= 0.75:
        return "#239a3b"  # Medium green
    else:
        return "#196c2f"  # Dark green
