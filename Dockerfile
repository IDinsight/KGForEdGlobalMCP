# Hosted Streamable HTTP image for the Knowledge Graph For Education Global MCP server.
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.2 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app/backend

# Locked runtime dependencies first so source and data changes reuse this layer.
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend/src ./src
RUN uv sync --locked --no-dev

COPY config /app/config
COPY data/graph_packages /app/data/graph_packages

ENV KGFEGMCP_ENV=prod \
    PATHS_PROJECT_DIR=/app \
    PATH="/app/backend/.venv/bin:$PATH"

RUN useradd --create-home --uid 10001 kgfegmcp
USER kgfegmcp

CMD ["python", "-m", "kgfegmcp.http_server"]
