# --- Build stage ---
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install kbm
WORKDIR /app
COPY . .
RUN uv pip install --system .

# --- Runtime stage ---
FROM python:3.14-slim

# Copy environment
COPY --from=builder /usr/local /usr/local

# Data config
ENV KBM_HOME=/data
VOLUME /data

# Network config
ENV KBM_TRANSPORT=http
ENV KBM_HOST=0.0.0.0
ENV KBM_PORT=8000
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["kbm"]
CMD ["start"]
