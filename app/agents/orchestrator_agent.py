"""OrchestratorAgent — top-level MAF agent that routes and delegates work.

Tools:
    run_analysis_workflow  — kicks off the full analysis pipeline
    route_to_analyst       — hands off a document task to the AnalystAgent
    route_to_reviewer      — hands off a result to the ReviewerAgent
"""
from __future__ import annotations

import json

import structlog
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from app.config import settings

logger = structlog.get_logger(__name__)


def _make_client() -> OpenAIChatClient:
    kwargs: dict = {"model": settings.openai_model}
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    return OpenAIChatClient(**kwargs)


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

async def run_analysis_workflow(document_ids: str, prompt: str) -> str:
    """
    Kick off the full AnalizerAI analysis pipeline for a set of documents.

    Parameters
    ----------
    document_ids : str
        Comma-separated list of document UUIDs to analyse.
    prompt : str
        The user's analysis request / question.

    Returns a JSON string with the workflow run status and result summary.
    """
    try:
        from app.workflows.analysis_workflow import analysis_workflow  # noqa: PLC0415

        ids = [d.strip() for d in document_ids.split(",") if d.strip()]
        result = await analysis_workflow.run(
            {"document_ids": ids, "prompt": prompt}
        )
        return json.dumps({"status": "completed", "result": str(result)})
    except Exception as exc:
        logger.error("orchestrator_workflow_failed", error=str(exc))
        return json.dumps({"error": str(exc), "status": "failed"})


async def route_to_analyst(document_id: str, task: str) -> str:
    """
    Delegate a document analysis task to the AnalystAgent.

    Parameters
    ----------
    document_id : str
        UUID of the document to analyse.
    task : str
        Description of the analysis task for the analyst.

    Returns a JSON string with the analyst's response.
    """
    try:
        from app.agents.analyst_agent import analyst_agent  # noqa: PLC0415

        response = await analyst_agent.run(
            f"Task: {task}\nDocument ID: {document_id}"
        )
        return json.dumps({"status": "delegated", "response": str(response.message)})
    except Exception as exc:
        logger.error("orchestrator_route_to_analyst_failed", error=str(exc))
        return json.dumps({"error": str(exc), "status": "failed"})


async def route_to_reviewer(result_json: str) -> str:
    """
    Delegate a completed analysis result to the ReviewerAgent for quality review.

    Parameters
    ----------
    result_json : str
        JSON string of an AnalysisResult to be reviewed.

    Returns a JSON string with the reviewer's validation report.
    """
    try:
        from app.agents.reviewer_agent import reviewer_agent  # noqa: PLC0415

        response = await reviewer_agent.run(
            f"Please validate this analysis result:\n{result_json}"
        )
        return json.dumps({"status": "reviewed", "response": str(response.message)})
    except Exception as exc:
        logger.error("orchestrator_route_to_reviewer_failed", error=str(exc))
        return json.dumps({"error": str(exc), "status": "failed"})


# ---------------------------------------------------------------------------
# Agent — lazy singleton
# ---------------------------------------------------------------------------

_orchestrator_agent: Agent | None = None


def _build_orchestrator_agent() -> Agent:
    return Agent(
        name="OrchestratorAgent",
        client=_make_client(),
        instructions=(
            "You are the OrchestratorAgent for AnalizerAI. "
            "Your job is to understand the user's analysis request, determine the right "
            "approach, and coordinate the AnalystAgent and ReviewerAgent. "
            "Always use run_analysis_workflow for complete pipeline runs. "
            "Use route_to_analyst for targeted document analysis tasks. "
            "Use route_to_reviewer to quality-check any analysis result before delivering it. "
            "Never perform analysis computations yourself — delegate to specialist agents."
        ),
        tools=[run_analysis_workflow, route_to_analyst, route_to_reviewer],
    )


def __getattr__(name: str) -> object:
    global _orchestrator_agent
    if name == "orchestrator_agent":
        if _orchestrator_agent is None:
            _orchestrator_agent = _build_orchestrator_agent()
        return _orchestrator_agent
    raise AttributeError(name)
