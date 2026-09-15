from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec

SERIES = (
    ("noteCount", "#e8935f"),
    ("relationCount", "#3fb5b0"),
    ("islandCount", "#d98f45"),
    ("orphanCount", "#a07b63"),
)


class GraphirstStatsAutomation(Automation):
    spec = AutomationSpec(
        id="graphirst_stats",
        title="Graphirst Stats",
        description="Render a minimal line chart of graphirst's note/relation history.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        settings_path_raw = ctx.config.settings.get("graphirst_settings_path")
        if not settings_path_raw:
            raise ValueError(
                "graphirst_stats requires 'graphirst_settings_path' setting in config.yaml"
            )

        settings_path = Path(str(settings_path_raw)).expanduser().resolve()
        if not settings_path.exists():
            raise FileNotFoundError(f"Graphirst settings file does not exist: {settings_path}")

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        graph_path = data.get("graphPath")
        history = (data.get("statsHistory") or {}).get(graph_path, [])
        if not history:
            raise ValueError(f"No stats history found for graph path: {graph_path}")

        history = sorted(history, key=lambda entry: entry["date"])
        series_values = {key: [entry["last"][key] for entry in history] for key, _ in SERIES}

        output_path_raw = ctx.config.settings.get(
            "graphirst_stats_output_image", "output/graphirst_stats.png"
        )
        output_path = Path(str(output_path_raw)).expanduser()
        if not output_path.is_absolute():
            output_path = ctx.config.project_root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        _render_chart(series_values, output_path)

        return {
            "image_path": str(output_path),
            "point_count": len(history),
        }


def _render_chart(series_values: dict[str, list[int]], output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10.5, 2.8), dpi=150)
    for key, color in SERIES:
        ax.plot(series_values[key], color=color, linewidth=2.5, solid_capstyle="round")

    ax.set_axis_off()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.tight_layout(pad=0)
    fig.savefig(output_path, transparent=True)
    plt.close(fig)
