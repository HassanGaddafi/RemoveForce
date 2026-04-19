"""
tests/test_scanner.py
Unit tests for PathScanner.
"""

import os
import pytest
from core.scanner import PathScanner


@pytest.fixture
def scanner():
    return PathScanner()


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("hello world")
    return str(f)


@pytest.fixture
def temp_dir(tmp_path):
    d = tmp_path / "folder"
    d.mkdir()
    (d / "a.txt").write_text("aaa")
    (d / "b.txt").write_text("bbb")
    return str(d)


class TestPathScanner:

    def test_scan_file_exists(self, scanner, temp_file):
        report = scanner.scan(temp_file)
        assert report.exists is True
        assert report.is_file is True

    def test_scan_file_size(self, scanner, temp_file):
        report = scanner.scan(temp_file)
        assert report.total_size_bytes > 0

    def test_scan_directory(self, scanner, temp_dir):
        report = scanner.scan(temp_dir)
        assert report.exists is True
        assert report.is_file is False
        assert report.file_count == 2

    def test_scan_nonexistent(self, scanner):
        report = scanner.scan("/this/does/not/exist/xyz")
        assert report.exists is False
        assert len(report.warnings) > 0

    def test_scan_not_locked_normally(self, scanner, temp_file):
        report = scanner.scan(temp_file)
        assert isinstance(report.locked_by, list)

    def test_size_readable(self, scanner, temp_file):
        report = scanner.scan(temp_file)
        assert any(u in report.total_size_readable for u in ["B", "KB", "MB", "GB"])

    def test_system_path_detection(self, scanner):
        report = scanner.scan("C:\\Windows\\System32")
        if report.exists:
            assert report.is_system_path is True
