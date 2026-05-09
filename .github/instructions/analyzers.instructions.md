---
description: "Use when creating or editing analyzer modules in app/analyzers/. Covers AbstractAnalyzer protocol, LLM-only-for-text rule, AuditEvent emission, and AnalysisResult structure."
applyTo: "app/analyzers/**/*.py"
---
# Analyzer Module Conventions

## Protocol Compliance

Every analyzer **must** implement the `AbstractAnalyzer` protocol from `app/analyzers/base.py`:

```python
class AbstractAnalyzer(Protocol):
    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult: ...
```

Do not add extra public methods. Keep the interface stable.

## The Golden Rule: LLM for Text, Code for Numbers

- **LLMs**: summarization, narrative, explanation, insight, recommendations.
- **Deterministic Python**: every number, ratio, total, YoY, CAGR, z-score.
- If an analyzer needs a calculation → call `app/financial/calculator.py`, then pass the result to the LLM.
- **Never pass a calculation task to the LLM.**

## Audit Events

Every analyzer must emit two `AuditEvent`s — one at start, one at end:

```python
await audit_logger.emit(AuditEvent(
    event_type="analysis",
    request_id=request.id,
    status="started",
    detail=f"{self.__class__.__name__} started",
))
# ... analysis work ...
await audit_logger.emit(AuditEvent(
    event_type="analysis",
    request_id=request.id,
    status="completed",
    model_used=self.llm_provider.model_name,
))
```

## Return Type

Always return a fully populated `AnalysisResult`. Never return `None` or raise on
missing data — instead, populate `warnings` with a human-readable explanation of
what data was missing.

## Stub Pattern (for Phase 1 incomplete analyzers)

```python
async def analyze(self, request, chunks, metrics=None) -> AnalysisResult:
    raise NotImplementedError(f"{self.__class__.__name__} is not yet implemented")
```
