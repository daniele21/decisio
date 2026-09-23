# llama.cpp reference runtime migration

Status: ACTIVE  
Owner: repository  
Convergence branch: `product/define-decisio-foundation`  
Pull request: #1  
Last shaped: 2026-09-23

## Axes

- PRODUCT: `PRODUCT_STRATEGIC`
- DELIVERY: `ITERATION`
- VALIDATION: `STRONG`
- EXECUTION: `AGENT_LOCAL` + `REMOTE_AUTOMATED` for pinned real-model CPU evidence

## Goal

Make local GGUF + llama.cpp the canonical Decisio v1 runtime and prove the product boundary:

> stable decision context is reusable model state; changing application state stays in the dynamic
> suffix; bounded actions are returned without answer generation.

Semantic-v2 remains a separate evidence lane. Its failed general-purpose gate is not reinterpreted.

## Product intent

- **User:** engineers building repeated bounded decisions over evolving local application state.
- **Problem:** direct logits are a shared primitive; re-prefilling stable task context on every
  decision leaves the application/runtime value unresolved.
- **Outcome:** keep stable task/policy context warm, append current state + deterministic sensors +
  valid actions, and return typed zero-generation decisions with explicit reuse/provenance.
- **Reference:** Qwen3.5-2B Q4_K_M GGUF + llama.cpp CPU for reproducible evidence; compatible GGUFs
  remain separate evidence identities.
- **Risks:** VALUE `MEDIUM`; USABILITY `LOW`; FEASIBILITY `MEDIUM` because reuse must preserve
  fresh outputs and native batch semantics; VIABILITY `LOW`.

## Non-goals

- no hosted service or workflow engine;
- no broad backend matrix before the reference path is proven;
- no quantization/runtime equivalence claim;
- no calibrated-confidence claim without a matching calibration artifact;
- no fast path without a fresh oracle.

## Technical invariants

- native scoring generates zero answer tokens;
- deterministic invalid candidates are removed before model scoring;
- stable task policy belongs in the reusable prefix; changing world state/sensors in the suffix;
- scorer/compiler semantics remain backend-independent;
- evidence binds exact GGUF SHA, quantization, compiler/scorer and runtime settings;
- shared execution restores complete model context state, not a KV-only assumption;
- cache state is bounded, observable and clearable;
- every optimized path is compared with fresh evaluation before promotion.

## Execution DAG

| ID | State | Outcome |
| --- | --- | --- |
| W0 | DONE | Transformers/BF16 no longer controls promotion. |
| W1 | DONE | Real Q4_K_M llama.cpp scorer primitives proven. |
| W2 | DONE | Local-GGUF backend/CLI and provenance stabilized. |
| W3 | DONE | Exact single-sequence snapshot/restore + bounded cache proven on 0.8B smoke. |
| W4 | DONE | 2B semantic scorer-gate identity frozen before results. |
| W5 | FAILED | Semantic-v2 short/fresh general gate failed family + latency criteria. |
| W5a | DONE | Repeated-state diagnostic justified a scoped semantic experiment. |
| W5b | ACTIVE | Frozen repeated-state gate v3 decides only semantic-v2 repeated-state scope. |
| W6 | BLOCKED | Record semantic-v2 scope from W5b without rewriting failed evidence. |
| W7 | ACTIVE | Prove stateful direct Snake loop with fixed context and fresh/cache oracle. |

## Runtime contract

```text
stable decision context
        |
 deterministic compiler
        |
 reusable llama.cpp model context
        |
current state + deterministic sensors + valid candidates
        |
 direct or scoped semantic readout
        |
 typed DecisionResult + provenance + runtime metrics
```

llama.cpp owns execution and context mechanics. Decisio owns the decision-context boundary, scorer
semantics, deterministic-constraint contract, probability status, provenance and evidence.

## Shared model-context primitive

The accepted primitive uses one canonical llama.cpp sequence plus
`llama_state_seq_get_data` / `llama_state_seq_set_data`. Earlier multi-sequence reuse changed
scores and was rejected rather than tolerated.

Pinned 0.8B smoke evidence established the invariant:

- fresh/reused choice and scores matched exactly;
- one candidate-prefix run reduced 376 logical tokens to 224 physical;
- a longer repeated-state run evaluated 526 physical tokens versus 2574 fresh;
- cache entries/bytes returned to zero after clear.

These are mechanism proofs, not representative 2B product-performance claims. Native checkpoint
boundaries remain conservative: a compiler-marked prefix is an upper bound and the backend checkpoints
only where the fresh native decode schedule is reproducible.

## Semantic-v2 evidence lane

Scorer-gate v2 on the pinned 2B artifact remains **FAIL**:

- overall quality/order robustness/zero generation/runtime correctness passed;
- `evidence_entailment` failed its family guardrail;
- short/fresh semantic latency was worse than generated JSON.

The result remains authoritative for general short/fresh semantic-v2 use.

Repeated-state diagnostic v2 later found equal observed quality on 6/7 unique cases and materially
lower latency for semantic scoring with heavy context reuse. That justified the separately frozen
48-decision repeated-state gate v3. A PASS can support only `NARROW_SCOPE`; it cannot erase v2.

Contract: `benchmarks/repeated-state-gate-v3.md`.

## W7 stateful direct reference loop

Snake is the first product-shaped reference:

```text
fixed controller contract -> reusable llama.cpp model context
                                      |
current board + deterministic sensors + valid actions
                                      |
                             direct A/B/C logits
                                      |
                                  typed move
```

The application filters reverse/wall/body failures and computes local sensors before scoring. The
model request does not replay previous boards. Snake direct scoring enables fixed-context reuse by
default; `--fresh-prefix` runs the same stateful prompt without reuse.

Required evidence is split deliberately:

- **runtime correctness:** cached and fresh same-prompt scoring return identical choice/scores;
- **reuse:** cache hits occur and physical input work is below logical input work;
- **controller quality:** gameplay/optimality is measured separately from cache efficiency;
- **resource honesty:** context snapshots remain bounded and instrumented.

Direct option logits are not claimed as novel. The product claim is the stateful application/runtime
contract around them.

## Calibration compatibility

A future calibration artifact must bind GGUF SHA, quantization, scorer/compiler/readout, llama.cpp
build, method and calibration dataset. Without an exact match, output remains uncalibrated.

## Completion

Before PR #1 returns to ready:

1. record W5b from its unchanged criteria as the semantic-v2 scope decision;
2. prove W7 fresh/cache equivalence plus physical-token reduction on exact-head real-model smoke;
3. keep controller-quality evidence distinct from runtime-reuse evidence;
4. update durable docs and PR metadata;
5. run required exact-head integration gates and inspect the complete diff against live `main`.

Historical failed gates remain failed; the stateful product direction does not rewrite them.
