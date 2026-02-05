FROM python:3.12-slim
RUN pip install uv

# Install in system python
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv pip install --system .

# Runtime config
ENV KBM_HOME=/data
VOLUME /data
EXPOSE 8000

# Entrypoint handles init-if-missing
COPY scripts/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["default"]
