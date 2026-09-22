# llama.cpp reference runtime migration

Status: ACTIVE  
Owner: repository  
Convergence branch: `product/define-decisio-foundation`  
Pull request: #1  
Last shaped: 2026-09-22

## Axes

- PRODUCT: `PRODUCT_STRATEGIC`
- DELIVERY: `ITERATION` until the new gate is proven; then `INTEGRATION`
- VALIDATION: `STRONG`
- EXECUTION: `AGENT_LOCAL` for deterministic work plus `REMOTE_AUTOMATED` for the pinned Linux CPU gate

## Goal

Make GGUF + llama.cpp the canonical Decisio v1 runtime so scorer selection is performed on the same runtime/artifact class users run locally.

Reference target: Qwen3.5-4B Q4_K_M GGUF on CPU. Freeze the exact GGUF SHA-256 and llama.cpp/binding build identity before representative scorer evidence.

## Product intent

- **User:** engineers using local open-weight models for bounded semantic decisions.
- **Problem:** current scorer evidence is BF16/Transformers while the intended product runtime is GGUF/llama.cpp.
- **Outcome:** point Decisio at a local compatible GGUF and obtain typed zero-generation decisions with reproducible evidence.
- **Decision:** `BUILD`; llama.cpp/GGUF becomes the v1 reference path, not an optional later adapter.

## Non-goals

- no HTTP/server transport in this migration;
- no broad model/backend/quantization matrix before the reference path is proven;
- no claim that Q4_K_M is equivalent to BF16;
- no calibrated-probability claim without a matching calibration artifact;
- no Metal/CUDA performance gate; representative scorer evidence remains CPU-only;
- no shared fast path is trusted without fresh-path equivalence evidence; fresh evaluation remains the correctness oracle.

## Risks and assumptions

| Item | Level | Consequence / next evidence |
| --- | --- | --- |
| VALUE | LOW | Directly aligns with the local/open product promise. |
| USABILITY | MEDIUM | Local paths/builds need explicit CLI and provenance. |
| FEASIBILITY | HIGH | W1 must prove Qwen3.5 tokenizer, logits and generation through llama.cpp. |
| VIABILITY | MEDIUM | Pin runtime/build identity; never depend on `latest`. |
| A1 llama.cpp exposes required scorer primitives | HIGH | If not, use the smallest direct libllama bridge. |
| A2 `llama-cpp-python` is sufficient in-process | HIGH | Prove in W1; do not fall back to HTTP merely for logits. |
| A3 Q4_K_M preserves enough scorer quality | HIGH | Decide only with the frozen 64-case gate; never lower thresholds post-result. |
| A4 calibration remains possible | MEDIUM | Preserve exact runtime identity; validate in a later milestone. |

## Technical invariants

- native scorers generate zero answer tokens;
- deterministic/domain constraints filter impossible candidates before scoring;
- scorer/compiler semantics stay backend-independent;
- backend exposes exact tokenizer IDs and required next-token logits;
- no silent truncation; candidate IDs stay order-independent;
- Q4_K_M is never described as BF16-equivalent;
- semantic results keep candidate-local YES/NO `binary_conditional_probability` separate from cross-candidate `distribution`; both remain uncalibrated unless a matching calibration artifact is active;
- evidence records GGUF SHA, quantization, llama.cpp/binding build, model metadata, CPU/threads and material context/batch settings;
- performance claims stay bound to the recorded host/runtime;
- shared execution reuses full model context state, not a KV-only assumption: Qwen3.5 hybrid recurrent state is part of the cache contract;
- shared execution falls back to fresh evaluation when an exact safe reuse boundary cannot be proven;
- reusable state is bounded and explicitly resettable; no unbounded cache growth;
- every shared-path choice and score delta is compared against fresh evaluation before promotion.

## Execution DAG

| ID | State | Outcome | Owns / writes | Depends on |
| --- | --- | --- | --- | --- |
| W0 | DONE | Stop treating Transformers/BF16 as promotion authority; reshape product truth. | product/architecture/roadmap/current-state/gate status | — |
| W1 | ACTIVE | Prove all four scorer paths on pinned Q4_K_M through in-process llama.cpp. | backend + real-model smoke | W0 |
| W2 | ACTIVE | Stable `LlamaCppBackend` + local-GGUF CLI implemented; real-runtime validation pending. | `src/decisio/backends/**`, CLI, packaging, tests | W1 evidence |
| W3 | ACTIVE | Candidate branching implemented; repeated-state cache + real fresh equivalence pending. | llama.cpp runtime, cache lifecycle, equivalence/perf tests | W2 |
| W4 | BLOCKED | Freeze scorer-gate v2 runtime/artifact contract with shared execution as the production path. | benchmark contract/evaluator/workflow metadata | W3 |
| W5 | BLOCKED | Full 64-case CPU evidence and semantic-v2 decision plus repeated-state speed evidence. | remote workflow/artifacts/current-state | W4 |
| W6 | BLOCKED | Stabilize public local runtime only if scorer and fast path survive. | public API/README/usage | W5 PASS |

## W1 compatibility spike

Use one exact local Qwen3.5-4B Q4_K_M GGUF and prove:

1. artifact SHA-256 and runtime/model metadata are captured;
2. tokenizer IDs come from the GGUF/runtime tokenizer;
3. semantic-v2/v1 read YES/NO logits and preserve their binary softmax as candidate-local support;
4. letters reads candidate-slot logits;
5. generated JSON uses the same loaded model/runtime;
6. repeated identical inputs are deterministic within documented tolerance;
7. the 8-case CPU scorer matrix completes;
8. wall-clock timing and process RSS can be recorded.

If `llama-cpp-python` cannot provide these primitives cleanly, W1 may choose a small direct libllama bridge. The llama.cpp product decision remains unchanged.

## W2 backend contract

Target flow:

```text
ChoiceRequest
 -> compiler
 -> scorer
 -> LlamaCppBackend
 -> local GGUF
 -> logits / generated baseline
 -> DecisionResult
```

The backend exposes only required capabilities. Scorers never import llama.cpp directly. Runtime knobs use conservative defaults and are recorded in provenance.

Reference CLI shape:

```bash
decisio compare \
  --input .artifacts/scorer-gate-v2.jsonl \
  --output-dir .artifacts/scorer-gate-v2 \
  --model /absolute/path/Qwen3.5-4B-Q4_K_M.gguf \
  --device cpu \
  --warmup-rounds 1 \
  --performance-rounds 4
```

## W3 shared context-state reuse

This is a v1 requirement, not a post-gate optimization.

### Korgis reference patterns

Korgis remains the control-plane/lifecycle reference: llama.cpp owns native model memory, while
Decisio owns scorer-specific reuse semantics and equivalence evidence. Reuse Korgis' pinned runtime
identity, explicit close/lease and fail-conservative ownership patterns; do not duplicate its
residency, serving-concurrency, eviction or resource-manager policy here.

For Decisio branching, use llama.cpp generic memory/sequence primitives in-process rather than an
HTTP prompt-cache abstraction. Fresh evaluation remains the scorer oracle.

Two reuse levels are required:

1. **candidate branching:** evaluate the exact common token prefix of semantic candidate prompts once,
   then branch model state for each candidate suffix;
2. **repeated-state reuse:** retain a bounded reusable state prefix across calls so many questions over
   the same long state do not re-prefill that state from scratch.

For Qwen3.5, the cache contract is **model context state**, not merely KV tensors. llama.cpp sequence
state/memory must preserve the hybrid attention + recurrent state required for exact continuation.

Acceptance:

- shared path and fresh path produce the same choice on the equivalence fixture;
- score and `binary_conditional_probability` deltas stay within a predeclared tolerance;
- changed rows/argmaxes are reported, never hidden;
- unsupported/unsafe prefix reuse falls back to fresh evaluation;
- cache entries are bounded and can be cleared deterministically;
- instrumentation reports logical input tokens, physically evaluated tokens, prefix reuse/hit rate
  and wall-clock latency;
- a long-state/many-question fixture demonstrates measurable physical-token and latency reduction.

The scorer prefers `shared_prefix_batch_next_token_logits(...)`. The llama.cpp backend now
implements candidate branching with a dedicated multi-sequence scoring context that shares the
loaded model weights with the generation context. It builds the same flat logical batch shape used
by llama.cpp's multiple-choice/HellaSwag path: common-prefix token rows belong to every candidate
sequence, followed by each candidate suffix on its own sequence. Decoding is split only at
`n_batch` boundaries, so hybrid recurrent rollback/snapshot handling stays inside llama.cpp rather
than being reconstructed by Decisio. No KV-only sequence copying is used.

Run `35715986281` proved that merely attaching the prefix to all sequences while decoding suffixes
in separate calls still reproduced the old numerical mismatch, despite 40.4% physical-token reuse.
Run `35716601748` then reproduced the exact same mismatch with the upstream-shaped flat batch:
score delta `0.1005306244`, binary-probability delta `0.0170685730`, and final-distribution delta
`0.0001724743`. The predeclared fresh-equivalence tolerances remain unchanged.

Run `35716946549` isolated the cause: a single sequence decoded fresh versus the same sequence
split at common-prefix token 152 produced exactly identical YES/NO logits for both candidates
(max absolute logit delta `0.0`). The mismatch therefore comes from multi-sequence sharing, not
from the prefix/suffix decode boundary.

The candidate primitive is now llama.cpp single-sequence state snapshot/restore. Decisio prefills
the common prefix once on sequence 0, captures the complete sequence memory with
`llama_state_seq_get_data`, then restores it with `llama_state_seq_set_data` before each later
candidate suffix. This follows llama.cpp's own save/load-state test pattern while avoiding the
multi-sequence hybrid path that failed the fresh oracle.

The remaining W3 work is exact fresh-equivalence evidence for this sequence-state primitive plus a
bounded checkpoint/cache boundary for reusing an unchanged long state across later questions.

## W4/W5 scorer gate

Keep the frozen 64-case workload unless W1 finds a genuine fixture defect. Before the representative run, freeze:

- exact GGUF SHA-256 and Q4_K_M identity;
- pinned llama.cpp/binding build;
- CPU-only execution and exact Decisio commit;
- semantic-v2, semantic-v1, letters and generated JSON;
- normal and reversed candidate order;
- one warm-up plus four position-balanced measured rounds;
- semantic scorer measurements use the production shared-context path after equivalence passes;
- a fresh semantic reference run remains available for changed-row diagnostics;
- quality, family, order-robustness, zero-generation and generation-latency criteria;
- repeated-state evidence records physical-token reduction, cache hit/reuse rate and latency speedup.

Existing promotion thresholds remain the starting contract. Any change requires pre-result justification and explicit gate versioning. Peak RSS is diagnostic only.

A PASS promotes v2 only for the pinned reference configuration. A FAIL keeps v2 experimental; inspect discordant rows and, if useful, compare a higher-fidelity GGUF before changing scorer semantics.

## Calibration compatibility

GGUF/llama.cpp does not remove calibration. A future artifact must bind at least GGUF SHA, quantization, scorer/compiler/verbalizers, llama.cpp build, calibration method and calibration-dataset identity. Without that match, results stay uncalibrated.

## Success

**Acceptance:** Q4_K_M loads through llama.cpp without Torch/Transformers; all four scorers share the backend; native paths generate zero tokens; full provenance is recorded; the 64-case gate evaluates automatically.

**Outcome:** everyday local inference and scorer-selection evidence use the same runtime/artifact class.

**Product impact:** unknown until real workloads; success requires competitive decision quality/robustness with materially lower local deployment friction/resource cost.

## Validation and handoff

Before PR #1 returns to ready:

1. inspect the complete diff against live `main`;
2. run repository deterministic gates and package/install checks;
3. run exact-head integration preflight;
4. run the full pinned llama.cpp/GGUF CPU scorer gate;
5. apply the committed evaluator without weakening failures;
6. update `docs/current-state.md` with exact evidence.

The existing Transformers/BF16 gate is historical/directional only after W0.

At completion, transfer durable truth to product/architecture/roadmap, `benchmarks/`, README/USAGE and code/tests, then delete this workstream by default.
