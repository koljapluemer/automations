from __future__ import annotations

import base64
import json
import mimetypes
import random
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image
from jinja2 import Environment, FileSystemLoader

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec

IMAGE_RE = re.compile(r"!\[\[([^\]]+)\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
DESCRIPTION_RE = re.compile(r"^- \*\*(.+?)\*\*\s*$", re.MULTILINE)
OBSIDIAN_LINK_RE = re.compile(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]")

CARD_WIDTH = 1772   # 15cm at 300 DPI
CARD_HEIGHT = 1181  # 10cm at 300 DPI


class ProjectCardsAutomation(Automation):
    spec = AutomationSpec(
        id="project_cards",
        title="Project Cards",
        description="Generate 15cm x 10cm card images for Obsidian project notes.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        vault_path = _resolve_path(ctx, "vault_path")
        vault_media_path = _resolve_path(ctx, "vault_media_path")
        output_folder = _resolve_output_folder(ctx, "project_cards_output_folder", "output/project_cards")
        html_output_folder = _resolve_output_folder(ctx, "project_cards_html_output", "output/project_cards_html")
        output_folder.mkdir(parents=True, exist_ok=True)
        html_output_folder.mkdir(parents=True, exist_ok=True)

        template_dir = Path(__file__).parent
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("template.html")

        generated = 0
        skipped = 0
        valid_titles: set[str] = set()

        for note in sorted(vault_path.rglob("⌬*.md")):
            content = note.read_text(encoding="utf-8")
            image_path = _find_first_image(content, vault_media_path, note.parent, vault_path)

            if image_path is None or not _is_exact_dimensions(image_path, 1920, 1080):
                skipped += 1
                continue

            metadata = _extract_metadata(content, note.stem.lstrip("⌬").strip())
            title = metadata["title"]
            valid_titles.add(title)

            # HTML/JSON export
            dest_image = html_output_folder / image_path.name
            shutil.copy2(image_path, dest_image)
            json_data: dict[str, Any] = {"title": title, "image": image_path.name}
            if metadata.get("description"):
                json_data["description"] = metadata["description"]
            if metadata.get("archived"):
                json_data["archived"] = True
            if metadata.get("showcase"):
                json_data["showcase"] = True
            if metadata.get("failed"):
                json_data["failed"] = metadata["failed"]
            if metadata.get("links"):
                json_data["links"] = metadata["links"]
            json_path = html_output_folder / f"{title}.json"
            json_path.write_text(
                json.dumps(json_data, indent=2),
                encoding="utf-8",
            )

            # Card generation
            output_path = output_folder / f"{title}.png"

            if _is_up_to_date(note, image_path, output_path):
                generated += 1
                continue

            image_uri = _image_to_data_uri(image_path)

            html = template.render(
                image_uri=image_uri,
                title=title,
                description=metadata.get("description", ""),
                width=CARD_WIDTH,
                height=CARD_HEIGHT,
                font_size=round(CARD_WIDTH * 0.04),
                desc_font_size=round(CARD_WIDTH * 0.025),
            )

            html_path = output_folder / f".{title}.tmp.html"
            try:
                html_path.write_text(html, encoding="utf-8")
                _render_html_to_image(html_path, output_path)
                generated += 1
            finally:
                html_path.unlink(missing_ok=True)

        # Clean up stale files
        _cleanup_stale_files(output_folder, valid_titles, ".png")
        _cleanup_stale_files(html_output_folder, valid_titles, ".json")

        card_files = sorted(output_folder.glob("*.png"))
        random_card = str(random.choice(card_files)) if card_files else ""

        total_projects = generated + skipped

        return {
            "cards_generated": generated,
            "cards_skipped": skipped,
            "projects_total": total_projects,
            "projects_valid": generated,
            "output_folder": str(output_folder),
            "html_output_folder": str(html_output_folder),
            "random_card_path": random_card,
        }


def _resolve_path(ctx: AutomationContext, key: str) -> Path:
    raw = ctx.config.settings.get(key)
    if not raw:
        raise ValueError(f"missing config key: {key}")
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = ctx.config.project_root / path
    return path


def _resolve_output_folder(ctx: AutomationContext, key: str, default: str) -> Path:
    raw = ctx.config.settings.get(key, default)
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = ctx.config.project_root / path
    return path


def _extract_metadata(content: str, fallback_title: str) -> dict[str, Any]:
    result: dict[str, Any] = {"title": fallback_title}

    # Parse frontmatter
    fm_match = FRONTMATTER_RE.match(content)
    if fm_match:
        frontmatter = fm_match.group(1)
        in_links = False
        links: dict[str, str] = {}

        for line in frontmatter.splitlines():
            if line.startswith("title:"):
                value = line[6:].strip().strip('"').strip("'")
                if value:
                    result["title"] = value
            elif line.startswith("archived:"):
                value = line[9:].strip().lower()
                if value == "true":
                    result["archived"] = True
            elif line.startswith("showcase:"):
                value = line[9:].strip().lower()
                if value == "true":
                    result["showcase"] = True
            elif line.startswith("failed:"):
                value = line[7:].strip()
                if value:
                    result["failed"] = value
            elif line.startswith("links:"):
                in_links = True
            elif in_links and line.startswith("  "):
                # Parse nested link entry like "  Website: https://..."
                link_line = line.strip()
                if ":" in link_line:
                    key, url = link_line.split(":", 1)
                    # Replace dashes with spaces in key
                    key = key.replace("-", " ").strip()
                    links[key] = url.strip()
            elif in_links and not line.startswith(" "):
                in_links = False

        if links:
            result["links"] = links

    # Parse description from body (first line starting with "- **")
    desc_match = DESCRIPTION_RE.search(content)
    if desc_match:
        raw_desc = desc_match.group(1)
        # Strip Obsidian link syntax: [[link|alias]] -> alias, [[link]] -> link
        clean_desc = OBSIDIAN_LINK_RE.sub(r"\1", raw_desc)
        result["description"] = clean_desc.strip()

    return result


def _is_exact_dimensions(path: Path, width: int, height: int) -> bool:
    try:
        with Image.open(path) as img:
            return img.size == (width, height)
    except Exception:
        return False


def _cleanup_stale_files(folder: Path, valid_titles: set[str], suffix: str) -> None:
    for file in folder.glob(f"*{suffix}"):
        if file.name.startswith("."):
            continue
        title = file.stem
        if title not in valid_titles:
            file.unlink()


def _is_up_to_date(note: Path, image: Path, output: Path) -> bool:
    if not output.exists():
        return False
    output_mtime = output.stat().st_mtime
    return note.stat().st_mtime < output_mtime and image.stat().st_mtime < output_mtime


def _image_to_data_uri(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _find_first_image(
    content: str,
    vault_media_path: Path,
    note_dir: Path,
    vault_path: Path,
) -> Path | None:
    for ref in IMAGE_RE.findall(content):
        clean_ref = ref.split("|", 1)[0].strip()
        if not clean_ref:
            continue

        for base in (vault_media_path, note_dir, vault_path):
            candidate = base / clean_ref
            if candidate.exists():
                return candidate

    return None


def _render_html_to_image(html_path: Path, output_path: Path) -> None:
    html_uri = html_path.resolve().as_uri()

    for candidate in ("wkhtmltoimage", "chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        if shutil.which(candidate):
            _run_renderer(candidate, html_uri, output_path)
            return

    raise RuntimeError(
        "No HTML renderer available. Install wkhtmltoimage or chromium/google-chrome for headless rendering."
    )


def _run_renderer(renderer: str, html_uri: str, output_path: Path) -> None:
    if renderer == "wkhtmltoimage":
        cmd = [
            renderer,
            "--enable-local-file-access",
            "--width",
            str(CARD_WIDTH),
            "--height",
            str(CARD_HEIGHT),
            html_uri,
            str(output_path),
        ]
    elif renderer in {"chromium", "chromium-browser", "google-chrome", "google-chrome-stable"}:
        cmd = [
            renderer,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
            "--force-device-scale-factor=1",
            f"--window-size={CARD_WIDTH},{CARD_HEIGHT}",
            f"--screenshot={output_path}",
            html_uri,
        ]
    else:
        raise RuntimeError(f"Unsupported renderer: {renderer}")

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Renderer '{renderer}' failed: {stderr}")
