# Current state

Status: active  
Owner: repository

## Current milestone

Migrate Decisio's reference runtime from PyTorch/Transformers BF16 to local GGUF inference through llama.cpp, then rerun the frozen scorer decision on the runtime/artifact class that defines the product.

Active plan: [llama.cpp reference runtime migration](workstreams/llama-cpp-reference-runtime.md).

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| llama.cpp reference runtime | W1/W2 backend + local-GGUF CLI implemented | DONE | scorer primitives proven on pinned real GGUF smoke |
| Shared context-state fast path | single-sequence branching + bounded repeated-state cache | DONE | pinned 0.8B smoke is exactly fresh-equivalent |
| Scorer decision | Frozen 64-case gate-v2 on pinned 4B Q4_K_M llama.cpp | ACTIVE | representative 4B run pending |
| Product foundation | Consolidated candidate in PR #1 | ACTIVE | runtime migration and representative evidence |
| Repository quality | Baseline/health/package gates | ACTIVE | final exact-head integration |
| Examples | Snake, support routing, policy gate | ACTIVE | exploratory only, not scorer-quality evidence |

## Product/runtime decision

The v1 canonical target is Qwen3.5-4B Q4_K_M GGUF through llama.cpp, with CPU-only representative scorer evidence and exact GGUF/runtime/host provenance.

Scorer-gate v2 is frozen on `lmstudio-community/Qwen3.5-4B-GGUF` revision `e52a809eba94f740f51bdd80a73f189d06ac9347`, file `Qwen3.5-4B-Q4_K_M.gguf`, SHA-256 `25082a7dd3776cc3c741c6347d3bd04523f05796607b3fbc32fa3a25dfa1418c`, with `llama-cpp-python==0.3.35` on CPU. This is the reference evidence artifact, not a restriction on compatible user-selected GGUFs.

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

Run `35717350247` on pinned Qwen3.5-0.8B Q4_K_M proved the single-sequence state primitive exactly fresh-equivalent on the smoke fixture: score, binary-probability and distribution deltas were all `0.0`; physical input fell from 376 to 224 tokens (40.4% reuse). The captured sequence state was 22,072,908 bytes.

Run `35726724805` then proved the bounded repeated-state cache on the same pinned 0.8B artifact after aligning reusable checkpoints to native `n_batch` boundaries. The same-state/different-question hit was exactly fresh-equivalent (`0.0` max score, binary-probability and distribution deltas), evaluated 526 physical tokens versus 2574 fresh, reused 1024 cached-state tokens, and reduced observed latency from 32.24 s to 7.05 s (~4.57x). Cache clear returned entries/bytes to zero. This is mechanism evidence, not the representative 4B performance claim.

## Remaining gate

### W5 — representative scorer decision

The gate-v2 contract is now frozen before representative 4B results. The blocking run must use:

- the exact 4B Q4_K_M artifact/revision/SHA above;
- `llama-cpp-python==0.3.35` on CPU with the frozen context/batch/thread/cache settings;
- the full 64-case workload SHA `087ee8bbec3393609689046ea9c5d8219d0f39562e322180ca8f1e08eb368d3a`;
- semantic v2, semantic v1, letters and generated JSON in normal and reversed order;
- the unchanged quality/family/order/zero-generation/generation-latency criteria;
- full-workload shared-vs-fresh equivalence plus a same-state/different-question repeated-cache oracle.

A quality or equivalence failure keeps semantic v2 experimental. Cache latency is recorded, but no 4B cache-speed threshold was invented from the earlier 0.8B observation.

### Later

Answerability, larger-scale multi-question scheduling, calibration and stable public API follow after
the scorer and shared runtime path survive the representative gate.

## Next

1. Run scorer-gate v2 on the frozen Qwen3.5-4B Q4_K_M reference artifact.
2. Diagnose any failed scientific/runtime criterion without weakening the precommitted gate.
3. Update durable evidence with the exact-head 4B result.
4. If the gate passes, return PR #1 to ready and run exact-head integration preflight.
