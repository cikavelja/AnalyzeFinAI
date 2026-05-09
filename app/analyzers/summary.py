"""SummaryAnalyzer — backward-compatibility alias for UniversalAnalyzer.

Replaced by UniversalAnalyzer, which handles all non-financial analysis types
using the same LLM + prompt-template pattern. Import UniversalAnalyzer directly
in new code.
"""
from app.analyzers.universal import UniversalAnalyzer

SummaryAnalyzer = UniversalAnalyzer
