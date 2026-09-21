---
name: validate-change
description: Run the cheapest sufficient edit/test loop, diagnose failures with discriminating evidence, and expand validation as the changed risk or delivery stage requires.
---

# Validate Change

Use during implementation. Read the relevant operation/validation fields of `.engineering/commands.json`, or the equivalent repository-owned selector summary. A summary must expose its source identity and unresolved scope; it cannot override configuration or applicable guides.

## Choose feedback

Start from the observable outcome and owner. Resolve **risks -> concrete gates -> profile** with the native selector. Prefer formatter/static checks, affected compile and focused behavior tests; add material direct consumers when a boundary changes.

- Contained owner/module: usually `SCOPED`.
- Shared protocol, persistence/security, lifecycle, native/JNI/package/manifest/R8: usually `STRONG`, with gates justified by the actual risk.
- Selector/global validation/build/toolchain changes, unknown executable scope or release: `FULL`.
- Pure docs/copy/metadata: normally `LEAN`; executable examples, policy or configuration changes must be assessed for their actual behavior.

During **ITERATION**, exact-head publication, full-diff review, durable docs, broad E2E and remote preflight are not routine requirements. If a cheap gate is unavailable locally, defer its execution until readiness unless it is needed to test the current hypothesis now; then use focused repository automation.

At **INTEGRATION**, hand off to `../preflight-change/SKILL.md` for exact candidate/base, affected docs, required automated gates and critical journeys. At **RELEASE**, that procedure additionally requires full release evidence and blocking real-environment confirmation.

## Diagnose a failing gate

Classify before changing production code: change regression, baseline failure, environment/toolchain, flaky/non-deterministic, base drift or incorrect requirement/contract assumption. A suspected flake needs evidence; a rerun does not erase a real failure.

Record short decision facts in the existing task/workstream when useful:

| Evidence | Hypothesis | Discriminating experiment | Result / next action |
| --- | --- | --- | --- |
| <observed failure and source/run> | <possible owning cause> | <expected observation if true; what would refute it> | <confirmed/excluded/unresolved> |

Trace the violated invariant to its owner. Choose the cheapest experiment that separates plausible causes: targeted instrumentation, a smaller reproducer, comparison with the baseline or a direct contract test. Fix that owner and add regression evidence where it can actually detect the fault.

Never suppress, delete or weaken a legitimate failing test to obtain green. Each failed repair needs a new falsifiable hypothesis before another patch. **After two failed repairs with the same failure signature, change diagnostic strategy and obtain new evidence before a third repair**: reduce the reproducer, instrument the boundary or revisit the owner/assumption. This is an autonomous diagnostic pivot, not an automatic user-approval gate. Do not increase timeouts merely to hide a lifecycle failure.

## E2E and UI

When the changed claim needs a complete journey, consult `.engineering/e2e.json`. Select the smallest critical journey and cheapest sufficient automated environment. Executor capability and physical fidelity are separate.

- `ASSERTIONS`: UI is incidental to a non-visual system invariant.
- `SCREENSHOTS`: stable visible states need inspection and the journey is not a material UI/UX integration outcome.
- `FULL_MEDIA`: screenshots plus continuous journey video for material UI/UX critical outcomes entering shared development, or claims depending on motion, timing, navigation, gestures or release acceptance.

Required missing media means `E2E_EVIDENCE_INCOMPLETE`; never downgrade after execution to get PASS. Preserve privacy, source/run identity, bounded retention and cleanup. Physical/target-specific confirmation is deferred to release by default; earlier runs may diagnose explicitly environment-specific defects.

## Report only useful results

Use a bounded summary: stage, risks/profile, required gates with reasons and PASS/FAIL/PENDING/N/A, evidence refs and smallest useful next action. Include journey/environment/fidelity/media only when applicable. Success needs no log dump; failure needs the first relevant error plus context and a full-log reference. Batch independent reads, reuse unchanged output and poll remote state only when a meaningful update is expected. Do not repeat unchanged matrices or unrelated N/A fields in each update.
