from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec


class DailyRepoMaintainAutomation(Automation):
    spec = AutomationSpec(
        id="daily_repo_maintain",
        title="Daily Repo to Maintain",
        description="Select a random local repo to maintain each day.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        cached = ctx.log.latest_event(self.spec.id, "repo_chosen")
        if cached:
            return {"repo": cached.get("repo", ""), "cached": True}

        git_project_folder_raw = ctx.config.settings.get("git_project_folder")
        if not git_project_folder_raw:
            return {"repo": ""}

        git_project_folder = Path(str(git_project_folder_raw)).expanduser()
        repos = [p.name for p in sorted(git_project_folder.iterdir()) if p.is_dir()]
        if not repos:
            return {"repo": ""}

        chosen = random.choice(repos)
        ctx.log.append(self.spec.id, "repo_chosen", {"repo": chosen})
        return {"repo": chosen, "cached": False}
