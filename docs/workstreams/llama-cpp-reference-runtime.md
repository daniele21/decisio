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
- no shared-prefix optimization before fresh llama.cpp scoring is correctness-stable.

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
- future shared-prefix execution must be compared against the fresh reference path.

## Execution DAG

| ID | State | Outcome | Owns / writes | Depends on |
| --- | --- | --- | --- | --- |
| W0 | DONE | Stop treating Transformers/BF16 as promotion authority; reshape product truth. | product/architecture/roadmap/current-state/gate status | — |
| W1 | READY | Prove all four scorer paths on exact Q4_K_M through in-process llama.cpp. | llama.cpp spike + focused backend tests + 8-case smoke | W0 |
| W2 | BLOCKED | Stable `LlamaCppBackend` + local-GGUF CLI; remove Transformers from reference path. | `src/decisio/backends/**`, CLI, packaging, tests | W1 |
| W3 | BLOCKED | Freeze scorer-gate v2 runtime/artifact contract before representative results. | benchmark contract/evaluator/workflow metadata | W1, W2 |
| W4 | BLOCKED | Full 64-case CPU evidence and semantic-v2 decision. | remote workflow/artifacts/current-state | W3 |
| W5 | BLOCKED | Stabilize public local runtime only if scorer survives. | public API/README/usage | W4 PASS |
| W6 | BLOCKED | Shared state/question reuse with fresh-path equivalence. | runtime optimization + equivalence benchmark | W4 |

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

## W3/W4 scorer gate

Keep the frozen 64-case workload unless W1 finds a genuine fixture defect. Before the representative run, freeze:

- exact GGUF SHA-256 and Q4_K_M identity;
- pinned llama.cpp/binding build;
- CPU-only execution and exact Decisio commit;
- semantic-v2, semantic-v1, letters and generated JSON;
- normal and reversed candidate order;
- one warm-up plus four position-balanced measured rounds;
- quality, family, order-robustness, zero-generation and generation-latency criteria.

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
