"""Report writer — serialises AnalysisResult to Markdown and JSON."""
from __future__ import annotations

from pathlib import Path

import structlog

from app.models.analysis import AnalysisResult

logger = structlog.get_logger(__name__)


def write_markdown_report(result: AnalysisResult, output_path: str) -> Path:
    """Render *result* as a Markdown file and write it to *output_path*.

    Parameters
    ----------
    result:
        Populated AnalysisResult to render.
    output_path:
        Destination file path (will be created including parent dirs).

    Returns
    -------
    Path
        Resolved path to the written file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        f"# Analysis Report — {str(result.analysis_type).upper()}",
        "",
        f"**Request ID:** `{result.request_id}`",
        f"**Completed:** {result.completed_at.isoformat()}",
        f"**Model:** {result.model_used or 'N/A'}",
        "",
        "## Summary",
        "",
        result.summary or "_No summary available._",
        "",
    ]

    if result.narrative and result.narrative != result.summary:
        lines += ["## Narrative", "", result.narrative, ""]

    if result.key_findings:
        lines += ["## Key Findings", ""]
        for finding in result.key_findings:
            lines.append(f"- {finding}")
        lines.append("")

    if result.recommendations:
        lines += ["## Recommendations", ""]
        for rec in result.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    if result.metrics:
        lines += ["## Metrics", ""]
        for key, val in result.metrics.items():
            lines.append(f"- **{key}:** {val:.4f}")
        lines.append("")

    if result.warnings:
        lines += ["## Warnings", ""]
        for warn in result.warnings:
            lines.append(f"> ⚠️ {warn}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("report_written", path=str(path), result_id=str(result.id))
    return path.resolve()
