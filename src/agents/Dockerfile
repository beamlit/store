FROM node:20-slim

ARG AGENT_FOLDER="beamlit-agent"
ARG UV_VERSION="latest"

RUN apt update && apt install -y curl

RUN curl -fsSL https://raw.githubusercontent.com/beamlit/toolkit/main/install.sh | BINDIR=/bin sh
WORKDIR /beamlit

# Install dependencies
COPY src/agents/${AGENT_FOLDER} /beamlit
RUN npm i

# Copy source code and utils files

RUN npm run build
RUN cp -r dist/* /beamlit

ENV COMMAND="node index.js"

ENTRYPOINT ["bl","serve","--port","80","--module","src.agent.agent","--remote"]
