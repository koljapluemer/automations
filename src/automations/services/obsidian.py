from __future__ import annotations

from pathlib import Path


def count_markdown_files(vault_path: Path) -> int:
    """Count markdown files directly in the vault directory (not in subfolders)."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Obsidian vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise NotADirectoryError(f"Obsidian vault path is not a directory: {vault_path}")

    return sum(1 for path in vault_path.glob("*.md") if path.is_file())


def count_location_occurrences(vault_path: Path) -> int:
    """Count occurrences of 'location: ' in markdown files (excludes hidden directories)."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Obsidian vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise NotADirectoryError(f"Obsidian vault path is not a directory: {vault_path}")

    count = 0
    for path in vault_path.rglob("*.md"):
        # Skip files in hidden directories (starting with ".")
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(vault_path).parts[:-1]):
            continue

        try:
            content = path.read_text(encoding="utf-8")
            count += content.count("location: ")
        except (UnicodeDecodeError, PermissionError):
            # Skip files that can't be read
            continue

    return count


def count_zettelkasten_notes(vault_path: Path) -> int:
    """Count markdown files containing 'zk-id:' directly in the vault directory."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Obsidian vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise NotADirectoryError(f"Obsidian vault path is not a directory: {vault_path}")

    count = 0
    for path in vault_path.glob("*.md"):
        if not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
            if "zk-id:" in content:
                count += 1
        except (UnicodeDecodeError, PermissionError):
            continue

    return count


def count_leaf_notes(vault_path: Path) -> int:
    """Count markdown files NOT containing '[[' directly in the vault directory."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Obsidian vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise NotADirectoryError(f"Obsidian vault path is not a directory: {vault_path}")

    count = 0
    for path in vault_path.glob("*.md"):
        if not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
            if "[[" not in content:
                count += 1
        except (UnicodeDecodeError, PermissionError):
            continue

    return count
