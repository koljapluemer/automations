from __future__ import annotations

from pathlib import Path


def count_markdown_files(vault_path: Path) -> int:
    if not vault_path.exists():
        raise FileNotFoundError(f"Obsidian vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise NotADirectoryError(f"Obsidian vault path is not a directory: {vault_path}")

    return sum(
        1 for path in vault_path.rglob("*.md")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(vault_path).parts[:-1])
    )
