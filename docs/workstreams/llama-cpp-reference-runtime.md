# llama.cpp reference runtime migration

Status: ACTIVE  
Owner: repository  
Convergence branch: `product/define-decisio-foundation`  
Pull request: #1  
Last shaped: 2026-09-22

## Axes

- PRODUCT: `PRODUCT_STRATEGIC`
- DELIVERY: `ITERATION` until the new reference gate is proven; then `INTEGRATION`
- VALIDATION: `STRONG`
- EXECUTION: `AGENT_LOCAL` for deterministic code/tests plus `REMOTE_AUTOMATED` for the pinned Linux CPU evidence run

## Goal

Make GGUF + llama.cpp the canonical Decisio v1 inference path so the scorer decision is made on
the runtime and model artifact users are expected to run locally.

The first reference target is Qwen3.5-4B in Q4_K_M GGUF form on CPU. The exact GGUF artifact
SHA-256 and llama.cpp/binding build identity must be frozen before the full scorer gate.

## Product intent

**User / consumer:** AI/application engineers who want bounded semantic decisions from a local
open-weight model without a PyTorch/Transformers deployment stack.

**Problem / job:** Decisio currently evaluates its core scorer on a BF16 Transformers path even
though the intended local product workflow is a compact GGUF/llama.cpp runtime. That makes the
scientific gate and the product runtime diverge.

**Desired outcome:** a user can point Decisio at a local compatible GGUF, obtain zero-generation
typed decisions, and reproduce scorer evidence using the same llama.cpp execution model.

**Why it matters:** scorer quality, order robustness, latency and memory can change with runtime
and quantization. The stable scorer must therefore be selected on the runtime/artifact class that
defines the product.

**Non-goals:**

- no HTTP/server transport in this migration;
- no broad model/backend matrix before the Qwen3.5-4B reference path is proven;
- no claim that Q4_K_M is numerically equivalent to BF16;
- no calibrated-probability claim without a calibration artifact fitted for the exact runtime
  identity;
- no Metal/CUDA performance gate; the scientific reference gate remains CPU-only;
- no shared-prefix optimization before fresh llama.cpp scoring is correctness-stable.

## Product risks

| Risk | Level | Reason / mitigation |
| --- | --- | --- |
| VALUE | LOW | GGUF/llama.cpp aligns directly with the local/open product promise. |
| USABILITY | MEDIUM | Local model paths/build variants can be confusing; CLI and provenance must make the active artifact explicit. |
| FEASIBILITY | HIGH | Decisio needs reliable next-token logits, tokenizer/readout verification and generated-baseline support for Qwen3.5 through llama.cpp bindings. Prove this first. |
| VIABILITY | MEDIUM | llama.cpp moves quickly; exact runtime/build and binding identity must be pinned and recorded rather than relying on `latest`. |

## Material assumptions

### A1 — llama.cpp exposes the scorer primitives Decisio needs

If wrong: the reference-runtime choice cannot support semantic-v2/v1/letters without a custom
low-level bridge.

Evidence: llama.cpp provides batched decode/logit primitives; repository-specific Qwen3.5 behavior
is not yet proven in Decisio.

Next evidence: W1 compatibility spike on the exact Qwen3.5-4B Q4_K_M artifact.

### A2 — `llama-cpp-python` is a sufficient in-process bridge

If wrong: use the smallest direct libllama/C-ABI bridge that preserves the same backend contract.
Do not fall back to a server/HTTP dependency merely to obtain logits.

Evidence: not yet proven against Decisio's required low-level semantics.

Next evidence: W1.

### A3 — Q4_K_M preserves enough scorer quality for the product gate

If wrong: keep llama.cpp but choose a higher-fidelity GGUF quantization or narrow the supported
reference artifact. Do not lower scorer thresholds after seeing the result.

Evidence: none yet on the frozen 64-case gate.

Next evidence: W3/W4.

### A4 — calibration remains available

If wrong: probability semantics would need to stay explicitly uncalibrated.

Evidence: calibration is post-hoc over Decisio scores and does not require Transformers, but it
must be fitted and validated for the exact GGUF/scorer/compiler/runtime identity.

Next evidence: later calibration milestone; this migration only preserves the identity contract.

## Technical invariants

- native Decisio scoring generates zero answer tokens;
- deterministic/domain constraints filter impossible candidates before model scoring;
- scorer/compiler semantics remain backend-independent;
- the backend exposes exact tokenizer IDs and next-token logits required by each scorer;
- no silent prompt/input truncation;
- candidate IDs remain independent from presentation order;
- Q4_K_M results are never described as BF16-equivalent;
- conditional score distributions remain labeled uncalibrated unless a matching calibration
  artifact is active;
- benchmark provenance includes GGUF SHA-256, quantization, llama.cpp build/version, binding
  version, tokenizer/model metadata, CPU identity, thread count and relevant context/batch settings;
- performance claims are bound to the exact recorded host/runtime identity;
- a future shared-prefix path must be compared against the fresh reference path and report changed
  choices/scores.

## Execution DAG

| ID | State | Outcome | Owns / writes | Depends on | Validation |
| --- | --- | --- | --- | --- | --- |
| W0 | DONE | Stop treating the Transformers/BF16 run as the scorer-promotion authority and reshape product truth around llama.cpp/GGUF. | product/architecture/roadmap/current-state, scorer-gate status, PR state | — | docs/governance checks |
| W1 | READY | Prove the exact Qwen3.5-4B Q4_K_M GGUF can run all four Decisio scorer paths through in-process llama.cpp semantics. | experimental llama.cpp backend, focused backend tests, 8-case smoke | W0 | load/tokenize/logits/generation/determinism smoke |
| W2 | BLOCKED | Replace the Transformers reference backend with a stable llama.cpp backend contract and local-GGUF CLI path. | `src/decisio/backends/**`, CLI, packaging/lock, backend tests | W1 | unit + package/install + 8-case matrix |
| W3 | BLOCKED | Freeze scorer-gate v2 for GGUF/llama.cpp without post-result threshold tuning. | benchmark contract/evaluator/workflow metadata | W1, W2 | fixture SHA, artifact SHA, provenance contract, evaluator tests |
| W4 | BLOCKED | Produce the full 64-case CPU evidence on pinned Q4_K_M + llama.cpp and decide semantic v2. | remote CPU workflow/artifacts, current-state result | W3 | normal/reversed matrix, 4 balanced perf rounds, gate PASS/FAIL |
| W5 | BLOCKED | Stabilize the public local runtime only if the scorer survives the new gate. | public API/README/usage and removal of obsolete Transformers path | W4 PASS | STRONG preflight + exact-head CI |
| W6 | BLOCKED | Investigate shared state/question reuse using llama.cpp sequence/cache primitives after fresh-path semantics are stable. | runtime optimization + equivalence benchmark | W4 | fresh-vs-shared changed-row report + performance evidence |

### W1 — compatibility spike

The spike must use one exact local Qwen3.5-4B Q4_K_M GGUF and prove:

1. artifact SHA-256 can be captured and reported;
2. tokenizer IDs come from the GGUF/runtime tokenizer rather than Transformers assets;
3. semantic-v2 and semantic-v1 can read the required YES/NO next-token logits;
4. letters can read candidate-slot logits;
5. generated JSON baseline can use the same loaded model/runtime;
6. repeated identical inputs are deterministic within the documented numerical tolerance;
7. the 8-case scorer matrix can complete on CPU;
8. process RSS and wall-clock timing can be collected without pretending they are portable
   hardware claims.

If `llama-cpp-python` cannot satisfy these primitives cleanly, W1 chooses between narrowing the
binding usage and a small direct libllama bridge. It does not change the llama.cpp product decision.

### W2 — backend contract and CLI

Target shape:

```text
ChoiceRequest
  -> deterministic compiler
  -> scorer (semantic-v2 / semantic-v1 / letters / generated)
  -> LlamaCppBackend
  -> local GGUF
  -> logits / generated baseline
  -> DecisionResult
```

The backend contract should expose only capabilities Decisio actually uses. Candidate batching,
cache/sequence controls and generation are explicit capabilities; scorer code must not import
llama.cpp directly.

Expected CLI reference:

```bash
decisio compare \
  --input .artifacts/scorer-gate-v2.jsonl \
  --output-dir .artifacts/scorer-gate-v2 \
  --model /absolute/path/Qwen3.5-4B-Q4_K_M.gguf \
  --device cpu \
  --warmup-rounds 1 \
  --performance-rounds 4
```

Runtime-specific knobs should have conservative defaults and be recorded in provenance. Do not
surface speculative configuration merely because llama.cpp supports it.

### W3 — scorer-gate v2

Keep the existing frozen 64-case workload unless W1 exposes a genuine fixture defect. A runtime
migration is not a reason to change labeled cases.

The new gate freezes before the representative run:

- exact Qwen3.5-4B Q4_K_M GGUF SHA-256;
- pinned llama.cpp/binding identity;
- CPU-only execution;
- exact Decisio commit;
- normal and reversed candidate order;
- semantic-v2, semantic-v1, letters and generated JSON;
- one warm-up plus four position-balanced measured rounds;
- quality, family, order-robustness, zero-generation and generation-latency criteria.

The current promotion thresholds remain the starting contract. Any change must be justified before
the representative result exists and versioned explicitly. Never tune a threshold after observing
the full gate.

Peak RSS remains diagnostic, not a scorer-promotion threshold.

### W4 — representative evidence

The remote workflow must retrieve or otherwise materialize the exact frozen GGUF, verify its SHA,
record host/runtime identity and retain raw rows plus JSON/Markdown reports.

A PASS may promote semantic-v2 only for the pinned Q4_K_M/llama.cpp reference configuration. It is
not evidence of universal generalization, calibration or quantization equivalence.

A FAIL keeps v2 experimental. Diagnose discordant rows and, if needed, compare a higher-fidelity
GGUF quantization before changing scorer semantics or product claims.

## Calibration compatibility

GGUF/llama.cpp does not remove calibration. Decisio calibration remains a later, optional post-hoc
layer over scorer outputs.

Any future calibration artifact must bind at least:

```text
GGUF SHA-256
quantization
scorer identity
compiler/prompt identity
readout verbalizers
llama.cpp runtime/build identity
calibration method
calibration dataset identity
```

Without a matching artifact, results remain `uncalibrated_conditional_scores`.

## Success

### Acceptance

- Decisio loads the frozen Qwen3.5-4B Q4_K_M GGUF through llama.cpp without Torch/Transformers;
- all four scorer paths run through the same backend;
- native scorers generate zero answer tokens;
- local model path and complete runtime provenance are represented explicitly;
- the repository-owned 64-case gate can run and evaluate automatically.

### Outcome

A developer can use the same local GGUF/runtime class for everyday Decisio inference and for the
evidence used to select the default scorer.

### Product impact

The migration is valuable if the Q4_K_M reference path keeps decision quality/robustness competitive
while materially reducing local deployment friction and resource requirements. Product success
remains unknown until real workloads are evaluated.

## Validation and convergence

W1/W2 use the narrowest local tests plus the real 8-case model smoke. W3/W4 require STRONG
validation because they change the reference runtime and scientific evidence contract.

Before PR #1 returns to ready-for-review:

1. inspect the complete diff against live `main`;
2. run repository-owned deterministic gates;
3. run exact-head integration preflight;
4. run the full pinned llama.cpp/GGUF scorer gate;
5. interpret the committed evaluator without weakening failed criteria;
6. update `docs/current-state.md` with exact evidence.

The existing Transformers/BF16 CPU gate is historical/directional only after this workstream
decision and must not authorize merge or scorer promotion.

## Durable handoff

When complete, transfer durable truth to:

- `docs/product.md` — local runtime/product promise;
- `docs/architecture.md` — canonical llama.cpp component boundary;
- `docs/roadmap.md` — completed reference-runtime milestone and remaining prefix/calibration work;
- `benchmarks/` — gate v2 contract and result methodology;
- README/USAGE — supported local workflow;
- code/tests — runtime capabilities and provenance invariants.

Then update `docs/current-state.md` and delete this workstream by default.
