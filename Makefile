ARGS:= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

run-function-dev:
	FUNCTION=$(ARGS) uv run fastapi dev --port 1338 src/apps/app-function

run-function:
	FUNCTION=$(ARGS) uv run fastapi run --port 1338 src/apps/app-function

build-function:
	docker build --build-arg FUNCTION=$(ARGS) -t functions:$(ARGS) -f src/functions/Dockerfile .

run-docker-function:
	docker run --rm -p 1338:80 functions:$(ARGS)

run-agent-dev:
	AGENT=$(ARGS) uv run fastapi dev --port 1338 src/apps/app-agent

run-agent:
	AGENT=$(ARGS) uv run fastapi run --port 1338 src/apps/app-agent

build-agent:
	docker build --build-arg AGENT=$(ARGS) -t agents:$(ARGS) -f src/agents/Dockerfile .

run-docker-agent:
	docker run --rm -p 1338:80 agents:$(ARGS)

%:
	@:

.PHONY: run-function run-function-dev build-function