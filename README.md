# repo-template-sw

Agent-native reference **product-engineering** baseline for software repositories maintained by humans and coding agents.

`repo-template-sw` is not an application framework, product-management framework or universal build system. It defines a compact product/engineering standard, reusable adopter template, product-development routing, operating/development-velocity contracts, E2E environment/evidence semantics, optional product-experience semantics, coding-agent Skills and deterministic repository health checks.

## Start here

- [`USAGE.md`](USAGE.md) — practical adoption, ordinary development and migration guide.
- [`STANDARD.md`](STANDARD.md) — canonical L0/L1/L2 product-engineering standard.
- [`PRODUCT-DEVELOPMENT-CONTRACT.md`](PRODUCT-DEVELOPMENT-CONTRACT.md) — product intent, product-risk, assumption/evidence, shaping, success and learning semantics.
- [`OPERATING-CONTRACT.md`](OPERATING-CONTRACT.md) — command/build/artifact/runtime lifecycle semantics.
- [`EXECUTION-CAPABILITY-CONTRACT.md`](EXECUTION-CAPABILITY-CONTRACT.md) — delivery stages, risk-based validation, executor routing and evidence reuse.
- [`E2E-ENVIRONMENT-CONTRACT.md`](E2E-ENVIRONMENT-CONTRACT.md) — target-environment/fidelity semantics, stage policy and UI evidence modes.
- [`PRODUCT-EXPERIENCE-CONTRACT.md`](PRODUCT-EXPERIENCE-CONTRACT.md) — optional stack-neutral UX/UI contract.

## 0.11.x: Product Engineering

The baseline now separates **product impact** from engineering delivery and validation depth:

```text
Product depth:      PRODUCT_NONE | PRODUCT_LOCAL | PRODUCT_FEATURE | PRODUCT_STRATEGIC
Delivery stage:     ITERATION -> INTEGRATION -> RELEASE
Validation depth:   LEAN | SCOPED | STRONG | FULL
```

These answer different questions:

- **Product depth** says how much problem/outcome/risk/evidence reasoning is justified before substantial implementation.
- **Stage** says when the engineering change is in its lifecycle.
- **Validation depth** says how much technical evidence the actual risk requires.

For meaningful product work, the preferred decision flow is:

```text
user / consumer
-> problem / job
-> desired outcome
-> value / usability / feasibility / viability risks
-> material assumptions + evidence
-> smallest sufficient solution
-> UX + engineering shape
-> acceptance / outcome / product-impact evidence
-> release / rollout
-> learn from real use only where material uncertainty remains
```

`PRODUCT_NONE` work bypasses product ceremony. `PRODUCT_LOCAL` needs only enough context to preserve settled behavior. `PRODUCT_FEATURE` and `PRODUCT_STRATEGIC` use `shape-product-change` before substantial implementation.

The rules are:

> **Outcomes before output. Evidence before commitment. Product reasoning proportional to product risk.**

> **Shipping proves delivery; it does not by itself prove product success.**

## Development Velocity

The engineering delivery model remains explicitly two-dimensional:

```text
Delivery stage:     ITERATION -> INTEGRATION -> RELEASE
Validation depth:   LEAN | SCOPED | STRONG | FULL
```

### ITERATION

Default while implementation is changing. Optimize for a short feedback loop: touched formatter/static checks, affected compile/typecheck, focused tests and direct contract tests when needed.

Do not automatically require exact-head publication evidence, complete-diff review, durable-documentation freshness, remote preflight, release packaging, broad emulator suites or E2E media for every edit.

### INTEGRATION

Begins when a coherent **vertical outcome** is ready to converge into the shared development/integration branch. Refresh exact head/base, inspect the complete diff, update affected durable docs, select concrete risk gates and prove affected complete workflows with the smallest sufficient automated E2E.

For a material UI/UX critical journey, integration evidence defaults to `FULL_MEDIA`: bounded screenshots plus a continuous journey video. If UI is only an incidental harness for a non-visual invariant, assertions may remain sufficient.

Residual `REAL_ENVIRONMENT` requirements are explicit but **do not normally block integration**. They are `DEFERRED_TO_RELEASE`.

### RELEASE

Promotion/release/reference checkpoints use `FULL` validation plus release-critical build/package/E2E. Every real-environment confirmation required by the release claim is blocking before `RELEASE_READY`.

The practical rule is:

> **Prove the feature automatically before dev; prove the residual target-environment delta before main/release.**

The objective is:

> **high-confidence incremental product delivery without process or validation waterfall.**

## What it optimizes for

- explicit product intent and observable outcomes for material product work;
- proportional discovery instead of feature/PRD ceremony by default;
- clear separation of assumptions from evidence and permission to narrow/change/reject a requested solution;
- product-quality attributes translated into measurable engineering invariants;
- explicit ownership and simple architecture;
- bounded resources/concurrency/failure behavior;
- fast deterministic feedback during implementation;
- risk-to-gate validation instead of full-suite-by-default;
- agent-triggerable remote automation when local tooling is unavailable;
- reuse of equivalent successful validation evidence instead of duplicate runs;
- critical E2E matched to both claim strength and environment fidelity;
- material UI/UX integration evidence that is directly inspectable through screenshots + video;
- real-environment validation concentrated at release rather than repeated on every feature PR;
- reproducible builds and immutable traceable artifacts;
- zero-residue runtime/build/E2E lifecycles;
- low repository/documentation entropy and low agent context cost;
- observable vertical slices and early convergence of parallel work;
- clear, accessible and progressively disclosed product experiences where UI exists;
- explicit post-release learning only when real use can answer a material product question.

Core principles:

> **Outcomes before output; evidence before commitment.**

> **Make ownership, limits, failures and costs explicit, using the simplest solution that preserves the required invariants.**

> **Optimize for sufficient confidence per unit of feedback time.**

> **Automation executes automatable work; humans make material decisions and provide genuinely real-environment evidence.**

> **Integration proves the complete changed outcome automatically; final target-environment validation confirms only the residual release gap.**

## Validation model

The selector should resolve:

```text
changed outcome
-> risk dimensions
-> required gates
-> LEAN | SCOPED | STRONG | FULL summary
-> AGENT_LOCAL | REMOTE_AUTOMATED | REAL_ENVIRONMENT executor
```

Profiles are shorthand, not monolithic suite aliases.

Typical examples:

- contained UI/ViewModel/domain change -> `SCOPED` owner/direct-consumer gates;
- Binder/shared contract, persistence, lifecycle, native/JNI, packaging/R8/manifest -> relevant `STRONG` risk cone;
- selector/global build/toolchain/dependency inventory -> `FULL` because narrowing machinery changed;
- stable/release promotion -> `FULL`.

Execution class and stage placement remain separate. A physical-device requirement may be real-environment evidence without becoming an integration blocker; required real-environment evidence becomes blocking at release.

## Remote preflight and evidence reuse

Before starting another expensive run, reuse successful evidence when it still proves the required claim.

For an integration candidate, evidence normally matches:

- exact source head;
- source Git tree when available;
- material target/base relationship;
- required gates;
- selected profile or stronger equivalent;
- E2E environment/fidelity/evidence mode where relevant.

PR number, draft/ready state, labels and comments are not source-evidence identity by themselves. A replacement PR with the same head/base/gates should not rerun unchanged validation solely because its UI identity changed.

After a content-preserving squash/rebase into an integration branch, post-merge CI may reuse the green candidate evidence even though the commit SHA changed **only** when the final Git tree is identical and the push base is exactly the target/base used by the validation. A moved base, changed tree, broader gate set, direct push without trusted evidence or release candidate falls back to normal validation.

This distinction preserves exact-head integration proof while avoiding a second expensive run caused only by commit-history metadata.

## E2E model

Execution capability and environment fidelity are independent.

```text
host/fake
-> simulator/emulator
-> representative virtual
-> representative physical
-> target environment
```

At integration, use the cheapest automated environment that proves the complete changed outcome. Carry only the residual fidelity delta to release.

For UI-bearing critical journeys, select evidence from the changed claim and stage:

- `ASSERTIONS` — UI is incidental to deterministic system behavior;
- `SCREENSHOTS` — bounded stable visible layout/hierarchy/copy/state/recovery/adaptive behavior needs inspection;
- `FULL_MEDIA` — screenshots plus continuous journey video when UI/UX is materially part of the integration outcome, or when motion, timing/progression, navigation/transition sequence, lifecycle visibility, gesture continuity or release acceptance requires observing sequence over time.

UI presence alone does not force video when the UI is merely an incidental harness. Evidence required by the selected mode must be complete and identity-bearing.

## Vertical slices and parallel work

Prefer an observable user/system outcome over a small technical layer.

```text
agent A subtask ─┐
agent B subtask ─┼─> feature/integration branch -> coherent vertical-slice PR
agent C subtask ─┘
```

Parallel development does not imply stacked publication. Stacked PRs remain useful when levels are independently mergeable/reviewable/value-bearing, but sync-only stack-maintenance PRs are a smell.

## Repository layout

- `STANDARD.md` — universal product-engineering standard.
- `PRODUCT-DEVELOPMENT-CONTRACT.md` — product-development decision/evidence/learning contract.
- `OPERATING-CONTRACT.md` — operations/build/artifact/runtime contract.
- `EXECUTION-CAPABILITY-CONTRACT.md` — development velocity, validation/executor/evidence-reuse contract.
- `E2E-ENVIRONMENT-CONTRACT.md` — E2E environment/stage/evidence contract.
- `PRODUCT-EXPERIENCE-CONTRACT.md` — optional UX/UI contract.
- `template/` — files adopted and then specialized locally.
- `template/.engineering/product.json` — machine-readable product-development applicability/routing.
- `template/docs/product.md` — concise product mission/users/problems/outcomes/principles/quality source template.
- `template/.engineering/commands.json` — machine-readable commands, stages, validation routing and preflight policy.
- `template/.engineering/e2e.json` — machine-readable E2E environments, stage policy, journeys and UI evidence policy.
- `template/skills/` — recurring project-local agent workflows, including `shape-product-change`.
- `profiles/` — optional stack/domain/product deltas such as Android/local-AI/product-ui.
- `skills/adopt-engineering-standard/` — first adoption.
- `skills/update-engineering-standard/` — explicit baseline migration.

## Use with a new project

1. Read `USAGE.md`, `STANDARD.md` and only the focused contracts/profiles that apply.
2. Copy/specialize `template/`.
3. Specialize `docs/product.md` and `.engineering/product.json`; set product reasoning depth proportionally rather than forcing discovery onto implementation-only work.
4. Select only applicable profiles.
5. Map `.engineering/commands.json` to the project's native commands and specialize `development_velocity`/risk selector/remote-preflight routing.
6. Decide E2E applicability and specialize `.engineering/e2e.json` with target/execution environments, stage policy, critical journeys, residual gaps and minimum UI evidence modes.
7. If UI is material, adopt `product-ui` and map the real design-system/brand owner.
8. Preserve stronger existing tooling rather than replacing it for compliance aesthetics.
9. Record baseline version/profiles and run repository health checks, including `verify_product_development.py`.

## Use with an existing project

Adoption is semantic, not file replacement. Preserve stronger local product strategy/discovery, ownership, CI, E2E, build/release and design mechanisms; merge only missing invariants/routing.

Later upgrades use `update-engineering-standard`: read the version delta, classify each change as APPLY/MERGE/N/A/DEFER/CONFLICT, preserve intentional customization and bump baseline metadata only after the new behavior is real.

## Current version

Reference baseline: **0.11.0**.

See [`CHANGELOG.md`](CHANGELOG.md) for the adopter-facing delta.

## Agent efficiency

0.11.0 adds a bounded `product` context route instead of adding product-development material to every engineering task. `PRODUCT_NONE` and `PRODUCT_LOCAL` keep ordinary work cheap; feature/strategic work loads product intent and shaping only when justified. The 0.10.0 compact context/diagnostic/evidence behavior remains intact.

Run `python3 template/scripts/verify_agent_context.py --root template --template-mode` to measure complete representative reading routes, or select `--route product --format json` / `--route bug --format json` for file/cost output. These are character-based instruction/configuration estimates, not measured session consumption. See `evals/README.md` for behavioral scenarios used when the template's guidance changes significantly.
