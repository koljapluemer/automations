from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .config import Config
from .log_store import LogStore
from .report.html import render_stats_html
from .services.github import GitHubClient
from .services.obsidian import count_markdown_files


@dataclass(frozen=True)
class AutomationResult:
    repo_count: int
    md_count: int
    html_path: Path


def run_automations(config: Config) -> AutomationResult:
    project_root = config.output_html.parent.parent
    log_store = LogStore(project_root / "runtime" / "automation.log.jsonl")

    md_count = count_markdown_files(config.obsidian_vault_path)
    log_store.append(
        "obsidian_md_count",
        {"count": md_count, "vault": str(config.obsidian_vault_path)},
    )

    repo_count = _get_repo_count(config, log_store)

    html = render_stats_html(
        repo_count=repo_count,
        md_count=md_count,
        screen_width=config.screen_width,
        screen_height=config.screen_height,
        generated_at=datetime.now(),
    )
    config.output_html.parent.mkdir(parents=True, exist_ok=True)
    config.output_html.write_text(html, encoding="utf-8")

    log_store.append(
        "html_generated",
        {
            "output_path": str(config.output_html),
            "repo_count": repo_count,
            "md_count": md_count,
        },
    )

    return AutomationResult(
        repo_count=repo_count,
        md_count=md_count,
        html_path=config.output_html,
    )


def _get_repo_count(config: Config, log_store: LogStore) -> int:
    today = date.today()
    existing = log_store.latest_for_date("github_repo_count", today)
    if existing:
        cached = existing.payload.get("count")
        if isinstance(cached, int):
            return cached
        if isinstance(cached, str) and cached.isdigit():
            return int(cached)

    client = GitHubClient(token=config.github_token, username=config.github_username)
    result = client.count_owned_repos()
    log_store.append(
        "github_repo_count",
        {"count": result.count, "username": config.github_username},
    )
    return result.count
