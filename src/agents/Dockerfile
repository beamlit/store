FROM python:3.12-slim

ARG AGENT="langchain-external-providers"
ARG UV_VERSION="latest"

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /beamlit

# Install the application dependencies.
COPY src/agents/${AGENT}/pyproject.toml /beamlit/pyproject.toml
RUN uv sync --no-cache

# Copy the application into the container.
COPY src/apps/app-agent /beamlit
COPY src/common /beamlit/common
COPY README.md /beamlit/README.md
COPY LICENSE /beamlit/LICENSE

COPY src/agents/${AGENT} /beamlit/agents/${AGENT}

# Clean app init file.
RUN rm /beamlit/__init__.py
# Run the application.
ENV AGENT=${AGENT}
ENV PATH="/beamlit/.venv/bin:$PATH"

CMD ["python", "main.py"]