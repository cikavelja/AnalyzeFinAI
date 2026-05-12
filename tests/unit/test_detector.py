"""Tests for app/ingestion/detector.py"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.exceptions import IngestionError
from app.ingestion.detector import detect_file_type

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def txt_file(tmp_path: Path) -> str:
    p = tmp_path / "sample.txt"
    p.write_text("hello world", encoding="utf-8")
    return str(p)


@pytest.fixture
def pdf_file(tmp_path: Path) -> str:
    p = tmp_path / "report.pdf"
    p.write_bytes(b"%PDF-1.4 fake pdf content")
    return str(p)


@pytest.fixture
def csv_file(tmp_path: Path) -> str:
    p = tmp_path / "data.csv"
    p.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------

def test_detect_file_type_txt_returns_txt_mime(txt_file: str) -> None:
    ext, mime = detect_file_type(txt_file)
    assert ext == ".txt"
    assert "text" in mime


def test_detect_file_type_pdf_returns_pdf_mime(pdf_file: str) -> None:
    ext, mime = detect_file_type(pdf_file)
    assert ext == ".pdf"
    assert mime == "application/pdf"


def test_detect_file_type_csv_returns_csv_mime(csv_file: str) -> None:
    ext, mime = detect_file_type(csv_file)
    assert ext == ".csv"


def test_detect_file_type_returns_lowercase_extension(tmp_path: Path) -> None:
    p = tmp_path / "DOC.TXT"
    p.write_text("test", encoding="utf-8")
    ext, _ = detect_file_type(str(p))
    assert ext == ".txt"


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

def test_detect_file_type_missing_file_raises_ingestion_error() -> None:
    with pytest.raises(IngestionError, match="not found"):
        detect_file_type("/nonexistent/path/file.pdf")


def test_detect_file_type_unsupported_extension_raises_ingestion_error(
    tmp_path: Path,
) -> None:
    p = tmp_path / "file.xyz"
    p.write_bytes(b"data")
    with pytest.raises(IngestionError, match="Unsupported file extension"):
        detect_file_type(str(p))


def test_detect_file_type_directory_raises_ingestion_error(tmp_path: Path) -> None:
    with pytest.raises(IngestionError, match="not a regular file"):
        detect_file_type(str(tmp_path))
