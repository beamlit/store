
FROM python:3.12-slim

ARG AGENT="langchain-chat-completions"
ARG UV_VERSION="latest"

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY apps/app-agent /beamlit/app
COPY uv.lock /beamlit/uv.lock
COPY README.md /beamlit/README.md
COPY LICENSE /beamlit/LICENSE

COPY agents/${AGENT} /beamlit/app/agents/
COPY agents/${AGENT}/pyproject.toml /beamlit/pyproject.toml

# Install the application dependencies.
WORKDIR /beamlit
RUN uv sync --frozen --no-cache

# Run the application.
CMD ["/beamlit/.venv/bin/fastapi", "run", "app/main.py", "--port", "80", "--host", "0.0.0.0"]