ARGS:= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

run-function-dev:
	TOOL=$(ARGS) PACKAGE=apps.app-function uv run fastapi dev --port 1338 apps/app-function

run-function:
	cp -r functions/$(ARGS)/* apps/app-function/functions/
	PACKAGE=apps.app-function uv run fastapi run --port 1338 apps/app-function

build-function:
	docker build --build-arg TOOL=$(ARGS) -t functions:$(ARGS) -f functions/Dockerfile .

run-docker-function:
	docker run --rm -p 1338:80 functions:$(ARGS)

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

.PHONY: run-function run-function-dev build-function