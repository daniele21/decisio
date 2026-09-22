# Current state

Status: active  
Owner: repository

## Current milestone

Migrate Decisio's reference runtime from PyTorch/Transformers BF16 to local GGUF inference through llama.cpp, then rerun the frozen scorer decision on the runtime/artifact class that defines the product.

Active plan: [llama.cpp reference runtime migration](workstreams/llama-cpp-reference-runtime.md).

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| llama.cpp reference runtime | W1/W2 backend + local-GGUF CLI implemented | ACTIVE | real Qwen3.5 GGUF smoke/evidence pending |
| Shared context-state fast path | single-sequence branching fresh-equivalent; bounded repeated-state cache implemented | ACTIVE | repeated-state real-model evidence pending |
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
- in-process `LlamaCppBackend` for local GGUF on CPU with exact artifact SHA/provenance;
- GGUF chat-template/tokenizer readout, native logits and generated JSON through one loaded model;
- semantic candidate branching via full single-sequence llama.cpp state snapshot/restore;
- compiler-marked exact state-prefix reuse with a byte/entry-bounded LRU cache;
- logical/physical token, snapshot/restore and cache hit/reuse metrics;
- current Qwen3.5 Transformers backend retained only as migration-source code;
- frozen 64-case workload, normal/reversed comparison and paired correctness evidence;
- deterministic gate evaluator with quality, family, order, zero-generation and latency criteria;
- CPU timing/p50/p95/throughput/RSS infrastructure;
- 0.8B real-model matrix and Snake smoke;
- repository health, package/install and integration-preflight workflows.

The current runtime details are migration-source evidence, not the target v1 runtime contract.

## Evidence status

Support PRs #2–#4 were converged into PR #1 with exact-head integration evidence before the runtime decision changed.

PR #1 is deliberately **draft** again.

Qwen3.5-4B BF16/Transformers CPU run `35680562215` is non-authoritative for scorer promotion after this decision. It may remain historical/directional evidence.

Run `35717350247` on pinned Qwen3.5-0.8B Q4_K_M proved the single-sequence state primitive exactly fresh-equivalent on the smoke fixture: score, binary-probability and distribution deltas were all `0.0`; physical input fell from 376 to 224 tokens (40.4% reuse). The captured sequence state was 22,072,908 bytes. This is mechanism evidence, not the representative 4B scorer decision.

## Blockers

### W1/W2 — real runtime evidence

- prove GGUF tokenizer/readout, native logits and generated JSON on pinned Qwen3.5 Q4_K_M artifacts;
- verify the 0.8B CI smoke artifact SHA and then freeze the exact 4B reference artifact/runtime;
- remove Torch/Transformers from supported setup after migration diagnostics are no longer needed.

### W3 — complete shared context-state reuse

- candidate branching now passes the pinned 0.8B fresh oracle with the precommitted tolerances;
- prove the bounded exact-state-prefix cache on repeated questions over one long state;
- retain explicit cache reset, byte bounds and logical-vs-physical token evidence.

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
3. Complete W3 by proving the bounded repeated-state cache against fresh evaluation and recording speed evidence.
4. Freeze gate-v2 artifact/runtime/fast-path identity before representative results.
5. Run the full CPU gate and repeated-state benchmark, then decide semantic v2.
6. Only then return PR #1 to ready and run exact-head integration preflight.
