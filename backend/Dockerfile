# Production-ready Dockerfile for EchoFix Backend
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 echofix && \
    mkdir -p /app && \
    chown -R echofix:echofix /app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY --chown=echofix:echofix requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn==21.2.0

# Copy application code
COPY --chown=echofix:echofix . .

# Ensure fixtures directory is included
RUN test -d fixtures || mkdir -p fixtures

# Switch to non-root user
USER echofix

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
