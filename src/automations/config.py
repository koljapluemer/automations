from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import yaml

DEFAULT_SCREEN_WIDTH = 2560
DEFAULT_SCREEN_HEIGHT = 1600


@dataclass(frozen=True)
class Config:
    obsidian_vault_path: Path
    github_username: str
    github_token: str
    screen_width: int
    screen_height: int
    output_html: Path


def project_root() -> Path:
    env_root = os.getenv("AUTOMATIONS_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def load_config(root: Path | None = None, filename: str = "config.yaml") -> Config:
    base = root or project_root()
    config_path = base / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    missing = [
        key
        for key in ("obsidian-vault-path", "github-username", "github-token")
        if key not in raw
    ]
    if missing:
        raise ValueError(f"Missing config keys: {', '.join(missing)}")

    obsidian_raw = str(raw["obsidian-vault-path"]).strip()
    github_username = str(raw["github-username"]).strip()
    github_token = str(raw["github-token"]).strip()

    if not obsidian_raw:
        raise ValueError("obsidian-vault-path must not be empty")
    if not github_username:
        raise ValueError("github-username must not be empty")
    if not github_token:
        raise ValueError("github-token must not be empty")

    obsidian_vault_path = Path(obsidian_raw).expanduser()

    screen_width = int(raw.get("screen-width", DEFAULT_SCREEN_WIDTH))
    screen_height = int(raw.get("screen-height", DEFAULT_SCREEN_HEIGHT))

    output_html = base / "output" / "stats.html"

    return Config(
        obsidian_vault_path=obsidian_vault_path,
        github_username=github_username,
        github_token=github_token,
        screen_width=screen_width,
        screen_height=screen_height,
        output_html=output_html,
    )
