"""Analysis route — POST /api/v1/analyze, GET /api/v1/results/{request_id}.

Routes the user prompt to the appropriate analyzer and returns an AnalysisResult.
"""
from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException

from app.analyzers.financial import FinancialAnalyzer
from app.analyzers.universal import UniversalAnalyzer
from app.api.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.financial.calculator import calculate_metrics
from app.financial.extractor import extract_dataframe
from app.ingestion.document_loader import load_chunks
from app.llm.factory import get_llm_provider
from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisType
from app.routing.router import route
from app.storage.base import AbstractStorage
from app.storage.filesystem import FilesystemStorage

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])

_results_storage: AbstractStorage = FilesystemStorage(base_dir="data/results")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    """Route the prompt to the correct analyzer and return the analysis result."""
    try:
        # MED-5: honour analysis_type override from the request body
        if body.analysis_type:
            try:
                analysis_type = AnalysisType(body.analysis_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid analysis_type '{body.analysis_type}'. "
                           f"Valid values: {[e.value for e in AnalysisType]}",
                ) from None
        else:
            analysis_type = route(body.prompt)
        request = AnalysisRequest(
            analysis_type=analysis_type,
            prompt=body.prompt,
            document_ids=body.document_ids,
        )

        chunks = await load_chunks(body.document_ids)

        llm_provider = get_llm_provider(provider=body.provider, model_id=body.model_id)

        if analysis_type == AnalysisType.FINANCIAL:
            df = extract_dataframe(chunks)
            metrics = calculate_metrics(df) if not df.empty else None
            analyzer_fin = FinancialAnalyzer(llm_provider=llm_provider)
            result: AnalysisResult = await analyzer_fin.analyze(request, chunks=chunks, metrics=metrics)
        else:
            analyzer = UniversalAnalyzer(llm_provider=llm_provider)
            result = await analyzer.analyze(request, chunks=chunks)

        # MED-11: persist result for later retrieval
        await _results_storage.save(result.request_id, result.model_dump_json(indent=2), suffix=".json")

        logger.info(
            "api_analyze_ok",
            analysis_type=str(analysis_type),
            request_id=str(request.id),
        )

        return AnalyzeResponse(
            request_id=result.request_id,
            analysis_type=str(result.analysis_type),
            summary=result.summary,
            narrative=result.narrative,
            key_findings=result.key_findings,
            recommendations=result.recommendations,
            warnings=result.warnings,
            metrics=result.metrics,
            model_used=result.model_used,
        )

    except Exception as exc:
        logger.error("api_analyze_error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/results/{request_id}", response_model=AnalyzeResponse)
async def get_result(request_id: UUID) -> AnalyzeResponse:
    """Retrieve a previously persisted analysis result by request_id."""
    storage_key = _results_storage.key_for(request_id, suffix=".json")
    try:
        if not await _results_storage.exists(storage_key):
            raise HTTPException(status_code=404, detail=f"Result {request_id} not found.")
        raw = await _results_storage.load(storage_key)
        result = AnalysisResult.model_validate_json(raw)
        return AnalyzeResponse(
            request_id=result.request_id,
            analysis_type=str(result.analysis_type),
            summary=result.summary,
            narrative=result.narrative,
            key_findings=result.key_findings,
            recommendations=result.recommendations,
            warnings=result.warnings,
            metrics=result.metrics,
            model_used=result.model_used,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("api_get_result_error", request_id=str(request_id), error=str(exc))
        raise HTTPException(status_code=500, detail="Internal server error") from exc
