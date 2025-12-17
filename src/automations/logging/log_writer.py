from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LogEntry:
    timestamp: str
    event: str
    run_id: str
    payload: dict[str, Any]


class LogWriter:
    def __init__(self, root: Path, run_date: date, run_id: str) -> None:
        self._root = root
        self._run_date = run_date
        self._run_id = run_id

    def append(self, automation_id: str, event: str, payload: dict[str, Any]) -> None:
        entry = LogEntry(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            event=event,
            run_id=self._run_id,
            payload=payload,
        )
        log_path = self._automation_path(automation_id)
        self._write_entry(log_path, entry)

    def append_run(self, event: str, payload: dict[str, Any]) -> None:
        entry = LogEntry(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            event=event,
            run_id=self._run_id,
            payload=payload,
        )
        log_path = self._run_path()
        self._write_entry(log_path, entry)

    def latest_event(self, automation_id: str, event: str) -> dict[str, Any] | None:
        log_path = self._automation_path(automation_id)
        if not log_path.exists():
            return None

        last: dict[str, Any] | None = None
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if data.get("event") != event:
                continue
            payload = data.get("payload")
            if isinstance(payload, dict):
                last = payload
        return last

    def _automation_path(self, automation_id: str) -> Path:
        date_dir = self._root / self._run_date.isoformat()
        return date_dir / f"{automation_id}.jsonl"

    def _run_path(self) -> Path:
        date_dir = self._root / self._run_date.isoformat()
        return date_dir / "run.jsonl"

    def _write_entry(self, path: Path, entry: LogEntry) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.__dict__, sort_keys=True, default=str))
            handle.write("\n")
