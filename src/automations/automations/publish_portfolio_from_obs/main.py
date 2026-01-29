from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec

PORTFOLIO_PATH = Path("/home/brokkoli/GITHUB/zk-best-learning-tool")
OBSIDIAN_COMMAND = [".venv/bin/obsidian-to-web", "--config", "config.yaml"]


class PublishPortfolioFromObsAutomation(Automation):
    spec = AutomationSpec(
        id="publish_portfolio_from_obs",
        title="Publish Portfolio from Obsidian",
        description="Build and publish the Obsidian portfolio site.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        # Check if already deployed today (unless force flag is set)
        force = "zk_deploy" in ctx.force_flags
        if not force:
            cached = _load_cached_result(ctx, self.spec.id)
            if cached is not None:
                cached["cached"] = True
                return cached

        _ensure_portfolio_path()
        _ensure_obsidian_cli()

        _run_command(OBSIDIAN_COMMAND, cwd=PORTFOLIO_PATH)

        _run_command(["git", "add", "."], cwd=PORTFOLIO_PATH)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        committed = _run_commit(
            ["git", "commit", "-m", f"auto-commit {timestamp}"],
            cwd=PORTFOLIO_PATH,
        )
        if not committed:
            return {"status": "no_changes", "cached": False}
        _run_command(["git", "push"], cwd=PORTFOLIO_PATH)

        return {"status": "updated", "timestamp": timestamp, "cached": False}


def _ensure_portfolio_path() -> None:
    if not PORTFOLIO_PATH.is_dir():
        raise FileNotFoundError(f"Portfolio repo not found: {PORTFOLIO_PATH}")


def _ensure_obsidian_cli() -> None:
    cli_path = PORTFOLIO_PATH / OBSIDIAN_COMMAND[0]
    if not cli_path.is_file():
        raise FileNotFoundError(f"obsidian-to-web not found: {cli_path}")


def _run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        detail = f": {stderr}" if stderr else ""
        raise RuntimeError(f"Command failed ({' '.join(cmd)}){detail}")
    return result


def _run_commit(cmd: list[str], cwd: Path) -> bool:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        output = "\n".join([result.stdout.strip(), result.stderr.strip()]).strip()
        if _is_nothing_to_commit(output):
            return False
        detail = f": {output}" if output else ""
        raise RuntimeError(f"Command failed ({' '.join(cmd)}){detail}")
    return True


def _is_nothing_to_commit(output: str) -> bool:
    lowered = output.lower()
    return "nothing to commit" in lowered or "no changes added to commit" in lowered


def _load_cached_result(ctx: AutomationContext, automation_id: str) -> dict[str, Any] | None:
    """Return cached result if this automation already ran successfully today."""
    latest = ctx.log.latest_event(automation_id, "result")
    if not latest:
        return None
    if latest.get("status") != "ok":
        return None
    payload = latest.get("payload")
    if not isinstance(payload, dict):
        return None
    status = payload.get("status")
    if status in ("updated", "no_changes"):
        return {"status": status, "timestamp": payload.get("timestamp")}
    return None
