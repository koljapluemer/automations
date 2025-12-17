from __future__ import annotations

from datetime import date, datetime

from .config import AppConfig
from .context import AutomationContext
from .logging.log_writer import LogWriter
from .models import AutomationResult, ReportModel, RunSummary
from .registry import load_automations
from .report.html import render_report
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
    _safe_log_run(log, "run_start", {"run_id": run_id, "automation_count": len(automations)})

    results: list[AutomationResult] = []
    report_elements = []
    warnings: list[str] = []

    for automation in automations:
        result = _run_single(automation, ctx, only=only, skip=skip)
        results.append(result)
        report_elements.extend(automation.build_report(result))
        if result.status == "error" and result.message:
            warnings.append(f"{result.automation_id}: {result.message}")

    report_path = _write_report(config, report_elements, warnings)
    if not report_path:
        warnings.append("Report generation failed; see run log for details")

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
        report_path=report_path,
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


def _write_report(config: AppConfig, elements: list, warnings: list[str]) -> str | None:
    report = ReportModel(
        elements=elements,
        generated_at=datetime.now(),
        screen_width=config.report.screen_width,
        screen_height=config.report.screen_height,
        warnings=warnings,
    )
    html = render_report(report)
    try:
        config.report.output_html.parent.mkdir(parents=True, exist_ok=True)
        config.report.output_html.write_text(html, encoding="utf-8")
    except Exception:
        return None
    return str(config.report.output_html)


def _safe_log(callable_, *args) -> None:
    try:
        callable_(*args)
    except Exception:
        return


def _safe_log_run(log: LogWriter, event: str, payload: dict) -> None:
    _safe_log(log.append_run, event, payload)
