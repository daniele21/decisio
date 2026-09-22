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

Reference target: Qwen3.5-2B Q4_K_M on CPU. Exact GGUF SHA, runtime build and host identity are
frozen before representative evidence.

## Product intent

- **User:** engineers building bounded local semantic decisions.
- **Problem:** earlier scorer evidence used BF16/Transformers, not the intended GGUF runtime.
- **Outcome:** point Decisio at a compatible local GGUF and obtain typed zero-generation decisions
  with reproducible provenance and shared-state execution.
- **Decision:** BUILD.
- **Reference-model decision:** use Qwen3.5-2B Q4_K_M as the canonical CPU evidence artifact so
  the local-first workflow is materially easier to run; larger compatible GGUFs remain supported as
  separate evidence identities.
- **Risks:** VALUE `LOW`; USABILITY `LOW`; FEASIBILITY `MEDIUM` because the smaller model may change
  scorer quality and therefore still must pass the unchanged frozen gate; VIABILITY `LOW` because
  the smaller artifact lowers the hardware/memory burden.

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
| W1 | DONE | Scorer primitives proven on pinned real Q4_K_M llama.cpp smoke. |
| W2 | DONE | Local-GGUF backend/CLI and provenance stabilized. |
| W3 | DONE | Candidate branching + bounded repeated-state reuse proved fresh-equivalent on pinned 0.8B smoke. |
| W4 | DONE | Scorer-gate v2 runtime/artifact/fast-path identity frozen before 2B results. |
| W5 | ACTIVE | Run full 64-case 2B CPU gate plus representative runtime-equivalence evidence. |
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

Run `35726724805` additionally proved the bounded cache after native-batch alignment: on a long same-state/different-question request it matched fresh scores/probabilities/distribution exactly, reused 1024 cached-state tokens, evaluated 526 physical tokens versus 2574 fresh, and observed 7.05 s versus 32.24 s latency (~4.57x). Cache clear returned entries/bytes to zero.

These runs prove the branching/cache mechanism on 0.8B, not the representative 2B product result.

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

Current defaults are 2 entries and 256 MiB. The pinned 0.8B real-model smoke has proved a same-state, different-question hit, fresh equivalence, physical-token reduction and deterministic clear behavior. W5 repeats the oracle on the frozen 2B reference artifact. Latency is recorded; the v2 contract deliberately does not invent a 2B cache-speed threshold from the 0.8B observation.

## W4/W5 scorer gate

The gate-v2 contract was re-frozen for the 2B reference before any 2B scorer-matrix result was
accepted. The earlier 4B runtime oracle only informed the native-batch-safe cache invariant; it does
not authorize the 2B scorer decision. The frozen 64-case workload and all promotion thresholds are
unchanged:

- artifact: `unsloth/Qwen3.5-2B-GGUF`;
- revision: `1c466474d208da1a7c4b8cb87ebcdac78f160e34`;
- file: `Qwen3.5-2B-Q4_K_M.gguf`;
- file SHA-256: `aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223`;
- binding/runtime package: `llama-cpp-python==0.3.35`, CPU;
- context/batching: `n_ctx=8192`, `n_batch=512`, `n_ubatch=512`, two scoring threads and two batch threads;
- shared-state primitive: single-sequence state snapshot/restore;
- repeated-state cache: exact compiler token-prefix LRU, 2 entries / 256 MiB;
- full frozen 64-case workload, original + reversed candidates;
- one warm-up plus four position-balanced measured rounds;
- full-workload shared-vs-fresh oracle and long repeated-state cache oracle;
- unchanged quality, family, order, zero-generation and generated-latency criteria.

The reference artifact is evidence identity, not a product restriction: users may select another compatible Qwen GGUF, but its results are a different evidence/calibration identity.

A PASS promotes only the pinned reference configuration. A FAIL keeps v2 experimental.

## Calibration compatibility

GGUF/llama.cpp does not remove calibration. A future calibration artifact must bind at least GGUF
SHA, quantization, scorer/compiler/verbalizers, llama.cpp build, method and calibration dataset.
Without that match, outputs remain uncalibrated.

## Completion

Before PR #1 returns to ready:

1. run the frozen 2B scorer-gate v2 and representative shared/fresh + repeated-cache oracle;
2. diagnose any failed criterion without weakening the precommitted contract;
3. update durable docs with exact 2B evidence;
4. run repository deterministic gates and exact-head integration preflight;
5. inspect the complete diff against live `main`.

Completion means product intent, implementation, tests, docs and evidence agree. Representative 2B
hardware evidence, not code completion, decides release readiness.
