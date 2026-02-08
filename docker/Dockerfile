FROM python:3.14-slim
RUN pip install uv

# Install in system python
WORKDIR /app
COPY . .
RUN uv pip install --system .

# Runtime config
ENV KBM_HOME=/data
VOLUME /data
EXPOSE 8000

# Entrypoint
COPY docker/entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
