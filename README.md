# CLI-first Python app

A minimal Python application where the CLI is ready on day one. Change the application, update OpenAPI, and test through the generated `appctl` CLI.

Requires Python 3.14+, uv, and Go 1.26+.

```sh
uv sync
make check
uv run --locked python -m src.server
```

In another terminal:

```sh
./bin/appctl search "create task" --json
./bin/appctl commands show tasks create --json
./bin/appctl tasks create --set title="Ship from the CLI" -o json
```

`make check` regenerates the CLI from `openapi/openapi.yaml`, builds it, and runs acceptance tests through CLI commands. `make test` only builds and tests the checked-in generated CLI.

Generated output under `internal/generated/` and `skills/appctl/` is committed with API changes. The pipeline uses [Lathe](https://github.com/lathe-cli/lathe), pinned by version.

## Application versioning

Application releases follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html):

- The core is `X.Y.Z`, with nonnegative integers and no leading zeroes (clause 2).
- Published versions are immutable (clause 3). Never change their contents or move, rename, delete, or reuse their release tags.
- Changes require a new version.
- Prereleases use only `X.Y.Z-alpha.N`, `X.Y.Z-beta.N`, or `X.Y.Z-rc.N` (clause 9).
- `N` starts at 1 and increases for each publication within the same target version and stage, without leading zeroes.
- SemVer precedence compares the core and `N` numerically (clause 11).

For the same core version, precedence is `alpha < beta < rc < final`.
For example, `1.2.3-rc.2 < 1.2.3-rc.10 < 1.2.3`.
Release versions exclude `-fix.N`, `-hotfix.N`, build metadata, and `git describe` output.
The public contract includes the API, CLI, configuration, and data formats.
Increment MAJOR for incompatible changes, MINOR for compatible features, and PATCH for compatible fixes.
Reset lower components to zero when incrementing MAJOR or MINOR.
During `0.y.z`, increment MINOR for incompatible changes.

The Python version source is `pyproject.toml` `project.version`.
Derive the release tag from that value with this exact [PEP 440 mapping](https://packaging.python.org/en/latest/specifications/version-specifiers/#pre-releases):

| Release Git tag | `project.version` | Example |
| --- | --- | --- |
| `vX.Y.Z` | `X.Y.Z` | `v1.2.3` → `1.2.3` |
| `vX.Y.Z-alpha.N` | `X.Y.ZaN` | `v1.2.3-alpha.1` → `1.2.3a1` |
| `vX.Y.Z-beta.N` | `X.Y.ZbN` | `v1.2.3-beta.2` → `1.2.3b2` |
| `vX.Y.Z-rc.N` | `X.Y.ZrcN` | `v1.2.3-rc.2` → `1.2.3rc2` |

Before release, make sure that the tag and manifest at the tagged commit represent the same logical version.
Python metadata excludes `v` and artifact prefixes.
Prereleases stay out of stable channels.
If the Python server and generated Go CLI release independently, each artifact uses a separate version sequence and a fixed tag prefix.
For example, `v1.2.3-rc.2` represents Python version `1.2.3rc2`, while `appctl-v0.4.0` represents CLI version `0.4.0`.
The CLI tag supplies its Go version, without a separate version file.
This convention applies to future releases and does not change published tags.

