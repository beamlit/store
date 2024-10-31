ARGS:= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

run-tool-dev:
	TOOL=$(ARGS) PACKAGE=apps.app-tool uv run fastapi dev --port 1338 apps/app-tool

run-tool:
	cp -r agent-tools/$(ARGS)/* apps/app-tool/tools/
	PACKAGE=apps.app-tool uv run fastapi run --port 1338 apps/app-tool

build-tool:
	docker build --build-arg TOOL=$(ARGS) -t agent-tools:$(ARGS) -f agent-tools/Dockerfile .

run-docker-tool:
	docker run --rm -p 1338:80 agent-tools:$(ARGS)

run-agent-dev:
	AGENT=$(ARGS) PACKAGE=apps.app-agent uv run fastapi dev --port 1338 apps/app-agent

run-agent:
	cp -r agents/$(ARGS)/* apps/app-agent/agents/
	PACKAGE=apps.app-agent uv run fastapi run --port 1338 apps/app-agent

build-agent:
	docker build --build-arg AGENT=$(ARGS) -t agents:$(ARGS) -f agents/Dockerfile .

run-docker-agent:
	docker run --rm -p 1338:80 agents:$(ARGS)

%:
	@:

.PHONY: run-tool run-tool-dev build-tool