"""
tests/test_engine.py
Unit tests for the ForceDeleteEngine.
"""

import os
import tempfile
import shutil
import pytest

from core.engine import ForceDeleteEngine
from utils.logger import AppLogger


@pytest.fixture
def engine():
    logger = AppLogger()
    return ForceDeleteEngine(logger=logger)


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test_file.txt"
    f.write_text("RemoveForce test file")
    return str(f)


@pytest.fixture
def temp_dir(tmp_path):
    d = tmp_path / "test_folder"
    d.mkdir()
    (d / "a.txt").write_text("file a")
    (d / "b.txt").write_text("file b")
    sub = d / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("file c")
    return str(d)


class TestForceDeleteEngine:

    def test_delete_existing_file(self, engine, temp_file):
        result = engine.delete(temp_file)
        assert result.success is True
        assert not os.path.exists(temp_file)

    def test_delete_existing_directory(self, engine, temp_dir):
        result = engine.delete(temp_dir)
        assert result.success is True
        assert not os.path.exists(temp_dir)

    def test_delete_nonexistent_path(self, engine):
        result = engine.delete("/nonexistent/path/xyz")
        assert result.success is False
        assert result.error is not None

    def test_result_has_method(self, engine, temp_file):
        result = engine.delete(temp_file)
        assert result.method_used != ""

    def test_result_has_duration(self, engine, temp_file):
        result = engine.delete(temp_file)
        assert result.duration_ms >= 0

    def test_find_locking_processes_empty(self, engine, temp_file):
        lockers = engine.find_locking_processes(temp_file)
        assert isinstance(lockers, list)

    def test_remove_readonly_file(self, engine, tmp_path):
        import stat
        f = tmp_path / "readonly.txt"
        f.write_text("test")
        os.chmod(str(f), stat.S_IREAD)
        engine._remove_readonly(str(f))
        result = engine.delete(str(f))
        assert result.success is True


class TestDeletionResult:

    def test_delete_returns_correct_path(self, engine, temp_file):
        result = engine.delete(temp_file)
        assert result.path == os.path.abspath(temp_file)

    def test_processes_killed_is_list(self, engine, temp_file):
        result = engine.delete(temp_file)
        assert isinstance(result.processes_killed, list)
