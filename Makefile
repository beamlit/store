ARGS:= $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

run-tool-dev:
	TOOL=$(ARGS) uv run fastapi dev --port 1338

run-tool:
	cp -r agent-tools/$(ARGS)/* app/tools/
	uv run fastapi run --port 1338

build-tool:
	docker build --build-arg TOOL=$(ARGS) -t agent-tools:$(ARGS) -f agent-tools/Dockerfile .

%:
	@:

.PHONY: run-tool run-tool-dev build-tool