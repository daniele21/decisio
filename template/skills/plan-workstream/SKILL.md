---
name: plan-workstream
description: Create or reshape a compact active implementation workstream when substantial work needs dependency, parallelism, ownership or progress coordination, while preferring observable vertical outcomes and early branch convergence over stacked publication ceremony.
---

# Plan Workstream

## Goal

Turn a substantial product/engineering goal into a bounded execution DAG that coding agents can continue without rereading narrative history and without turning every technical subtask into its own publication-grade PR.

## First decide whether a plan is justified

Do not create a workstream when the change can be understood, implemented and validated coherently in one task/PR without persistent coordination.

Create one when at least one is true:

- multiple independently executable subtasks/slices exist;
- dependencies/blockers must survive across agent sessions;
- multiple agents may work in parallel;
- integration/evidence spans several execution environments or checkpoints;
- scope is large enough that current executable state would otherwise be reconstructed repeatedly.

## Product intent is conditional, not another plan

Before planning, classify product impact when the change materially affects supported behavior/product promise.

- `PRODUCT_NONE` / `PRODUCT_LOCAL`: do not add a Product Intent section beyond the local outcome/acceptance already needed.
- `PRODUCT_FEATURE` / `PRODUCT_STRATEGIC`: run `skills/shape-product-change/SKILL.md` first and carry only the compact current user/problem/outcome, material product risks/assumptions, success evidence and post-release question into the **same** workstream.

Do not create a PRD/product-plan/progress document beside the workstream merely to hold the same decision state.

## Vertical slice rule

Prefer slices that unlock an **observable user/system outcome** end to end.

A technical layer, model, adapter, test harness or ViewModel change is normally a **subtask of the vertical slice** unless it is independently valuable, mergeable and reviewable.

Avoid decomposition that produces many individually complete-looking PRs but no useful product behavior until the final one lands.

Ask for each proposed slice:

- what observable outcome becomes true when this lands?
- can it integrate safely without waiting for later layers?
- does separating it reduce risk/coordination, or only create ceremony?

## Parallel development does not imply stacked publication

Use temporary branches/worktrees to parallelize non-conflicting ownership, then converge them early onto a shared feature/integration branch when the pieces belong to one vertical outcome.

Preferred pattern:

```text
agent A subtask ─┐
agent B subtask ─┼─> feature/integration branch -> coherent vertical-slice PR
agent C subtask ─┘
```

Stacked publication is exceptional. Use stacked PRs only when each level is independently mergeable/reviewable/value-bearing or when separate ownership/review genuinely requires it.

A PR whose only purpose is to sync a parent into a child is a coordination smell. Prefer branch convergence or explicit integration points over repeated stack-maintenance PRs.

## Workflow

1. Find owning product/architecture/feature sources and current state.
2. For `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC`, carry the already-shaped compact Product Intent into the workstream; do not rediscover it here.
3. State one outcome-oriented Goal and explicit Non-goals.
4. List only invariants that materially constrain implementation, including product-quality constraints that have technical consequences.
5. Decompose into the smallest coherent **vertical outcomes**, then list parallel technical subtasks beneath them.
6. Give every slice/subtask a stable ID and explicit `Owns/writes` boundary.
7. Express dependencies as a DAG. Mark work parallel only when writes are non-conflicting or the integration point is explicit.
8. Choose the convergence branch/checkpoint for related parallel work.
9. Use only `READY`, `ACTIVE`, `BLOCKED`, `DONE` states.
10. Name the currently executable work; do not make agents infer it from prose.
11. Put FAST/iteration validation beside each subtask and integration/E2E evidence beside the vertical outcome it proves.
12. Reserve release-grade validation for the release checkpoint rather than copying it onto every subtask.
13. Declare durable documentation destinations so completion can transfer current truth and delete the plan.
14. Link the active workstream once from `docs/current-state.md` only when repository-level coordination needs that pointer.

## Size discipline

Use `docs/workstreams/_template.md`. Keep the workstream under the configured token/line budget.

If it grows, split by genuinely independent domain/outcome rather than appending history.

Do not maintain separate `plan.md`, `product-plan.md`, `progress.md` and `status.md` for the same work. Update current product intent and execution state in the existing workstream. Completed work remains as terse `DONE` rows only while needed for active dependency context.

Do not update `docs/current-state.md` or `docs/product.md` for every agent commit or temporary branch synchronization; they own durable integrated/product truth, not active progress.

## Completion standard

A useful plan lets a fresh agent determine quickly:

- intended observable outcome and exclusions;
- material product intent/risks only when applicable;
- what can execute now;
- what blocks what;
- which paths/contracts each subtask owns;
- what may run in parallel;
- where related work converges;
- which iteration checks belong to subtasks;
- which integration/release gates belong to checkpoints;
- what durable product/engineering knowledge must remain after the plan is deleted;
- which residual release or post-release question must survive completion when material.

## Resume without reconstructing history

For multi-session work use the optional resume checkpoint in the existing workstream: source/base/dirty state, confirmed facts with evidence, excluded hypotheses, unresolved questions and the next concrete action. Replace it after a meaningful finding or handoff; do not keep a diary or a second status file. On resume verify current source identity and relevant changes before trusting old evidence. Transfer durable lessons into product/feature/architecture/tests/contracts/docs at completion, then delete the plan.
