FROM python:3.12-slim

ARG TOOL="search"
ARG UV_VERSION="latest"

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY apps/app-function /beamlit/app
COPY uv.lock /beamlit/uv.lock
COPY README.md /beamlit/README.md
COPY LICENSE /beamlit/LICENSE

COPY functions/${TOOL} /beamlit/app/functions/
COPY functions/${TOOL}/pyproject.toml /beamlit/pyproject.toml

# Install the application dependencies.
WORKDIR /beamlit
RUN uv sync --frozen --no-cache

# Run the application.
ENV PATH="/beamlit/.venv/bin:$PATH"
CMD ["/beamlit/.venv/bin/fastapi", "run", "app/main.py", "--port", "80", "--host", "0.0.0.0"]