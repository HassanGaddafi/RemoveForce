"""
core/scanner.py
Pre-scan a path to report what's locked, who's locking it, and what will be deleted.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
import psutil


@dataclass
class ScanReport:
    path: str
    is_file: bool
    exists: bool
    total_size_bytes: int = 0
    file_count: int = 0
    folder_count: int = 0
    locked_by: list[dict] = field(default_factory=list)
    is_system_path: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def total_size_readable(self) -> str:
        size = self.total_size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def is_locked(self) -> bool:
        return len(self.locked_by) > 0


# Paths that should never be deleted
PROTECTED_PATHS = {
    "C:\\Windows",
    "C:\\Windows\\System32",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Users",
    os.environ.get("WINDIR", "C:\\Windows"),
    os.environ.get("SystemRoot", "C:\\Windows"),
}


class PathScanner:

    def scan(self, path: str) -> ScanReport:
        path = os.path.abspath(path)
        report = ScanReport(path=path, is_file=os.path.isfile(path), exists=os.path.exists(path))

        if not report.exists:
            report.warnings.append("Path does not exist.")
            return report

        # Check if protected
        for protected in PROTECTED_PATHS:
            if path.lower().startswith(protected.lower()):
                report.is_system_path = True
                report.warnings.append(
                    f"WARNING: This path is inside a protected system directory ({protected}). "
                    "Deleting it may break Windows."
                )
                break

        # Calculate size and counts
        if os.path.isfile(path):
            report.file_count = 1
            report.total_size_bytes = os.path.getsize(path)
        else:
            for root, dirs, files in os.walk(path):
                report.folder_count += len(dirs)
                for f in files:
                    report.file_count += 1
                    try:
                        report.total_size_bytes += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass

        # Find locking processes
        for proc in psutil.process_iter(["pid", "name", "username", "open_files"]):
            try:
                open_files = proc.info.get("open_files") or []
                for f in open_files:
                    if f.path == path or (os.path.isdir(path) and f.path.startswith(path)):
                        report.locked_by.append({
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "user": proc.info.get("username", "unknown"),
                        })
                        break
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

        return report
