from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..dto import DashboardDTO


def render_dashboard(dto: DashboardDTO) -> str:
    """Render dashboard HTML from DTO using Jinja2 template."""
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("template.html")
    return template.render(**dto.to_dict())
