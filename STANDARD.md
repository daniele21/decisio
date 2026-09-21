# Agent-Native Reference Engineering Standard

Version: 0.11.0

## Purpose

This standard defines the minimum product-engineering properties expected from software repositories maintained by humans and coding agents. It optimizes for product-outcome clarity, correctness, operational simplicity, bounded resources, change safety, reproducibility, clean lifecycle behavior, product-experience quality where applicable, low context cost and **fast delivery at sufficient confidence**.

The product rule is:

> Outcomes before output. Evidence before commitment. Product reasoning must be proportional to product risk.

The central engineering rule is:

> Make ownership, limits, failures and costs explicit, using the simplest solution that preserves the required invariants.

The delivery rule is:

> Optimize for sufficient confidence per unit of feedback time. Iterate cheaply, integrate rigorously, release comprehensively.

The automation rule is:

> Automation executes automatable work; humans make material decisions and provide evidence that genuinely requires a real environment.

The E2E rule is:

> Integration must prove affected complete workflows automatically. Final target-environment validation confirms residual environment-specific claims at release rather than becoming part of every feature-integration loop.

For products with a material UI:

> Make the user's next decision obvious, reveal complexity progressively, communicate state clearly, and keep the interface consistent, accessible and recoverable.

The standard is intentionally not a framework. Common semantics do not require common product-management, build, test, design or UI tools.

Focused normative contracts:

- [`PRODUCT-DEVELOPMENT-CONTRACT.md`](PRODUCT-DEVELOPMENT-CONTRACT.md) — product intent, proportional discovery/shaping, product risks, assumptions/evidence, success and learning semantics;
- [`OPERATING-CONTRACT.md`](OPERATING-CONTRACT.md) — command/build/artifact/runtime lifecycle semantics;
- [`EXECUTION-CAPABILITY-CONTRACT.md`](EXECUTION-CAPABILITY-CONTRACT.md) — delivery stages, risk-based validation, executor routing and evidence reuse;
- [`E2E-ENVIRONMENT-CONTRACT.md`](E2E-ENVIRONMENT-CONTRACT.md) — E2E environment fidelity and UI evidence modes;
- [`PRODUCT-EXPERIENCE-CONTRACT.md`](PRODUCT-EXPERIENCE-CONTRACT.md) — optional UX/UI semantics.

## 1. Product impact and engineering delivery are separate

Product impact depth, delivery stage and validation depth are independent axes.

### Product impact depth

- `PRODUCT_NONE` — no material change to supported behavior/product promise; no product ceremony;
- `PRODUCT_LOCAL` — small already-settled behavior change; establish local user/consumer outcome and acceptance only;
- `PRODUCT_FEATURE` — new capability or meaningful supported workflow/behavior change; establish product intent, risks/assumptions, success and non-goals before substantial implementation;
- `PRODUCT_STRATEGIC` — material change to target user, product boundary, value proposition, trust/platform/distribution/business model or another broad product decision; use stronger discovery/evidence and rollout/learning reasoning.

Product depth follows impact, uncertainty and reversibility, not file count or estimated coding effort. Discovery may validly conclude `DO_NOT_BUILD`, `NARROW_SCOPE` or `CHOOSE_ALTERNATIVE`.

### Delivery stages

`ITERATION`

- default while implementation is changing;
- optimize for rapid falsification of the current edit;
- formatter/static checks, focused tests, affected compile/typecheck and direct-contract tests as needed;
- no automatic exact-head/full-diff/docs/preflight/release ceremony.

`INTEGRATION`

- begins when a coherent vertical slice produces an observable user/system outcome and is ready to converge into the shared development/integration branch;
- refresh exact head/base, review the complete diff, make affected durable documentation current and execute/route the required risk gates;
- affected complete workflows are proven with the smallest sufficient automated E2E journey when lower-level evidence cannot prove the outcome;
- residual `REAL_ENVIRONMENT` requirements are recorded but do not normally block integration into the shared development branch.

`RELEASE`

- stable-branch promotion, release candidates and reference-grade checkpoints;
- `FULL` validation is expected;
- release-critical build/package/E2E run;
- every required residual `REAL_ENVIRONMENT` confirmation is blocking before the strongest release/stable claim is made.

### Validation depth

- `LEAN` — docs/governance/metadata or cheap universal guards;
- `SCOPED` — contained owner/module plus direct consumers/tests/lint/compile;
- `STRONG` — cross-boundary or release-sensitive risk cone;
- `FULL` — release/promotion or changes where safe narrowing cannot be trusted.

`FULL` is normal at release and exceptional during ordinary feature work.

The selector should identify **risk dimensions and concrete required gates first**, then summarize them with a profile. Profiles are not monolithic suite aliases.

## 2. Simplicity and ownership

Every dependency, abstraction, cache, worker, service, queue, layer and document adds maintenance and reasoning cost. Add one only for an observed or clearly specified problem.

Mutable state, public contracts, configuration values, persisted data, caches, significant resources, product intent, design tokens and durable decisions must have an identifiable owner. Avoid parallel sources of truth and duplicated policy.

Before changing a shared boundary, inspect its owner, direct consumers, fakes/adapters and nearby tests.

A repository should be understandable at a high level from its product source where applicable, README, architecture document and accepted ADRs without broad historical ingestion.

## 3. Vertical outcomes and parallel work

Prefer changes that unlock an observable user/system outcome end to end.

A technical layer, adapter, ViewModel, migration helper or test harness is normally a **subtask** of a vertical slice unless it is independently valuable, mergeable and reviewable.

Parallel development does not imply stacked publication. Independent branches/worktrees may execute in parallel, but related work should converge early onto the coherent feature/integration outcome.

A PR whose only purpose is synchronizing a parent into a child is a coordination smell. Stacked PRs are justified only when each layer has independent integration/review value or separate ownership genuinely requires them.

## 4. Failure and recovery

Failure is normal behavior, not an exception to design.

Critical workflows define applicable behavior for:

- invalid input;
- partial initialization/dependency failure;
- timeout/cancellation;
- shutdown during work;
- restart/recovery;
- interrupted persistence/migration;
- failed build/package promotion;
- stale temporary/process/lock state.

For UI products, loading, empty, error, disabled, offline, permission and partial-result states are also normal product states.

A failing validation gate is evidence. Classify the cause and identify the violated invariant/owner before changing production code. Do not suppress a legitimate test or repeatedly patch symptoms without a new falsifiable hypothesis.

## 5. Resource lifecycle

For every significant resource define as applicable:

- owner/acquisition;
- lifetime/cardinality;
- memory/disk/CPU/GPU budget;
- concurrency/backpressure;
- timeout/cancellation;
- release/failure cleanup;
- idle/pressure behavior;
- observability.

No unbounded queue/list/cache is acceptable on an unbounded input path.

Processes, listeners, ports, locks, temp directories, build staging areas, test databases, browser/device sessions, logs, caches and evidence artifacts are resources too.

Cleanup must cover success, failure, timeout, cancellation, interruption and partial initialization. Cleanup may remove only resources whose ownership is established.

## 6. Automation and execution capability

Every required gate is classified for the current agent/session as:

- `AGENT_LOCAL` — current agent can execute it directly;
- `REMOTE_AUTOMATED` — deterministic/automatable but unavailable in the current agent environment;
- `REAL_ENVIRONMENT` — genuinely requires representative hardware, protected authority/external environment or human judgement.

An ordinary compile/lint/test/R8/package/emulator gate does not become `REAL_ENVIRONMENT` merely because the current agent lacks the SDK.

A human must not become the fallback runner for automatable deterministic work.

When equivalent local execution exists, use it for faster feedback. When it does not, repository-owned remote automation is a valid execution backend.

At `INTEGRATION`, all affected automatable gates must be satisfied; `REAL_ENVIRONMENT` evidence is classified and deferred to `RELEASE` unless the repository explicitly defines a different product branch model.

At `RELEASE`, required `REAL_ENVIRONMENT` evidence is blocking.

## 7. Equivalent evidence reuse

At `INTEGRATION` and `RELEASE`, exact-head evidence must be current for the claim, but **unchanged evidence should not be rerun for collaboration metadata changes**.

Reuse successful evidence when it remains sufficient for:

- exact source head;
- material target/base relationship;
- required gates;
- selected profile or stronger equivalent;
- E2E environment/fidelity/evidence mode when relevant.

PR number, draft/ready state, labels and comments are not source-evidence identity by themselves.

Rerun only missing, stale or insufficient evidence.

## 8. Environment fidelity

Execution capability and environment fidelity are independent dimensions.

A CI Android emulator can be `REMOTE_AUTOMATED` while only `simulated_or_emulated`. A physical device farm can also be `REMOTE_AUTOMATED` while providing `representative_physical` evidence.

Critical E2E journeys declare target environments, automated execution environments and fidelity gaps in `.engineering/e2e.json`.

At `INTEGRATION`, use the cheapest automated environment sufficient to prove the complete changed outcome. Carry remaining target-environment deltas explicitly to `RELEASE` instead of repeatedly paying real-environment cost on every feature PR.

## 9. E2E evidence

E2E proves a complete critical user/system outcome across assembled boundaries when lower-level tests cannot establish it. Keep critical journeys small and high-value.

Do not move deterministic logic coverage into E2E merely because an E2E framework exists.

For UI-bearing journeys, evidence strength follows the actual claim and stage:

- `ASSERTIONS` — UI is incidental to deterministic system behavior;
- `SCREENSHOTS` — bounded stable visible layout/hierarchy/copy/state/recovery/adaptive semantics need inspection;
- `FULL_MEDIA` — screenshots plus continuous video when UI/UX is materially part of the integration outcome, or when motion, timing/progression, navigation/transition sequence, lifecycle visibility, gesture continuity or release/product acceptance depends on observing the journey over time.

For a material UI/UX critical journey entering the shared development branch, `FULL_MEDIA` is the default integration evidence. UI presence alone still does not force video when the UI is merely an incidental harness for a non-visual system invariant.

A run is `E2E_EVIDENCE_INCOMPLETE` when evidence required by the **selected mode** is missing. Never silently downgrade the selected mode after execution to obtain a green result.

All E2E evidence is identity-bearing, privacy-safe and bounded-retention. Emulator/simulator evidence cannot satisfy a physical/target-environment claim.

## 10. Build and artifact lifecycle

Material builds have unique build identity distinct from product version. Successful distributable artifacts are immutable and promoted only after validation.

Where applicable, successful artifacts carry:

- source/build identity;
- manifest;
- checksum;
- generated build delta against the previous successful comparable build;
- bounded lineage-aware retention.

Failed or partial artifacts must not be placed where they can be mistaken for successful outputs.

Local runtimes and build/test/E2E operations leave no unintended project-owned process, listener, lock, temporary state or resource residue.

Detailed semantics live in `OPERATING-CONTRACT.md`.

## 11. Security and data

Repositories document trust boundaries and sensitive-data lifecycle.

For persisted/user-sensitive data define creation, storage, encryption/trust boundary, retention, deletion, migration/recovery, backup/export when applicable and logging restrictions.

Never introduce silent cloud fallback, secret persistence, sensitive payload logging or destructive migration behavior without an explicit contract/review.

Remote execution of change-branch code uses least privilege and does not gain production/signing/deployment secrets merely for convenience.

## 12. Product development

When product development is applicable, the repository declares a concise durable product owner such as `docs/product.md` and machine-readable routing in `.engineering/product.json`.

Meaningful product work follows at proportional depth:

```text
user / consumer
-> problem / job
-> desired outcome
-> material product risks: value / usability / feasibility / viability
-> assumptions + evidence
-> smallest sufficient solution
-> product quality constraints
-> UX + engineering shape
-> acceptance / outcome / product-impact evidence
-> release / rollout
-> post-release question / learning when material
```

Do not force this sequence onto implementation-only work. `PRODUCT_NONE` bypasses it; `PRODUCT_LOCAL` uses only enough context to preserve settled behavior.

Treat important uncertain beliefs as assumptions. Choose the cheapest useful, least invasive evidence that can change the decision. A complete implementation is not the default experiment for a question a prototype, technical spike, existing evidence or bounded test can answer.

Product quality attributes are part of product intent when they materially shape value. Examples include privacy/data locality, reliability, performance, compatibility, resource budgets, accessibility, developer experience and cost constraints. Engineering owners translate them into explicit invariants/budgets/evidence.

Distinguish success at three levels:

- **acceptance** — the intended supported contract was implemented;
- **outcome** — the user/consumer can achieve the intended result better;
- **product impact** — a meaningful real-use signal improved when such evidence is material.

`SHIPPED` is not equivalent to `PRODUCT_SUCCESS_CONFIRMED`.

Product discovery may conclude that a requested feature should not be built, should be narrowed or should use a different solution. Durable learning updates the owning product/feature/architecture/test truth rather than accumulating a research diary.

Detailed semantics live in `PRODUCT-DEVELOPMENT-CONTRACT.md`.

## 13. Product experience

When `product-ui` is adopted, meaningful product-experience work follows at proportional depth:

```text
user outcome
-> task model
-> information architecture / critical journey
-> information + action hierarchy
-> progressive disclosure / defaults
-> interactions / states / feedback / recovery
-> adaptive / platform behavior
-> accessibility
-> design system / components
-> motion
-> visual polish / graphics
-> validation
```

Structure precedes polish. Motion has a product purpose. The canonical design system/source of truth is reused rather than duplicated.

Accessibility, adaptive behavior, recovery and usability are separate claims from visual appearance.

Product experience receives product intent/outcome/constraints from product shaping when they are material; it does not need to rediscover settled product strategy for every UI change.

## 14. Documentation and agent context

Git is implementation history. Durable docs describe the system that exists now.

- `AGENTS.md` — bounded routing/invariants;
- `.engineering/product.json` — product-development applicability/routing;
- `.engineering/commands.json` — operation/development-velocity/execution routing;
- `.engineering/e2e.json` — E2E environment/evidence routing;
- `docs/product.md` — concise durable product mission/users/problems/outcomes/principles when applicable;
- architecture/feature/ADR docs — durable current truth;
- `docs/current-state.md` — integrated/blocked/next repository truth;
- `docs/workstreams/` — active bounded coordination only;
- Skills — conditional recurring procedures;
- scripts/CI — deterministic enforcement/execution.

During `ITERATION`, affected durable documentation may remain pending while behavior changes. Before `INTEGRATION`, every affected canonical documentation owner must be current with the candidate.

Do not update `current-state.md` for every agent commit or branch synchronization.

Completed workstream plans are deleted by default after durable knowledge transfer; Git retains history.

Machines should enforce what machines can check. Avoid spending agent context repeating deterministic rules already enforced by scripts/CI.

Context is loaded by task and stage. Measure representative reading routes including applicable guide chains, required Skills and configuration, not just individual file size. Routes are accounting aids; relevant source/consumers and applicable instructions remain required. Summaries are derived views with source identity, never new policy or evidence authority. Prefer bounded tool results and on-demand logs.

For meaningful implementation state the observable outcome, owner, preserved invariants and proof in the existing task/PR. For `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC`, the existing workstream may prepend only the compact current product intent/risks/success needed for execution. Multi-session work may keep a compact checkpoint in its active workstream: confirmed/excluded/unresolved facts, evidence and next action. Refresh source identity on resume. Do not maintain duplicate PRD/progress/status documents.

After two failed repairs with the same failure signature, change diagnostic strategy and gather new evidence before another repair. This does not imply a user approval step; diagnosis remains autonomous within the authorized task.

## 15. Validation economics

Where practical, observe validation gates for:

- duration;
- flake rate;
- unique regression signal;
- overlap with other gates.

Use this evidence to move cheap high-signal checks earlier and expensive low-frequency checks toward integration/release checkpoints.

This is not a mandate to delete tests. It is a mandate to place each test where its confidence contribution justifies its feedback cost.

Real-environment validation is intentionally concentrated at release when it protects a residual target-specific claim; it is not a default per-feature integration tax.

If `FULL` runs frequently for contained changes, improve scope/risk selection. If narrow validation repeatedly misses affected regressions, strengthen the risk-to-gate mapping.

## 16. Maturity levels

### L0 — Healthy product-engineering repository

At minimum:

- clear purpose and architecture/ownership;
- when product development applies, explicit primary users/consumers, core problems/outcomes/non-goals and material product-quality promises;
- bounded agent routing/context;
- reproducible setup and pinned/locked dependencies where applicable;
- machine-readable product routing and project operating/development-velocity contract;
- deterministic formatting/static/test/build validation appropriate to the stack;
- explicit risk-based validation routing and no-human-runner semantics;
- explicit E2E applicability/environment contract;
- build/artifact/resource cleanup invariants where applicable;
- security/trust-boundary documentation;
- repository hygiene and no secret/private/generated artifact leakage;
- bounded active workstreams/current-state documentation;
- product-experience contracts when `product-ui` applies.

### L1 — Production ready

L0 plus:

- `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC` changes are outcome-driven, assess material product risks/assumptions and define success evidence before substantial implementation;
- integration/contract tests for critical boundaries;
- bounded high-value automated E2E where full workflow evidence is needed;
- target/fidelity gaps declared and residual real-environment confirmation identified for release;
- migration/backward-compatibility strategy where state/contracts persist;
- critical failure/cancellation/recovery coverage;
- performance/resource budgets for important paths;
- useful observability and release/rollback procedures;
- immutable traceable distributable artifacts;
- least-privilege remote automation;
- accessibility/adaptive/recovery evidence for material UI workflows.

### L2 — Reference grade

L1 plus:

- significant released product changes identify useful post-release questions/evidence where pre-release validation cannot establish real-use impact;
- contradictory product evidence updates priorities/behavior instead of preserving assumptions;
- relevant adoption/task-success/product-quality signals are understood without requiring invasive telemetry;
- compatibility/deprecation decisions are deliberate;
- architecture fitness functions for critical ownership/dependency invariants;
- resource/memory/performance regression gates where stable measurement is possible;
- fault/pressure coverage for important lifecycle boundaries;
- high-value critical journeys at the highest practical automated fidelity before residual release target testing;
- representative hardware/device evidence when hardware materially changes release behavior;
- machine-enforced docs/context/operating/E2E/product-development/product-experience health;
- periodic validation-economics review so avoidable cost/flake/overlap is reduced;
- explicit complexity/dependency review for meaningful additions;
- active control of stale/duplicate documentation and design-system drift.

L2 is a target, not an excuse to add machinery the project does not need.

## Completion rule

A change is not “done” because every possible test ran or because a requested feature shipped.

It is done at the relevant product/delivery stage when:

- the intended observable outcome is correct;
- material product intent/risks/assumptions are resolved to the depth justified by the change;
- changed owners/contracts/failure/resource semantics agree;
- the narrowest sufficient required evidence for that stage is satisfied;
- affected durable documentation is current before integration/release;
- at `INTEGRATION`, all required automated evidence passes and residual real-environment requirements are explicitly deferred;
- at `RELEASE`, every applicable blocking real-environment requirement passes;
- when material product impact remains unknowable before release, the post-release question/evidence path is explicit rather than silently assuming success.

The objective is **high-confidence, outcome-driven product delivery without validation or process waterfall**.
