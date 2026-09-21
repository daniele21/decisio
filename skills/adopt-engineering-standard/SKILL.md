---
name: adopt-engineering-standard
description: Align a new or existing repository with repo-template-sw 0.11.0 without overwriting stronger project-specific product strategy, architecture, CI, documentation, build/E2E tooling, design systems or agent guidance. Audit first, then specialize proportional product reasoning, staged delivery, risk-based validation and the smallest useful baseline.
---

# Adopt Engineering Standard

## Goal

Make a repository self-contained and aligned with the Agent-Native Product Engineering Standard while preserving good existing product and engineering decisions.

Adoption is semantic. Do not call a repository 0.11.0-compliant merely because files or version metadata were copied.

## 1. Discover before changing

Inspect the current repository for:

- product/runtime/platforms, primary users/consumers and public boundaries;
- existing product mission/strategy/requirements/discovery/roadmap sources and whether they are current durable truth;
- product quality promises such as privacy, reliability, performance, compatibility, offline behavior, accessibility or developer experience;
- root/scoped agent guidance and existing Skills;
- architecture/ADRs/current plans and documentation ownership;
- setup/dev/check/test/E2E/build/package/clean commands;
- CI scope selection and typical validation latency;
- remote automation/preflight mechanisms;
- test suites and what risk each materially proves;
- E2E framework, critical journeys, target/execution environments and residual physical/manual tests;
- existing screenshot/video capture and evidence retention;
- build identity/artifact/release mechanisms;
- persistence/security/resource/lifecycle ownership;
- design source of truth and UX/UI system when material.

For an existing repository classify mechanisms as:

- `KEEP` — already satisfies/exceeds the invariant;
- `ADAPT` — keep mechanism, add missing semantics/routing;
- `ADD` — genuinely missing capability;
- `N/A` — concern does not apply.

Never replace a stronger incumbent framework or product source merely for template uniformity.

## 2. Install/specialize the baseline

For a new repository, copy the universal `template/` and then specialize it.

For an existing repository, merge only relevant files/semantics.

Specialize `.engineering/product.json` and map `docs/product.md` to the actual canonical product source. If the repository already has a stronger concise product strategy/charter source, preserve it and point routing there rather than duplicating truth.

Select only applicable profiles. Add `product-ui` only when a material user-facing interface exists.

Remove unresolved adopter placeholders before claiming adoption complete.

## 3. Configure proportional product development

Preserve four independent product depths:

- `PRODUCT_NONE` — implementation-only/no material product promise change; no product process;
- `PRODUCT_LOCAL` — settled local behavior; user/consumer impact + outcome + acceptance only;
- `PRODUCT_FEATURE` — new capability/meaningful behavior; user/problem/outcome, four product risks, material assumptions/evidence, non-goals, quality constraints and success;
- `PRODUCT_STRATEGIC` — broad product boundary/value/trust/platform/distribution change; stronger discovery, alternatives, rollout/compatibility and learning.

Do not classify by file count or engineering effort. Use impact, uncertainty and reversibility.

Adopt `shape-product-change` for feature/strategic work. It must allow `BUILD`, `NARROW_SCOPE`, `CHOOSE_ALTERNATIVE` and `DO_NOT_BUILD`; do not turn it into a mandatory PRD generator.

Distinguish success:

- acceptance — implemented supported behavior;
- outcome — user/consumer achieves the desired result better;
- product impact — meaningful real-use signal when material.

`SHIPPED` is not `PRODUCT_SUCCESS_CONFIRMED`.

Product quality attributes that materially shape value must flow into engineering owners/invariants/evidence rather than remain vague product prose.

## 4. Map project commands

In `.engineering/commands.json`, map canonical intents to native tooling:

`setup`, `doctor`, `dev`, `check`, `test`, `e2e`, `build`, `smoke`, `package`, `stop`, `clean`.

Mark only genuinely irrelevant intents `n/a`.

Do not introduce a wrapper framework solely for naming consistency.

Use operating contract `0.7.0` and preserve its integration/release real-environment stage fields.

## 5. Specialize development velocity

Preserve the three delivery stages independently from product depth:

### `ITERATION`

- default while implementation changes;
- fastest useful formatter/static/compile/focused-test/direct-contract feedback;
- no automatic exact-head/full-diff/docs/preflight/release-E2E ceremony.

### `INTEGRATION`

- coherent observable vertical outcome ready for the shared development/integration branch;
- exact head/base;
- complete diff review;
- affected durable docs current;
- concrete risk gates satisfied;
- affected complete critical journeys proven automatically when lower-level evidence is insufficient;
- residual `REAL_ENVIRONMENT` evidence explicit and `DEFERRED_TO_RELEASE`, not a normal integration blocker.

### `RELEASE`

- release/promotion/reference checkpoint;
- `FULL` validation and release-critical artifact/E2E evidence;
- every real-environment confirmation required by the release claim passes before `RELEASE_READY`.

Keep delivery stage separate from validation depth and product depth.

If repository-specific feedback-time budgets make sense, specialize reference iteration/integration targets without turning them into correctness-breaking hard timeouts.

## 6. Build risk-to-gate selection

Prefer the repository's existing dependency/ownership graph when available.

The selector should produce:

- changed owners;
- risk dimensions;
- concrete required gates;
- `LEAN | SCOPED | STRONG | FULL` summary/reason.

Typical escalation risks include shared/public contract, persistence/migration, security/trust/data lifecycle, runtime/resource/concurrency/lifecycle, native/JNI/backend, manifest/dependency/variant/package/R8, complete user/system journey and selector/global-build/toolchain/dependency-inventory changes.

Do not map an entire important feature area to `STRONG/FULL` without a changed invariant that requires those gates.

Unknown executable scope fails safe stronger. Selector/global-build machinery that controls narrowing validates `FULL` when it changes.

## 7. Configure execution capability and remote preflight

Required gates are classified as:

- `AGENT_LOCAL`;
- `REMOTE_AUTOMATED`;
- `REAL_ENVIRONMENT`.

Do not delegate ordinary automatable compile/lint/test/R8/package/emulator work to the user because the current agent lacks tooling.

When agents may lack a local environment, provide repository-owned remote automation with least privilege.

Configure evidence reuse so successful existing results can satisfy integration/release preflight when they still match exact source head, material base relationship, required gates/profile and E2E environment/evidence mode.

PR number/draft/ready/label/comment identity must not independently force duplicate validation.

Execution class and stage placement are separate: classify residual real-environment requirements during integration, but execute/block on required ones at release by default.

## 8. Configure E2E environments, stage policy and journeys

Decide E2E applicability explicitly.

When applicable, `.engineering/e2e.json` contract `0.2.1` declares target environments/material dimensions, automated execution environments/fidelity, integration/release stage policy, bounded critical journeys, minimum automated fidelity, residual gaps, real-environment confirmation policy and minimum UI evidence mode.

Preserve existing native E2E tooling when strong.

At integration, use the cheapest sufficient automated environment to prove the complete changed outcome. Carry only residual physical/target-specific gaps to release.

An early physical/target run may still diagnose an explicitly environment-specific defect without becoming the standard branch/PR integration gate.

## 9. Configure risk-based UI E2E evidence

Use:

- `ASSERTIONS` — UI incidental to non-visual deterministic behavior;
- `SCREENSHOTS` — bounded stable visible states/layout/hierarchy/copy/recovery/adaptive semantics;
- `FULL_MEDIA` — screenshots plus continuous journey video when UI/UX is materially part of the integration outcome, or when motion/timing/progression/navigation transitions/lifecycle visibility/gesture continuity/release acceptance matters.

A material UI/UX critical journey entering the shared development branch uses `FULL_MEDIA` by default.

Evidence required by the selected mode must be identity-bearing, privacy-safe and bounded-retention. Missing required evidence is `E2E_EVIDENCE_INCOMPLETE`.

## 10. Configure vertical work and parallelism

`plan-workstream` is used only when persistent dependency/parallel coordination adds value.

Prefer observable vertical outcomes. Treat technical layers as subtasks unless independently useful/mergeable/reviewable.

For `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC`, keep compact user/problem/outcome/risks/assumptions/success information in the same workstream before the DAG when persistent coordination is needed. Do not add parallel PRD/progress/status documents unless a stronger existing product system deliberately owns them.

Parallel work may use branches/worktrees, but related work should converge early onto a shared feature/integration outcome.

Stacked publication is exception-only. Do not design a workflow that requires repeated sync-only PRs for normal agent parallelism.

## 11. Configure documentation lifecycle

Keep:

- bounded `AGENTS.md` routing;
- a concise canonical product source (`docs/product.md` by default) when product development applies;
- durable architecture/features/ADRs;
- `docs/current-state.md` as integrated/blocked/next truth;
- active bounded workstreams only;
- completed workstreams deleted after durable knowledge transfer by default.

During `ITERATION`, affected durable docs may be pending while behavior changes. At `INTEGRATION`, affected canonical docs must be current.

Do not churn product/current-state/workstream metadata for every temporary branch synchronization.

## 12. Configure operating/build/resource invariants

Implement applicable unique build identity, immutable successful artifacts, manifest/checksum/build delta, bounded local/CI evidence retention, graceful runtime shutdown, isolated run resources and cleanup after success/failure/timeout/cancellation/interrupt/partial initialization.

Preserve stronger existing artifact/release systems.

## 13. Product experience

If `product-ui` applies, specialize `design/ux-contract.json` and `design/brand-kit.json` around actual users/jobs/surfaces and the real design-system source of truth.

Preserve the proportional decision order:

```text
user outcome -> task -> IA/journey -> hierarchy/disclosure/defaults
-> interaction/states/feedback/recovery -> adaptive/platform -> accessibility
-> design system -> motion -> visual/graphics -> validation
```

Material product shaping hands user/problem/outcome/constraints into UX; do not rediscover settled strategy or redesign a mature product merely to adopt the baseline.

## 14. Validation economics

Where practical, identify expensive gates and begin collecting/reviewing duration, flake rate, unique regression signal and overlap.

Do not delete real safety evidence for speed. Move cheap/focused evidence earlier, affected automated E2E to integration and real-environment acceptance to release.

## 15. Finalize adoption

Run applicable repository/operations/E2E/stage-policy/product-development/product-experience/docs/context verifiers and project-specific validation needed by the adoption itself.

Only then update `.engineering/baseline.json` to `0.11.0` and record local Skill customization truthfully.

Report:

```text
BASELINE: 0.11.0
PROFILES: <list>
PRODUCT_SOURCE: <canonical source>
PRODUCT_DEPTH_ROUTING: <none/local/feature/strategic specialization>
KEEP: <strong existing mechanisms preserved>
ADAPT: <mechanisms merged with new semantics>
ADD: <new capabilities>
N/A: <non-applicable concerns>
DELIVERY_MODEL: ITERATION / INTEGRATION / RELEASE <specialization>
RISK_SELECTOR: <owner/risk/gate strategy>
REMOTE_PREFLIGHT: <trigger + evidence reuse strategy>
E2E: <journeys/environments/stage policy/residual gaps/UI evidence modes>
VALIDATION_ECONOMICS: <implemented/deferred>
VALIDATION: <evidence>
DEFERRED_OR_CONFLICTS: <items or N/A>
```

Bootstrap structure alone does not prove L1/L2 maturity. Report maturity truthfully from actual evidence.

## Context, diagnosis and reporting

Specialize compact AGENTS owner/task routing without losing local invariants. Merge documentation-policy schema 2 and actual context routes, including the bounded `product` route for material product shaping. Run the route reporter; do not lower costs by removing necessary reads. Routes estimate instruction/configuration cost, not total session tokens.

Map `agent_reporting` into the existing native selector/CI result surface: identity, risk/gate reasons, statuses, evidence, gaps and next action. The source template has placeholder native commands; configure real execution/reporting before claiming adoption.

Use updated change/validation/preflight/remote Skills; preserve integration FULL_MEDIA and deferred physical-release rules. Use diagnostic pivots after repeated unsuccessful repairs and the existing workstream resume checkpoint only when useful. Reference `evals/` belongs to template maintenance; do not copy an agent benchmark gate into every project.
