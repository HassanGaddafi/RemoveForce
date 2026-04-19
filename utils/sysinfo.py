"""
utils/sysinfo.py
System information helpers used by the GUI.
"""

import os
import platform
import ctypes
import psutil
from datetime import datetime


def get_system_info() -> dict:
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_admin": _is_admin(),
        "disk_free": _disk_free(),
        "ram_total": _ram_total(),
        "ram_available": _ram_available(),
    }


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _disk_free() -> str:
    try:
        usage = psutil.disk_usage("C:\\")
        gb = usage.free / (1024 ** 3)
        return f"{gb:.1f} GB free"
    except Exception:
        return "unknown"


def _ram_total() -> str:
    try:
        gb = psutil.virtual_memory().total / (1024 ** 3)
        return f"{gb:.1f} GB"
    except Exception:
        return "unknown"


def _ram_available() -> str:
    try:
        gb = psutil.virtual_memory().available / (1024 ** 3)
        return f"{gb:.1f} GB"
    except Exception:
        return "unknown"


def format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
