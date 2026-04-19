# RemoveForce v2.0

> Force-delete any locked file or folder on Windows — with a 5-strategy engine, full audit history, and a professional dark GUI.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Version](https://img.shields.io/badge/Version-2.0.0-E8354A?style=flat)

---

## The Problem

Windows locks files held open by running processes — and even after the program closes, the handle sometimes stays alive. You get:

```
The action can't be completed because the file is open in another program.
```

RemoveForce solves this completely.

---

## What's New in v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Deletion strategies | 1 | **5** |
| Pre-scan report | — | **Yes** |
| Operation history | — | **Yes (JSON)** |
| Log files | — | **Daily rotating logs** |
| System path protection | — | **Yes** |
| Unit tests | — | **Yes** |
| Background threading | — | **Yes** |
| Read-only removal | Basic | **Recursive** |
| Final fallback | — | **Reboot-scheduled deletion** |

---

## Deletion Engine — 5 Strategies

RemoveForce tries each strategy in order, escalating until the file is gone:

```
1. Unlock & Delete     → Kill locking processes → delete normally
2. Take Ownership      → icacls/takeown → delete
3. Remove Read-only    → Strip attributes recursively → delete
4. CMD Force Delete    → cmd.exe /del /f /q
5. Schedule on Reboot  → MoveFileEx (Windows API) — file gone after restart
```

---

## Project Structure

```
RemoveForce/
├── main.py                  # Entry point — auto-elevates to Administrator
├── core/
│   ├── engine.py            # ForceDeleteEngine — all 5 strategies
│   └── scanner.py           # PathScanner — non-destructive pre-analysis
├── gui/
│   └── app.py               # Multi-tab dark GUI (Delete / History / Logs / System)
├── utils/
│   ├── logger.py            # AppLogger — file logging + live UI callbacks
│   ├── history.py           # HistoryManager — JSON operation audit trail
│   └── sysinfo.py           # System information helpers
├── tests/
│   ├── test_engine.py       # Unit tests for ForceDeleteEngine
│   └── test_scanner.py      # Unit tests for PathScanner
├── requirements.txt
├── setup.py
├── CHANGELOG.md
└── LICENSE
```

---

## Installation

**Requirements:** Python 3.8+, Windows OS

```bash
git clone https://github.com/HassanGaddafi/RemoveForce.git
cd RemoveForce
pip install -r requirements.txt
```

---

## Usage

**Right-click your terminal → Run as Administrator**, then:

```bash
python main.py
```

> The app automatically requests Administrator privileges on launch if not already elevated.

### Workflow

1. **Browse** or paste the path of the file/folder you want to delete
2. Click **Scan Target** to see size, file count, and which process is locking it
3. Check the confirmation box
4. Click **FORCE DELETE**

---

## GUI Tabs

| Tab | What it shows |
|-----|--------------|
| Delete | Target selection, scan report, deletion controls |
| History | All past operations with success/fail stats and freed space |
| Logs | Live log stream — color-coded by severity |
| System | OS version, RAM, disk, Python version, admin status |

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Data Stored Locally

RemoveForce saves two things to your home directory:

```
~/.removeforce/
├── history/
│   └── history.json      # All operations (last 500)
└── logs/
    └── removeforce_YYYY-MM-DD.log
```

No data is sent anywhere. Everything stays on your machine.

---

## Important Notes

- Requires **Administrator privileges** — the app will prompt automatically
- The "Schedule on Reboot" strategy means the file disappears after the next Windows restart
- System path protection warns you before deleting anything inside `C:\Windows` or `C:\Program Files`
- **There is no undo.** Deleted files do not go to the Recycle Bin

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI | CustomTkinter |
| Process management | psutil |
| Windows API | ctypes |
| System commands | subprocess (takeown, icacls, cmd) |
| Storage | JSON, Python logging |
| Tests | pytest |

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Author

**Hassan Gaddafi**
[GitHub](https://github.com/HassanGaddafi) · [LinkedIn](https://www.linkedin.com/in/hassan-gaddafi) · [Email](mailto:hassanalkzafy@gmail.com)
