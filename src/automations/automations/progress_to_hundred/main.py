from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec


class ProgressToHundredAutomation(Automation):
    spec = AutomationSpec(
        id="progress_to_hundred",
        title="Progress to Hundred",
        description="Track progress bars for files starting with ◩.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        folder_path = ctx.config.settings.get("progress_to_hundred_path")
        if not folder_path:
            return {"bars": []}

        folder = Path(folder_path).expanduser().resolve()
        if not folder.exists():
            return {"bars": []}

        bars = []
        for pattern in ("◩*.md", "◩*.txt"):
            for file in folder.rglob(pattern):
                bar_data = _parse_progress_file(file, ctx.run_date)
                if bar_data:
                    bars.append(bar_data)

        return {"bars": bars}


DATE_PATTERN = re.compile(r"^- \*(\d{2})-(\d{2})-(\d{2})")


def _parse_progress_file(file_path: Path, run_date: date) -> dict[str, Any] | None:
    title = file_path.stem.lstrip("◩").strip()
    if not title:
        title = file_path.stem

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    today = run_date
    week_start = today - timedelta(days=today.weekday())  # Monday

    older_count = 0
    week_count = 0
    today_count = 0

    for line in content.splitlines():
        match = DATE_PATTERN.match(line)
        if not match:
            continue

        yy, mm, dd = match.groups()
        try:
            entry_date = date(2000 + int(yy), int(mm), int(dd))
        except ValueError:
            continue

        if entry_date == today:
            today_count += 1
        elif entry_date >= week_start:
            week_count += 1
        else:
            older_count += 1

    total = older_count + week_count + today_count

    return {
        "title": title,
        "older": older_count,
        "week": week_count,
        "today": today_count,
        "total": total,
    }
