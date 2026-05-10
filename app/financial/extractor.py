"""Financial data extractor — parses document text into a pandas DataFrame.

No LLM calls. No network I/O. Purely deterministic text parsing.

Public API
----------
extract_dataframe(chunks) -> pd.DataFrame
    Extract financial figures from a list of DocumentChunks.
    Returns an empty DataFrame when no recognisable data is found.
    Never raises.

Strategy (in priority order):
1. Markdown table parsing — handles multi-period tables like annual reports.
2. Key-value regex scanning — handles prose like "Revenue: $1,200,000".

The returned DataFrame has columns drawn from:
    revenue, cogs, gross_profit, current_assets, current_liabilities
which match the recognised column names in app/financial/calculator.py.
"""
from __future__ import annotations

import re

import pandas as pd
import structlog

from app.models.document import DocumentChunk

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Column alias map: raw text → canonical calculator column name
# ---------------------------------------------------------------------------

_COLUMN_ALIASES: dict[str, str] = {
    "revenue": "revenue",
    "revenues": "revenue",
    "net revenue": "revenue",
    "net revenues": "revenue",
    "total revenue": "revenue",
    "total revenues": "revenue",
    "sales": "revenue",
    "net sales": "revenue",
    "total sales": "revenue",
    "cogs": "cogs",
    "cost of goods sold": "cogs",
    "cost of revenue": "cogs",
    "cost of sales": "cogs",
    "cost of products sold": "cogs",
    "gross profit": "gross_profit",
    "gross income": "gross_profit",
    "gross earnings": "gross_profit",
    "current assets": "current_assets",
    "total current assets": "current_assets",
    "current liabilities": "current_liabilities",
    "total current liabilities": "current_liabilities",
}

# ---------------------------------------------------------------------------
# Key-value regex patterns for prose scanning (fallback)
# ---------------------------------------------------------------------------

_KV_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "revenue",
        re.compile(
            r"(?:total\s+|net\s+)?(?:revenue|revenues|sales)[^\d$£€(]*"
            r"[$£€]?\s*([\d,().]+(?:\.\d+)?(?:[KkMmBb])?)",
            re.IGNORECASE,
        ),
    ),
    (
        "cogs",
        re.compile(
            r"cost\s+of\s+(?:goods\s+sold|revenue|sales|products?\s+sold)[^\d$£€(]*"
            r"[$£€]?\s*([\d,().]+(?:\.\d+)?(?:[KkMmBb])?)",
            re.IGNORECASE,
        ),
    ),
    (
        "gross_profit",
        re.compile(
            r"gross\s+(?:profit|income|earnings)[^\d$£€(]*"
            r"[$£€]?\s*([\d,().]+(?:\.\d+)?(?:[KkMmBb])?)",
            re.IGNORECASE,
        ),
    ),
    (
        "current_assets",
        re.compile(
            r"(?:total\s+)?current\s+assets[^\d$£€(]*"
            r"[$£€]?\s*([\d,().]+(?:\.\d+)?(?:[KkMmBb])?)",
            re.IGNORECASE,
        ),
    ),
    (
        "current_liabilities",
        re.compile(
            r"(?:total\s+)?current\s+liabilities[^\d$£€(]*"
            r"[$£€]?\s*([\d,().]+(?:\.\d+)?(?:[KkMmBb])?)",
            re.IGNORECASE,
        ),
    ),
]

# Multipliers for compact notation (K, M, B)
_MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}

# Separator between markdown table header and data rows
_MD_SEPARATOR = re.compile(r"^\|[-| :]+\|$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_number(raw: str) -> float | None:
    """Parse a raw value string into a float.

    Handles:
    - Currency symbols: $, £, €
    - Thousands separators: commas
    - Negative in parentheses: (1,234) → -1234
    - Compact suffixes: K / M / B (case-insensitive)
    """
    value = raw.strip()
    negative = value.startswith("(") and value.endswith(")")
    cleaned = re.sub(r"[$£€,()\s]+", "", value)

    # Detect and strip multiplier suffix
    multiplier = 1.0
    if cleaned and cleaned[-1].lower() in _MULTIPLIERS:
        multiplier = _MULTIPLIERS[cleaned[-1].lower()]
        cleaned = cleaned[:-1]

    try:
        number = float(cleaned) * multiplier
        return -number if negative else number
    except ValueError:
        return None


def _normalise_col(raw: str) -> str | None:
    """Map a raw column header to a canonical financial column, or None."""
    return _COLUMN_ALIASES.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Strategy 1: Markdown table parsing
# ---------------------------------------------------------------------------

def _parse_markdown_tables(text: str) -> list[pd.DataFrame]:
    """Extract all markdown tables that contain at least one known financial column.

    Returns a list of DataFrames (one per table), ordered by discovery order.
    Each DataFrame uses canonical column names and numeric values only.
    """
    tables: list[pd.DataFrame] = []
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # A potential table header row must contain at least two pipe chars
        if line.count("|") < 2:
            i += 1
            continue

        header_parts = [c.strip() for c in line.split("|") if c.strip()]
        if not header_parts:
            i += 1
            continue

        # Look for a separator line immediately after (skip blanks)
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1

        if j >= len(lines) or not _MD_SEPARATOR.match(lines[j].strip()):
            i += 1
            continue

        # Map header columns to canonical names (None = skip)
        canonical_cols = [_normalise_col(c) for c in header_parts]
        if not any(c is not None for c in canonical_cols):
            i += 1
            continue

        # Collect data rows
        data_rows: list[list[str]] = []
        k = j + 1
        while k < len(lines) and "|" in lines[k]:
            row_vals = [c.strip() for c in lines[k].split("|") if c.strip() != ""]
            data_rows.append(row_vals)
            k += 1

        if data_rows:
            col_data: dict[str, list[float | None]] = {}
            for col_idx, canon in enumerate(canonical_cols):
                if canon is None:
                    continue
                values: list[float | None] = []
                for row in data_rows:
                    raw_val = row[col_idx] if col_idx < len(row) else ""
                    values.append(_clean_number(raw_val))
                col_data[canon] = values

            if col_data:
                df = pd.DataFrame(col_data).dropna(how="all")
                if df.empty:
                    logger.warning(
                        "extractor_table_all_rows_dropped",
                        detail="All rows were non-numeric and dropped from a parsed table.",
                    )
                else:
                    tables.append(df)

        i = k

    return tables


# ---------------------------------------------------------------------------
# Strategy 2: Key-value regex scanning
# ---------------------------------------------------------------------------

def _parse_kv_patterns(text: str) -> pd.DataFrame | None:
    """Scan text for labelled financial figures.

    Returns a single-row DataFrame if at least one value is found, else None.
    """
    row: dict[str, float] = {}
    for col, pattern in _KV_PATTERNS:
        match = pattern.search(text)
        if match:
            val = _clean_number(match.group(1))
            if val is not None:
                row[col] = val

    if not row:
        return None
    return pd.DataFrame([row])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_dataframe(chunks: list[DocumentChunk]) -> pd.DataFrame:
    """Extract financial tabular data from document chunks into a DataFrame.

    Parameters
    ----------
    chunks:
        Pre-processed text chunks from a converted document.

    Returns
    -------
    pd.DataFrame
        Columns: any subset of revenue, cogs, gross_profit,
        current_assets, current_liabilities.
        Rows: one per reporting period (oldest first) or one KV row.
        Empty DataFrame if no financial data is found — never raises.
    """
    if not chunks:
        logger.warning("extractor_no_chunks")
        return pd.DataFrame()

    full_text = "\n".join(chunk.text for chunk in chunks)

    # Strategy 1: markdown tables
    tables = _parse_markdown_tables(full_text)
    if tables:
        # Pick the table with the most known financial columns, then most rows
        best = max(tables, key=lambda df: (len(df.columns), len(df)))
        logger.info(
            "extractor_table_found",
            rows=len(best),
            columns=list(best.columns),
        )
        return best.reset_index(drop=True)

    # Strategy 2: key-value prose
    kv_df = _parse_kv_patterns(full_text)
    if kv_df is not None:
        logger.info("extractor_kv_found", columns=list(kv_df.columns))
        return kv_df

    logger.warning("extractor_no_data_found")
    return pd.DataFrame()
