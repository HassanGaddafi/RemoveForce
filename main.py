"""
RemoveForce v2.0
Force-delete locked files and folders on Windows with advanced process management.
Author: Hassan Gaddafi
"""

import sys
import os
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    """Re-launch the script with admin privileges."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )

if __name__ == "__main__":
    if not is_admin():
        elevate()
        sys.exit(0)

    from gui.app import RemoveForceApp
    app = RemoveForceApp()
    app.run()
