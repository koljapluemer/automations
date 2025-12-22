from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import os
import re
import shutil
from typing import Any, Iterable

import markdown

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec, ReportElement

IMAGE_RE = re.compile(r"!\[\[([^\]]+)\]\]")


@dataclass(frozen=True)
class EssayConfig:
    vault_path: Path
    vault_media_path: Path
    essay_include_string: str
    essay_output_folder: Path
    essay_media_folder: Path


class ObsidianEssayToWebsiteAutomation(Automation):
    spec = AutomationSpec(
        id="obsidian_essay_to_website",
        title="Obsidian Essay to Website",
        description="Convert selected Obsidian notes into bespoke HTML pages.",
        default_enabled=False,
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        settings = ctx.settings_for(self.spec.id, default_enabled=self.spec.default_enabled)
        config = _load_config(ctx.config.settings, ctx)

        config.essay_output_folder.mkdir(parents=True, exist_ok=True)
        config.essay_media_folder.mkdir(parents=True, exist_ok=True)

        matched_notes = list(_find_matching_notes(config.vault_path, config.essay_include_string))
        outputs = []
        images_copied = 0

        for note_path in matched_notes:
            content = note_path.read_text(encoding="utf-8")
            content = _strip_front_matter(content)
            image_refs = _find_image_refs(content)
            media_map = _copy_images(
                image_refs=image_refs,
                note_path=note_path,
                config=config,
            )
            images_copied += len(media_map)

            markdown_body = _replace_image_refs(
                content=content,
                media_map=media_map,
                output_dir=config.essay_output_folder,
            )
            html_body = _render_markdown(markdown_body)
            html = _render_page(title=note_path.stem, body_html=html_body)

            relative_output = note_path.relative_to(config.vault_path).with_suffix(".html")
            output_path = config.essay_output_folder / relative_output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")
            outputs.append(str(output_path))

        return {
            "notes_processed": len(matched_notes),
            "images_copied": images_copied,
            "outputs": outputs,
            "enabled": settings.enabled,
        }

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        return []


def _load_config(settings: dict[str, Any], ctx: AutomationContext) -> EssayConfig:
    required = [
        "vault_path",
        "vault_media_path",
        "essay_include_string",
        "essay_output_folder",
        "essay_media_folder",
    ]
    missing = [key for key in required if not settings.get(key)]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"obsidian_essay_to_website missing config keys: {missing_str}")

    return EssayConfig(
        vault_path=_resolve_path(ctx.config.project_root, settings["vault_path"]),
        vault_media_path=_resolve_path(ctx.config.project_root, settings["vault_media_path"]),
        essay_include_string=str(settings["essay_include_string"]),
        essay_output_folder=_resolve_path(ctx.config.project_root, settings["essay_output_folder"]),
        essay_media_folder=_resolve_path(ctx.config.project_root, settings["essay_media_folder"]),
    )


def _resolve_path(base: Path, raw_value: Any) -> Path:
    value = str(raw_value).strip()
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path


def _find_matching_notes(vault_path: Path, include_string: str) -> Iterable[Path]:
    for path in vault_path.rglob("*.md"):
        if _is_hidden(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if include_string in content:
            yield path


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _strip_front_matter(content: str) -> str:
    if not content.startswith("---"):
        return content
    lines = content.splitlines()
    if len(lines) < 2 or lines[0].strip() != "---":
        return content
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :])
    return content


def _find_image_refs(content: str) -> list[str]:
    refs = []
    for ref in IMAGE_RE.findall(content):
        clean_ref = ref.split("|", 1)[0].strip()
        if clean_ref:
            refs.append(clean_ref)
    return refs


def _copy_images(
    image_refs: list[str],
    note_path: Path,
    config: EssayConfig,
) -> dict[str, Path]:
    copied: dict[str, Path] = {}
    for ref in image_refs:
        source = _resolve_image_path(ref, note_path, config)
        rel_ref = Path(ref)
        dest = config.essay_media_folder / rel_ref
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        copied[ref] = dest
    return copied


def _resolve_image_path(ref: str, note_path: Path, config: EssayConfig) -> Path:
    candidate_paths = [
        config.vault_media_path / ref,
        note_path.parent / ref,
        config.vault_path / ref,
    ]
    for candidate in candidate_paths:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Image not found for '{ref}' (note: {note_path})")


def _replace_image_refs(content: str, media_map: dict[str, Path], output_dir: Path) -> str:
    def replacer(match: re.Match[str]) -> str:
        raw = match.group(1)
        ref = raw.split("|", 1)[0].strip()
        dest = media_map.get(ref)
        if not dest:
            raise FileNotFoundError(f"Image '{ref}' was not copied")
        rel = os.path.relpath(dest, output_dir)
        src = Path(rel).as_posix()
        return f'\n\n<div class="card image-card"><img src="{escape(src)}" alt="Image"></div>\n\n'

    return IMAGE_RE.sub(replacer, content)


def _render_markdown(content: str) -> str:
    html_body = markdown.markdown(content, extensions=["extra"])
    return f'<div class="essay">{html_body}</div>'


def _render_page(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <style>
    * {{
      box-sizing: border-box;
    }}

    html {{
      font-family: serif;
      color: #1c1c1c;
        max-width: 90ch;
        padding: 3em 1em;
        margin: 0 auto;
        line-height: 1.95;
        font-size: 1.45rem;
        font-weight: bold;
        font-family: serif;
    }}

    h1 {{
        font-family: sans-serif;
          font-size: clamp(1.8rem, 4vw + 1rem, 3rem);
  line-height: 1.1;
    }}

    body {{
      margin: 0;
      padding: 0;
      background: rgb(184, 72, 27);
      background-image: radial-gradient(rgb(126, 48, 17) 5%, transparent 0);
      background-size: 35px 35px;
      min-height: 100vh;
    }}

    .essay {{
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }}

    .essay p {{
      margin: 0;
    }}

    .card {{
      display: flex;
      justify-content: center;
      align-items: center;
      background: white;
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
    }}

    .image-card img {{
      max-width: 100%;
      height: auto;
      display: block;
    }}
  </style>
</head>
<body>
<h1 class="title">{escape(title)}</h1>
{body_html}
</body>
</html>
"""
