# Current state

Status: active  
Owner: repository

## Current milestone

Decide whether comparative semantic v2 is a strong enough default on the pinned Qwen3.5-4B reference model, while keeping the repository reproducible and integration-ready.

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| Product foundation | Scope, architecture, constraints and roadmap | ACTIVE | stacked branches not yet converged to `main` |
| Scorer decision | Frozen v2/v1/letters/generated gate + order reversal | ACTIVE | representative Qwen3.5-4B BF16 CPU run |
| Runtime | Candidate batching + selected-vocabulary projection | ACTIVE | shared-prefix/cache reuse not implemented |
| Repository quality | Root Decisio baseline, locked setup, health/package gates | ACTIVE | final stacked-branch convergence |
| Examples | Snake, support routing and policy gate | ACTIVE | examples remain exploratory rather than quality evidence |

## Implemented on the active branches

### Decision path

- strict choice/request/result contracts with deterministic JSON state validation;
- comparative semantic v2 scorer and independent semantic v1 baseline;
- direct A/B/C baseline and generated JSON baseline;
- deterministic compiler and one-token readout verification;
- Qwen3.5 Transformers backend pinned to an exact model revision;
- one-batch candidate scoring and selected-vocabulary projection;
- deterministic candidate-ID tie breaking;
- zero generated answer tokens on native scoring paths;
- scorer/model/prompt provenance and frozen input SHA-256.

### Evidence

- frozen 64-example scorer-gate v1 workload across four semantic families;
- paired correctness and exact McNemar/binomial evidence;
- normal/reversed candidate-order comparison;
- generated-output invalid-rate accounting;
- repeated performance trials with warm-up, balanced scorer position, CPU wall-clock timing, p50/p95 workload latency, decisions/sec and process peak RSS;
- 8-case Qwen3.5-0.8B hosted-CPU directional scorer matrix;
- real-model semantic/Snake integration smoke.

### Repository

- `uv.lock` with frozen setup and lock verification;
- Apache-2.0 license, contribution/security guidance and Decisio-specific changelog/version;
- root `.engineering`, `skills/` and `scripts/` as the operational engineering authority;
- Repository health and integration-preflight workflows;
- CI lint/test/compile plus wheel build/install smoke;
- current-vs-target architecture separated in documentation;
- inherited repo-template contracts removed from the repository root;
- embedded `template/` retained only as baseline source material.

## Last validated automated evidence

Repository-specialization head `c7577c6a679e2574c80e80efffa0c987ed84f6ee`:

- Repository health: PASS — run `35655630899`;
- Decisio CI: PASS — run `35655631123`;
- CI includes lock verification, lint, tests, compile, wheel build and installed-wheel smoke.

Runtime-hardening head `69d0d187960289ae05563fc614eb1b165e8398d1`:

- Decisio CI: PASS — run `35653611378`;
- Real model smoke: PASS — run `35653611388`.

Latest completed directional scorer-matrix evidence remains the hosted-CPU Qwen3.5-0.8B run on `be12009660f7bd9c22cef3d7e7979a9cfe36371f`: all four methods scored 7/8; v2/v1 had 0/8 order changes, letters 1/8 and generated JSON 2/8. This is integration/directional evidence only.

## Remaining blockers

### Scorer decision

- The frozen 64-case Qwen3.5-4B BF16 CPU gate has not yet run under the full pinned CPU evidence contract.
- No stable-default conclusion should be made until that evidence exists.
- Broader paraphrase/wrapping, irrelevant-context, missing-evidence and candidate-count perturbations remain after the first scorer decision.

### Product capability

- Answerability is not implemented.
- Shared-prefix/cache execution and multi-question reuse are not implemented.
- Candidate batching still repeats shared prompt tokens across batch rows.
- Stable high-level Python API is intentionally deferred until scorer semantics are decided.

### Repository/integration

- The stacked product/benchmark/docs/hardening branches still need convergence into the product branch and then deliberate promotion to `main`.
- The full 64-case 4B CPU workflow has not yet produced retained scorer-gate evidence. The existing 0.8B hosted CPU smoke cannot satisfy the gate.

## Next

1. Finish exact-head automated validation for the repository-specialization slice and converge the stacked support PRs.
2. Run the frozen 64-case scorer gate on pinned Qwen3.5-4B BF16 CPU when the repository-owned CPU gate runs.
3. Decide from the precommitted gate whether comparative semantic v2 remains the default scorer.
4. If v2 survives, stabilize the small public Python entry point; if it fails, analyze discordant rows before expanding the API.
5. Continue broader perturbations, answerability and shared-prefix/cache work in that order.
