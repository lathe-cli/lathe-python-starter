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

## Application versioning

Use [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) for application releases:

- Use `X.Y.Z`, with nonnegative integers and no leading zeroes (clause 2).
- Never change the contents of a published version or move, rename, delete, or reuse its release tag (clause 3).
- Publish changes under a new version.
- Use only `X.Y.Z-alpha.N`, `X.Y.Z-beta.N`, or `X.Y.Z-rc.N` for prereleases (clause 9).
- Start `N` at 1 and increase it for each publication within the same target version and stage, without leading zeroes.
- Compare versions by SemVer precedence (clause 11), with numeric comparisons for the core and `N`.

For the same core version, precedence is `alpha < beta < rc < final`.
For example, `1.2.3-rc.2 < 1.2.3-rc.10 < 1.2.3`.
Do not use `-fix.N`, `-hotfix.N`, build metadata, or `git describe` output as release versions.
Declare the public API, CLI, configuration, and data contracts before choosing a version increment.
Increment MAJOR for incompatible changes, MINOR for compatible features, and PATCH for compatible fixes.
Reset lower components to zero when incrementing MAJOR or MINOR.
During `0.y.z`, increment MINOR for incompatible changes.

Use `pyproject.toml` `project.version` as the Python version source.
Derive the release tag from that value with this exact [PEP 440 mapping](https://packaging.python.org/en/latest/specifications/version-specifiers/#pre-releases):

| Release Git tag | `project.version` |
| --- | --- |
| `vX.Y.Z` | `X.Y.Z` |
| `vX.Y.Z-alpha.N` | `X.Y.ZaN` |
| `vX.Y.Z-beta.N` | `X.Y.ZbN` |
| `vX.Y.Z-rc.N` | `X.Y.ZrcN` |

Before release, make sure that the tag and manifest at the tagged commit represent the same logical version.
Keep `v` and artifact prefixes out of Python metadata.
Keep prereleases out of stable channels.
If the Python server and generated Go CLI release independently, use separate version sequences and a fixed tag prefix for each artifact.
For example, use `v1.2.3-rc.2` for Python version `1.2.3rc2` and `appctl-v0.4.0` for CLI version `0.4.0`.
Use the CLI tag as its Go version source, without a separate version file.
Apply this convention to future releases without changing published tags.

