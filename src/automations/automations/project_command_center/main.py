from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec

HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


class ProjectCommandCenterAutomation(Automation):
    spec = AutomationSpec(
        id="project_command_center",
        title="Project Command Center",
        description="Read project definitions from data folder and generate project overview.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        shared = ctx.config.settings
        git_project_folder = _resolve_required(ctx, "git_project_folder")
        output_data_folder = _resolve_required(ctx, "project_output_data_folder")
        output_img_folder = _resolve_required(ctx, "project_data_output_img_folder")

        local_repo_count = sum(1 for p in git_project_folder.iterdir() if p.is_dir())

        projects = _read_projects(output_data_folder)

        projects_with_image: list[dict[str, str]] = []
        for project in projects:
            img = output_img_folder / f"{project['id']}.webp"
            if img.exists():
                projects_with_image.append({
                    "name": project["name"],
                    "image_path": str(img),
                })

        overview_html_raw = shared.get("project_overview_html")
        if overview_html_raw:
            overview_path = Path(str(overview_html_raw)).expanduser()
            if not overview_path.is_absolute():
                overview_path = ctx.config.project_root / overview_path
            try:
                _generate_overview(git_project_folder, output_data_folder, output_img_folder, overview_path)
                ctx.log.append(self.spec.id, "overview", {"path": str(overview_path)})
            except Exception as e:
                ctx.log.append(self.spec.id, "overview_error", {"error": str(e)})

        random_project = random.choice(projects_with_image) if projects_with_image else {}

        ctx.log.append(self.spec.id, "result", {
            "projects_total": len(projects),
            "projects_with_image": len(projects_with_image),
            "local_repo_count": local_repo_count,
        })

        return {
            "projects_total": len(projects),
            "projects_with_image": len(projects_with_image),
            "random_project_name": random_project.get("name", ""),
            "random_project_image_path": random_project.get("image_path", ""),
            "local_repo_count": local_repo_count,
        }


# --- Project reading ---

def _read_projects(data_folder: Path) -> list[dict[str, Any]]:
    if not data_folder.is_dir():
        return []
    projects = []
    for path in sorted(data_folder.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(doc, dict) or doc.get("type") != "project":
            continue
        if "id" not in doc:
            doc = {"id": path.stem, **doc}
        projects.append(doc)
    return projects


# --- Overview HTML ---

def _generate_overview(
    git_project_folder: Path,
    data_folder: Path,
    output_img_folder: Path,
    output_path: Path,
) -> None:
    from datetime import datetime

    # Pass 1: read project definitions from data folder
    project_defs: dict[str, dict[str, Any]] = {}
    for project in _read_projects(data_folder):
        pid = project.get("id") or Path(data_folder).stem
        img = output_img_folder / f"{pid}.webp"
        project_defs[pid] = {
            "id": pid,
            "name": project["name"],
            "description": project.get("description", ""),
            "image_path": str(img) if img.exists() else "",
            "repos": [],
        }

    # Pass 2: scan repos for doc/projects.json and issues
    repo_meta: dict[str, dict[str, Any]] = {}
    for repo_dir in sorted(git_project_folder.iterdir()):
        if not repo_dir.is_dir():
            continue
        projects_membership: dict[str, str] = {}
        projects_path = repo_dir / "doc" / "projects.json"
        if projects_path.exists():
            try:
                raw = json.loads(projects_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    projects_membership = {k: str(v) for k, v in raw.items()}
            except Exception:
                pass
        repo_meta[repo_dir.name] = {
            "projects": projects_membership,
            "issues": _collect_issues(repo_dir),
        }

    # Attach repos to projects
    referenced: set[str] = set()
    for repo_name, meta in repo_meta.items():
        for pid, role in meta["projects"].items():
            if pid not in project_defs:
                continue
            project_defs[pid]["repos"].append({
                "name": repo_name,
                "role": role,
                "issues": meta["issues"],
            })
            referenced.add(repo_name)

    # Orphans: not referenced in any projects.json
    orphans = [
        {"name": name, "issues": meta["issues"]}
        for name, meta in repo_meta.items()
        if name not in referenced
    ]

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)))
    template = env.get_template("overview_template.html")
    html = template.render(
        projects=list(project_defs.values()),
        orphans=orphans,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _collect_issues(repo_dir: Path) -> list[str]:
    issues_dir = repo_dir / "doc" / "issues"
    if not issues_dir.is_dir():
        return []
    names = []
    for md in sorted(issues_dir.glob("*.md")):
        try:
            content = md.read_text(encoding="utf-8")
        except OSError:
            continue
        match = HEADING_RE.search(content)
        names.append(match.group(1).strip() if match else md.stem)
    return names


# --- Helpers ---

def _resolve_required(ctx: AutomationContext, key: str) -> Path:
    raw = ctx.config.settings.get(key)
    if not raw:
        raise ValueError(f"missing config key: {key}")
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = ctx.config.project_root / path
    return path
