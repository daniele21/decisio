# Current state

Status: active  
Owner: repository

## Current milestone

Migrate Decisio's reference runtime from PyTorch/Transformers BF16 to local GGUF inference through llama.cpp, then rerun the frozen scorer decision on the runtime/artifact class that defines the product.

Active plan: [llama.cpp reference runtime migration](workstreams/llama-cpp-reference-runtime.md).

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| llama.cpp reference runtime | W1 Qwen3.5-4B Q4_K_M compatibility spike | ACTIVE | prove tokenizer/logit/generation primitives through the in-process bridge |
| Shared context-state fast path | backend contract already wired; W3 real llama.cpp branching/cache pending | BLOCKED | W2 LlamaCppBackend |
| Scorer decision | Preserve frozen 64-case workload and promotion semantics | BLOCKED | shared llama.cpp path + gate-v2 identity |
| Product foundation | Consolidated candidate in PR #1 | ACTIVE | runtime migration and representative evidence |
| Repository quality | Baseline/health/package gates | ACTIVE | final exact-head integration |
| Examples | Snake, support routing, policy gate | ACTIVE | exploratory only, not scorer-quality evidence |

## Product/runtime decision

The v1 canonical target is Qwen3.5-4B Q4_K_M GGUF through llama.cpp, with CPU-only representative scorer evidence and exact GGUF/runtime/host provenance.

The exact artifact SHA and runtime build are frozen only after W1 proves the candidate artifact/binding can satisfy Decisio's scorer primitives.

The existing PyTorch/Transformers backend remains migration-source code; it no longer decides the stable scorer.

## Implemented today

- strict request/result contracts and deterministic compiler;
- comparative semantic v2, semantic v1, letters and generated JSON;
- semantic scorers preserve candidate-local YES/NO `binary_conditional_probability` separately from cross-candidate `distribution`;
- zero generated answer tokens on native paths;
- current Qwen3.5 Transformers backend with batching/selected-vocabulary projection;
- semantic scorer dispatch prefers an optional `shared_prefix_batch_next_token_logits` backend capability before generic batching;
- frozen 64-case workload, normal/reversed comparison and paired correctness evidence;
- deterministic gate evaluator with quality, family, order, zero-generation and latency criteria;
- CPU timing/p50/p95/throughput/RSS infrastructure;
- 0.8B real-model matrix and Snake smoke;
- repository health, package/install and integration-preflight workflows.

The current runtime details are migration-source evidence, not the target v1 runtime contract.

## Evidence status

Support PRs #2–#4 were converged into PR #1 with exact-head integration evidence before the runtime decision changed.

PR #1 is deliberately **draft** again.

Qwen3.5-4B BF16/Transformers CPU run `35680562215` is non-authoritative for scorer promotion after this decision. It may remain historical/directional evidence. The 0.8B hosted-CPU evidence is also directional only.

## Blockers

### W1 — llama.cpp compatibility

- load exact Qwen3.5-4B Q4_K_M GGUF and capture SHA/runtime metadata;
- verify GGUF/runtime tokenizer IDs for scorer readouts;
- obtain semantic-v2/v1 and letters next-token logits;
- run generated JSON through the same model/runtime;
- prove deterministic 8-case CPU smoke.

### W2/W3 — runtime and shared fast path

- stable llama.cpp backend contract and local-GGUF CLI;
- candidate-prefix branching from one shared model context state;
- bounded repeated-state cache for many questions over one long state;
- fresh-vs-shared choice/score/probability equivalence;
- logical vs physically evaluated token instrumentation;
- remove Torch/Transformers from the reference path.

### W4/W5 — scorer decision

Freeze the exact Q4_K_M/runtime/shared-execution identity, then run the full 64-case CPU matrix and
committed evaluator plus a long-state/many-question speed fixture. Any failed correctness criterion
keeps v2 experimental; the fast path cannot become default without fresh equivalence.

### Later

Answerability, larger-scale multi-question scheduling, calibration and stable public API follow after
the scorer and shared runtime path survive the new evidence gates.

## Next

1. Execute W1 from the active workstream.
2. Implement W2 if the in-process bridge is sufficient; otherwise use the smallest direct libllama bridge.
3. Implement W3 shared context-state reuse and prove fresh equivalence plus repeated-state speedup.
4. Freeze gate-v2 artifact/runtime/fast-path identity before representative results.
5. Run the full CPU gate and repeated-state benchmark, then decide semantic v2.
6. Only then return PR #1 to ready and run exact-head integration preflight.
