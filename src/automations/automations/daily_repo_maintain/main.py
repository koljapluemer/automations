from __future__ import annotations

import random
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec


class DailyRepoMaintainAutomation(Automation):
    spec = AutomationSpec(
        id="daily_repo_maintain",
        title="Daily Repo to Maintain",
        description="Select a random active repo to maintain each day.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        cached = ctx.log.latest_event(self.spec.id, "repo_chosen")
        if cached:
            return {"repo": cached.get("repo", ""), "cached": True}

        shared = ctx.config.settings
        service_cfg = ctx.services.service_config("github")
        username = shared.get("github_username") or service_cfg.get("username")
        token = shared.get("github_token") or service_cfg.get("token")
        if not username or not token:
            return {"repo": ""}

        client = ctx.services.github_client(username=str(username), token=str(token))
        repos = client.list_active_repos()
        if not repos:
            return {"repo": ""}

        chosen = random.choice(repos)
        repo_name = chosen.get("name", "")
        ctx.log.append(self.spec.id, "repo_chosen", {"repo": repo_name})
        return {"repo": repo_name, "cached": False}
