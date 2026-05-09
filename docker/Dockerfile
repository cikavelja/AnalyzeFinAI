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

# Create data directory for audit log
RUN mkdir -p data/converted

# Non-root user for security
RUN useradd --system --uid 1001 analizer
USER analizer

# Production entrypoint: Chainlit UI
# DevUI (devui_app.py) is NEVER used here
CMD ["chainlit", "run", "app/ui/chainlit_app.py", "--port", "8000", "--host", "0.0.0.0"]

EXPOSE 8000
