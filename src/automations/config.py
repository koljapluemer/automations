from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import os

import yaml

DEFAULT_SCREEN_WIDTH = 2560
DEFAULT_SCREEN_HEIGHT = 1600


@dataclass(frozen=True)
class ReportConfig:
    screen_width: int
    screen_height: int


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    report: ReportConfig
    services: dict[str, Any]
    settings: dict[str, Any]


def project_root() -> Path:
    env_root = os.getenv("AUTOMATIONS_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def load_config(root: Path | None = None, filename: str = "config.yaml") -> AppConfig:
    base = root or project_root()
    config_path = base / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a YAML mapping")

    report_raw = raw.get("report", {})
    if report_raw is None:
        report_raw = {}
    if not isinstance(report_raw, dict):
        raise ValueError("report must be a mapping")

    screen_width = int(report_raw.get("screen_width", DEFAULT_SCREEN_WIDTH))
    screen_height = int(report_raw.get("screen_height", DEFAULT_SCREEN_HEIGHT))

    services_raw = raw.get("services", {})
    if services_raw is None:
        services_raw = {}
    if not isinstance(services_raw, dict):
        raise ValueError("services must be a mapping")

    reserved = {"report", "services"}
    settings = {key: value for key, value in raw.items() if key not in reserved}

    report = ReportConfig(
        screen_width=screen_width,
        screen_height=screen_height,
    )

    return AppConfig(
        project_root=base,
        report=report,
        services=services_raw,
        settings=settings,
    )


def _resolve_path(base: Path, raw_value: Any) -> Path:
    if isinstance(raw_value, Path):
        return raw_value
    if raw_value is None:
        return base
    value = str(raw_value).strip()
    if not value:
        return base
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path
