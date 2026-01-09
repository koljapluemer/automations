from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec
from ...services.obsidian import count_location_occurrences


class UneditedKindleNotesAutomation(Automation):
    spec = AutomationSpec(
        id="unedited_kindle_notes",
        title="Unedited Kindle Notes",
        description="Count occurrences of 'location: ' in Obsidian vault markdown files.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        vault_path = _resolve_vault_path(ctx)
        count = count_location_occurrences(vault_path)
        return {"count": count, "vault_path": str(vault_path)}


def _resolve_vault_path(ctx: AutomationContext) -> Path:
    path_raw = ctx.config.settings.get("vault_path")
    if not path_raw:
        service_cfg = ctx.services.service_config("obsidian")
        path_raw = service_cfg.get("vault_path")
    if not path_raw:
        raise ValueError("unedited_kindle_notes requires 'vault_path' in config or services")
    return Path(str(path_raw)).expanduser()
