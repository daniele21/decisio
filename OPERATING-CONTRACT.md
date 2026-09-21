# Project Operating Contract

Version: 0.7.0

This contract defines common operational semantics for adopted repositories. It standardizes **intent and lifecycle**, not implementation tools.

The governing rule is:

> Every operation must be identifiable, owned, bounded, reversible and leave no unintended residue.

The delivery rule is:

> Iterate with the cheapest useful feedback, establish exact-head automated readiness when a coherent slice integrates, and reserve required real-environment acceptance for release checkpoints.

Execution and validation-stage semantics are further defined in [`EXECUTION-CAPABILITY-CONTRACT.md`](EXECUTION-CAPABILITY-CONTRACT.md). E2E fidelity/evidence semantics live in [`E2E-ENVIRONMENT-CONTRACT.md`](E2E-ENVIRONMENT-CONTRACT.md).

## 1. Command contract

Each adopted repository maps these intents in `.engineering/commands.json` to its native tooling:

- `setup` — prepare the supported development environment;
- `doctor` — verify prerequisites/capabilities;
- `dev` — start/install/launch the canonical development runtime when applicable;
- `check` — cheap broad structural/static validation;
- `test` — unit/integration/contract behavior;
- `e2e` — complete critical user/system workflow when lower-level tests cannot prove the outcome;
- `build` — create runnable output with unique build identity;
- `smoke` — prove minimum viability of the built/running artifact;
- `package` — create a distributable artifact when applicable;
- `stop` — stop project-owned local runtimes when applicable;
- `clean` — remove only project-owned generated state.

Genuinely irrelevant intents may be `n/a`. Do not introduce a universal wrapper merely to make command syntax identical.

The same machine-readable contract owns development stages, publication gates, validation profiles/risk routing, execution classes, remote preflight/evidence reuse and validation-economics policy.

## 2. Delivery stage contract

### `ITERATION`

Default while implementation is changing.

Use focused evidence that can falsify the current edit quickly. Exact-head readiness, complete-diff review, durable-documentation freshness and remote preflight are not automatically required for every edit, branch push or draft/collaboration update.

### `INTEGRATION`

Begins when a coherent vertical slice delivers an observable outcome and is ready to converge into the shared development/integration branch or be marked ready for merge/review.

At this point:

- record exact head and intended target/base;
- review the complete diff;
- make affected durable documentation current;
- select concrete risk dimensions and required gates;
- execute/route deterministic evidence;
- run affected critical E2E journeys automatically when lower-level evidence is insufficient;
- for material UI/UX journeys, preserve reviewable screenshot + video evidence;
- record residual `REAL_ENVIRONMENT` requirements and defer them to `RELEASE` rather than blocking ordinary integration.

### `RELEASE`

Stable/promotion/release-candidate checkpoints use full release-grade validation, artifact/package checks, release-critical E2E and every required residual real-environment confirmation.

Required real-environment evidence is blocking here.

## 3. Validation execution model

Required gates are classified for the current session as:

- `AGENT_LOCAL` — current agent can execute directly;
- `REMOTE_AUTOMATED` — deterministic/automatable but unavailable locally;
- `REAL_ENVIRONMENT` — genuinely depends on representative hardware, protected authority/external environment or human judgement.

An automatable deterministic gate MUST NOT be delegated to the user solely because the agent lacks tooling.

When equivalent local execution exists, use it for rapid feedback. Otherwise repository-owned remote automation is a valid execution backend.

Classification and delivery-stage placement are separate: a `REAL_ENVIRONMENT` requirement is reported at integration and normally executed as release acceptance.

## 4. Integration/release readiness

`preflight-change` owns readiness beginning at `INTEGRATION`.

The flow is:

```text
observable outcome ready
-> resolve material ambiguity
-> refresh target/base + exact head
-> inspect complete diff
-> make affected durable docs current
-> identify risks + required gates
-> select affected automated E2E journey/environment/evidence mode
-> classify executors
-> reuse equivalent successful evidence
-> execute only missing/stale/insufficient automated gates
-> automated preflight confirmed
-> integrate into shared development branch
-> release checkpoint
-> required residual real-environment evidence
-> release ready
```

### Material ambiguity

Inspect canonical repository evidence first. Ask the user only when unresolved alternatives materially change behavior, public contracts, persistence/migration, security/trust, lifecycle/resource semantics, compatibility, acceptance criteria or meaningful UX.

### Failure diagnosis

Before changing production behavior because a gate failed, classify the failure and identify the violated invariant/owner. Do not weaken legitimate gates merely to obtain green status. Repeated failure after a repair requires a new falsifiable hypothesis.

### Exact head/base

Integration/release evidence is relative to the exact source head and material intended-base relationship. Invalidate only evidence affected by a material source/base/dependency change.

PR number, draft/ready status, labels/comments or another collaboration-only change do not independently invalidate otherwise equivalent source evidence.

### Complete diff

At integration/release, inspect the whole candidate against the intended base for accidental/generated/private/debug residue, unrelated scope, duplicated ownership/policy, weakened tests, stale affected documentation and compatibility/security/resource/UX drift.

## 5. Evidence reuse

Before triggering expensive remote validation, reuse successful evidence when it still proves:

- exact source head;
- material target/base relationship;
- required gate identity;
- selected profile or stronger equivalent;
- E2E environment/fidelity/evidence mode when relevant.

The normal algorithm is:

```text
resolve required gates
-> reuse equivalent successful evidence
-> identify unsatisfied automated evidence
-> execute only missing/stale/insufficient automated gates
-> combine into one integration readiness result
```

Never rerun an expensive gate solely because an otherwise identical PR was recreated or moved from draft to ready.

Release-specific real-environment evidence may also be reused only when its target/environment/build identity remains sufficient for the release claim.

## 6. Remote preflight

Repositories maintained by execution-limited agents should expose a declared remote-preflight trigger.

Remote execution must:

- pin exact head;
- preserve intended-base identity;
- execute project-owned deterministic semantics;
- report selected risk/profile/gates and diagnosable results;
- preserve least privilege;
- avoid production/signing/deployment secrets in change-branch execution;
- use bounded timeout/artifact retention.

A separate reporting job may hold PR write permission when necessary.

Automated preflight does not need to wait for deferred real-environment release evidence to confirm integration readiness.

## 7. Test vs E2E vs smoke

These are distinct:

```text
unit/component
-> integration/contract
-> end-to-end critical outcome
-> smoke of built/running artifact
```

Cover invariants as low as practical. E2E is not coverage theater and should stay small/high-value.

Use E2E when correctness depends on assembled boundaries, for example first launch/core flow, create/use/save/reopen, persistence/restart, IPC/consumer integration, important import/export or failure/recovery journeys.

## 8. E2E implementation and evidence

Use stack-native established tooling. The universal standard does not mandate one framework.

When the claim concerns distributable behavior, run against the built/package artifact when material and practical.

For UI-bearing journeys, evidence mode is selected from the claim and stage:

- `ASSERTIONS` — UI incidental to deterministic system behavior;
- `SCREENSHOTS` — bounded stable visible states/layout/hierarchy/copy/recovery/adaptive behavior need inspection;
- `FULL_MEDIA` — screenshots plus continuous video when UI/UX is materially part of the integration outcome, or when motion, timing/progression, navigation/transition sequence, lifecycle visibility, gesture continuity or release acceptance requires observation over time.

Missing evidence required by the selected mode is `E2E_EVIDENCE_INCOMPLETE`. Do not silently downgrade the evidence mode after execution.

All E2E evidence carries run/source/build/environment identity, remains privacy-safe and has bounded retention.

## 9. Zero-residue contract

Every operation cleans project-owned temporary resources on success, failure, timeout, cancellation, interrupt and partial initialization.

This includes as applicable:

- application/server/helper processes;
- localhost listeners;
- browser/device/emulator sessions;
- temporary databases/storage/preferences;
- downloads/uploads/fixtures;
- screenshots/traces/videos/logs;
- workspaces/PID/lock files.

Cleanup may remove only resources whose ownership is established.

## 10. Build identity

Every material build has a unique identity, even when source revision is unchanged.

Build identity normally includes:

- product/version;
- build ID;
- source revision and dirty state;
- platform/architecture;
- channel/variant.

A changed output receives a new build ID rather than overwriting a successful artifact.

## 11. Artifact lifecycle

Successful artifacts are immutable and promoted only after validation.

Where applicable, each successful artifact includes:

- build/source identity;
- machine-readable manifest;
- SHA-256 checksum for distributable binaries/packages;
- generated build delta against the previous successful comparable lineage build.

Use a staging -> validate -> promote flow. Failed/partial artifacts must not be left where they can be mistaken for valid outputs.

Local artifact retention is bounded; the reference default is the latest two successful builds per comparable lineage. CI/E2E evidence uses bounded artifact-store retention. Durable releases belong in an appropriate release/package registry.

## 12. Build delta

`BUILD_CHANGELOG.md` (or equivalent) describes the exact delta between comparable successful builds and is distinct from the product-level `CHANGELOG.md`.

Include as applicable source, dependency, toolchain, configuration, migration/compatibility, artifact metric and validation differences.

## 13. Local runtime

Projects that open local processes/listeners own them explicitly.

Defaults where applicable:

- loopback binding unless external exposure is intentional;
- collision-aware configurable ports;
- readiness before declaring start success;
- graceful shutdown;
- child-process/listener cleanup;
- stale resource recovery;
- verification that stop leaves no project-owned listener/process behind.

## 14. Validation economics

Where practical, observe expensive gates for duration, flake rate, unique regression signal and overlap.

Move cheap high-signal gates earlier, affected automated E2E to integration, and expensive real-environment confirmation to release. This changes **placement and scope**, not the final invariant protected.

The operating objective is:

> the cheapest feedback loop that preserves sufficient confidence at the current delivery stage.

## Agent-facing summaries

`.engineering/commands.json` `agent_reporting` defines the bounded selector/gate-report surface. Existing native selectors and CI reporters should expose it without adding a second selector or universal command wrapper. Report stage, source identity (head/tree/base/dirty, unknown explicitly), risks/profile, required gates with reasons/executor/status, evidence refs, remaining gaps and next action. A pre-execution required gate is PENDING, never implicitly PASS.

Keep full logs/reports accessible by reference. Successful gates need brief results; failures need the first relevant error with enough surrounding context. A summary does not verify evidence or prove reuse: apply the execution capability contract's identity/trust rules. Do not hide failed/pending required gates, stale evidence, unresolved scope or deferred release obligations to meet an output budget. During iteration unknown/uncommitted identity is explicit and does not impose an exact-head publication gate.
