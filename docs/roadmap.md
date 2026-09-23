# Implementation roadmap

Status: active  
Owner: repository

## Objective

Build the smallest system that can test Decisio's central thesis:

> A general-purpose open-weight LLM can act as a useful probabilistic decision engine without answer generation or mandatory training, and semantic candidate scoring can improve the decision-specific trade-off over arbitrary answer-token scoring.

Implementation order must optimize for learning. Performance engineering that does not help answer this question should wait.

## Milestone 0 — Reproducible decision laboratory

**Implementation status:** the pinned Qwen3.5-2B Q4_K_M GGUF + llama.cpp reference runtime, scorer/compiler core, zero-generation readouts and runtime evidence tooling are implemented. The general short/fresh semantic-v2 gate has completed and failed; repeated-state scope is being tested separately.

Goal: establish a trustworthy baseline before building a service.

Features:

- Python package managed with `uv`;
- pinned Qwen 3.5 2B Q4_K_M GGUF artifact SHA-256;
- pinned llama.cpp runtime/build identity with an in-process backend and CPU scorer-gate execution;
- deterministic request/compiler representation;
- direct A/B/C answer-token scorer baseline;
- comparative semantic candidate Yes/No log-odds scorer;
- original independent semantic scorer retained as a baseline;
- shared-context candidate branching with fresh-path equivalence;
- bounded repeated-state context reuse for many questions over one state;
- JSONL benchmark input/output;
- provenance: model revision, tokenizer, prompt/compiler hash, scorer version, precision, backend;
- frozen smoke/evaluation fixtures;
- metrics for quality, latency, logical/physically-evaluated tokens, context reuse and token generation.

Exit evidence:

- both scorers run end-to-end on the same fixtures;
- generated answer tokens are zero;
- results are reproducible within documented numerical tolerance;
- shared execution matches fresh choices and reports score deltas;
- repeated-state workloads show measurable prefill/token reduction;
- first comparison report exists.

## Milestone 1 — Decide whether semantic scoring wins

**Harness status:** generated JSON, direct A/B/C logits, candidate-order reversal, comparative semantic v2, independent semantic v1 and real-model llama.cpp execution are implemented. Scorer-gate v2 failed for semantic v2 as a short/fresh general default; repeated-state gate v3 is the active precommitted experiment.

Goal: validate the core differentiator before investing in infrastructure.

Evaluation dimensions:

- balanced accuracy / task-appropriate accuracy;
- NLL and Brier-style metrics where labels make them meaningful;
- option-order reversal;
- option-description paraphrase/wrapping;
- irrelevant context;
- missing evidence;
- candidate-count scaling;
- prompt/verbalizer sensitivity;
- comparison with minimal autoregressive structured output.

Required experiment variants:

- direct answer-token scoring;
- comparative candidate binary log-odds (v2);
- independent candidate binary log-odds (v1 baseline);
- candidate likelihood baseline if useful;
- minimal generated structured answer.

Decision gate:

- scorer-gate v2 is already FAIL for semantic v2 as a short/fresh general-purpose default;
- repeated-state gate v3 may support only a narrower semantic-v2 scope if its frozen criteria pass;
- direct A/B/C logits remain available as a measured zero-generation alternative, including for
  latency-oriented examples such as Snake;
- no scorer becomes a universal default without scope-specific evidence.

## Milestone 2 — Answerability

Goal: make "cannot answer from the supplied evidence" first-class.

Features:

- independent answerability binary scorer;
- output schema separating answerability from choice distribution;
- missing/contradictory/irrelevant evidence fixtures;
- configurable downstream threshold policy without pretending the threshold is universally calibrated;
- metrics for answerability discrimination and selective accuracy/coverage.

Exit evidence:

- answerability adds useful signal beyond top candidate probability;
- false-confident decisions are measurable and documented.

## Milestone 3 — Scale shared execution

Core shared context-state reuse is now a Milestone-0 requirement. This milestone scales the proven
mechanism rather than introducing it for the first time.

Features:

- larger multi-question batches over one state;
- cache pressure/eviction and lifecycle tuning;
- broader context-length/candidate-count scaling;
- peak memory and throughput optimization;
- bounded batch/context/cache configuration.

Exit evidence:

- speedup persists at representative scale;
- cache/resource bounds hold under pressure;
- no silent correctness trade-off is hidden behind a performance headline.

## Milestone 4 — Stable developer API

Goal: make the proven inference path usable as a library/service.

Features:

- typed Python API;
- CLI;
- HTTP API;
- `boolean` and `choice` schemas;
- multi-question request;
- batch request;
- explicit scorer/probability status;
- timings and provenance;
- strict validation / no silent truncation;
- deterministic error model.

Indicative request:

```json
{
  "state": "Customer cannot access an account after a password reset.",
  "questions": {
    "route": {
      "type": "choice",
      "instruction": "Which queue should handle this request?",
      "candidates": [
        {"id": "access", "description": "Account access support"},
        {"id": "billing", "description": "Billing support"}
      ],
      "answerability": true
    }
  }
}
```

## Milestone 5 — Additional runtime portability

Goal: broaden beyond the proven llama.cpp/Q4_K_M reference path after semantics stabilize.

Features:

- additional GGUF quantizations such as Q8 where quality evidence justifies them;
- optional Metal/other llama.cpp device acceleration outside the CPU scientific gate;
- optional non-llama.cpp adapters only when they add user value;
- cross-runtime/quantization equivalence diagnostics;
- model capability registry;
- memory guards.

Do not claim backend/quantization equivalence without measurements.

## Milestone 6 — Calibration layer

Goal: optionally convert useful scores into workload-validated probabilities.

Possible features:

- temperature scaling;
- calibration artifact bound to model + scorer + prompt/compiler + backend/precision;
- held-out fitting only;
- ECE / reliability diagrams / Brier / NLL reports;
- rejection if calibration identity does not match runtime identity.

Calibration is optional and task-specific. Raw Decisio must remain usable without it.

## Milestone 7 — Additional decision primitives

Only after boolean/choice are strong:

- ordinal scores;
- numeric anchors/distributions;
- ranking/top-k;
- multi-label.

Each primitive needs its own semantics and benchmark. Avoid a "everything is choice" abstraction if it creates misleading probabilities.

## Milestone 8 — Optional training track

Training remains outside the core until evidence justifies it.

Potential later experiments:

- LoRA decision tuning;
- learned candidate scorer;
- explicit answerability/abstention training;
- soft-label distillation;
- calibration-aware objectives.

Training should remain optional unless the project intentionally changes its mission.

## Feature priority

### Must have for v1

- Qwen 3.5 2B Q4_K_M GGUF reference support through llama.cpp;
- semantic candidate scorer;
- direct-logit baseline;
- answerability;
- zero-generation invariant;
- boolean + choice;
- shared candidate/question execution;
- typed results;
- provenance;
- reproducible benchmark suite;
- CPU llama.cpp reference runtime for the scorer decision gate;
- CLI/library API.

### Should have after evidence

- HTTP API;
- additional runtimes such as MLX;
- additional quantizations beyond the reference Q4_K_M;
- post-hoc calibration;
- batching controls;
- result audit/debug mode.

### Not v1

- fine-tuning;
- hosted SaaS;
- stable product UI/playground (the local Snake UI under `examples/` is an explanatory demo, not a product surface);
- multimodal;
- workflow engine;
- arbitrary structured generation;
- numeric/ordinal types without dedicated validation.

## Benchmark suite design

The benchmark suite should contain both external/public evaluation sources where licensing allows and an owned frozen dataset designed around Decisio's failure modes.

Required owned families:

- obvious boolean entailment;
- nuanced routing;
- rule application;
- competing plausible candidates;
- missing evidence;
- contradictory evidence;
- irrelevant context;
- option reversal;
- candidate paraphrase;
- long shared state / many questions;
- growing candidate count.

Systems measurements:

- end-to-end latency;
- decisions/second;
- first decision latency;
- peak process RSS for the CPU gate;
- logical input tokens;
- physically evaluated tokens;
- generated tokens;
- scaling by state length, question count and candidate count.

## v1 release claim

The first public release should be able to make a narrow, defensible claim:

> Decisio is a training-free, zero-generation decision layer for open causal LLMs. It scores runtime-defined semantic candidates directly, separates answerability from candidate preference, and reuses shared context for efficient typed decisions.

Any stronger claim must be supported by the committed benchmark evidence.
