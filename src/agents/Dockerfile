FROM python:3.12-slim

ARG AGENT_FOLDER="beamlit-agent"
ARG UV_VERSION="latest"
RUN apt update && apt install -y curl

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN curl -fsSL https://raw.githubusercontent.com/beamlit/toolkit/main/install.sh | BINDIR=/bin sh
WORKDIR /beamlit

# Install the application dependencies.
COPY src/agents/${AGENT_FOLDER}/ /beamlit
RUN uv sync --no-cache

COPY README.m[d] /beamlit/README.md
COPY LICENS[E] /beamlit/LICENSE

ENV PATH="/beamlit/.venv/bin:$PATH"

ENTRYPOINT ["bl", "serve", "--module", "main.main", "--port", "80", "--remote"]