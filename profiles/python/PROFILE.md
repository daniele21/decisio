# Python profile

Add only when Python is a material implementation/runtime surface.

Minimum additions to the universal baseline:

- one canonical package/build configuration, normally `pyproject.toml`;
- committed lockfile for applications/tools where reproducibility matters;
- explicit supported Python versions;
- formatter/linter/static or type checks appropriate to the codebase;
- deterministic unit/integration tests with no hidden network dependency unless explicitly marked;
- CI matrix only across versions the project actually claims to support;
- virtual environments/caches/build artifacts excluded from source control;
- subprocesses, threads, temp files and external clients follow the resource lifecycle contract;
- packaging entry points and runtime data files validated from a clean environment.

Prefer standard-library or already-adopted tooling when it is sufficient; do not add overlapping lint/test/package systems without a concrete need.

## Operating-contract mapping

Map existing Python tooling to `.engineering/commands.json`; do not add Make/Docker wrappers solely to normalize naming.

Typical mapping:

- `setup` — create/sync the project-local environment using the declared package manager/lockfile;
- `doctor` — verify supported Python/toolchain and required local/native dependencies;
- `dev` — start the supported application/server/runtime in foreground mode when applicable;
- `check` — formatter/linter/type/static gates;
- `test` — pytest/unittest/unit/integration/contract gates as owned by the project;
- `e2e` — start the real application/server/executable and exercise one or more critical complete workflows through its public API/protocol/UI boundary;
- `build` — build wheel/sdist/application/server bundle or other material artifact with unique build identity;
- `smoke` — execute/import/start the built artifact and exercise a minimal real path;
- `package` — create the intended distributable when distinct from `build`;
- `stop` — stop project-owned local server/processes when applicable;
- `clean` — remove project-owned virtual/build/staging/temp output without deleting unrelated user/global caches.

For API/local-server projects, prefer process-level/API E2E using the existing Python HTTP/protocol client rather than adding Playwright when no browser surface exists. A strong E2E starts the real process, waits for readiness, performs a complete critical workflow, verifies externally visible state/result, shuts down and verifies zero residue.

## Python/server E2E environment fidelity

Specialize `.engineering/e2e.json` around material runtime/deployment dimensions such as supported Python/runtime/native-library versions, packaged artifact vs source execution, database/service implementation, OS/architecture, container/process topology and external dependencies when they are part of the product claim.

A real process started from the supported built/package artifact in CI can be `representative_virtual` for API/protocol/application behavior when its runtime, dependencies and service topology are representative enough. Containerized or substitute services remain weaker evidence for dimensions they do not reproduce. Real infrastructure/hardware may be `representative_physical` where material; an actual staging/production-equivalent environment is `target_environment` only for the dimensions it truly matches.

Final staging/production-like/manual validation should mainly close residual external topology, protected-authority, infrastructure or hardware gaps. Startup/readiness, protocol/API wiring, persistence with representative disposable dependencies, package entry points, restart/recovery and shutdown/cleanup should move into automated E2E whenever practical.

For localhost Python services, `dev` should bind to loopback by default, use a configurable collision-checked port, expose readiness/health when requests are accepted, and own all subprocesses/listeners. `stop`/failure/timeout/interrupt must verify that no project-owned listener remains.

E2E run-owned databases, files, sessions, downloads, subprocesses and diagnostics must be isolated and cleaned. Failure logs/traces are bounded evidence artifacts with build/run identity.

Build output is staged then promoted on success, gets a unique build ID plus manifest/checksum/build delta, and defaults to the latest two successful local artifacts per comparable lineage.
