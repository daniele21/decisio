# <PROJECT_NAME> — Coding Agent Guide

## Purpose and invariants

<REPLACE_WITH_3_TO_6_LINES_DESCRIBING_THE_PRODUCT_AND_PRIMARY_RUNTIME>

<REPLACE_WITH_PROJECT_SPECIFIC_DURABLE_INVARIANTS>

Keep project-specific invariants here; recurring procedures live in the owners below.

## Ownership

| Change | Owner | Direct consumers / evidence |
| --- | --- | --- |
| <product mission/users/outcomes/principles> | `docs/product.md` | product/UX/architecture decisions |
| <public/domain contract> | <owner path> | <consumers/tests> |
| <runtime/lifecycle> | <owner path> | <adapters/lifecycle tests> |
| <persistence> | <owner path> | <migrations/recovery tests> |
| <UI/transport> | <owner path> | <contract/journey tests> |
| <product experience> | `design/ux-contract.json` | <components/tokens/journeys> |
| <shared infrastructure> | `.engineering/infrastructure.json` + IaC root | <runtime/deploy/plan/E2E> |

Follow scoped `AGENTS.md`. Extend the existing owner before adding parallel state/policy; inspect material consumers when shared boundaries change.

## Read by task

| Task | Local source |
| --- | --- |
| README/copy/metadata | Affected source; `docs/README.md` if ownership is unclear. |
| Product capability/strategy | `.engineering/product.json`, `docs/product.md`, `skills/shape-product-change/SKILL.md`. |
| Behavior/bug/contract | `skills/structured-change/SKILL.md`, `skills/validate-change/SKILL.md`, commands. |
| Material product UI | Above + `skills/design-product-experience/SKILL.md` and design contracts. |
| Cloud/shared infrastructure | `.engineering/infrastructure.json`, `skills/provision-infrastructure/SKILL.md`, applicable profiles. |
| Integration/release | `skills/preflight-change/SKILL.md`, commands, `.engineering/e2e.json`, infrastructure policy if affected. |
| Missing remote gates | `skills/remote-preflight/SKILL.md`. |
| Coordination/completion | `skills/plan-workstream/SKILL.md` / `skills/finalize-workstream/SKILL.md`. |
| Reference milestone | `skills/review-reference-quality/SKILL.md`. |

Read architecture/features/ADRs only for concrete questions. Upstream baseline instructions apply only to migrations.

## Product and delivery boundaries

Product depth, delivery stage and validation depth are independent.

- **PRODUCT_NONE/LOCAL**: keep product reasoning local; preserve settled intent and prove the outcome.
- **PRODUCT_FEATURE/STRATEGIC**: establish user/problem/outcome, material product risks, assumptions, success and non-goals before substantial implementation. Discovery may narrow/change/reject the requested solution.
- **ITERATION**: fast owner-local feedback. No exact-head/full-diff/docs/publication ceremony per edit. Keep feature PRs draft while implementation changes; do not attach remote full-suite/E2E work to every commit.
- **INTEGRATION**: coherent outcome, current affected docs, exact candidate/base and required automated gates. Ready-for-review is the default CI boundary; later source changes rerun only stale/affected evidence and superseded runs are cancelled. Run affected critical E2E only when required. Material UI/UX journeys default to `FULL_MEDIA`; residual real-environment evidence is `DEFERRED_TO_RELEASE`.
- **RELEASE**: `FULL` release evidence plus applicable blocking real-environment confirmation.

`SHIPPED` proves delivery, not product impact. Select concrete risks/gates; unknown executable scope fails safe stronger. Reuse equivalent evidence. Missing local tools do not make the user the runner. Emulator proof never establishes physical behavior.

Persistent/shared infrastructure is IaC-owned when applicable. Preserve a fit existing IaC tool; for new cloud projects without one, Terraform is preferred. Manual console configuration is exception-only and must be reconciled to code.

## Context and completion

Use scoped search/bounded output; refresh source identity on resume. Notes are pointers, not proof.

`.engineering/documentation-policy.json` owns context routes/budgets. Use `python3 scripts/verify_agent_context.py --route product --format json` for material product shaping or `--route bug` for implementation; add `--path`/`--workstream` when relevant.

Before integration, follow preflight and update affected canonical docs. `docs/product.md` owns durable product truth; `docs/current-state.md` owns integrated/blocked/next truth. Transfer durable knowledge and deferred release obligations before deleting completed plans.

Surface material ambiguity/invariant conflicts. Never suppress legitimate tests, expose private state, claim missing evidence passed or silently downgrade gates.
