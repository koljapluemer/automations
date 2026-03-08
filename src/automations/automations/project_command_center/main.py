from __future__ import annotations

import json
import random
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
from jinja2 import Environment, FileSystemLoader

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec

HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)

_SCHEMA_PATH = Path(__file__).parent / "project_json_schema.json"
_SCHEMA: dict[str, Any] = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))

IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)", re.IGNORECASE)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".avif"}


class ProjectCommandCenterAutomation(Automation):
    spec = AutomationSpec(
        id="project_command_center",
        title="Project Command Center",
        description="Collect project data from git repos, scaffold doc/project.json from GitHub, and feed the dashboard.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        git_project_folder = _resolve_required(ctx, "git_project_folder")
        output_data_folder = _resolve_required(ctx, "project_output_data_folder")
        output_img_folder = _resolve_required(ctx, "project_data_output_img_folder")

        output_data_folder.mkdir(parents=True, exist_ok=True)
        output_img_folder.mkdir(parents=True, exist_ok=True)

        # --- GitHub: fetch repos and scaffold doc/project.json ---
        github_repos: dict[str, dict[str, Any]] = {}
        active_count = 0
        total_count = 0
        notes_written = 0

        shared = ctx.config.settings
        service_cfg = ctx.services.service_config("github")
        username = shared.get("github_username") or service_cfg.get("username")
        token = shared.get("github_token") or service_cfg.get("token")

        if username and token:
            force = "github" in ctx.force_flags
            cached = _load_cached_github(ctx, self.spec.id)

            if not force and cached is not None:
                total_count = cached.get("count", 0)
                active_count = cached.get("active_count", 0)
                ctx.log.append(self.spec.id, "github", {"cached": True, "count": total_count, "active_count": active_count})
            else:
                client = ctx.services.github_client(username=str(username), token=str(token))
                result = client.count_owned_repos()
                total_count = result.count
                active_count = client.count_active_repos()

                # Build name→repo map for repos with description AND homepage set
                for repo in result.repos:
                    desc = repo.get("description") or ""
                    url = repo.get("homepage") or ""
                    if desc and url:
                        github_repos[repo["name"]] = repo

                # Scaffold doc/project.json for matching local repos
                scaffolded = _scaffold_project_docs(git_project_folder, github_repos, ctx, self.spec.id)

                # Write Obsidian vault notes if configured
                vault_repo_folder = shared.get("vault_repo_folder")
                if vault_repo_folder:
                    notes_written = _write_repo_notes(Path(str(vault_repo_folder)).expanduser(), result.repos)

                ctx.log.append(self.spec.id, "github", {
                    "cached": False,
                    "count": total_count,
                    "active_count": active_count,
                    "scaffolded": scaffolded,
                    "notes_written": notes_written,
                })

        # --- Local scan: collect valid projects ---
        processed = 0
        skipped = 0
        images_copied = 0
        projects_with_image: list[dict[str, str]] = []

        for repo_dir in sorted(git_project_folder.iterdir()):
            if not repo_dir.is_dir():
                continue

            doc_path = repo_dir / "doc" / "project.json"
            if not doc_path.exists():
                ctx.log.append(self.spec.id, "skip", {"repo": repo_dir.name, "reason": "no doc/project.json"})
                skipped += 1
                continue

            try:
                doc = json.loads(doc_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                ctx.log.append(self.spec.id, "skip", {"repo": repo_dir.name, "reason": f"parse error: {e}"})
                skipped += 1
                continue

            try:
                jsonschema.validate(doc, _SCHEMA)
            except jsonschema.ValidationError as e:
                ctx.log.append(self.spec.id, "skip", {"repo": repo_dir.name, "reason": f"schema invalid: {e.message}"})
                skipped += 1
                continue

            project_id = doc["id"]
            project_name = doc["name"]

            output_doc = {
                "type": "project",
                "name": project_name,
                "description": doc["description"],
                "rows": 2,
                "cols": 2,
            }
            dest = output_data_folder / f"{project_id}.json"
            dest.write_text(json.dumps(output_doc, indent=2, ensure_ascii=False), encoding="utf-8")

            img_result = "none"
            readme = repo_dir / "README.md"
            if readme.exists():
                img_src = _find_first_image(readme, repo_dir)
                if img_src is not None:
                    dest_img = output_img_folder / f"{project_id}.webp"
                    _copy_as_webp(img_src, dest_img)
                    images_copied += 1
                    img_result = img_src.name
                    projects_with_image.append({"name": project_name, "image_path": str(dest_img)})

            ctx.log.append(self.spec.id, "processed", {
                "repo": repo_dir.name,
                "id": project_id,
                "name": project_name,
                "image": img_result,
            })
            processed += 1

        random_project = random.choice(projects_with_image) if projects_with_image else {}

        # --- Overview HTML ---
        overview_html_raw = shared.get("project_overview_html")
        if overview_html_raw:
            overview_path = Path(str(overview_html_raw)).expanduser()
            if not overview_path.is_absolute():
                overview_path = ctx.config.project_root / overview_path
            try:
                _generate_overview(git_project_folder, output_img_folder, overview_path)
                ctx.log.append(self.spec.id, "overview", {"path": str(overview_path)})
            except Exception as e:
                ctx.log.append(self.spec.id, "overview_error", {"error": str(e)})

        ctx.log.append(self.spec.id, "result", {
            "projects_processed": processed,
            "projects_skipped": skipped,
            "images_copied": images_copied,
            "active_count": active_count,
            "count": total_count,
        })

        return {
            "projects_processed": processed,
            "projects_skipped": skipped,
            "images_copied": images_copied,
            "random_project_name": random_project.get("name", ""),
            "random_project_image_path": random_project.get("image_path", ""),
            "active_count": active_count,
            "count": total_count,
        }


# --- Overview HTML ---

def _generate_overview(git_project_folder: Path, output_img_folder: Path, output_path: Path) -> None:
    # Pass 1: read all repo metadata
    repo_meta: dict[str, dict[str, Any]] = {}
    for repo_dir in sorted(git_project_folder.iterdir()):
        if not repo_dir.is_dir():
            continue

        project: dict[str, Any] | None = None
        doc_path = repo_dir / "doc" / "project.json"
        if doc_path.exists():
            try:
                doc = json.loads(doc_path.read_text(encoding="utf-8"))
                jsonschema.validate(doc, _SCHEMA)
                project = doc
            except Exception:
                pass

        belongs_to: dict[str, str] = {}
        belongs_path = repo_dir / "doc" / "belongs_to.json"
        if belongs_path.exists():
            try:
                raw = json.loads(belongs_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    belongs_to = {k: str(v) for k, v in raw.items()}
            except Exception:
                pass

        repo_meta[repo_dir.name] = {
            "project": project,
            "belongs_to": belongs_to,
            "issues": _collect_issues(repo_dir),
        }

    # Pass 2: build project structures
    # project_id → {id, name, description, image_path, repos[]}
    # Also track which repo defines each project, to prepend it as "main repo"
    projects: dict[str, dict[str, Any]] = {}
    project_defining_repo: dict[str, str] = {}  # pid → repo_name
    for repo_name, meta in repo_meta.items():
        if meta["project"] is None:
            continue
        pid = meta["project"]["id"]
        img = output_img_folder / f"{pid}.webp"
        projects[pid] = {
            "id": pid,
            "name": meta["project"]["name"],
            "description": meta["project"].get("description", ""),
            "image_path": str(img) if img.exists() else "",
            "repos": [],
        }
        project_defining_repo[pid] = repo_name

    # Attach repos to projects via belongs_to
    referenced: set[str] = set()
    for repo_name, meta in repo_meta.items():
        for pid, role in meta["belongs_to"].items():
            if pid not in projects:
                continue
            projects[pid]["repos"].append({
                "name": repo_name,
                "role": role,
                "issues": meta["issues"],
            })
            referenced.add(repo_name)

    # Prepend the defining repo as "main repo" if not already listed
    for pid, defining_repo in project_defining_repo.items():
        already_listed = any(r["name"] == defining_repo for r in projects[pid]["repos"])
        if not already_listed:
            projects[pid]["repos"].insert(0, {
                "name": defining_repo,
                "role": "main repo",
                "issues": repo_meta[defining_repo]["issues"],
            })
        referenced.add(defining_repo)

    # Orphans: no project.json and not referenced in any belongs_to
    orphans = [
        {"name": name, "issues": meta["issues"]}
        for name, meta in repo_meta.items()
        if meta["project"] is None and name not in referenced
    ]

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)))
    template = env.get_template("overview_template.html")
    html = template.render(
        projects=list(projects.values()),
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


# --- GitHub scaffolding ---

def _scaffold_project_docs(
    git_project_folder: Path,
    github_repos: dict[str, dict[str, Any]],
    ctx: AutomationContext,
    automation_id: str,
) -> int:
    scaffolded = 0
    for repo_dir in git_project_folder.iterdir():
        if not repo_dir.is_dir():
            continue
        gh = github_repos.get(repo_dir.name)
        if gh is None:
            continue

        doc_path = repo_dir / "doc" / "project.json"
        gh_description = gh.get("description") or ""
        gh_url = gh.get("homepage") or ""

        if not doc_path.exists():
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            doc = {
                "id": repo_dir.name,
                "name": repo_dir.name,
                "description": gh_description,
                "url": gh_url,
            }
            doc_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
            ctx.log.append(automation_id, "scaffold", {"repo": repo_dir.name, "action": "created"})
            scaffolded += 1
        else:
            try:
                doc = json.loads(doc_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            changed = False
            if not doc.get("description") and gh_description:
                doc["description"] = gh_description
                changed = True
            if not doc.get("url") and gh_url:
                doc["url"] = gh_url
                changed = True

            if changed:
                doc_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
                ctx.log.append(automation_id, "scaffold", {"repo": repo_dir.name, "action": "updated"})
                scaffolded += 1

    return scaffolded


def _load_cached_github(ctx: AutomationContext, automation_id: str) -> dict[str, Any] | None:
    latest = ctx.log.latest_event(automation_id, "github")
    if not latest or latest.get("cached") is True:
        return None
    count = latest.get("count")
    active_count = latest.get("active_count")
    if isinstance(count, int) and isinstance(active_count, int):
        return {"count": count, "active_count": active_count}
    return None


# --- Vault notes ---

def _write_repo_notes(folder: Path, repos: list[dict[str, Any]]) -> int:
    folder.mkdir(parents=True, exist_ok=True)
    count = 0
    for repo in repos:
        name = repo.get("name", "unknown")
        description = repo.get("description") or ""
        homepage = repo.get("homepage") or ""
        url = repo.get("html_url", "")
        stars = repo.get("stargazers_count", 0)
        pushed_at = repo.get("pushed_at", "")

        last_edited = ""
        if pushed_at:
            try:
                dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                last_edited = dt.strftime("%Y-%m-%d")
            except ValueError:
                last_edited = pushed_at[:10] if len(pushed_at) >= 10 else pushed_at

        lines = []
        if not repo.get("private", True):
            lines.extend(["---", "published: true", "---", ""])
        if description:
            lines.append(f"- **{description}**")
        lines.append(f"- [repository link]({url})")
        if homepage:
            lines.append(f"- [homepage]({homepage})")
        lines.append(f"- *Stars*: {stars}")
        if last_edited:
            lines.append(f"- *last edited at: {last_edited}*")
        lines.append("")

        (folder / f"⛁ {name}.md").write_text("\n".join(lines), encoding="utf-8")
        count += 1
    return count


# --- Helpers ---

def _resolve_required(ctx: AutomationContext, key: str) -> Path:
    raw = ctx.config.settings.get(key)
    if not raw:
        raise ValueError(f"missing config key: {key}")
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = ctx.config.project_root / path
    return path


def _find_first_image(readme: Path, repo_dir: Path) -> Path | None:
    content = readme.read_text(encoding="utf-8")
    for match in IMAGE_RE.finditer(content):
        url = match.group(1).strip()
        if url.startswith(("http://", "https://", "ftp://")):
            continue
        suffix = Path(url).suffix.lower()
        if suffix not in IMAGE_EXTS:
            continue
        candidate = (repo_dir / url).resolve()
        if candidate.exists():
            return candidate
    return None


def _copy_as_webp(src: Path, dest: Path) -> None:
    if src.suffix.lower() == ".webp":
        shutil.copy2(src, dest)
    else:
        from PIL import Image
        with Image.open(src) as img:
            img.save(dest, "WEBP")
