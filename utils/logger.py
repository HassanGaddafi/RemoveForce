"""
utils/logger.py
Persistent logger — writes every operation to a timestamped log file.
"""

import os
import logging
from datetime import datetime
from pathlib import Path


LOG_DIR = Path.home() / ".removeforce" / "logs"


class AppLogger:
    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"removeforce_{datetime.now().strftime('%Y-%m-%d')}.log"

        self._logger = logging.getLogger("RemoveForce")
        self._logger.setLevel(logging.DEBUG)

        if not self._logger.handlers:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
            fh.setFormatter(fmt)
            self._logger.addHandler(fh)

        self._callbacks = []

    def add_callback(self, cb):
        """Register a UI callback to receive log messages in real-time."""
        self._callbacks.append(cb)

    def log(self, message: str, level: str = "INFO"):
        level = level.upper()
        getattr(self._logger, level.lower(), self._logger.info)(message)
        for cb in self._callbacks:
            try:
                cb(f"[{level}] {message}")
            except Exception:
                pass

    def get_recent_logs(self, n: int = 100) -> list[str]:
        log_file = LOG_DIR / f"removeforce_{datetime.now().strftime('%Y-%m-%d')}.log"
        if not log_file.exists():
            return []
        lines = log_file.read_text(encoding="utf-8").splitlines()
        return lines[-n:]

    @staticmethod
    def get_all_log_files() -> list[Path]:
        if not LOG_DIR.exists():
            return []
        return sorted(LOG_DIR.glob("*.log"), reverse=True)
