"""AnalysisWorkflow — MAF sequential pipeline orchestrating the full analysis run.

Pipeline steps (sequential — each depends on the previous):
    1. ingest    — record document metadata
    2. convert   — convert file to text/markdown
    3. analyze   — run the appropriate analyzer
    4. review    — reviewer agent validates the result
    5. report    — package the final output

Import this workflow into devui_app.py for development visualization.

Uses WorkflowBuilder + @executor so that DevUI can detect the `executors`
attribute and render the workflow diagram.
"""
from __future__ import annotations

import json
from typing import Never

import structlog
from agent_framework import WorkflowBuilder, WorkflowContext
from agent_framework._workflows._function_executor import executor

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Step executors — each receives the shared context dict and passes it on
# ---------------------------------------------------------------------------

@executor(input=str)
async def ingest_step(context, ctx: WorkflowContext[dict]) -> None:
    """Step 1 — Ingest: load document metadata for each document ID."""
    from pathlib import Path  # noqa: PLC0415

    from app.audit.logger import audit_logger  # noqa: PLC0415
    from app.ingestion.loader import load_document  # noqa: PLC0415
    from app.models.audit import AuditEvent  # noqa: PLC0415

    # DevUI passes a string; coerce to dict for the pipeline.
    if not isinstance(context, dict):
        text = getattr(context, "text", str(context))
        context = {"prompt": text, "document_ids": []}

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="started",
        detail="ingest_step started",
    ))

    logger.info("workflow_step_ingest_start", document_ids=context.get("document_ids"))
    document_ids = context.get("document_ids", [])
    upload_dir = Path("data/uploads")

    ingested_metadata = []
    for doc_id_str in document_ids:
        matches = list(upload_dir.glob(f"{doc_id_str}.*"))
        if not matches:
            logger.warning("workflow_ingest_not_found", document_id=doc_id_str)
            continue
        try:
            metadata = await load_document(str(matches[0]))
            ingested_metadata.append(metadata.model_dump(mode="json"))
        except Exception as exc:
            logger.error("workflow_ingest_failed", document_id=doc_id_str, error=str(exc))

    from datetime import UTC, datetime  # noqa: PLC0415
    context["ingested_at"] = datetime.now(UTC).isoformat()
    context["ingestion_count"] = len(ingested_metadata)
    context["ingested_metadata"] = ingested_metadata

    logger.info("workflow_step_ingest_done", count=len(ingested_metadata))

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="completed",
        detail=f"ingest_step completed: {len(ingested_metadata)} documents ingested",
    ))

    await ctx.send_message(context)


@executor
async def convert_step(context: dict, ctx: WorkflowContext[dict]) -> None:
    """Step 2 — Convert: convert each document to text using the configured converter."""
    from pathlib import Path  # noqa: PLC0415
    from uuid import UUID  # noqa: PLC0415

    from app.audit.logger import audit_logger  # noqa: PLC0415
    from app.chunking.chunker import chunk_text  # noqa: PLC0415
    from app.conversion import get_converter  # noqa: PLC0415
    from app.models.audit import AuditEvent  # noqa: PLC0415

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="started",
        detail="convert_step started",
    ))

    logger.info("workflow_step_convert_start")
    converter = get_converter()
    context["converter_used"] = type(converter).__name__

    upload_dir = Path("data/uploads")
    all_chunks: list[dict] = []
    for doc_id_str in context.get("document_ids", []):
        doc_id = UUID(doc_id_str) if isinstance(doc_id_str, str) else doc_id_str
        matches = list(upload_dir.glob(f"{doc_id}.*"))
        if not matches:
            logger.warning("workflow_convert_document_not_found", document_id=str(doc_id))
            continue
        try:
            result = await converter.convert(str(matches[0]), doc_id)
            chunks = chunk_text(result.text_content, doc_id)
            all_chunks.extend(c.model_dump(mode="json") for c in chunks)
        except Exception as exc:
            logger.error("workflow_convert_failed", document_id=str(doc_id), error=str(exc))

    context["chunks"] = all_chunks
    logger.info(
        "workflow_step_convert_done",
        converter=context["converter_used"],
        chunk_count=len(all_chunks),
    )

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="completed",
        detail=f"convert_step completed: {len(all_chunks)} chunks from {context['converter_used']}",
    ))

    await ctx.send_message(context)


@executor
async def analyze_step(context: dict, ctx: WorkflowContext[dict]) -> None:
    """Step 3 — Analyze: route and run the appropriate analyzer."""
    from app.analyzers.financial import FinancialAnalyzer  # noqa: PLC0415
    from app.analyzers.universal import UniversalAnalyzer  # noqa: PLC0415
    from app.audit.logger import audit_logger  # noqa: PLC0415
    from app.financial.calculator import calculate_metrics  # noqa: PLC0415
    from app.financial.extractor import extract_dataframe  # noqa: PLC0415
    from app.models.analysis import AnalysisRequest, AnalysisType  # noqa: PLC0415
    from app.models.audit import AuditEvent  # noqa: PLC0415
    from app.routing.router import route  # noqa: PLC0415

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="started",
        detail="analyze_step started",
    ))

    prompt = context.get("prompt", "")
    analysis_type = route(prompt)
    logger.info("workflow_step_analyze_start", analysis_type=analysis_type)

    request = AnalysisRequest(analysis_type=analysis_type, prompt=prompt)

    # Rehydrate DocumentChunk objects from the serialized dicts produced by convert_step
    from app.models.document import DocumentChunk  # noqa: PLC0415
    chunks = [DocumentChunk(**c) for c in context.get("chunks", [])]

    if analysis_type == AnalysisType.FINANCIAL:
        df = extract_dataframe(chunks)
        metrics = calculate_metrics(df) if not df.empty else None
        analyzer_fin = FinancialAnalyzer()
        result = await analyzer_fin.analyze(request, chunks=chunks, metrics=metrics)
    else:
        analyzer = UniversalAnalyzer()
        result = await analyzer.analyze(request, chunks=chunks)

    context["analysis_result"] = result.model_dump(mode="json")
    context["analysis_type"] = str(analysis_type)
    logger.info("workflow_step_analyze_done", analysis_type=analysis_type)

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="completed",
        detail=f"analyze_step completed: {analysis_type}",
    ))

    await ctx.send_message(context)


@executor
async def review_step(context: dict, ctx: WorkflowContext[dict]) -> None:
    """Step 4 — Review: validate the analysis result via ReviewerAgent tool."""
    from app.agents.reviewer_agent import validate_analysis_result  # noqa: PLC0415
    from app.audit.logger import audit_logger  # noqa: PLC0415
    from app.models.audit import AuditEvent  # noqa: PLC0415

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="started",
        detail="review_step started",
    ))

    logger.info("workflow_step_review_start")
    result_json = json.dumps(context.get("analysis_result", {}))
    review_report_json = await validate_analysis_result(result_json)
    context["review_report"] = json.loads(review_report_json)
    logger.info("workflow_step_review_done", valid=context["review_report"].get("valid"))

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="completed",
        detail=f"review_step completed: valid={context['review_report'].get('valid')}",
    ))

    await ctx.send_message(context)


@executor(workflow_output=str)
async def report_step(context: dict, ctx: WorkflowContext[Never, str]) -> None:
    """Step 5 — Report: package the final output for delivery."""
    from app.audit.logger import audit_logger  # noqa: PLC0415
    from app.models.audit import AuditEvent  # noqa: PLC0415

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="started",
        detail="report_step started",
    ))

    logger.info("workflow_step_report_start")
    context["final_report"] = {
        "analysis_type": context.get("analysis_type"),
        "result": context.get("analysis_result"),
        "review": context.get("review_report"),
        "converter_used": context.get("converter_used"),
        "ingested_at": context.get("ingested_at"),
    }
    report = context["final_report"]
    result = report.get("result") or {}
    review = report.get("review") or {}
    lines = [
        "## Analysis Complete",
        f"**Type:** {report.get('analysis_type', 'N/A')}",
        f"**Converter:** {report.get('converter_used', 'N/A')}",
        f"**Ingested at:** {report.get('ingested_at', 'N/A')}",
        "",
        "### Summary",
        result.get("summary", "No summary available."),
    ]
    if result.get("warnings"):
        lines += ["", "### Warnings"] + [f"- {w}" for w in result["warnings"]]
    if review:
        valid = "✅ Valid" if review.get("valid") else "❌ Invalid"
        lines += ["", f"### Review: {valid}"]
        if review.get("issues"):
            lines += [f"- {i}" for i in review["issues"]]
    logger.info("workflow_step_report_done")

    await audit_logger.emit(AuditEvent(
        event_type="workflow_step",
        status="completed",
        detail="report_step completed",
    ))

    await ctx.yield_output("\n".join(lines))


# ---------------------------------------------------------------------------
# Workflow definition — WorkflowBuilder gives DevUI the `executors` attribute
# needed to detect this as a workflow and render the step diagram.
# ---------------------------------------------------------------------------

analysis_workflow = (
    WorkflowBuilder(
        name="AnalysisWorkflow",
        description="Sequential 5-step AnalizerAI pipeline",
        start_executor=ingest_step,
    )
    .add_edge(ingest_step, convert_step)
    .add_edge(convert_step, analyze_step)
    .add_edge(analyze_step, review_step)
    .add_edge(review_step, report_step)
    .build()
)
