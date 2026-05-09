"""Tests for app/financial/extractor.py"""
from __future__ import annotations

from uuid import uuid4

import pandas as pd
import pytest

from app.financial.extractor import extract_dataframe, _clean_number
from app.models.document import DocumentChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chunk(text: str) -> DocumentChunk:
    return DocumentChunk(document_id=uuid4(), index=0, text=text)


def chunks(*texts: str) -> list[DocumentChunk]:
    return [DocumentChunk(document_id=uuid4(), index=i, text=t) for i, t in enumerate(texts)]


# ---------------------------------------------------------------------------
# _clean_number unit tests
# ---------------------------------------------------------------------------

def test_clean_number_plain_integer() -> None:
    assert _clean_number("1000") == pytest.approx(1000.0)


def test_clean_number_with_commas() -> None:
    assert _clean_number("1,234,567") == pytest.approx(1_234_567.0)


def test_clean_number_with_currency_symbol() -> None:
    assert _clean_number("$1,200.50") == pytest.approx(1200.50)


def test_clean_number_negative_parentheses() -> None:
    assert _clean_number("(500)") == pytest.approx(-500.0)


def test_clean_number_k_suffix() -> None:
    assert _clean_number("1.5K") == pytest.approx(1_500.0)


def test_clean_number_m_suffix() -> None:
    assert _clean_number("2M") == pytest.approx(2_000_000.0)


def test_clean_number_b_suffix() -> None:
    assert _clean_number("1.2B") == pytest.approx(1_200_000_000.0)


def test_clean_number_non_numeric_returns_none() -> None:
    assert _clean_number("N/A") is None


def test_clean_number_empty_returns_none() -> None:
    assert _clean_number("") is None


# ---------------------------------------------------------------------------
# Markdown table parsing
# ---------------------------------------------------------------------------

_MD_TABLE_BASIC = """\
| Period | Revenue | COGS |
|--------|---------|------|
| 2022   | 100000  | 60000|
| 2023   | 110000  | 65000|
"""


def test_markdown_table_returns_dataframe() -> None:
    df = extract_dataframe(chunks(_MD_TABLE_BASIC))
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_markdown_table_columns_normalised() -> None:
    df = extract_dataframe(chunks(_MD_TABLE_BASIC))
    assert "revenue" in df.columns
    assert "cogs" in df.columns


def test_markdown_table_row_count() -> None:
    df = extract_dataframe(chunks(_MD_TABLE_BASIC))
    assert len(df) == 2


def test_markdown_table_values_parsed() -> None:
    df = extract_dataframe(chunks(_MD_TABLE_BASIC))
    assert df["revenue"].iloc[0] == pytest.approx(100_000.0)
    assert df["revenue"].iloc[1] == pytest.approx(110_000.0)
    assert df["cogs"].iloc[0] == pytest.approx(60_000.0)


def test_markdown_table_alias_total_revenue() -> None:
    text = """\
| Period | Total Revenue | Gross Profit |
|--------|---------------|--------------|
| 2023   | 500000        | 200000       |
"""
    df = extract_dataframe(chunks(text))
    assert "revenue" in df.columns
    assert "gross_profit" in df.columns


def test_markdown_table_currency_symbols_stripped() -> None:
    text = """\
| Year | Revenue    | COGS       |
|------|------------|------------|
| 2023 | $1,200,000 | $800,000   |
"""
    df = extract_dataframe(chunks(text))
    assert df["revenue"].iloc[0] == pytest.approx(1_200_000.0)
    assert df["cogs"].iloc[0] == pytest.approx(800_000.0)


def test_markdown_table_unknown_columns_ignored() -> None:
    text = """\
| Period | Product | Revenue | Notes    |
|--------|---------|---------|----------|
| 2023   | Widget  | 99000   | good year|
"""
    df = extract_dataframe(chunks(text))
    assert "revenue" in df.columns
    assert "product" not in df.columns
    assert "notes" not in df.columns


def test_markdown_table_multi_chunk() -> None:
    part1 = "Some intro text.\n\n"
    part2 = _MD_TABLE_BASIC
    df = extract_dataframe(chunks(part1, part2))
    assert len(df) == 2


def test_markdown_table_prefers_more_columns() -> None:
    """When two tables exist, prefer the one with more financial columns."""
    table1 = """\
| Period | Revenue |
|--------|---------|
| 2022   | 100000  |
"""
    table2 = """\
| Period | Revenue | COGS   | Gross Profit |
|--------|---------|--------|--------------|
| 2022   | 100000  | 60000  | 40000        |
| 2023   | 110000  | 65000  | 45000        |
"""
    df = extract_dataframe(chunks(table1 + "\n" + table2))
    assert "cogs" in df.columns
    assert "gross_profit" in df.columns


def test_markdown_table_no_financial_columns_ignored() -> None:
    """Table with no known financial columns should not be returned."""
    text = """\
| Product | Category | Units |
|---------|----------|-------|
| Widget  | Gadget   | 100   |
"""
    df = extract_dataframe(chunks(text))
    assert df.empty


# ---------------------------------------------------------------------------
# Key-value prose scanning
# ---------------------------------------------------------------------------

_KV_TEXT = """\
The company reported Total Revenue of $1,500,000 for the fiscal year.
Cost of Goods Sold was $900,000.
Gross Profit came in at $600,000.
Current Assets totalled $2,000,000 and Current Liabilities were $800,000.
"""


def test_kv_returns_dataframe() -> None:
    df = extract_dataframe(chunks(_KV_TEXT))
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_kv_revenue_found() -> None:
    df = extract_dataframe(chunks(_KV_TEXT))
    assert "revenue" in df.columns
    assert df["revenue"].iloc[0] == pytest.approx(1_500_000.0)


def test_kv_cogs_found() -> None:
    df = extract_dataframe(chunks(_KV_TEXT))
    assert df["cogs"].iloc[0] == pytest.approx(900_000.0)


def test_kv_gross_profit_found() -> None:
    df = extract_dataframe(chunks(_KV_TEXT))
    assert df["gross_profit"].iloc[0] == pytest.approx(600_000.0)


def test_kv_current_assets_found() -> None:
    df = extract_dataframe(chunks(_KV_TEXT))
    assert df["current_assets"].iloc[0] == pytest.approx(2_000_000.0)


def test_kv_current_liabilities_found() -> None:
    df = extract_dataframe(chunks(_KV_TEXT))
    assert df["current_liabilities"].iloc[0] == pytest.approx(800_000.0)


def test_kv_single_value() -> None:
    df = extract_dataframe(chunks("Net revenue was $500,000."))
    assert "revenue" in df.columns
    assert df["revenue"].iloc[0] == pytest.approx(500_000.0)


def test_kv_compact_millions() -> None:
    df = extract_dataframe(chunks("Revenue: $1.5M, Cost of Goods Sold: $0.9M"))
    assert df["revenue"].iloc[0] == pytest.approx(1_500_000.0)
    assert df["cogs"].iloc[0] == pytest.approx(900_000.0)


# ---------------------------------------------------------------------------
# No data / edge cases
# ---------------------------------------------------------------------------

def test_no_financial_data_returns_empty_dataframe() -> None:
    df = extract_dataframe(chunks("This document contains no financial data."))
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_empty_chunks_returns_empty_dataframe() -> None:
    df = extract_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_markdown_table_preferred_over_kv() -> None:
    """When a table is found it should take priority over KV prose."""
    text = """\
Revenue was $999 mentioned in prose.

| Period | Revenue |
|--------|---------|
| 2023   | 500000  |
"""
    df = extract_dataframe(chunks(text))
    # Table value (500000) should win over prose value (999)
    assert df["revenue"].iloc[0] == pytest.approx(500_000.0)
