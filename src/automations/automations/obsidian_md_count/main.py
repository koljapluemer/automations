from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec, ReportElement
from ...services.obsidian import count_markdown_files


class ObsidianMarkdownCountAutomation(Automation):
    spec = AutomationSpec(
        id="obsidian_md_count",
        title="Obsidian Markdown Count",
        description="Count markdown files in the configured Obsidian vault.",
        default_enabled=True,
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        settings = ctx.settings_for(self.spec.id, default_enabled=self.spec.default_enabled)
        vault_path = _resolve_vault_path(ctx.config.settings, settings.config, ctx)
        count = count_markdown_files(vault_path)
        return {"count": count, "vault_path": str(vault_path)}

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        value = None
        note = "Markdown notes"
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
                title="Obsidian Vault",
                value=value,
                note=note,
                status=status,
            )
        ]


def _resolve_vault_path(shared: dict[str, Any], legacy: dict[str, Any], ctx: AutomationContext) -> Path:
    path_raw = shared.get("vault_path") or legacy.get("vault_path")
    if not path_raw:
        service_cfg = ctx.services.service_config("obsidian")
        path_raw = service_cfg.get("vault_path")
    if not path_raw:
        raise ValueError("obsidian_md_count requires 'vault_path' in config or services")
    return Path(str(path_raw)).expanduser()
