from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass(frozen=True)
class AutomationSpec:
    id: str
    title: str
    description: str
    default_enabled: bool = True
    stage: str = "primary"


AutomationStatus = Literal["ok", "skipped", "error"]


@dataclass(frozen=True)
class AutomationResult:
    automation_id: str
    status: AutomationStatus
    payload: dict[str, Any] = field(default_factory=dict)
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def duration_ms(self) -> int | None:
        if not self.started_at or not self.finished_at:
            return None
        delta = self.finished_at - self.started_at
        return int(delta.total_seconds() * 1000)


@dataclass(frozen=True)
class ReportElement:
    id: str
    kind: str
    title: str | None = None
    value: str | None = None
    note: str | None = None
    status: str | None = None
    col_span: int = 1
    row_span: int = 1
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReportModel:
    elements: list[ReportElement]
    generated_at: datetime
    screen_width: int
    screen_height: int
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RunSummary:
    results: tuple[AutomationResult, ...]
    report_path: str | None
    warnings: tuple[str, ...]
