from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LogEntry:
    event: str
    timestamp: str
    date: str
    payload: dict[str, Any]


class LogStore:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path

    def append(self, event: str, payload: dict[str, Any]) -> None:
        entry = LogEntry(
            event=event,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            date=date.today().isoformat(),
            payload=payload,
        )
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.__dict__, sort_keys=True))
            handle.write("\n")

    def latest_for_date(self, event: str, target_date: date) -> LogEntry | None:
        if not self.log_path.exists():
            return None

        last: LogEntry | None = None
        date_str = target_date.isoformat()
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if data.get("event") != event:
                continue
            if data.get("date") != date_str:
                continue
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
            last = LogEntry(
                event=data.get("event", ""),
                timestamp=str(data.get("timestamp", "")),
                date=str(data.get("date", "")),
                payload=payload,
            )
        return last
