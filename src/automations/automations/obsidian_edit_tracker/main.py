from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec


class ObsidianEditTrackerAutomation(Automation):
    spec = AutomationSpec(
        id="obsidian_edit_tracker",
        title="Obsidian Edit Tracker",
        description="Track markdown file edits in Obsidian vault over last 14 days",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        vault_path_raw = ctx.config.settings.get("vault_path")
        if not vault_path_raw:
            raise ValueError(
                "obsidian_edit_tracker requires 'vault_path' setting in config.yaml"
            )

        vault_path = Path(str(vault_path_raw)).expanduser().resolve()

        if not vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {vault_path}")

        if not vault_path.is_dir():
            raise ValueError(f"Vault path is not a directory: {vault_path}")

        # Count files edited today
        today = date.today()
        today_edits = _count_edits_today(vault_path, today)

        # Log today's count
        ctx.log.append(
            self.spec.id,
            "daily_edit_count",
            {"date": today.isoformat(), "count": today_edits},
        )

        # Build heatmap from last 14 days of logs
        log_root = ctx.config.project_root / "runtime" / "logs"
        daily_edits = _load_daily_edits(log_root, 14)

        return {
            "today_edits": today_edits,
            "daily_edits": daily_edits,
        }


def _count_edits_today(vault_path: Path, target_date: date) -> int:
    """Count markdown files modified on target_date."""
    count = 0
    try:
        for md_file in vault_path.rglob("*.md"):
            if not md_file.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime).date()
                if mtime == target_date:
                    count += 1
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass
    return count


def _load_daily_edits(log_root: Path, days: int = 14) -> dict[str, int]:
    """Load daily edit counts from logs for last N days."""
    daily_edits: dict[str, int] = {}
    today = date.today()

    for i in range(days):
        day = today - timedelta(days=i)
        day_str = day.isoformat()
        log_path = log_root / day_str / "obsidian_edit_tracker.jsonl"

        if not log_path.exists():
            continue

        # Read the last entry for this day
        try:
            for line in log_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("event") == "daily_edit_count":
                        payload = data.get("payload", {})
                        if isinstance(payload, dict):
                            count = payload.get("count", 0)
                            if isinstance(count, int):
                                daily_edits[day_str] = count
                except json.JSONDecodeError:
                    continue
        except (OSError, PermissionError):
            continue

    return daily_edits
