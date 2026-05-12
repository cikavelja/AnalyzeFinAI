"""Tests for app/financial/calculator.py"""
from __future__ import annotations

import pandas as pd
import pytest

from app.exceptions import CalculationError
from app.financial.calculator import calculate_metrics
from app.models.financial import FinancialMetrics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_df(**kwargs: list[float]) -> pd.DataFrame:
    """Convenience: build a DataFrame from keyword=list pairs."""
    return pd.DataFrame(kwargs)


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------

def test_calculator_returns_financial_metrics_instance() -> None:
    df = make_df(revenue=[100.0, 110.0])
    result = calculate_metrics(df)
    assert isinstance(result, FinancialMetrics)


def test_calculator_revenue_populated() -> None:
    df = make_df(revenue=[200.0, 220.0])
    result = calculate_metrics(df)
    assert result.revenue == pytest.approx(220.0)


def test_calculator_yoy_correct() -> None:
    df = make_df(revenue=[100.0, 110.0])
    result = calculate_metrics(df)
    # (110 - 100) / 100 * 100 = 10.0
    assert result.yoy_revenue_growth == pytest.approx(10.0)


def test_calculator_cagr_two_periods() -> None:
    df = make_df(revenue=[100.0, 121.0])
    result = calculate_metrics(df)
    # (121/100)^(1/1) - 1 = 0.21
    assert result.cagr == pytest.approx(0.21)


def test_calculator_gross_margin_computed() -> None:
    df = make_df(revenue=[200.0], cogs=[120.0])
    result = calculate_metrics(df)
    # (200 - 120) / 200 = 0.4
    assert result.gross_margin == pytest.approx(0.4)


def test_calculator_current_ratio_computed() -> None:
    df = make_df(
        revenue=[100.0],
        current_assets=[300.0],
        current_liabilities=[150.0],
    )
    result = calculate_metrics(df)
    assert result.current_ratio == pytest.approx(2.0)


def test_calculator_trend_slope_positive() -> None:
    df = make_df(revenue=[100.0, 110.0, 120.0, 130.0])
    result = calculate_metrics(df)
    assert result.revenue_trend_slope is not None
    assert result.revenue_trend_slope > 0


def test_calculator_no_revenue_column_adds_warning() -> None:
    df = make_df(cogs=[50.0, 60.0])
    result = calculate_metrics(df)
    assert result.revenue is None
    assert any("revenue" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Zero-division paths
# ---------------------------------------------------------------------------

def test_calculator_zero_prior_revenue_yoy_is_none() -> None:
    df = make_df(revenue=[0.0, 110.0])
    result = calculate_metrics(df)
    assert result.yoy_revenue_growth is None
    assert any("zero" in w.lower() for w in result.warnings)


def test_calculator_zero_revenue_gross_margin_is_none() -> None:
    df = make_df(revenue=[0.0], cogs=[50.0])
    result = calculate_metrics(df)
    assert result.gross_margin is None
    assert any("zero" in w.lower() for w in result.warnings)


def test_calculator_zero_liabilities_current_ratio_is_none() -> None:
    df = make_df(
        revenue=[100.0],
        current_assets=[100.0],
        current_liabilities=[0.0],
    )
    result = calculate_metrics(df)
    assert result.current_ratio is None
    assert any("zero" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def test_calculator_anomaly_detected() -> None:
    # Ten stable values then one extreme outlier — z-score of outlier will be > 2.5
    revenues = [100.0] * 9 + [10000.0]
    df = make_df(revenue=revenues)
    result = calculate_metrics(df)
    assert len(result.anomalies) >= 1


def test_calculator_no_anomaly_in_flat_series() -> None:
    df = make_df(revenue=[100.0, 100.0, 100.0])
    result = calculate_metrics(df)
    # std=0 → no anomaly detection run
    assert len(result.anomalies) == 0


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_calculator_empty_dataframe_raises_calculation_error() -> None:
    with pytest.raises(CalculationError, match="empty"):
        calculate_metrics(pd.DataFrame())


def test_calculator_none_raises_calculation_error() -> None:
    with pytest.raises(CalculationError):
        calculate_metrics(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_calculator_single_row_skips_yoy() -> None:
    df = make_df(revenue=[500.0])
    result = calculate_metrics(df)
    assert result.revenue == pytest.approx(500.0)
    # YoY needs 2 rows — check warning added
    assert any("two" in w.lower() or "period" in w.lower() for w in result.warnings)
