from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec


class GitHubRepoCountAutomation(Automation):
    spec = AutomationSpec(
        id="github_repo_count",
        title="GitHub Repo Count",
        description="Count repositories owned by the configured GitHub user.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        force = "github" in ctx.force_flags

        if not force:
            cached = _load_cached_count(ctx, self.spec.id)
            if cached is not None:
                cached["cached"] = True
                return cached

        service_cfg = ctx.services.service_config("github")
        shared = ctx.config.settings
        username = shared.get("github_username") or service_cfg.get("username")
        token = shared.get("github_token") or service_cfg.get("token")
        if not username or not token:
            raise ValueError(
                "github_repo_count requires 'github_username' and 'github_token' in config (or legacy services)"
            )

        client = ctx.services.github_client(username=str(username), token=str(token))
        result = client.count_owned_repos()
        active_count = client.count_active_repos()

        vault_repo_folder = shared.get("vault_repo_folder")
        notes_written = 0
        if vault_repo_folder:
            notes_written = _write_repo_notes(Path(vault_repo_folder).expanduser(), result.repos)

        return {
            "count": result.count,
            "active_count": active_count,
            "username": str(username),
            "notes_written": notes_written,
            "cached": False
        }


def _write_repo_notes(folder: Path, repos: list[dict[str, Any]]) -> int:
    """Write Obsidian-style markdown notes for each repository."""
    folder.mkdir(parents=True, exist_ok=True)
    count = 0

    for repo in repos:
        name = repo.get("name", "unknown")
        description = repo.get("description") or ""
        homepage = repo.get("homepage") or ""
        url = repo.get("html_url", "")
        stars = repo.get("stargazers_count", 0)
        pushed_at = repo.get("pushed_at", "")

        # Parse and format the date
        last_edited = ""
        if pushed_at:
            try:
                dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                last_edited = dt.strftime("%Y-%m-%d")
            except ValueError:
                last_edited = pushed_at[:10] if len(pushed_at) >= 10 else pushed_at

        # Build markdown content
        lines = []
        is_public = not repo.get("private", True)
        if is_public:
            lines.extend(["---", "published: true", "---", ""])

        if description:
            lines.append(f"- **{description}**")
        lines.append(f"- [repository link]({url})")
        if homepage:
            lines.append(f"- [homepage]({homepage})")
        lines.append(f"- *Stars*: {stars}")
        if last_edited:
            lines.append(f"- *last edited at: {last_edited}*")
        lines.append("")

        content = "\n".join(lines)
        note_path = folder / f"⛁ {name}.md"
        note_path.write_text(content, encoding="utf-8")
        count += 1

    return count


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
