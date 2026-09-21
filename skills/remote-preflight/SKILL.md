---
name: remote-preflight
description: Execute missing integration/release gates through repository-owned automation with equivalent evidence reuse, exact source identity and least privilege.
---

# Remote Preflight

Use after `../preflight-change/SKILL.md` identifies missing `REMOTE_AUTOMATED` gates. Consume its stage, head/tree/base, risk/gate selection, applicable E2E identity and existing evidence; do not reconstruct unchanged checks or reload the same configuration.

## Resolve missing work

Verify successful evidence still matches the exact candidate, target/base, required gates/profile and E2E environment/fidelity/media, including freshness and trusted provenance. Trigger only missing, stale or insufficient gates with the native `auto` selector. Never request full merely because it is easier to dispatch. If all required automated gates are satisfied, return their references without a new run.

### Post-merge content-equivalent reuse

Repository-owned automation may reuse successful integration evidence after squash/rebase only when:

- the merged Git tree is identical to the validated candidate tree;
- the push base is exactly the target/base used for validation;
- gates/profile and relevant E2E identity are equal or weaker than the proof;
- evidence is current and trusted; the workflow controls artifact/identity lookup.

Report `tree-equivalent` reuse with the original run, never pretend it executed on the new commit. A changed tree/base, expired proof, broader gates, missing identity or direct push without matching evidence validates normally. Release remains exact-candidate unless an explicit release equivalence policy permits otherwise.

## Execute and inspect

Pin new runs to exact head and target/base. Preserve trusted requesters, same-repository heads by default, bounded timeouts/artifacts, read-only execution credentials and separate reporting privileges. Do not expose production/deployment/signing secrets to change-branch execution.

Inspect the bounded gate summary first. Fetch relevant failing steps/log excerpts or required artifacts when necessary. On failure follow `../validate-change/SKILL.md`; do not delegate automatable reruns to the user. Re-evaluate risks and evidence validity after a repair. Avoid repeated unchanged polling/output.

Missing automation is `AUTOMATION_CAPABILITY_GAP`. Unknown validation scope is `VALIDATION_SCOPE_GAP`; fail safe stronger while repairing the selector. Missing required E2E/media is `E2E_EVIDENCE_INCOMPLETE`.

## Output

Return source/base identity, selected risks/profile, required gate statuses/reasons, reused/new evidence refs, applicable E2E environment/fidelity/media and next action. Preserve FAIL/PENDING and explicit capability gaps. At integration report residual real-environment requirements as `DEFERRED_TO_RELEASE`; at release they remain blocking. `AUTOMATED_PREFLIGHT_CONFIRMED` requires all required automated evidence; release readiness is determined by preflight's full acceptance rule. Link full reports instead of repeating them.
