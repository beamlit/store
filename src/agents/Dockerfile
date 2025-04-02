FROM node:22-alpine


WORKDIR /blaxel

COPY src/agents/blaxel-agent/package.json /blaxel/package.json

COPY src/agents/blaxel-agent/pnpm-lock.yaml /blaxel/pnpm-lock.yaml

RUN npm install -g pnpm && pnpm install
COPY src/agents/blaxel-agent .

RUN pnpm build

ENTRYPOINT ["node", "dist/index.js"]