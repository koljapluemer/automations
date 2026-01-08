from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from .config import AppConfig
from .context import AutomationContext
from .dto import DashboardDTO
from .logging.log_writer import LogWriter
from .models import AutomationResult, RunSummary
from .registry import load_automations
from .report.html import render_dashboard
from .services.registry import ServiceRegistry


def run_automations(
    config: AppConfig,
    only: set[str] | None = None,
    skip: set[str] | None = None,
) -> RunSummary:
    run_date = date.today()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    log = LogWriter(config.logging.root, run_date, run_id)
    services = ServiceRegistry(config.services)
    ctx = AutomationContext(
        config=config,
        services=services,
        log=log,
        run_date=run_date,
        run_id=run_id,
    )

    automations = load_automations()
    primary = [automation for automation in automations if automation.spec.stage == "primary"]
    post_report = [automation for automation in automations if automation.spec.stage == "post_report"]
    _safe_log_run(log, "run_start", {"run_id": run_id, "automation_count": len(automations)})

    results: list[AutomationResult] = []
    warnings: list[str] = []

    for automation in primary:
        result = _run_single(automation, ctx, only=only, skip=skip)
        results.append(result)
        if result.status == "error" and result.message:
            warnings.append(f"{result.automation_id}: {result.message}")

    report_path = _write_dashboard(config, results, datetime.now())
    if not report_path:
        warnings.append("Report generation failed; see run log for details")
    else:
        ctx = AutomationContext(
            config=config,
            services=services,
            log=log,
            run_date=run_date,
            run_id=run_id,
            report_path=report_path,
        )

    for automation in post_report:
        result = _run_single(automation, ctx, only=only, skip=skip)
        results.append(result)
        if result.status == "error" and result.message:
            warnings.append(f"{result.automation_id}: {result.message}")

    _safe_log_run(
        log,
        "run_complete",
        {
            "run_id": run_id,
            "report_path": report_path,
            "warnings": warnings,
        },
    )

    return RunSummary(
        results=tuple(results),
        report_path=str(report_path) if report_path else None,
        warnings=tuple(warnings),
    )


def _run_single(automation, ctx: AutomationContext, only: set[str] | None, skip: set[str] | None) -> AutomationResult:
    automation_id = automation.spec.id

    if only and automation_id not in only:
        result = AutomationResult(
            automation_id=automation_id,
            status="skipped",
            message="Not selected",
        )
        _log_result(ctx.log, result)
        return result

    if skip and automation_id in skip:
        result = AutomationResult(
            automation_id=automation_id,
            status="skipped",
            message="Skipped by user",
        )
        _log_result(ctx.log, result)
        return result

    settings = ctx.settings_for(automation_id, default_enabled=automation.spec.default_enabled)
    if not settings.enabled:
        result = AutomationResult(
            automation_id=automation_id,
            status="skipped",
            message="Disabled in config",
        )
        _log_result(ctx.log, result)
        return result

    started_at = datetime.now()
    try:
        payload = automation.run(ctx)
        status = "ok"
        message = None
    except Exception as exc:
        payload = {}
        status = "error"
        message = f"{type(exc).__name__}: {exc}"
    finished_at = datetime.now()

    result = AutomationResult(
        automation_id=automation_id,
        status=status,
        payload=payload,
        message=message,
        started_at=started_at,
        finished_at=finished_at,
    )
    _log_result(ctx.log, result)
    return result


def _log_result(log: LogWriter, result: AutomationResult) -> None:
    payload = {
        "status": result.status,
        "payload": result.payload,
        "message": result.message,
        "started_at": result.started_at.isoformat(timespec="seconds") if result.started_at else None,
        "finished_at": result.finished_at.isoformat(timespec="seconds") if result.finished_at else None,
        "duration_ms": result.duration_ms(),
    }
    _safe_log(log.append, result.automation_id, "result", payload)
    _safe_log_run(log, "automation_result", {"automation_id": result.automation_id, **payload})


def _write_dashboard(config: AppConfig, results: list[AutomationResult], generated_at: datetime) -> Path | None:
    """Build DTO from results and render dashboard HTML."""
    dto = _build_dto(results, generated_at)
    html = render_dashboard(dto)
    try:
        config.report.output_html.parent.mkdir(parents=True, exist_ok=True)
        config.report.output_html.write_text(html, encoding="utf-8")
    except Exception:
        return None
    return config.report.output_html


def _build_dto(results: list[AutomationResult], generated_at: datetime) -> DashboardDTO:
    """Build dashboard DTO from automation results."""
    # Create map of automation_id → payload (only successful results)
    data_map = {r.automation_id: r.payload for r in results if r.status == "ok"}

    # Extract data from specific automations with fallbacks
    git_data = data_map.get("git_commit_tracker", {})
    github_data = data_map.get("github_repo_count", {})
    obsidian_data = data_map.get("obsidian_md_count", {})
    art_data = data_map.get("random_art", {})
    obs_edits_data = data_map.get("obsidian_edit_tracker", {})

    # Convert daily_commits dict to list of 14 counts
    daily_commits = git_data.get("daily_commits", {})
    from datetime import date, timedelta
    today = date.today()
    commit_heatmap = [
        daily_commits.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), 0)
        for i in range(13, -1, -1)
    ]

    # Convert daily_edits dict to list of 14 counts
    daily_edits = obs_edits_data.get("daily_edits", {})
    obs_edits_heatmap = [
        daily_edits.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), 0)
        for i in range(13, -1, -1)
    ]

    return DashboardDTO(
        generated_at=generated_at,
        artwork_image_path=art_data.get("image_path", ""),
        artwork_filename=art_data.get("image_name", "N/A"),
        active_repos=github_data.get("active_count", 0),
        vault_notes=obsidian_data.get("count", 0),
        zk_percentage=obsidian_data.get("zk_percentage", 0.0),
        leaf_percentage=obsidian_data.get("leaf_percentage", 0.0),
        commit_heatmap=commit_heatmap,
        obs_edits_heatmap=obs_edits_heatmap,
    )


def _safe_log(callable_, *args) -> None:
    try:
        callable_(*args)
    except Exception:
        return


def _safe_log_run(log: LogWriter, event: str, payload: dict) -> None:
    _safe_log(log.append_run, event, payload)
