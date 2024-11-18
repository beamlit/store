FROM python:3.12-slim

ARG TOOL="search"
ARG UV_VERSION="latest"

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY src/apps/app-function /beamlit/app
COPY src/common /beamlit/common
COPY README.md /beamlit/README.md
COPY LICENSE /beamlit/LICENSE

COPY src/functions/${TOOL} /beamlit/app/functions/
COPY src/functions/${TOOL}/pyproject.toml /beamlit/pyproject.toml

# Install the application dependencies.
WORKDIR /beamlit
RUN uv sync --no-cache

# Run the application.
ENV PATH="/beamlit/.venv/bin:$PATH"
CMD ["/beamlit/.venv/bin/fastapi", "run", "app/main.py", "--port", "80", "--host", "0.0.0.0"]