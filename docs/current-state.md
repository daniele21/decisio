# Current state

Status: active  
Owner: repository

## Current milestone

Migrate Decisio's reference runtime from PyTorch/Transformers BF16 to local GGUF inference through
llama.cpp, then rerun the frozen scorer decision on the runtime/artifact class that defines the
product.

Active plan: [llama.cpp reference runtime migration](workstreams/llama-cpp-reference-runtime.md).

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| llama.cpp reference runtime | W1 compatibility spike on Qwen3.5-4B Q4_K_M GGUF | ACTIVE | prove tokenizer/logit/generation primitives through the in-process llama.cpp bridge |
| Scorer decision | Preserve frozen 64-case workload and precommitted promotion semantics | BLOCKED | llama.cpp backend + gate-v2 runtime/artifact identity |
| Product foundation | Consolidated product/scorer/repository candidate in PR #1 | ACTIVE | llama.cpp migration and new representative evidence |
| Repository quality | Root Decisio baseline, locked setup, health/package gates | ACTIVE | final exact-head integration after runtime migration |
| Examples | Snake, support routing and policy gate | ACTIVE | examples remain exploratory rather than scorer-quality evidence |

## Product/runtime decision

The v1 canonical runtime target is now:

- Qwen3.5-4B;
- Q4_K_M GGUF;
- llama.cpp through an in-process backend;
- CPU-only representative scorer gate;
- exact GGUF SHA-256 plus llama.cpp/binding/build and host/thread provenance.

The exact reference artifact SHA and runtime build are intentionally not frozen until W1 proves the
candidate artifact and binding can satisfy Decisio's scorer primitives.

The existing PyTorch/Transformers implementation remains in the branch as the current executable
migration source. It is no longer the product authority for choosing the stable scorer.

## Implemented today

### Decision semantics

- strict choice/request/result contracts with deterministic JSON state validation;
- comparative semantic v2 scorer and independent semantic v1 baseline;
- direct A/B/C baseline and generated JSON baseline;
- deterministic compiler and one-token readout verification;
- deterministic candidate-ID tie breaking;
- zero generated answer tokens on native scoring paths;
- frozen input/provenance infrastructure.

### Current runtime implementation

- Qwen3.5 PyTorch/Transformers backend;
- candidate batching and selected-vocabulary projection;
- CPU timing, p50/p95, throughput and process peak RSS;
- hosted 0.8B real-model smoke and scorer-matrix smoke.

These runtime details are migration source evidence, not the target v1 runtime contract.

### Evidence harness

- frozen 64-example workload across four semantic families;
- paired correctness and exact McNemar/binomial evidence;
- normal/reversed candidate-order comparison;
- generated-output invalid-rate accounting;
- deterministic scorer-gate evaluator with quality, family, order-robustness,
  zero-generation and generation-latency criteria.

The workload and gate semantics should be preserved across the runtime migration unless a genuine
fixture/measurement defect is found before representative llama.cpp results exist.

## Evidence status

Support PRs #2–#4 were converged into PR #1 with exact-head integration evidence before the runtime
decision changed.

PR #1 is now deliberately **draft** again because the reference runtime and scientific evidence
contract are being changed.

The previously triggered Qwen3.5-4B BF16/Transformers CPU gate (run `35680562215`) is
non-authoritative for scorer promotion after this decision. It may remain useful as historical or
directional comparison evidence, but it cannot make semantic v2 the stable default.

Latest completed 0.8B hosted-CPU scorer-matrix evidence also remains directional only.

## Remaining blockers

### W1 — llama.cpp compatibility

- load an exact local Qwen3.5-4B Q4_K_M GGUF;
- capture its SHA-256 and runtime/model metadata;
- verify GGUF/runtime tokenization for all scorer readout tokens;
- obtain next-token logits for semantic-v2/v1 and letters;
- run generated JSON through the same loaded llama.cpp model;
- prove deterministic 8-case CPU smoke behavior.

### W2/W3 — runtime and gate contract

- replace the reference Transformers backend with a stable llama.cpp backend contract;
- make local GGUF path the reference CLI flow;
- freeze exact Q4_K_M artifact/runtime identity;
- version the scorer gate for llama.cpp/GGUF;
- preserve probability honesty: no calibrated-probability claim without a matching calibration
  artifact.

### W4 — representative scorer decision

- run the full frozen 64-case matrix on the pinned Q4_K_M + llama.cpp CPU configuration;
- apply the precommitted evaluator;
- keep v2 experimental if any criterion fails rather than weakening thresholds after the result.

### Later product capability

- answerability;
- shared state/question reuse through llama.cpp sequence/cache primitives;
- multi-question reuse;
- optional calibration bound to exact GGUF/scorer/compiler/runtime identity;
- stable high-level Python API after scorer semantics survive the new gate.

## Next

1. Execute W1 from `docs/workstreams/llama-cpp-reference-runtime.md`.
2. If the in-process binding proves sufficient, implement W2 and remove Torch/Transformers from the
   reference path; otherwise use the smallest direct libllama bridge.
3. Freeze scorer-gate v2 artifact/runtime identity before representative results exist.
4. Run the full CPU gate and decide semantic v2 from that evidence.
5. Only then return PR #1 to ready-for-review and run exact-head integration preflight.
