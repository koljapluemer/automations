from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Automation
from ..context import AutomationContext
from ..models import AutomationResult, AutomationSpec, ReportElement
from ..services.obsidian import count_location_occurrences


class UneditedKindleNotesAutomation(Automation):
    spec = AutomationSpec(
        id="unedited_kindle_notes",
        title="Unedited Kindle Notes",
        description="Count occurrences of 'location: ' in Obsidian vault markdown files.",
        default_enabled=True,
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        settings = ctx.settings_for(self.spec.id, default_enabled=self.spec.default_enabled)
        vault_path = _resolve_vault_path(settings.config, ctx)
        count = count_location_occurrences(vault_path)
        return {"count": count, "vault_path": str(vault_path)}

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        value = None
        note = "Unedited highlights"
        status = result.status
        if result.status == "ok":
            count = result.payload.get("count")
            value = str(count) if count is not None else "N/A"
        else:
            value = "N/A"
            if result.message:
                note = "Unavailable (see log)"
        return [
            ReportElement(
                id=self.spec.id,
                kind="stat",
                title="Kindle Notes",
                value=value,
                note=note,
                status=status,
            )
        ]


def _resolve_vault_path(config: dict[str, Any], ctx: AutomationContext) -> Path:
    path_raw = config.get("vault_path")
    if not path_raw:
        service_cfg = ctx.services.service_config("obsidian")
        path_raw = service_cfg.get("vault_path")
    if not path_raw:
        raise ValueError("unedited_kindle_notes requires 'vault_path' in config or services")
    return Path(str(path_raw)).expanduser()
