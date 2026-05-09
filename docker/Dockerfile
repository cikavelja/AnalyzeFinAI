### Stage 1 — Build React UI
FROM node:20-slim AS ui-builder

WORKDIR /ui
COPY ui/package.json ui/package-lock.json* ./
RUN npm ci --ignore-scripts
COPY ui/ .
RUN npm run build

### Stage 2 — Python runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specs first (layer caching)
COPY pyproject.toml ./

# Install production dependencies only (no dev extras)
RUN pip install --no-cache-dir -e .

# Copy application source
COPY app/ ./app/

# Copy built React assets from Stage 1
COPY --from=ui-builder /ui/dist ./ui/dist

# Non-root user for security
RUN useradd --system --uid 1001 analizer

# Create data directories and assign ownership before switching to non-root
RUN mkdir -p data/uploads data/converted && chown -R analizer:analizer data/

USER analizer

# Production entrypoint: FastAPI via uvicorn (serves React static files too)
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
