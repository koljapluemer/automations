from __future__ import annotations

import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec


class WeeklyCommitTrackerAutomation(Automation):
    spec = AutomationSpec(
        id="weekly_commit_tracker",
        title="Weekly Commit Tracker",
        description="Track commits to portfolio and main repos this calendar week (Monday-Sunday)",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        # Get config values
        portfolio_repo_raw = ctx.config.settings.get("portfolio_repo_path")
        main_repo_raw = ctx.config.settings.get("main_repo_path")

        # Validate config
        if not portfolio_repo_raw or not main_repo_raw:
            raise ValueError(
                "weekly_commit_tracker requires 'portfolio_repo_path' and 'main_repo_path' in config.yaml"
            )

        # Expand paths
        portfolio_repo = Path(str(portfolio_repo_raw)).expanduser().resolve()
        main_repo = Path(str(main_repo_raw)).expanduser().resolve()

        # Get Monday of current week
        monday = _get_monday_of_week()

        # Check commits
        portfolio_has_commits = _has_commits_this_week(portfolio_repo, monday)
        main_has_commits = _has_commits_this_week(main_repo, monday)

        return {
            "portfolio_has_commits": portfolio_has_commits,
            "main_has_commits": main_has_commits,
            "week_start": monday.isoformat(),
            "portfolio_repo_path": str(portfolio_repo),
            "main_repo_path": str(main_repo),
        }


def _get_monday_of_week() -> date:
    """Get Monday of current ISO 8601 week."""
    today = date.today()
    # weekday() returns 0 for Monday, 6 for Sunday
    monday = today - timedelta(days=today.weekday())
    return monday


def _has_commits_this_week(repo_path: Path, monday: date) -> bool:
    """Check if repo has commits since Monday of current week."""
    # Validate repo exists
    if not repo_path.exists():
        return False

    if not repo_path.is_dir():
        return False

    # Check if it's a git repo
    if not (repo_path / ".git").is_dir():
        return False

    # Format date for git log
    monday_str = monday.strftime("%Y-%m-%d 00:00:00")

    try:
        result = subprocess.run(
            ["git", "log", f"--since={monday_str}", "--pretty=format:%H"],
            cwd=str(repo_path),
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return False

        # Check if there are any commit hashes in output
        return bool(result.stdout.strip())

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
