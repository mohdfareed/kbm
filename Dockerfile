FROM python:3.12-slim

# Install uv for faster installs
RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install in system python (no venv needed in container)
RUN uv pip install --system .

# Data volume and HTTP defaults
ENV KBM_HOME=/data
EXPOSE 8000

# Default: start HTTP server for memory mounted at /config.yaml
ENTRYPOINT ["kbm"]
CMD ["start", "-c", "/config.yaml", "-t", "http"]
