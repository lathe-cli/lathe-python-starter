.PHONY: cli-sync cli-build test check

cli-sync:
	cp cli.yaml cmd/appctl/cli.yaml
	go tool lathe bootstrap
	go mod tidy

cli-build:
	go build -o bin/appctl ./cmd/appctl

test: cli-build
	uv run --locked python -m unittest discover -s tests

check: cli-sync test
	uv run --locked python -m compileall -q src tests
	go vet ./...
