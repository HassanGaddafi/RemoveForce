# Changelog

All notable changes to RemoveForce are documented here.

---

## [2.0.0] — 2024-04-19

### Added
- Multi-strategy deletion engine with 5 escalating methods
- Pre-scan report: size, file count, lock detection, system path warnings
- Persistent operation history stored as JSON (`~/.removeforce/history/`)
- Daily log files stored at `~/.removeforce/logs/`
- History tab showing all past operations with stats (total, success, freed space)
- Logs tab with live log stream and color-coded severity levels
- System info tab: OS version, RAM, disk space, Python version, admin status
- `PathScanner` module for non-destructive pre-analysis
- `AppLogger` with real-time UI callback system
- `HistoryManager` with stats aggregation
- Full unit test suite (`tests/test_engine.py`, `tests/test_scanner.py`)
- System path protection — warns before deleting Windows directories
- Auto-elevation: relaunches with admin rights if needed
- Confirmation checkbox to prevent accidental deletion

### Changed
- Complete rewrite of the GUI — multi-tab layout, professional dark theme
- Deletion now runs on a background thread — UI stays responsive
- Engine now tries CMD force-delete and MoveFileEx reboot-schedule as final fallbacks

### Fixed
- Read-only files that previously caused silent failures
- Processes that ignored `terminate()` are now force-killed

---

## [1.0.0] — 2023-11-01

### Added
- Initial release
- Basic GUI with file/folder selection
- Single-strategy deletion: kill locking process + shutil.rmtree
- Arabic UI
