"""Tests for app/conversion/markitdown_converter.py"""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import pytest_mock
from pydantic import ValidationError

from app.conversion.markitdown_converter import MarkitdownConverter
from app.exceptions import ConversionError


@pytest.fixture
def converter() -> MarkitdownConverter:
    return MarkitdownConverter()


@pytest.fixture
def txt_file(tmp_path: Path) -> str:
    p = tmp_path / "sample.txt"
    p.write_text("# Hello\nThis is a test document.", encoding="utf-8")
    return str(p)


@pytest.fixture
def csv_file(tmp_path: Path) -> str:
    p = tmp_path / "data.csv"
    p.write_text("name,value\nalpha,1\nbeta,2\n", encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------

async def test_markitdown_converter_txt_returns_text_content(
    converter: MarkitdownConverter, txt_file: str
) -> None:
    doc_id = uuid4()
    result = await converter.convert(txt_file, doc_id)

    assert result.document_id == doc_id
    assert "Hello" in result.text_content
    assert result.markdown_content == result.text_content
    assert result.converter_used == "MarkitdownConverter"


async def test_markitdown_converter_csv_returns_content(
    converter: MarkitdownConverter, csv_file: str
) -> None:
    result = await converter.convert(csv_file, uuid4())

    assert result.text_content  # non-empty
    assert result.converter_used == "MarkitdownConverter"


async def test_markitdown_converter_result_is_frozen(
    converter: MarkitdownConverter, txt_file: str
) -> None:
    result = await converter.convert(txt_file, uuid4())
    with pytest.raises(ValidationError):  # frozen Pydantic model raises on mutation
        result.text_content = "overwritten"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

async def test_markitdown_converter_missing_file_raises(
    converter: MarkitdownConverter, tmp_path: Path
) -> None:
    with pytest.raises(ConversionError, match="File not found"):
        await converter.convert(str(tmp_path / "ghost.txt"), uuid4())


async def test_markitdown_converter_directory_raises(
    converter: MarkitdownConverter, tmp_path: Path
) -> None:
    with pytest.raises(ConversionError, match="not a file"):
        await converter.convert(str(tmp_path), uuid4())


async def test_markitdown_converter_library_error_raises_conversion_error(
    converter: MarkitdownConverter, txt_file: str, mocker: pytest_mock.MockerFixture
) -> None:
    mocker.patch.object(converter._md, "convert", side_effect=RuntimeError("boom"))
    with pytest.raises(ConversionError, match="MarkItDown failed"):
        await converter.convert(txt_file, uuid4())
