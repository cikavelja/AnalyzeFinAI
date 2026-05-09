"""app/__main__.py — CLI entry point for AnalizerAI.

Run with:
    python -m app --help
    python -m app validate path/to/file.pdf
    python -m app analyze "What is the revenue trend?" path/to/file.pdf
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import structlog
import typer

app = typer.Typer(
    name="analizer-ai",
    help="AnalizerAI — AI-powered document analysis platform.",
    add_completion=False,
)
logger = structlog.get_logger(__name__)


@app.command()
def validate(
    file_path: str = typer.Argument(..., help="Path to the file to validate."),
) -> None:
    """Validate that a file is supported and passes ingestion checks."""
    from app.ingestion.detector import detect_file_type  # noqa: PLC0415
    from app.ingestion.validator import validate_file  # noqa: PLC0415

    path = Path(file_path)
    if not path.exists():
        typer.echo(f"❌ File not found: {file_path}", err=True)
        raise typer.Exit(code=1)

    try:
        validate_file(file_path)
        ext, mime = detect_file_type(file_path)
        typer.echo(f"✅ Valid file: {path.name}")
        typer.echo(f"   Extension : {ext}")
        typer.echo(f"   MIME type : {mime}")
        typer.echo(f"   Size      : {path.stat().st_size:,} bytes")
    except Exception as exc:
        typer.echo(f"❌ Validation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def analyze(
    prompt: str = typer.Argument(..., help="Analysis question or instruction."),
    file_path: str | None = typer.Option(
        None, "--file", "-f", help="Optional path to a document to analyse."
    ),
    output: str = typer.Option(
        "data/report.md", "--output", "-o", help="Output path for the Markdown report."
    ),
) -> None:
    """Run an analysis on an optional document and print the result."""
    from app.routing.router import route  # noqa: PLC0415

    analysis_type = route(prompt)
    typer.echo(f"🔍 Detected analysis type: {analysis_type}")

    async def _run() -> None:
        from app.analyzers.summary import SummaryAnalyzer  # noqa: PLC0415
        from app.models.analysis import AnalysisRequest, AnalysisType  # noqa: PLC0415
        from app.reporting.writer import write_markdown_report  # noqa: PLC0415

        request = AnalysisRequest(
            analysis_type=analysis_type,
            prompt=prompt,
        )

        if analysis_type == AnalysisType.SUMMARY:
            analyzer = SummaryAnalyzer()
            result = await analyzer.analyze(request, chunks=[])
        else:
            from app.models.analysis import AnalysisResult  # noqa: PLC0415

            result = AnalysisResult(
                request_id=request.id,
                analysis_type=analysis_type,
                summary=f"Analyzer for '{analysis_type}' is a Phase 1 stub.",
                warnings=["Full implementation coming in a later phase."],
            )

        report_path = write_markdown_report(result, output)
        typer.echo(f"✅ Report written to: {report_path}")
        if result.warnings:
            typer.echo("⚠️  Warnings:")
            for w in result.warnings:
                typer.echo(f"   - {w}")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
