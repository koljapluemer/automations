# Adding an automation

This project is designed for many small, independent automations. Each automation lives in its own module, declares metadata, runs with a shared context, and returns data.

## Steps

1. **Create a module**
   - Add a new folder in `src/automations/automations/`, e.g. `my_automation/`.
   - Add `main.py` inside that folder and implement the `Automation` interface with a `spec` and `run()` method.

2. **Register it**
   - Add the new class to `src/automations/automations/__init__.py`.
   - Add an instance to `load_automations()` in `src/automations/registry.py`.

3. **Add config**
   - Add any shared config keys in `config.yaml.demo` (top-level), if needed.
   - Your automation should read shared config via `ctx.config.settings`.

4. **Add to dashboard (optional)**
   - If you want data on the dashboard, update `_build_dto()` in `src/automations/runner.py` to extract your data.
   - Update `DashboardDTO` in `src/automations/dto.py` with new fields.
   - Update the Jinja2 template in `src/automations/report/template.html` to display your data.

5. **Run & verify**
   - `uv run automations` runs all automations.

## Skeleton example

```python
from __future__ import annotations

from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec


class MyAutomation(Automation):
    spec = AutomationSpec(
        id="my_automation",
        title="My Automation",
        description="What it does.",
        # stage="post_report" if it needs the HTML output
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        # shared config values are under ctx.config.settings
        # do work here
        return {"my_data": 42, "status": "completed"}
```

## Configuration pattern

```yaml
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
