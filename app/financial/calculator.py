"""Financial calculation engine — deterministic, no LLM, no network I/O.

The single public function is ``calculate_metrics``.  It accepts a pandas
DataFrame whose columns must include a subset of the recognised names below,
and returns a fully typed ``FinancialMetrics`` model.

Recognised column names (case-insensitive after stripping):
    revenue, cogs, gross_profit, current_assets, current_liabilities

Raises:
    CalculationError — if the DataFrame is empty or an irrecoverable problem
                       is detected (e.g. wrong dtype).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.exceptions import CalculationError
from app.models.financial import FinancialMetrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with lower-stripped column names."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def _safe_float(value: object) -> float | None:
    """Convert *value* to float, returning None if conversion fails."""
    try:
        f = float(value)  # type: ignore[arg-type]
        return None if (np.isnan(f) or np.isinf(f)) else f
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_metrics(df: pd.DataFrame) -> FinancialMetrics:
    """Compute financial metrics from a tabular DataFrame.

    Parameters
    ----------
    df:
        Raw financial data. Each row typically represents one reporting period.
        Required for growth calculations: at least two rows.

    Returns
    -------
    FinancialMetrics
        Fully populated model. Fields that cannot be computed are ``None``
        and a human-readable explanation is appended to ``warnings``.

    Raises
    ------
    CalculationError
        When *df* is empty or contains an incompatible dtype that prevents
        numpy/pandas operations from running at all.
    """
    if df is None or df.empty:
        raise CalculationError("Input DataFrame is empty — cannot calculate metrics.")

    df = _normalise_columns(df)
    warnings: list[str] = []
    metrics = FinancialMetrics()

    # ── Revenue ────────────────────────────────────────────────────────────
    if "revenue" in df.columns:
        try:
            revenue_series = pd.to_numeric(df["revenue"], errors="coerce")
            metrics.revenue = _safe_float(revenue_series.iloc[-1])
        except Exception as exc:
            raise CalculationError(f"Cannot parse 'revenue' column: {exc}") from exc
    else:
        warnings.append("Column 'revenue' not found — revenue metrics skipped.")

    # ── COGS & Gross Profit ────────────────────────────────────────────────
    if "cogs" in df.columns:
        try:
            cogs_series = pd.to_numeric(df["cogs"], errors="coerce")
            metrics.cogs = _safe_float(cogs_series.iloc[-1])
        except Exception as exc:
            raise CalculationError(f"Cannot parse 'cogs' column: {exc}") from exc

    if metrics.revenue is not None and metrics.cogs is not None:
        metrics.gross_profit = metrics.revenue - metrics.cogs
        if metrics.revenue != 0:
            metrics.gross_margin = metrics.gross_profit / metrics.revenue
        else:
            metrics.gross_margin = None
            warnings.append("Revenue is zero — gross_margin is undefined.")
    elif "gross_profit" in df.columns:
        gp_series = pd.to_numeric(df["gross_profit"], errors="coerce")
        metrics.gross_profit = _safe_float(gp_series.iloc[-1])

    # ── YoY Revenue Growth ─────────────────────────────────────────────────
    if "revenue" in df.columns:
        rev_series = pd.to_numeric(df["revenue"], errors="coerce").dropna()
        if len(rev_series) >= 2:
            prior = float(rev_series.iloc[-2])
            current = float(rev_series.iloc[-1])
            if prior != 0:
                metrics.yoy_revenue_growth = (current - prior) / prior * 100
            else:
                metrics.yoy_revenue_growth = None
                warnings.append("Prior-period revenue is zero — YoY growth is undefined.")
        else:
            warnings.append("Need at least two revenue periods to compute YoY growth.")

    # ── CAGR ───────────────────────────────────────────────────────────────
    if "revenue" in df.columns:
        rev_series = pd.to_numeric(df["revenue"], errors="coerce").dropna()
        if len(rev_series) >= 2:
            start_val = float(rev_series.iloc[0])
            end_val = float(rev_series.iloc[-1])
            n_years = len(rev_series) - 1
            if start_val > 0 and end_val > 0:
                metrics.cagr = (end_val / start_val) ** (1 / n_years) - 1
            else:
                metrics.cagr = None
                warnings.append("Start or end revenue ≤ 0 — CAGR is undefined.")

    # ── Trend Slopes ───────────────────────────────────────────────────────
    if "revenue" in df.columns:
        rev_series = pd.to_numeric(df["revenue"], errors="coerce").dropna()
        if len(rev_series) >= 2:
            metrics.revenue_trend_slope = float(
                np.polyfit(range(len(rev_series)), rev_series.values, 1)[0]
            )

    if "gross_profit" in df.columns:
        gp_series = pd.to_numeric(df["gross_profit"], errors="coerce").dropna()
        if len(gp_series) >= 2:
            metrics.profit_trend_slope = float(
                np.polyfit(range(len(gp_series)), gp_series.values, 1)[0]
            )

    # ── Liquidity ──────────────────────────────────────────────────────────
    if "current_assets" in df.columns:
        ca_series = pd.to_numeric(df["current_assets"], errors="coerce")
        metrics.current_assets = _safe_float(ca_series.iloc[-1])

    if "current_liabilities" in df.columns:
        cl_series = pd.to_numeric(df["current_liabilities"], errors="coerce")
        metrics.current_liabilities = _safe_float(cl_series.iloc[-1])

    if metrics.current_assets is not None and metrics.current_liabilities is not None:
        if metrics.current_liabilities != 0:
            metrics.current_ratio = metrics.current_assets / metrics.current_liabilities
        else:
            metrics.current_ratio = None
            warnings.append("Current liabilities is zero — current_ratio is undefined.")

    # ── Anomaly Detection ──────────────────────────────────────────────────
    if "revenue" in df.columns:
        rev_series = pd.to_numeric(df["revenue"], errors="coerce").dropna()
        if len(rev_series) >= 3:
            mean = rev_series.mean()
            std = rev_series.std()
            if std > 0:
                z_scores = (rev_series - mean) / std
                anomaly_mask = z_scores.abs() > 2.5
                for idx, val in rev_series[anomaly_mask].items():
                    metrics.anomalies.append({"period": str(idx), "value": float(val)})

    metrics.warnings = warnings
    return metrics
