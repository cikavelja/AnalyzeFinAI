"""Tests for app/routing/router.py"""
from __future__ import annotations

from app.models.analysis import AnalysisType
from app.routing.router import route

# ---------------------------------------------------------------------------
# Financial routing
# ---------------------------------------------------------------------------

def test_router_financial_prompt_returns_financial() -> None:
    assert route("Show me the revenue and profit margins") == AnalysisType.FINANCIAL


def test_router_yoy_keyword_returns_financial() -> None:
    assert route("What is the YoY growth rate?") == AnalysisType.FINANCIAL


def test_router_balance_sheet_returns_financial() -> None:
    assert route("Analyse the balance sheet") == AnalysisType.FINANCIAL


def test_router_cash_flow_returns_financial() -> None:
    assert route("Summarise the cash flow statement") == AnalysisType.FINANCIAL


# ---------------------------------------------------------------------------
# Legal routing
# ---------------------------------------------------------------------------

def test_router_contract_keyword_returns_legal() -> None:
    assert route("Review the contract for liability clauses") == AnalysisType.LEGAL


def test_router_compliance_keyword_returns_legal() -> None:
    assert route("Check for regulatory compliance issues") == AnalysisType.LEGAL


# ---------------------------------------------------------------------------
# Audit routing
# ---------------------------------------------------------------------------

def test_router_audit_keyword_returns_audit() -> None:
    assert route("Run an internal audit on this document") == AnalysisType.AUDIT


def test_router_control_weakness_returns_audit() -> None:
    assert route("Identify control weaknesses") == AnalysisType.AUDIT


# ---------------------------------------------------------------------------
# Comparison routing
# ---------------------------------------------------------------------------

def test_router_compare_returns_comparison() -> None:
    assert route("Compare these two documents") == AnalysisType.COMPARISON


def test_router_versus_keyword_returns_comparison() -> None:
    assert route("Q1 vs Q2 performance") == AnalysisType.COMPARISON


# ---------------------------------------------------------------------------
# Default (summary) routing
# ---------------------------------------------------------------------------

def test_router_generic_prompt_returns_summary() -> None:
    assert route("Tell me about this document") == AnalysisType.SUMMARY


def test_router_empty_string_returns_summary() -> None:
    assert route("") == AnalysisType.SUMMARY


def test_router_whitespace_only_returns_summary() -> None:
    assert route("   ") == AnalysisType.SUMMARY


def test_router_none_like_prompt_returns_summary() -> None:
    # Passing a non-keyword phrase
    assert route("Hello, can you help me?") == AnalysisType.SUMMARY


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

def test_router_case_insensitive_financial() -> None:
    assert route("REVENUE GROWTH IS IMPORTANT") == AnalysisType.FINANCIAL


def test_router_mixed_case_legal() -> None:
    assert route("CONTRACT Terms and CONDITIONS") == AnalysisType.LEGAL
