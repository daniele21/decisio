# llama.cpp reference runtime migration

Status: ACTIVE  
Owner: repository  
Convergence branch: `product/define-decisio-foundation`  
Pull request: #1  
Last shaped: 2026-09-22

## Axes

- PRODUCT: `PRODUCT_STRATEGIC`
- DELIVERY: `ITERATION` until the runtime gate is proven
- VALIDATION: `STRONG`
- EXECUTION: `AGENT_LOCAL` plus `REMOTE_AUTOMATED` for pinned CPU evidence

## Goal

Make local GGUF + llama.cpp the canonical Decisio v1 runtime, then decide the scorer on the same
artifact/runtime class users run.

Reference target: Qwen3.5-4B Q4_K_M on CPU. Exact GGUF SHA, runtime build and host identity are
frozen before representative evidence.

## Product intent

- **User:** engineers building bounded local semantic decisions.
- **Problem:** earlier scorer evidence used BF16/Transformers, not the intended GGUF runtime.
- **Outcome:** point Decisio at a compatible local GGUF and obtain typed zero-generation decisions
  with reproducible provenance and shared-state execution.
- **Decision:** BUILD.

## Non-goals

- no HTTP/server transport here;
- no broad backend/quantization matrix before the reference path is proven;
- no Q4_K_M/BF16 equivalence claim;
- no calibrated-probability claim without a matching calibration artifact;
- no Metal/CUDA promotion gate;
- no fast path without a fresh-path oracle.

## Technical invariants

- native scorers generate zero answer tokens;
- deterministic invalid candidates are removed before model scoring;
- scorer/compiler semantics stay backend-independent;
- no silent truncation; candidate IDs remain presentation-order independent;
- semantic YES/NO support and cross-candidate distribution remain distinct and uncalibrated;
- evidence records GGUF SHA, quantization, binding/runtime, model metadata and material CPU/context settings;
- shared execution reuses complete model context state, not a KV-only assumption;
- unsafe or unproven reuse falls back to fresh/shared-prefix evaluation;
- repeated state is bounded by entries and serialized bytes and is explicitly clearable;
- every optimized path is compared with fresh evaluation before promotion.

## Execution DAG

| ID | State | Outcome |
| --- | --- | --- |
| W0 | DONE | Transformers/BF16 no longer controls promotion. |
| W1 | ACTIVE | Prove scorer primitives on pinned Q4_K_M llama.cpp. |
| W2 | ACTIVE | Stabilize local-GGUF backend/CLI and provenance. |
| W3 | ACTIVE | Prove candidate branching + bounded repeated-state reuse. |
| W4 | BLOCKED | Freeze scorer-gate v2 runtime/artifact/fast-path identity. |
| W5 | BLOCKED | Run full 64-case CPU gate plus repeated-state performance evidence. |
| W6 | BLOCKED | Stabilize public runtime only if the evidence survives. |

## W1/W2 runtime contract

```text
ChoiceRequest
 -> deterministic compiler
 -> scorer
 -> LlamaCppBackend
 -> local GGUF
 -> requested logits / generated baseline
 -> DecisionResult
```

The backend owns llama.cpp details; scorers never import llama.cpp. W1/W2 must prove tokenizer/chat
template, YES/NO and letter logits, generated JSON baseline, deterministic repeatability, timing/RSS
and exact artifact/runtime provenance.

If `llama-cpp-python` cannot expose a required primitive cleanly, use the smallest direct libllama
bridge rather than changing the product boundary.

## W3 shared context-state reuse

Shared execution is a v1 requirement because repeated CPU prefill can dominate latency.

Two levels are required:

1. **candidate branching:** common candidate prefix is evaluated once, then each candidate suffix
   continues from the same complete sequence state;
2. **repeated-state reuse:** later questions over identical serialized state restore a bounded cached
   state prefix instead of repeating that prefill.

Korgis remains a lifecycle reference only: reuse its explicit ownership/close and conservative
resource patterns, but do not copy serving concurrency, residency or eviction responsibilities into
Decisio.

### Evidence so far

The original multi-sequence approaches were rejected without loosening thresholds:

- run `35715986281`: prefix attached to all sequences still produced score delta
  `0.1005306244` despite 40.4% physical-token reuse;
- run `35716601748`: upstream-shaped flat multiple-choice batching produced the same mismatch;
- run `35716946549`: one sequence split at the same 152-token prefix matched fresh logits exactly
  (max delta `0.0`).

The replacement primitive uses `llama_state_seq_get_data` / `llama_state_seq_set_data` on one
canonical sequence. Run `35717350247` passed the fresh oracle on pinned Qwen3.5-0.8B Q4_K_M:

- same choice;
- max score, binary-probability and distribution delta: `0.0`;
- logical tokens: 376;
- physical tokens: 224;
- reuse: 152 tokens / 40.4%;
- serialized prefix state: 22,072,908 bytes.

This proves the branching mechanism, not the representative 4B product result.

### Repeated-state cache contract

Semantic compilers mark a conservative token-safe boundary after serialized state/evidence. The
llama.cpp backend snapshots that exact prefix in an in-memory LRU keyed by exact tokens within the
loaded runtime.

The cache:

- is bounded by both entry count and serialized bytes;
- never guesses a semantic boundary;
- tracks hits, misses, reused tokens, bytes, evictions and state copies;
- can be cleared independently of metrics;
- does not affect the fresh reference view;
- skips storage when one snapshot exceeds the byte budget.

Current defaults are 2 entries and 256 MiB. The real-model gate must prove a same-state,
different-question hit, fresh equivalence, physical-token reduction and deterministic clear
behavior. Latency is recorded; representative 4B speed evidence remains W5.

## W4/W5 scorer gate

Keep the frozen 64-case workload unless a genuine fixture defect is found. Before the representative
run, freeze:

- exact 4B Q4_K_M GGUF SHA and pinned llama.cpp/binding;
- CPU-only execution and exact Decisio revision;
- semantic-v2, semantic-v1, letters and generated JSON;
- normal/reversed candidate order;
- one warm-up plus four position-balanced measured rounds;
- production shared-context path plus fresh diagnostics;
- quality, family, order, zero-generation and latency criteria;
- repeated-state physical-token, hit-rate and latency evidence.

Existing promotion thresholds stay fixed unless a pre-result gate version explicitly changes them.
A PASS promotes only the pinned reference configuration. A FAIL keeps v2 experimental.

## Calibration compatibility

GGUF/llama.cpp does not remove calibration. A future calibration artifact must bind at least GGUF
SHA, quantization, scorer/compiler/verbalizers, llama.cpp build, method and calibration dataset.
Without that match, outputs remain uncalibrated.

## Completion

Before PR #1 returns to ready:

1. prove the repeated-state cache on the pinned real-model smoke;
2. freeze the 4B artifact/runtime/fast-path identity;
3. run the full 64-case CPU gate and repeated-state performance fixture;
4. run repository deterministic gates and exact-head integration preflight;
5. update durable docs with exact evidence;
6. inspect the complete diff against live `main`.

Completion means product intent, implementation, tests, docs and evidence agree. Representative 4B
hardware evidence, not code completion, decides release readiness.
