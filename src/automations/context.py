from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .config import AppConfig
from .logging.log_writer import LogWriter
from .services.registry import ServiceRegistry


@dataclass(frozen=True)
class AutomationContext:
    config: AppConfig
    services: ServiceRegistry
    log: LogWriter
    run_date: date
    run_id: str
    report_path: Path | None = None
    force_flags: frozenset[str] = frozenset()
