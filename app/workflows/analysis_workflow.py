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
    """Step 1 — Ingest: record document metadata for each document ID."""
    from datetime import UTC, datetime  # noqa: PLC0415

    # DevUI passes a string; coerce to dict for the pipeline.
    if not isinstance(context, dict):
        text = getattr(context, "text", str(context))
        context = {"prompt": text, "document_ids": []}

    logger.info("workflow_step_ingest_start", document_ids=context.get("document_ids"))
    document_ids = context.get("document_ids", [])
    context["ingested_at"] = datetime.now(UTC).isoformat()
    context["ingestion_count"] = len(document_ids)
    logger.info("workflow_step_ingest_done", count=len(document_ids))
    await ctx.send_message(context)


@executor
async def convert_step(context: dict, ctx: WorkflowContext[dict]) -> None:
    """Step 2 — Convert: convert each document to text using the configured converter."""
    from app.config import settings  # noqa: PLC0415
    from app.conversion.local_converter import LocalConverter  # noqa: PLC0415
    from app.conversion.mcp_converter import MCPConverter  # noqa: PLC0415

    logger.info("workflow_step_convert_start", mode=settings.conversion_mode)
    converter = MCPConverter() if settings.conversion_mode == "mcp" else LocalConverter()
    context["converter_used"] = type(converter).__name__
    logger.info("workflow_step_convert_done", converter=context["converter_used"])
    await ctx.send_message(context)


@executor
async def analyze_step(context: dict, ctx: WorkflowContext[dict]) -> None:
    """Step 3 — Analyze: route and run the appropriate analyzer."""
    from app.analyzers.summary import SummaryAnalyzer  # noqa: PLC0415
    from app.models.analysis import AnalysisRequest, AnalysisType  # noqa: PLC0415
    from app.routing.router import route  # noqa: PLC0415

    prompt = context.get("prompt", "")
    analysis_type = route(prompt)
    logger.info("workflow_step_analyze_start", analysis_type=analysis_type)

    request = AnalysisRequest(analysis_type=analysis_type, prompt=prompt)

    if analysis_type == AnalysisType.SUMMARY:
        analyzer = SummaryAnalyzer()
        result = await analyzer.analyze(request, chunks=[])
    else:
        from app.models.analysis import AnalysisResult  # noqa: PLC0415

        result = AnalysisResult(
            request_id=request.id,
            analysis_type=analysis_type,
            summary=f"Analyzer for '{analysis_type}' not yet implemented in Phase 1.",
            warnings=["Phase 1 stub — only SUMMARY type is fully implemented."],
        )

    context["analysis_result"] = result.model_dump(mode="json")
    context["analysis_type"] = str(analysis_type)
    logger.info("workflow_step_analyze_done", analysis_type=analysis_type)
    await ctx.send_message(context)


@executor
async def review_step(context: dict, ctx: WorkflowContext[dict]) -> None:
    """Step 4 — Review: validate the analysis result via ReviewerAgent tool."""
    from app.agents.reviewer_agent import validate_analysis_result  # noqa: PLC0415

    logger.info("workflow_step_review_start")
    result_json = json.dumps(context.get("analysis_result", {}))
    review_report_json = await validate_analysis_result(result_json)
    context["review_report"] = json.loads(review_report_json)
    logger.info("workflow_step_review_done", valid=context["review_report"].get("valid"))
    await ctx.send_message(context)


@executor(workflow_output=str)
async def report_step(context: dict, ctx: WorkflowContext[Never, str]) -> None:
    """Step 5 — Report: package the final output for delivery."""
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
