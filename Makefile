ARGS:= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

run-function-dev:
	bl serve --hotreload --module src.functions.$(ARGS).main.main --port 1337

run-function:
	bl serve --module src.functions.$(ARGS).main.main --port 1337

build-function:
	docker build --no-cache --build-arg FUNCTION_FOLDER=$(ARGS) -t functions:$(ARGS) -f src/functions/Dockerfile .

run-docker-function:
	docker run --rm -p 1337:80 functions:$(ARGS)

run-agent-dev:
	bl serve --hotreload --module src.agents.$(ARGS).main.main

run-agent:
	bl serve --hotreload --module src.agents.$(ARGS).main.main

build-agent:
	docker build --no-cache --build-arg AGENT_FOLDER=$(ARGS) -t agents:$(ARGS) -f src/agents/Dockerfile .

run-docker-agent:
	docker run --rm -p 1338:80 agents:$(ARGS)

%:
	@:

.PHONY: run-function run-function-dev build-function