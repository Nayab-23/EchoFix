# Production-ready Dockerfile for EchoFix Backend
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 echofix && \
    mkdir -p /app && \
    chown -R echofix:echofix /app

# Set working directory
WORKDIR /app

# Install system dependencies including GitHub CLI
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    git \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
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

# Run with gunicorn (authenticate gh CLI first)
CMD sh -c 'echo "$GITHUB_TOKEN" | gh auth login --with-token 2>/dev/null || true && gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app'
