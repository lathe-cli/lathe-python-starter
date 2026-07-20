# Agent Development Contract

This repository is CLI-first. The generated `appctl` CLI is the primary acceptance surface for application behavior.

For every API-facing change:

1. Update the Python application under `src/`.
2. Update `openapi/openapi.yaml` in the same change. It is the API contract and CLI source of truth.
3. Run `make check` to regenerate, build, and test through `appctl`.
4. Commit the matching changes under `internal/generated/`, `skills/appctl/`, and `cmd/appctl/cli.yaml`.

Do not hand-edit generated files. Use direct HTTP only for transport-level checks that the generated CLI cannot express.

Before guessing a command or flag, use `appctl search "<intent>" --json`, then `appctl commands show <path...> --json`.

Keep the Python application on the standard library until a concrete requirement needs a package. Use `uv` for Python commands. Do not add database, authentication, deployment, or compatibility scaffolding without an explicit requirement.

