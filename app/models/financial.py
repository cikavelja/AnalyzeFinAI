"""FinancialMetrics — typed output of the financial calculation engine.

All numeric fields are Optional so that a missing metric is expressed as None
rather than a silent zero. The ``warnings`` list records why a field is None.
"""
from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class FinancialMetrics(BaseModel):
    """Typed output returned by app/financial/calculator.py."""

    model_config = ConfigDict(frozen=False)

    id: UUID = Field(default_factory=uuid4)

    # Revenue & profitability
    revenue: float | None = None
    cogs: float | None = None
    gross_profit: float | None = None
    gross_margin: float | None = None  # fraction, e.g. 0.42 = 42 %

    # Growth
    yoy_revenue_growth: float | None = None  # percent
    cagr: float | None = None                # fraction

    # Trend
    revenue_trend_slope: float | None = None
    profit_trend_slope: float | None = None

    # Liquidity
    current_assets: float | None = None
    current_liabilities: float | None = None
    current_ratio: float | None = None

    # Anomalies — list of (period_label, value) tuples serialised as dicts
    anomalies: list[dict[str, float | str]] = Field(default_factory=list)

    # Audit trail
    warnings: list[str] = Field(default_factory=list)
