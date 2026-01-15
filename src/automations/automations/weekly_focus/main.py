from __future__ import annotations

import json
import random
from datetime import timedelta
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec


class WeeklyFocusAutomation(Automation):
    spec = AutomationSpec(
        id="weekly_focus",
        title="Weekly Focus",
        description="Select a random focus item for the current week.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        file_path = ctx.config.settings.get("weekly_focus_file")
        if not file_path:
            return {"focus": ""}

        cached = _find_week_focus(ctx, self.spec.id)
        if cached:
            return {"focus": cached, "cached": True}

        items = _read_focus_items(file_path)
        if not items:
            return {"focus": ""}

        chosen = random.choice(items)
        ctx.log.append(self.spec.id, "focus_chosen", {"focus": chosen})
        return {"focus": chosen, "cached": False}


def _find_week_focus(ctx: AutomationContext, automation_id: str) -> str | None:
    today = ctx.run_date
    monday = today - timedelta(days=today.weekday())

    log_root = ctx.log._root
    for i in range((today - monday).days + 1):
        day = monday + timedelta(days=i)
        log_path = log_root / day.isoformat() / f"{automation_id}.jsonl"
        if not log_path.exists():
            continue
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if data.get("event") == "focus_chosen":
                return data.get("payload", {}).get("focus")
    return None


def _read_focus_items(file_path: str) -> list[str]:
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]
