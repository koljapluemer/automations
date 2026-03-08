from __future__ import annotations

import json
import random
import re
import shutil
from pathlib import Path
from typing import Any

import jsonschema

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec

_SCHEMA_PATH = Path(__file__).parent / "project_json_schema.json"
_SCHEMA: dict[str, Any] = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))

IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)", re.IGNORECASE)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".avif"}


class ProjectCommandCenterAutomation(Automation):
    spec = AutomationSpec(
        id="project_command_center",
        title="Project Command Center",
        description="Collect project doc.json files and images from git repos into output folders.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        git_project_folder = _resolve_required(ctx, "git_project_folder")
        output_data_folder = _resolve_required(ctx, "project_output_data_folder")
        output_img_folder = _resolve_required(ctx, "project_data_output_img_folder")

        output_data_folder.mkdir(parents=True, exist_ok=True)
        output_img_folder.mkdir(parents=True, exist_ok=True)

        processed = 0
        skipped = 0
        images_copied = 0
        projects_with_image: list[dict[str, str]] = []

        for repo_dir in sorted(git_project_folder.iterdir()):
            if not repo_dir.is_dir():
                continue

            doc_path = repo_dir / "doc/project.json"
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

            dest = output_data_folder / f"{project_id}.json"
            dest.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

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

        # Pick a random project with image for the dashboard
        random_project = random.choice(projects_with_image) if projects_with_image else {}

        ctx.log.append(self.spec.id, "result", {
            "projects_processed": processed,
            "projects_skipped": skipped,
            "images_copied": images_copied,
            "random_project": random_project,
        })

        return {
            "projects_processed": processed,
            "projects_skipped": skipped,
            "images_copied": images_copied,
            "random_project_name": random_project.get("name", ""),
            "random_project_image_path": random_project.get("image_path", ""),
        }


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
