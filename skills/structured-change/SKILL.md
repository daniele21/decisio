---
name: structured-change
description: Shape a meaningful behavior, contract, resource or UI change around its owner, observable outcome and regression evidence before editing and before completion.
---

# Structured Change

Use for meaningful code/product changes. A copy-only or formatting edit does not need this procedure. Keep reasoning proportional; a local change normally needs a few lines in the task/PR, not another document.

## Establish the change

State the **observable outcome, canonical owner, invariants to preserve and proof of success**. Inspect the owner, material direct consumers/fakes and nearby tests. For a reproducible bug, establish failing evidence at the lowest useful level before the repair when practical; otherwise record the observation and what remains uncertain.

Resolve material ambiguity from current code/contracts/ADRs first. Ask only when unresolved alternatives change product behavior, compatibility, public contracts, persistence, security/privacy, lifecycle or meaningful UX. Equivalent local implementation choices remain autonomous.

## Implement at the owner

Search before adding state, configuration, constants or policy. Extend the existing owner; keep domain policy out of adapters that merely translate it. Each new abstraction, dependency, cache, worker or UI pattern needs a concrete requirement and a smaller-solution check. Avoid speculative extensibility and unrelated refactors.

Deliver the smallest coherent observable outcome. Technical layers are subtasks unless independently valuable and mergeable. Use `../plan-workstream/SKILL.md` only when persistent coordination helps; parallel work converges early with explicit write boundaries.

## Review applicable risks

| Changed surface | Preserve / inspect |
| --- | --- |
| Public/shared contract | Material consumers, fakes, adapters, compatibility and owning regression tests. |
| Resource/concurrency | Owner, lifetime/cardinality, bounds/backpressure, cancellation, timeout, pressure, release and cleanup on partial initialization and every exit path. No unbounded state on unbounded input. |
| Failure/recovery | Invalid input, dependency loss, partial results, cancellation/shutdown, restart and interrupted persistence/migration. Restore the invariant instead of hiding the error. |
| Data/security | Trust boundaries, creation/storage, retention/deletion, logging/export, migrations and recovery. No silent cloud fallback, content logging or destructive behavior outside the explicit contract. |
| Setup/build/runtime | Relevant `.engineering/commands.json` fields: build identity, immutable successful artifacts, delta/retention, owned ephemeral resources and zero residue. Preserve the native operating path. |
| Product UI | Use `../design-product-experience/SKILL.md` and existing design owners: task/journey, hierarchy/disclosure/defaults, states/recovery, accessibility/adaptive behavior, then motion/polish. |

Use `../validate-change/SKILL.md` for focused feedback and failure diagnosis. The implementation is complete when the behavior, consumers, relevant failure/resource semantics and focused evidence agree. At integration, `../preflight-change/SKILL.md` owns full-diff, affected documentation and final evidence readiness; do not repeat it on every edit.
