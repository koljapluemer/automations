from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .config import AppConfig, AutomationSettings
from .logging.log_writer import LogWriter
from .services.registry import ServiceRegistry


@dataclass(frozen=True)
class AutomationContext:
    config: AppConfig
    services: ServiceRegistry
    log: LogWriter
    run_date: date
    run_id: str

    def settings_for(self, automation_id: str, default_enabled: bool = True) -> AutomationSettings:
        return self.config.automation_settings(automation_id, default_enabled=default_enabled)
