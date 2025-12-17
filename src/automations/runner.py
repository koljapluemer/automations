from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .config import Config
from .log_store import LogStore
from .report.html import render_stats_html
from .services.github import GitHubClient
from .services.obsidian import count_markdown_files


@dataclass(frozen=True)
class AutomationError:
    step: str
    message: str


@dataclass(frozen=True)
class AutomationResult:
    repo_count: int | None
    md_count: int | None
    html_path: Path | None
    errors: tuple[AutomationError, ...]


def run_automations(config: Config) -> AutomationResult:
    project_root = config.output_html.parent.parent
    log_store = LogStore(project_root / "runtime" / "automation.log.jsonl")
    errors: list[AutomationError] = []

    md_count: int | None = None
    try:
        md_count = count_markdown_files(config.obsidian_vault_path)
        _safe_log(
            log_store,
            errors,
            "obsidian_md_count",
            {"count": md_count, "vault": str(config.obsidian_vault_path)},
        )
    except Exception as exc:
        _record_error(log_store, errors, "obsidian_md_count", exc)

    repo_count: int | None = None
    try:
        repo_count = _get_repo_count(config, log_store, errors)
    except Exception as exc:
        _record_error(log_store, errors, "github_repo_count", exc)

    html_path: Path | None = None
    try:
        html = render_stats_html(
            repo_count=repo_count,
            md_count=md_count,
            screen_width=config.screen_width,
            screen_height=config.screen_height,
            generated_at=datetime.now(),
            error_count=len(errors),
        )
        config.output_html.parent.mkdir(parents=True, exist_ok=True)
        config.output_html.write_text(html, encoding="utf-8")
        html_path = config.output_html

        _safe_log(
            log_store,
            errors,
            "html_generated",
            {
                "output_path": str(config.output_html),
                "repo_count": repo_count,
                "md_count": md_count,
                "error_count": len(errors),
            },
        )
    except Exception as exc:
        _record_error(log_store, errors, "html_generated", exc)

    return AutomationResult(
        repo_count=repo_count,
        md_count=md_count,
        html_path=html_path,
        errors=tuple(errors),
    )



def _get_repo_count(
    config: Config,
    log_store: LogStore,
    errors: list[AutomationError],
) -> int:
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
    _safe_log(
        log_store,
        errors,
        "github_repo_count",
        {"count": result.count, "username": config.github_username},
    )
    return result.count


def _record_error(
    log_store: LogStore,
    errors: list[AutomationError],
    step: str,
    exc: Exception,
) -> None:
    message = f"{type(exc).__name__}: {exc}"
    _safe_log(
        log_store,
        errors,
        "automation_error",
        {"step": step, "error": message, "error_type": type(exc).__name__},
    )
    errors.append(AutomationError(step=step, message=message))


def _safe_log(
    log_store: LogStore,
    errors: list[AutomationError],
    event: str,
    payload: dict[str, Any],
) -> None:
    try:
        log_store.append(event, payload)
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        errors.append(AutomationError(step="log_store", message=message))
