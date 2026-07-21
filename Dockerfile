# Stage 1: Build & Dependencies Environment
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency specifications
COPY pyproject.toml README.md ./

# Sync project dependencies
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache -e .

# Stage 2: Runtime Environment
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime OS dependencies and Playwright dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2t64 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Playwright Chromium browser binaries
RUN playwright install chromium --with-deps

# Create non-root system user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

# Expose metrics port
EXPOSE 8000

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["system", "health"]
