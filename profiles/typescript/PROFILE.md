# TypeScript profile

Add only when TypeScript/JavaScript is a material source surface.

Minimum additions:

- one declared package manager and committed lockfile;
- no dynamic dependency ranges for critical application tooling without explicit justification;
- typecheck, lint, test and production build gates appropriate to the project;
- generated/minified/hash-named assets are built from source and are not edited manually;
- API/configuration contracts have one owner rather than duplicated literals across clients;
- timers, subscriptions, workers, streams and browser/native bridges have explicit cleanup;
- user-facing persisted state has migration/reset semantics;
- bundle-size/performance budgets are added when they materially affect product quality.

## Operating-contract mapping

Use the declared package manager's native scripts/tasks behind `.engineering/commands.json`; do not add a second task runner only for naming consistency.

Typical mapping:

- `setup` — install/sync from the committed lockfile;
- `doctor` — verify Node/runtime/package-manager versions and required local tools;
- `dev` — start the development application/server in foreground mode;
- `check` — formatting/lint/typecheck plus cheap structural gates;
- `test` — unit/integration/contract tests as appropriate;
- `e2e` — complete critical browser/application journeys;
- `build` — create a uniquely identified production/runnable build artifact;
- `smoke` — serve/run the built output and exercise a minimal real path;
- `package` — create distributable archive/desktop bundle/package when applicable;
- `stop` — stop project-owned local servers/workers when applicable;
- `clean` — remove project-owned generated bundles/staging/temp output.

## Browser E2E

For browser/web E2E, **prefer Playwright** unless the repository already has an equally strong established solution. Do not introduce Playwright merely to replace a working equivalent for naming consistency.

Keep E2E focused on a small set of critical journeys whose complete outcome depends on the assembled application. Keep deterministic component/domain behavior in unit/integration tests.

When the claim concerns production output, run E2E against the built/served production artifact when practical rather than only the dev server.

## Browser E2E environment fidelity

Specialize `.engineering/e2e.json` around material browser/runtime/deployment dimensions: supported browser engine/version family, viewport/device class when behavior changes materially, built production output vs dev server, backend/API implementation, authentication/external services and network/deployment topology when part of the claim.

A CI browser running the supported production build can be `representative_virtual` for browser/application behavior when the browser/OS/deployment dimensions are sufficiently representative. Browser emulation of viewport/device characteristics does not become physical-device evidence. Real browser/device farms can be `representative_physical` when hardware/input/device behavior is material; a real deployed/customer-equivalent target is `target_environment` only for the dimensions it actually represents.

Final production-like/manual validation should primarily close residual deployment, real-device/input, protected-service or external-topology gaps. Navigation, persistence, API wiring, authentication flow, built-asset loading and ordinary recovery paths should be automated earlier whenever practical.

Playwright/browser E2E cleanup must close browser/context processes and project-owned servers/listeners, and isolate/remove run-owned profiles, storage, downloads and temporary data. Traces/screenshots/videos/logs produced on failure are bounded CI evidence artifacts with build/run identity, not permanent repository content.

Local dev/test servers bind to loopback by default unless external access is intentional, use configurable collision-aware ports, and leave no project-owned listener or worker after stop/failure/interrupt.

Material build artifacts use staging/promote, unique build identity, manifest/checksum/build delta and bounded local retention. Generated bundle assets remain reproducible from source and lockfile.
