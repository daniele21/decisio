# Documentation map

Use progressive disclosure. Start from `AGENTS.md`, add the closest scoped guide, then read only the canonical source required by the task.

## Canonical owners

| Question | Source |
| --- | --- |
| What is this repository/project and why does it exist? | README identity sections: title/summary/`Why this exists` |
| Who is the product for, what problem/outcome does it own, and which principles/quality promises constrain product decisions? | `product.md` when product development applies |
| How does a person install, configure, start or use it? | README usage sections: setup/run/use/configuration/public examples |
| How is product-impact depth/routing declared? | `.engineering/product.json` |
| What exists and who owns it? | `architecture.md` |
| What is integrated, blocked or next? | `current-state.md` |
| How does a durable feature behave? | `features/` when code/tests alone are insufficient |
| Why was a durable architectural choice made? | `adr/` |
| What substantial implementation is active now? | `workstreams/` |
| How should an agent perform a recurring procedure? | `skills/`, not docs |
| How does setup/run/check/test/E2E/build/package/cleanup work? | `.engineering/commands.json` |
| Which E2E environments/journeys/evidence modes apply? | `.engineering/e2e.json` |
| What are UX/brand/design-system constraints when `product-ui` applies? | `design/ux-contract.json` + `design/brand-kit.json` + declared design owner |
| What changed between concrete build artifacts? | generated `BUILD_CHANGELOG.md` |
| What happened historically during implementation? | Git history |

## Documentation impact contract

Code and affected durable documentation must agree **when a coherent change is integrated/released**.

During `ITERATION`, documentation may remain pending while behavior is still changing. Do not churn README/product/current-state/feature docs after every private edit, temporary branch commit or parent/child branch synchronization.

Before an `INTEGRATION` candidate is declared ready, assess documentation impact from the resulting observable behavior and make every affected canonical owner describe the exact candidate behavior.

Do not update every document mechanically. Update only owners whose durable truth changed.

| Change affects | Update |
| --- | --- |
| core project purpose or public top-level framing | README identity sections |
| durable primary users/consumers, owned problem/job, value proposition, core outcomes/non-goals, product principles or material product-quality promise | `product.md`; update README identity only when its public framing also changed |
| product-development applicability/routing/depth semantics | `.engineering/product.json` and applicable agent/skill routing |
| installation, prerequisites, public configuration, public CLI/API/UI use/examples | README usage sections |
| durable non-obvious feature behavior/constraints | existing/new `features/` owner |
| architecture boundaries/ownership | `architecture.md` |
| material durable decision/rationale | ADR |
| security/trust/data-lifecycle contract | `SECURITY.md` and/or owning architecture/feature doc |
| canonical operational/development-velocity semantics | `.engineering/commands.json` plus human-facing README usage only when needed |
| E2E environment/journey/evidence semantics | `.engineering/e2e.json` plus durable feature/operations docs only when user/operator behavior changed |
| product-experience/brand contract | owning `design/*` source when `product-ui` applies |
| integrated/blocked/next repository state | `current-state.md` |

### Product source ownership

`product.md` is concise durable product truth, not a backlog or long-form PRD. Keep only information that should guide future decisions: primary users/consumers, owned problems/jobs, value, outcomes/non-goals, durable principles, material quality promises and useful success signals.

Feature-local assumptions, experiments and temporary shaping belong in the active issue/workstream/change context. Promote only durable learning into `product.md`, feature docs, architecture, tests or another owning contract.

Do not duplicate a stronger incumbent product charter/strategy source merely to satisfy a filename. During adoption, `.engineering/product.json.strategy_source` may point to the actual canonical source instead.

### README section ownership

Treat README as multiple semantic owners rather than one document rewritten as a unit.

**Identity** describes what the project is, why it exists and its primary audience/outcome. Update only when those public claims materially change.

**Usage** describes what a user/developer must do now: prerequisites, setup, run/start, configuration, public API/CLI/UI flow, examples and shortest successful path. Before integration, update usage when the old instructions would fail, omit a newly required step, advertise a removed path, use stale defaults/options or otherwise mislead users of the integrated candidate.

A feature can legitimately produce `README_IDENTITY: N/A` and `README_USAGE: UPDATED`.

README summaries may link to canonical technical/product owners instead of duplicating detailed contracts. README is a reliable entry point, not an implementation diary.

## Current-state ownership

`current-state.md` owns short repository-level **integrated / blocked / next** truth.

Do not update it for:

- every agent commit;
- temporary feature-branch progress;
- draft/ready metadata changes;
- stack sync/rebase mechanics with no repository-level state change.

Update it when the repository's actual integrated/blocked/next truth changes.

## Workstream lifecycle

A fact has one canonical owner. Summaries link to that owner instead of duplicating detailed acceptance/status.

Active workstream documents are disposable:

`shape when material -> plan -> parallel/serial subtasks -> integrate outcome -> transfer durable knowledge -> delete plan`

For `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC`, the existing workstream may carry a compact Product Intent section before the engineering DAG. Delete that section for `PRODUCT_NONE`/`PRODUCT_LOCAL`; do not create a second product-plan document merely because product reasoning occurred.

Prefer observable vertical outcomes. Technical-layer progress belongs in terse workstream state while active, not permanent documentation.

Keep a completed plan only with independent audit/regulatory/release/historical value; move such exceptional material to an explicitly historical location and never treat it as current truth.

Generated build manifests/deltas and E2E/screenshots/videos/traces are evidence and follow artifact retention, not durable documentation retention.

For `product-ui`, keep only bounded key reference views needed to communicate the product system. Do not use exported screenshot history as a parallel design source of truth.

## Before creating/updating documentation

1. Identify product impact and delivery stage when relevant.
2. During iteration, avoid durable-doc churn unless updating the doc materially helps the implementation decision itself.
3. Before integration, assess documentation impact from observable resulting behavior.
4. Search for an existing canonical owner.
5. Update that owner; for README, touch only affected identity/usage sections.
6. Create a document only for durable independently readable knowledge or an active bounded workstream.
7. Link it from the map/closest domain index when needed.
8. Delete obsolete temporary planning/mockup/research material and stale instructions/examples after durable learning is transferred.

Do not create a document solely to record that a PR/task completed.

## Context routes and resume pointers

`.engineering/documentation-policy.json` defines representative instruction/configuration reading routes and budgets, including the bounded `product` route for material product shaping, Skills and actual scoped-guide chains. `scripts/verify_agent_context.py` reports their files/costs; read relevant source, consumers and additional contracts as the task requires. Avoid treating the route manifest as a complete context limit or validation selector.

Multi-session state stays in the optional checkpoint of the active workstream. Refresh repository/source identity before trusting it; preserve confirmed facts separately from hypotheses. On integration completion, transfer residual physical acceptance and any material post-release product question to their canonical owners before deleting the plan. No duplicate status or narrative archive is needed.
