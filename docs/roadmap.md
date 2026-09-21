# Implementation roadmap

Status: proposed  
Owner: repository

## Objective

Build the smallest system that can test Decisio's central thesis:

> A general-purpose open-weight LLM can act as a useful probabilistic decision engine without answer generation or mandatory training, and semantic candidate scoring can improve the decision-specific trade-off over arbitrary answer-token scoring.

Implementation order must optimize for learning. Performance engineering that does not help answer this question should wait.

## Milestone 0 — Reproducible decision laboratory

Goal: establish a trustworthy baseline before building a service.

Features:

- Python package managed with `uv`;
- pinned Qwen 3.5 4B reference revision;
- PyTorch/CUDA reference backend;
- deterministic request/compiler representation;
- direct A/B/C answer-token scorer baseline;
- semantic candidate Yes/No log-odds scorer;
- fresh execution only;
- JSONL benchmark input/output;
- provenance: model revision, tokenizer, prompt/compiler hash, scorer version, precision, backend;
- frozen smoke/evaluation fixtures;
- metrics for quality, latency and token generation.

Exit evidence:

- both scorers run end-to-end on the same fixtures;
- generated answer tokens are zero;
- results are reproducible within documented numerical tolerance;
- first comparison report exists.

## Milestone 1 — Decide whether semantic scoring wins

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
- candidate binary log-odds;
- candidate likelihood baseline if useful;
- minimal generated structured answer.

Decision gate:

- if semantic scoring is not competitive, diagnose why before building a large API/runtime surface;
- if it is competitive and improves robustness or semantics materially, promote it as the default scorer.

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

## Milestone 3 — Shared and parallel execution

Goal: obtain the systems benefit without changing semantics materially.

Features:

- candidate micro-batching;
- shared state/question prefill where supported;
- cache branch/copy abstraction;
- many questions over one state;
- fresh-vs-shared equivalence diagnostics;
- peak memory and throughput metrics;
- bounded batch/context configuration.

Exit evidence:

- measurable speedup on repeated-state workloads;
- every changed argmax/probability movement against fresh execution is reported;
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

## Milestone 5 — Local runtime portability

Goal: broaden usability after semantics stabilize.

Features:

- MLX/Apple Silicon adapter;
- BF16 equivalence diagnostics;
- Q8/Q4 experiments with quality delta reporting;
- model capability registry;
- local checkpoint path and pinned remote revision support;
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

- Qwen 3.5 4B reference support;
- semantic candidate scorer;
- direct-logit baseline;
- answerability;
- zero-generation invariant;
- boolean + choice;
- shared candidate/question execution;
- typed results;
- provenance;
- reproducible benchmark suite;
- CUDA reference runtime;
- CLI/library API.

### Should have after evidence

- HTTP API;
- MLX;
- quantization;
- post-hoc calibration;
- batching controls;
- result audit/debug mode.

### Not v1

- fine-tuning;
- hosted SaaS;
- UI/playground;
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
- peak VRAM/RAM;
- logical input tokens;
- physically evaluated tokens;
- generated tokens;
- scaling by state length, question count and candidate count.

## v1 release claim

The first public release should be able to make a narrow, defensible claim:

> Decisio is a training-free, zero-generation decision layer for open causal LLMs. It scores runtime-defined semantic candidates directly, separates answerability from candidate preference, and reuses shared context for efficient typed decisions.

Any stronger claim must be supported by the committed benchmark evidence.
