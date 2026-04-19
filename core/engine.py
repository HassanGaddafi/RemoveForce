"""
core/engine.py
The heart of RemoveForce — handles process detection, unlocking, and deletion.
"""

import os
import shutil
import ctypes
import subprocess
import time
import stat
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import psutil


@dataclass
class DeletionResult:
    success: bool
    path: str
    method_used: str
    processes_killed: list[str]
    error: Optional[str] = None
    duration_ms: float = 0.0


class ForceDeleteEngine:
    """
    Multi-strategy forced deletion engine.
    Tries increasingly aggressive methods until the file/folder is deleted.
    """

    STRATEGIES = [
        "unlock_and_delete",
        "take_ownership",
        "remove_readonly",
        "cmd_force_delete",
        "schedule_on_reboot",
    ]

    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, message: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(message, level)

    # ─────────────────────────────────────────────────────────────
    # Step 1: Find and kill processes locking the target
    # ─────────────────────────────────────────────────────────────
    def find_locking_processes(self, path: str) -> list[dict]:
        """Return a list of processes that have the path open."""
        path = os.path.abspath(path)
        lockers = []

        for proc in psutil.process_iter(["pid", "name", "open_files", "exe"]):
            try:
                open_files = proc.info.get("open_files") or []
                for f in open_files:
                    if f.path == path or (
                        os.path.isdir(path) and f.path.startswith(path)
                    ):
                        lockers.append({
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "exe": proc.info.get("exe", "unknown"),
                        })
                        break
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

        return lockers

    def kill_locking_processes(self, path: str) -> list[str]:
        """Kill all processes locking the target. Returns names of killed processes."""
        lockers = self.find_locking_processes(path)
        killed = []

        for proc_info in lockers:
            try:
                proc = psutil.Process(proc_info["pid"])
                proc.terminate()
                proc.wait(timeout=3)
                killed.append(proc_info["name"])
                self._log(f"Terminated: {proc_info['name']} (PID {proc_info['pid']})")
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    killed.append(proc_info["name"])
                    self._log(f"Force-killed: {proc_info['name']} (PID {proc_info['pid']})", "WARN")
                except Exception as e:
                    self._log(f"Failed to kill {proc_info['name']}: {e}", "ERROR")
            except Exception as e:
                self._log(f"Error killing {proc_info['name']}: {e}", "ERROR")

        if killed:
            time.sleep(0.5)  # Give OS time to release handles

        return killed

    # ─────────────────────────────────────────────────────────────
    # Step 2: Remove read-only and hidden attributes
    # ─────────────────────────────────────────────────────────────
    def _remove_readonly(self, path: str):
        """Recursively remove read-only attribute from files."""
        def _make_writable(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for name in files + dirs:
                    full = os.path.join(root, name)
                    try:
                        os.chmod(full, stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
        else:
            try:
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────
    # Step 3: Take ownership via icacls / takeown (Windows only)
    # ─────────────────────────────────────────────────────────────
    def _take_ownership(self, path: str) -> bool:
        """Use Windows takeown and icacls to claim ownership."""
        try:
            subprocess.run(
                ["takeown", "/F", path, "/R", "/D", "Y"],
                capture_output=True, timeout=10
            )
            subprocess.run(
                ["icacls", path, "/grant", "Everyone:F", "/T"],
                capture_output=True, timeout=10
            )
            self._log(f"Took ownership of: {path}")
            return True
        except Exception as e:
            self._log(f"Ownership claim failed: {e}", "WARN")
            return False

    # ─────────────────────────────────────────────────────────────
    # Step 4: CMD force delete as fallback
    # ─────────────────────────────────────────────────────────────
    def _cmd_force_delete(self, path: str) -> bool:
        """Use cmd.exe commands to delete."""
        try:
            if os.path.isdir(path):
                result = subprocess.run(
                    ["cmd", "/c", "rd", "/s", "/q", path],
                    capture_output=True, timeout=30
                )
            else:
                result = subprocess.run(
                    ["cmd", "/c", "del", "/f", "/q", path],
                    capture_output=True, timeout=30
                )
            return result.returncode == 0
        except Exception as e:
            self._log(f"CMD delete failed: {e}", "WARN")
            return False

    # ─────────────────────────────────────────────────────────────
    # Step 5: Schedule deletion on next Windows reboot
    # ─────────────────────────────────────────────────────────────
    def _schedule_on_reboot(self, path: str) -> bool:
        """Use MoveFileEx to schedule deletion on next reboot."""
        try:
            MOVEFILE_DELAY_UNTIL_REBOOT = 0x4
            result = ctypes.windll.kernel32.MoveFileExW(path, None, MOVEFILE_DELAY_UNTIL_REBOOT)
            if result:
                self._log(f"Scheduled for deletion on reboot: {path}", "WARN")
            return bool(result)
        except Exception as e:
            self._log(f"Reboot schedule failed: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────────────────────────
    # Main delete method — orchestrates all strategies
    # ─────────────────────────────────────────────────────────────
    def delete(self, path: str) -> DeletionResult:
        start = time.time()
        path = os.path.abspath(path)
        killed_processes = []

        if not os.path.exists(path):
            return DeletionResult(
                success=False, path=path,
                method_used="none", processes_killed=[],
                error="Path does not exist"
            )

        self._log(f"Starting deletion: {path}")

        # Strategy 1: Kill lockers + standard delete
        killed_processes = self.kill_locking_processes(path)
        self._remove_readonly(path)

        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)

            duration = (time.time() - start) * 1000
            self._log(f"Deleted successfully via standard method in {duration:.0f}ms")
            return DeletionResult(
                success=True, path=path,
                method_used="unlock_and_delete",
                processes_killed=killed_processes,
                duration_ms=duration
            )
        except Exception:
            pass

        # Strategy 2: Take ownership then delete
        self._take_ownership(path)
        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)

            duration = (time.time() - start) * 1000
            self._log(f"Deleted via ownership takeover in {duration:.0f}ms")
            return DeletionResult(
                success=True, path=path,
                method_used="take_ownership",
                processes_killed=killed_processes,
                duration_ms=duration
            )
        except Exception:
            pass

        # Strategy 3: CMD force delete
        if self._cmd_force_delete(path):
            duration = (time.time() - start) * 1000
            self._log(f"Deleted via CMD in {duration:.0f}ms")
            return DeletionResult(
                success=True, path=path,
                method_used="cmd_force_delete",
                processes_killed=killed_processes,
                duration_ms=duration
            )

        # Strategy 4: Schedule on reboot
        if self._schedule_on_reboot(path):
            duration = (time.time() - start) * 1000
            return DeletionResult(
                success=True, path=path,
                method_used="schedule_on_reboot",
                processes_killed=killed_processes,
                error="File will be deleted on next Windows restart",
                duration_ms=duration
            )

        # All strategies failed
        duration = (time.time() - start) * 1000
        return DeletionResult(
            success=False, path=path,
            method_used="all_failed",
            processes_killed=killed_processes,
            error="All deletion strategies failed. Try rebooting in Safe Mode.",
            duration_ms=duration
        )
