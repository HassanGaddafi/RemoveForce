"""
utils/history.py
Stores a persistent history of all deletion operations as JSON.
"""

import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


HISTORY_DIR = Path.home() / ".removeforce" / "history"


@dataclass
class HistoryEntry:
    timestamp: str
    path: str
    success: bool
    method_used: str
    processes_killed: list[str]
    duration_ms: float
    error: Optional[str] = None
    size_bytes: int = 0
    file_count: int = 0


class HistoryManager:

    def __init__(self):
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        self._file = HISTORY_DIR / "history.json"
        self._entries: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self._file.exists():
            try:
                return json.loads(self._file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self):
        self._file.write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def record(self, entry: HistoryEntry):
        self._entries.insert(0, asdict(entry))
        # Keep only last 500 entries
        self._entries = self._entries[:500]
        self._save()

    def get_all(self) -> list[dict]:
        return self._entries

    def get_stats(self) -> dict:
        total = len(self._entries)
        successes = sum(1 for e in self._entries if e.get("success"))
        total_size = sum(e.get("size_bytes", 0) for e in self._entries if e.get("success"))
        total_files = sum(e.get("file_count", 0) for e in self._entries if e.get("success"))

        return {
            "total_operations": total,
            "successful": successes,
            "failed": total - successes,
            "total_size_freed": total_size,
            "total_files_deleted": total_files,
        }

    def clear(self):
        self._entries = []
        self._save()
