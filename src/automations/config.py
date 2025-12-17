from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import os

import yaml

DEFAULT_SCREEN_WIDTH = 2560
DEFAULT_SCREEN_HEIGHT = 1600
DEFAULT_OUTPUT_HTML = "output/stats.html"


@dataclass(frozen=True)
class ReportConfig:
    screen_width: int
    screen_height: int
    output_html: Path


@dataclass(frozen=True)
class LoggingConfig:
    root: Path


@dataclass(frozen=True)
class AutomationSettings:
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    report: ReportConfig
    logging: LoggingConfig
    automations: dict[str, AutomationSettings]
    services: dict[str, Any]

    def automation_settings(self, automation_id: str, default_enabled: bool = True) -> AutomationSettings:
        settings = self.automations.get(automation_id)
        if settings:
            return settings
        return AutomationSettings(enabled=default_enabled, config={})


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
    output_html_raw = report_raw.get("output_html", DEFAULT_OUTPUT_HTML)
    output_html = _resolve_path(base, output_html_raw)

    logging_raw = raw.get("logging", {})
    if logging_raw is None:
        logging_raw = {}
    if not isinstance(logging_raw, dict):
        raise ValueError("logging must be a mapping")
    log_root_raw = logging_raw.get("root", base / "runtime" / "logs")
    log_root = _resolve_path(base, log_root_raw)

    automations_raw = raw.get("automations", {})
    if automations_raw is None:
        automations_raw = {}
    if not isinstance(automations_raw, dict):
        raise ValueError("automations must be a mapping")

    automations: dict[str, AutomationSettings] = {}
    for automation_id, settings_raw in automations_raw.items():
        if settings_raw is None:
            settings_raw = {}
        if not isinstance(settings_raw, dict):
            raise ValueError(f"automation '{automation_id}' must be a mapping")
        enabled = bool(settings_raw.get("enabled", True))
        config = {k: v for k, v in settings_raw.items() if k != "enabled"}
        automations[str(automation_id)] = AutomationSettings(enabled=enabled, config=config)

    services_raw = raw.get("services", {})
    if services_raw is None:
        services_raw = {}
    if not isinstance(services_raw, dict):
        raise ValueError("services must be a mapping")

    report = ReportConfig(
        screen_width=screen_width,
        screen_height=screen_height,
        output_html=output_html,
    )
    logging_config = LoggingConfig(root=log_root)

    return AppConfig(
        project_root=base,
        report=report,
        logging=logging_config,
        automations=automations,
        services=services_raw,
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
