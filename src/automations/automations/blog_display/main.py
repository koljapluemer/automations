from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec

# Matches the dashboard's own body text color (see report/template.html).
DASHBOARD_FONT_COLOR = "#e2e8f0"
PREVIEW_FILENAME = ".dashboard_preview.html"
FONT_OVERRIDE_STYLE = (
    f"<style>*, *::before, *::after {{ color: {DASHBOARD_FONT_COLOR} !important}} .back{{display:none}}</style>"
)


class BlogDisplayAutomation(Automation):
    spec = AutomationSpec(
        id="blog_display",
        title="Blog Post Display",
        description="Display a random blog post from a configured blog folder on the dashboard.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        blog_folder_raw = ctx.config.settings.get("blog_folder")
        if not blog_folder_raw:
            raise ValueError(
                "blog_display requires 'blog_folder' setting in config.yaml"
            )

        blog_folder = Path(str(blog_folder_raw)).expanduser().resolve()

        if not blog_folder.exists():
            raise FileNotFoundError(f"Blog folder does not exist: {blog_folder}")

        if not blog_folder.is_dir():
            raise ValueError(f"Blog folder path is not a directory: {blog_folder}")

        html_files = self._find_post_files(blog_folder)

        if not html_files:
            raise ValueError(f"No blog post HTML files found in blog folder: {blog_folder}")

        selected_post = random.choice(html_files)
        preview_path = self._write_preview(blog_folder, selected_post)

        return {
            "blog_html_path": str(preview_path),
            "blog_html_name": selected_post.name,
            "total_posts": len(html_files),
        }

    def _find_post_files(self, folder: Path) -> list[Path]:
        """Find all *.html files in the given folder, excluding index.html (non-recursive)."""
        html_files = []

        for item in folder.iterdir():
            if (
                item.is_file()
                and item.suffix.lower() == ".html"
                and item.name.lower() != "index.html"
                and item.name != PREVIEW_FILENAME
            ):
                html_files.append(item)

        return html_files

    def _write_preview(self, folder: Path, post: Path) -> Path:
        """Write a copy of the post with a forced font color, alongside the original.

        The copy is written into the same directory as the source post so that
        its relative image/stylesheet references keep resolving correctly.
        """
        content = post.read_text(encoding="utf-8")

        lower_content = content.lower()
        head_close_idx = lower_content.rfind("</head>")
        if head_close_idx != -1:
            content = (
                content[:head_close_idx] + FONT_OVERRIDE_STYLE + content[head_close_idx:]
            )
        else:
            content = FONT_OVERRIDE_STYLE + content

        preview_path = folder / PREVIEW_FILENAME
        preview_path.write_text(content, encoding="utf-8")
        return preview_path
