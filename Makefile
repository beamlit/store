ARGS:= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

run-function-dev:
	FUNCTION=$(ARGS) PACKAGE=apps.app-function uv run fastapi dev --port 1338 src/apps/app-function

run-function:
	mkdir -p src/apps/app-function/functions
	cp -r src/functions/$(ARGS)/* src/apps/app-function/functions/
	PACKAGE=apps.app-function uv run fastapi run --port 1338 src/apps/app-function

build-function:
	docker build --build-arg FUNCTION=$(ARGS) -t functions:$(ARGS) -f src/functions/Dockerfile .

run-docker-function:
	docker run --rm -p 1338:80 functions:$(ARGS)

run-agent-dev:
	AGENT=$(ARGS) PACKAGE=apps.app-agent uv run fastapi dev --port 1338 src/apps/app-agent

run-agent:
	rm -rf src/apps/app-agent/agents/beamlit.py
	mkdir -p src/apps/app-agent/agents
	cp -r src/agents/$(ARGS)/* src/apps/app-agent/agents/
	PACKAGE=apps.app-agent uv run fastapi run --port 1338 src/apps/app-agent

build-agent:
	docker build --build-arg AGENT=$(ARGS) -t agents:$(ARGS) -f src/agents/Dockerfile .

run-docker-agent:
	docker run --rm -p 1338:80 agents:$(ARGS)

%:
	@:

.PHONY: run-function run-function-dev build-function
