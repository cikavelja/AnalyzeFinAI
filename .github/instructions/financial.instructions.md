---
description: "Use when creating or editing code in app/financial/. Enforces deterministic-only calculations, no LLM calls, typed FinancialMetrics returns, and correct pandas/numpy formulas."
applyTo: "app/financial/**/*.py"
---
# Financial Calculation Engine Conventions

## Absolute Rules

1. **No LLM calls anywhere in `app/financial/`.** This module is a pure calculation engine.
2. **No `requests`, `httpx`, or any network I/O.** Calculations are deterministic and offline.
3. Every public function must return a typed Pydantic model from `app/financial/metrics.py`.
4. Use `pandas` and `numpy` for all calculations. Never implement math loops manually.

## Standard Formulas

```python
# Year-over-Year change (%)
yoy = (current - prior) / prior * 100

# CAGR
cagr = (end_value / start_value) ** (1 / n_years) - 1

# Trend slope (linear regression over time series)
slope = float(numpy.polyfit(range(len(series)), series, 1)[0])

# Anomaly detection — flag if |z-score| > 2.5
z_scores = (series - series.mean()) / series.std()
anomalies = series[z_scores.abs() > 2.5]

# Gross margin
gross_margin = (revenue - cogs) / revenue

# Current ratio
current_ratio = current_assets / current_liabilities
```

## Error Handling

- If a required column is missing from the DataFrame → raise `CalculationError` (from `app/exceptions.py`).
- If a denominator is zero → return `None` for that metric, populate the `warnings` list.
- Never silently return 0 for a division-by-zero; that would corrupt the analysis.

## Testing Requirement

Every calculation function must have a corresponding test in `tests/unit/test_calculator.py`
with known inputs and expected outputs. No exceptions.
