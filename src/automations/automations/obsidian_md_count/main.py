from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec, ReportElement
from ...services.obsidian import count_markdown_files, count_zettelkasten_notes, count_leaf_notes


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
        total_count = count_markdown_files(vault_path)
        zk_count = count_zettelkasten_notes(vault_path)
        leaf_count = count_leaf_notes(vault_path)

        zk_percentage = (zk_count / total_count * 100) if total_count > 0 else 0
        leaf_percentage = (leaf_count / total_count * 100) if total_count > 0 else 0

        return {
            "count": total_count,
            "zk_count": zk_count,
            "leaf_count": leaf_count,
            "zk_percentage": zk_percentage,
            "leaf_percentage": leaf_percentage,
            "vault_path": str(vault_path)
        }

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        status = result.status
        if result.status != "ok":
            return [
                ReportElement(
                    id=f"{self.spec.id}_total",
                    kind="stat",
                    title="Obsidian Vault",
                    value="N/A",
                    note="",
                    status=status,
                )
            ]

        total_count = result.payload.get("count", 0)
        zk_count = result.payload.get("zk_count", 0)
        leaf_count = result.payload.get("leaf_count", 0)
        zk_percentage = result.payload.get("zk_percentage", 0)
        leaf_percentage = result.payload.get("leaf_percentage", 0)

        return [
            ReportElement(
                id=f"{self.spec.id}_total",
                kind="stat",
                title="Total Notes",
                value=str(total_count),
                note="",
                status=status,
            ),
            ReportElement(
                id=f"{self.spec.id}_zk_count",
                kind="stat",
                title="Zettelkasten",
                value=str(zk_count),
                note="",
                status=status,
            ),
            ReportElement(
                id=f"{self.spec.id}_zk_pct",
                kind="stat",
                title="% in ZK",
                value=f"{zk_percentage:.1f}%",
                note="",
                status=status,
            ),
            ReportElement(
                id=f"{self.spec.id}_leaf_pct",
                kind="stat",
                title="% Leaves",
                value=f"{leaf_percentage:.1f}%",
                note="",
                status=status,
            ),
        ]


def _resolve_vault_path(shared: dict[str, Any], legacy: dict[str, Any], ctx: AutomationContext) -> Path:
    path_raw = shared.get("vault_path") or legacy.get("vault_path")
    if not path_raw:
        service_cfg = ctx.services.service_config("obsidian")
        path_raw = service_cfg.get("vault_path")
    if not path_raw:
        raise ValueError("obsidian_md_count requires 'vault_path' in config or services")
    return Path(str(path_raw)).expanduser()
