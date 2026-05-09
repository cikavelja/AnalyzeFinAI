"""Stub analyzers — replaced by UniversalAnalyzer.

ComparisonAnalyzer, AuditAnalyzer, LegalAnalyzer, and CustomAnalyzer
were consolidated into UniversalAnalyzer which uses request.analysis_type
to select the correct prompt template. Import from app.analyzers.universal.
"""
from app.analyzers.universal import UniversalAnalyzer

ComparisonAnalyzer = UniversalAnalyzer
AuditAnalyzer = UniversalAnalyzer
LegalAnalyzer = UniversalAnalyzer
CustomAnalyzer = UniversalAnalyzer
