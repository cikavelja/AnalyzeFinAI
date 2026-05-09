"""Tests for app/ingestion/validator.py"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.exceptions import IngestionError
from app.ingestion.validator import validate_file


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_file(tmp_path: Path) -> str:
    p = tmp_path / "valid.txt"
    p.write_text("some content here", encoding="utf-8")
    return str(p)


@pytest.fixture
def empty_file(tmp_path: Path) -> str:
    p = tmp_path / "empty.txt"
    p.write_bytes(b"")
    return str(p)


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------

def test_validate_file_valid_file_passes(valid_file: str) -> None:
    """A normal file should pass validation without raising."""
    validate_file(valid_file)  # should not raise


def test_validate_file_custom_max_size_passes(valid_file: str) -> None:
    """File within custom max_size limit passes."""
    validate_file(valid_file, max_size=10 * 1024 * 1024)  # 10 MB — plenty


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

def test_validate_file_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(IngestionError, match="does not exist"):
        validate_file(str(tmp_path / "ghost.txt"))


def test_validate_file_empty_file_raises(empty_file: str) -> None:
    with pytest.raises(IngestionError, match="empty"):
        validate_file(empty_file)


def test_validate_file_too_large_raises(tmp_path: Path) -> None:
    p = tmp_path / "big.txt"
    p.write_bytes(b"x" * 101)  # 101 bytes
    with pytest.raises(IngestionError, match="too large"):
        validate_file(str(p), max_size=100)


def test_validate_file_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(IngestionError, match="Not a regular file"):
        validate_file(str(tmp_path))
