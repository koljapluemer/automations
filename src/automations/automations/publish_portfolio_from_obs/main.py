from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec, ReportElement

PORTFOLIO_PATH = Path("/home/brokkoli/GITHUB/zk-best-learning-tool")
OBSIDIAN_COMMAND = [".venv/bin/obsidian-to-web", "--config", "config.yaml"]


class PublishPortfolioFromObsAutomation(Automation):
    spec = AutomationSpec(
        id="publish_portfolio_from_obs",
        title="Publish Portfolio from Obsidian",
        description="Build and publish the Obsidian portfolio site.",
        default_enabled=True,
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
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
            return {"status": "no_changes"}
        _run_command(["git", "push"], cwd=PORTFOLIO_PATH)

        return {"status": "updated", "timestamp": timestamp}

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        if result.status == "skipped":
            return []
        message = "Portfolio update failed"
        status = None
        if result.status == "ok":
            status_flag = result.payload.get("status")
            if status_flag == "no_changes":
                message = "Nothing new in portfolio"
            else:
                message = "Portfolio updated"
        else:
            status = "error"
        return [
            ReportElement(
                id=self.spec.id,
                kind="stat",
                title="Portfolio Publish",
                value=message,
                status=status,
            )
        ]


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
