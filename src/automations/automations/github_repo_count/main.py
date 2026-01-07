from __future__ import annotations

from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec


class GitHubRepoCountAutomation(Automation):
    spec = AutomationSpec(
        id="github_repo_count",
        title="GitHub Repo Count",
        description="Count repositories owned by the configured GitHub user.",
        default_enabled=True,
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        cached = _load_cached_count(ctx, self.spec.id)
        if cached is not None:
            cached["cached"] = True
            return cached

        settings = ctx.settings_for(self.spec.id, default_enabled=self.spec.default_enabled)
        service_cfg = ctx.services.service_config("github")
        shared = ctx.config.settings
        username = shared.get("github_username") or settings.config.get("username") or service_cfg.get("username")
        token = shared.get("github_token") or settings.config.get("token") or service_cfg.get("token")
        if not username or not token:
            raise ValueError(
                "github_repo_count requires 'github_username' and 'github_token' in config (or legacy services)"
            )

        client = ctx.services.github_client(username=str(username), token=str(token))
        result = client.count_owned_repos()
        active_count = client.count_active_repos()
        return {
            "count": result.count,
            "active_count": active_count,
            "username": str(username),
            "cached": False
        }


def _load_cached_count(ctx: AutomationContext, automation_id: str) -> dict[str, Any] | None:
    latest = ctx.log.latest_event(automation_id, "result")
    if not latest:
        return None
    if latest.get("status") != "ok":
        return None
    payload = latest.get("payload")
    if not isinstance(payload, dict):
        return None
    count = payload.get("count")
    if isinstance(count, int):
        result = {"count": count, "username": payload.get("username")}
        active_count = payload.get("active_count")
        if active_count is not None:
            result["active_count"] = active_count
        return result
    if isinstance(count, str) and count.isdigit():
        result = {"count": int(count), "username": payload.get("username")}
        active_count = payload.get("active_count")
        if active_count is not None:
            result["active_count"] = active_count
        return result
    return None
