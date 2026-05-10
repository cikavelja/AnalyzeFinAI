"""FastAPI application factory.

Production entrypoint: uvicorn app.api.main:app
Development:          uvicorn app.api.main:app --reload --port 8000

In production the built React assets are served as static files from ui/dist/.
"""
from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.analysis import router as analysis_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.models import router as models_router

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AnalizerAI API",
    description="REST API for AI-powered document analysis",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the React dev server and any same-origin production access
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # CRA / alternative dev port
        "http://localhost:8000",  # same-origin in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

app.include_router(health_router)
app.include_router(analysis_router)
app.include_router(documents_router)
app.include_router(models_router)

# ---------------------------------------------------------------------------
# Serve React static build in production (ui/dist must exist)
# ---------------------------------------------------------------------------

_STATIC_DIR = Path(__file__).parent.parent.parent / "ui" / "dist"

if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
    logger.info("static_files_mounted", path=str(_STATIC_DIR))
else:
    logger.info("static_files_skipped", reason="ui/dist not found — run 'npm run build' in ui/")
