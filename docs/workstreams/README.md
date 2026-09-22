# Active workstreams

Use this directory only when a substantial change needs durable dependency or state coordination across multiple sessions.

Small coherent changes should stay in their issue/PR and code; they do not need a workstream document.

An active workstream owns both plan and progress. When it is complete:

1. move durable truth into code, tests, architecture, feature docs or ADRs;
2. update `docs/current-state.md`;
3. delete the completed workstream by default.

The current repository-hardening backlog is intentionally owned by [`docs/repository-quality.md`](../repository-quality.md), not duplicated here.
