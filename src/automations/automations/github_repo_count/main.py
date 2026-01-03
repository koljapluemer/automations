from __future__ import annotations

from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec, ReportElement


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

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        status = result.status
        if result.status != "ok":
            return [
                ReportElement(
                    id=f"{self.spec.id}_total",
                    kind="stat",
                    title="GitHub Repos",
                    value="N/A",
                    note="",
                    status=status,
                )
            ]

        total_count = result.payload.get("count")
        active_count = result.payload.get("active_count", total_count)

        return [
            ReportElement(
                id=f"{self.spec.id}_total",
                kind="stat",
                title="Total Repos",
                value=str(total_count) if total_count is not None else "N/A",
                note="",
                status=status,
            ),
            ReportElement(
                id=f"{self.spec.id}_active",
                kind="stat",
                title="Active Repos",
                value=str(active_count) if active_count is not None else "N/A",
                note="",
                status=status,
            ),
        ]


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
        return {"count": count, "username": payload.get("username")}
    if isinstance(count, str) and count.isdigit():
        return {"count": int(count), "username": payload.get("username")}
    return None
