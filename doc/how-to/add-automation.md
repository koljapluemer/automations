# Adding an automation

This project is designed for many small, independent automations. Each automation lives in its own module, declares metadata, runs with a shared context, and can optionally emit report elements.

## Steps

1. **Create a module**
   - Add a new file in `src/automations/automations/`, e.g. `my_automation.py`.
   - Implement the `Automation` interface with a `spec` and `run()` method.

2. **Register it**
   - Add the new class to `src/automations/automations/__init__.py`.
   - Add an instance to `load_automations()` in `src/automations/registry.py`.

3. **Add config**
   - Add any shared config keys in `config.yaml.demo` (top-level), if needed.
   - Add your automation id to `enabled_automations` in `config.yaml.demo`.
   - Your automation should read shared config via `ctx.config.settings`.

4. **Add report elements (optional)**
   - Implement `build_report()` to return one or more `ReportElement`s.
   - Use `col_span`/`row_span` if you need larger tiles, or `kind="image"` for image tiles.

5. **Run & verify**
   - `uv run automations --list` should show your automation.
   - `uv run automations --only your_id` runs just your automation.

## Skeleton example

```python
from __future__ import annotations

from typing import Any

from .base import Automation
from ..context import AutomationContext
from ..models import AutomationResult, AutomationSpec, ReportElement


class MyAutomation(Automation):
    spec = AutomationSpec(
        id="my_automation",
        title="My Automation",
        description="What it does.",
        default_enabled=True,
        # stage="post_report" if it needs the HTML output
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        settings = ctx.settings_for(self.spec.id, default_enabled=self.spec.default_enabled)
        # shared config values are under ctx.config.settings
        # do work here
        return {"result": "ok"}

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        if result.status != "ok":
            return []
        return [
            ReportElement(
                id=self.spec.id,
                kind="stat",
                title="My Stat",
                value=str(result.payload.get("result", "N/A")),
                note="Optional note",
            )
        ]
```

## Configuration pattern

```yaml
enabled_automations:
  - my_automation

my_service_api_key: "..."
my_automation_mode: "fast"
```

Use `ctx.config.settings` for shared config. Use `ServiceRegistry` if you create new shared clients.

## Logging & caching

- Logs are per-automation and per-day in `runtime/logs/YYYY-MM-DD/`.
- If you need a daily cache, read the latest event with:
  - `ctx.log.latest_event(automation_id, "result")`
  - Store cached values in the payload you return, then re-use them on the next run.

## Stages

- Default stage is `primary` (runs before report generation).
- Use `stage="post_report"` if the automation needs the HTML output (e.g. wallpaper).
