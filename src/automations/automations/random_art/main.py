from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationResult, AutomationSpec


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}


class RandomArtAutomation(Automation):
    spec = AutomationSpec(
        id="random_art",
        title="Random Art Display",
        description="Display a random image from a configured art folder on the dashboard.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        art_folder_raw = ctx.config.settings.get("art_folder")
        if not art_folder_raw:
            raise ValueError(
                "random_art requires 'art_folder' setting in config.yaml"
            )

        art_folder = Path(str(art_folder_raw)).expanduser().resolve()

        if not art_folder.exists():
            raise FileNotFoundError(f"Art folder does not exist: {art_folder}")

        if not art_folder.is_dir():
            raise ValueError(f"Art folder path is not a directory: {art_folder}")

        image_files = self._find_image_files(art_folder)

        if not image_files:
            raise ValueError(f"No image files found in art folder: {art_folder}")

        selected_image = random.choice(image_files)

        return {
            "image_path": str(selected_image),
            "image_name": selected_image.name,
            "total_images": len(image_files),
        }

    def _find_image_files(self, folder: Path) -> list[Path]:
        """Find all image files in the given folder (non-recursive)."""
        image_files = []

        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(item)

        return image_files
