FROM python:3.12-slim

ARG FUNCTION="search"
ARG UV_VERSION="latest"

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /beamlit

# Install the application dependencies.
COPY src/functions/${FUNCTION}/pyproject.toml /beamlit/pyproject.toml
RUN uv sync --no-cache

# Copy the application into the container.
COPY src/apps/app-function /beamlit
COPY src/common /beamlit/common
COPY README.md /beamlit/README.md
COPY LICENSE /beamlit/LICENSE

COPY src/functions/${FUNCTION} /beamlit/functions/${FUNCTION}

# Clean app init file.
RUN rm /beamlit/__init__.py
# Run the application.
ENV FUNCTION=${FUNCTION}
ENV PATH="/beamlit/.venv/bin:$PATH"

CMD ["/beamlit/.venv/bin/fastapi", "run", "main.py", "--port", "80", "--host", "0.0.0.0"]