# OS-MCP Server Dockerfile
# Multi-stage build for production deployment

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only dependency files first for better caching
COPY pyproject.toml README.md ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OS_MCP_MODE=prod

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Health check for HTTP transport
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default to HTTP transport on port 8000
EXPOSE 8000

# Entry point - can be overridden for stdio transport
ENTRYPOINT ["python", "-m", "server"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
