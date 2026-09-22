---
name: preflight-change
description: Establish integration or release readiness for a coherent outcome using exact candidate/base identity, affected docs, risk-selected gates and equivalent evidence reuse.
---

# Preflight Change

Use when a coherent observable outcome is ready for the shared development branch or stable/release promotion. Draft pushes and ordinary edits remain `ITERATION`; use `../validate-change/SKILL.md` there.

The default CI boundary is the **feature candidate, not each commit**. Keep a feature PR draft while substantial implementation is still changing. Moving it to ready-for-review is the normal transition into `INTEGRATION` and may trigger the repository's expensive remote preflight. Subsequent source changes while ready invalidate only evidence that becomes stale/affected; superseded remote runs should be cancelled rather than allowed to finish pointlessly.

## Establish the candidate

1. State `INTEGRATION` or `RELEASE` and the observable outcome. Resolve material ambiguity using owners/ADRs/consumers/acceptance; ask only if alternatives still materially change the product or contract.
2. Refresh exact head, intended target/base and source tree. Confirm base freshness or proven merge compatibility under repository policy.
3. Review the complete candidate diff: scope, private/generated/debug residue, duplicate ownership, suppressed tests, missed consumers and compatibility/security/resource/UX drift.
4. Make affected durable documentation current. Use `../../docs/README.md` only if ownership is unclear. Assess README identity and usage separately, feature docs, architecture/ADR, security/data, operations, product experience and current state; report affected owners only. Current state describes integrated/blocked/next truth, not temporary branch activity.

## Resolve required evidence

Use `.engineering/commands.json` and its native selector: risks and concrete gates before profile. Preserve its stronger floor; unknown executable scope and changes to selector/global validation/build/toolchain fail safe `FULL`. Release requires `FULL`.

For each gate record reason, executor (`AGENT_LOCAL`, `REMOTE_AUTOMATED`, `REAL_ENVIRONMENT`) and evidence status. Lack of local tooling does not turn automatable work into a user task. A selector summary is a derived view, not a substitute for source identity or unresolved-risk review.

If a complete workflow is affected, consult `.engineering/e2e.json`: smallest critical journey, sufficient automated environment/fidelity, required UI evidence. At integration, material UI/UX journeys require screenshots plus continuous video (`FULL_MEDIA`); incidental UI may use assertions. Missing required media is `E2E_EVIDENCE_INCOMPLETE`, never a reason to downgrade the mode. Emulator/simulator proof does not establish physical behavior.

If shared infrastructure is affected, consult `.engineering/infrastructure.json` and `../provision-infrastructure/SKILL.md`: include IaC validation/plan evidence appropriate to blast radius, without turning every iteration commit into a remote cloud plan/apply.

## Reuse, then execute

Inspect existing successful evidence before any expensive run. Integration candidates require matching exact head, material target/base, required gates/profile and relevant E2E environment/fidelity/media. Check validity/expiry and trusted provenance. Changed PR number, draft status, labels or comments alone do not invalidate proof.

Run missing required local gates. Use `../remote-preflight/SKILL.md` only for missing remote gates; it owns remote dispatch/security and post-merge tree-equivalent reuse. A changed source/base invalidates evidence unless the repository's explicit equivalence policy proves it remains applicable. Ordinary integration candidates still need exact-head evidence.

On failure use the diagnostic protocol in `../validate-change/SKILL.md`, re-evaluate scope and rerun invalidated gates. Stronger risk may require stronger validation; unrelated suites do not replace diagnosis.

## Stage acceptance and output

| Stage | Required acceptance | Real-environment status |
| --- | --- | --- |
| `INTEGRATION` | Current base/diff/docs, all required automated gates and affected automated critical E2E on the candidate. | Residual required confirmations are `DEFERRED_TO_RELEASE`; retain the release obligation in its canonical owner. |
| `RELEASE` | Full release-grade automated/artifact/E2E evidence plus every applicable required real-environment confirmation. | Required confirmations must PASS before `RELEASE_READY`. |

Return a compact summary of stage, outcome, head/tree/base, risks/profile, required gates and reasons, reused/new evidence, affected docs, remaining gaps and readiness. Keep the complete gate report as linked evidence. Omission of unrelated fields is allowed; omission of failed/pending required gates is not.

Readiness: `READY_FOR_CI` for passed required local deterministic gates awaiting CI; `READY_FOR_REMOTE_PREFLIGHT` for passed semantic/base/diff/docs checks with remote work remaining; `AUTOMATED_PREFLIGHT_CONFIRMED` when all required automated evidence is valid; `RELEASE_READY` only after release acceptance above; otherwise `NOT_READY_FOR_AUTOMATED_PREFLIGHT`. Automatic preflight confirmation never claims deferred physical evidence passed.
