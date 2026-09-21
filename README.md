# Decisio

**Turn open-weight LLMs into probabilistic decision engines — without generating text and without requiring fine-tuning.**

Decisio is an inference layer for software that needs decisions rather than prose. It takes unstructured or structured state, a question, and runtime-defined candidates, then returns typed scores/distributions that software can use directly.

The core project hypothesis is that a general-purpose causal LLM such as **Qwen 3.5 4B** can be used more effectively for bounded decisions by scoring candidates semantically from model logits instead of asking the model to generate JSON, prose, or arbitrary answer tokens.

## Why Decisio exists

Many production AI tasks are not generation problems:

- route this request;
- choose the best action;
- decide whether evidence supports a condition;
- classify an item into runtime-defined categories;
- determine whether enough evidence exists to make a decision.

A chat-style LLM usually solves these by generating text that software immediately parses back into a decision. That adds autoregressive latency, output-format failure modes, and often exposes a generated "confidence" value that is not tied to the model's actual output distribution.

Decisio explores a different path:

```text
state + question + candidates
            |
            v
      shared model context
            |
      candidate scoring
            |
            v
 typed decision distribution
```

No answer sentence is generated.

## Product thesis

> For bounded semantic decisions, an open-weight LLM should be used as a scorer before it is used as a writer.

Decisio v1 is deliberately **training-free**. The project must first establish how far inference-time methods can go before adding fine-tuning, adapters, or decision-specific training.

The primary scoring hypothesis is **semantic candidate scoring**:

1. prefill shared state/question context;
2. branch candidate suffixes in parallel;
3. evaluate each candidate with a binary semantic judgment;
4. derive a candidate score from the model's Yes/No log-odds;
5. normalize candidate scores into a conditional decision distribution;
6. assess answerability separately from candidate selection.

The classic A/B/C answer-token method remains a benchmark baseline, not the core product identity.

## What Decisio is

- a local/open inference engine for runtime-defined semantic decisions;
- a training-free decision layer over compatible causal LLMs;
- a zero-generated-token execution path;
- a typed API for boolean and choice decisions first;
- a benchmarkable system with explicit probability semantics and provenance;
- an engine designed to reuse shared state across candidates and questions.

## What Decisio is not

- a Jev clone or reproduction of TypeSafe's proprietary architecture/training;
- a chat or text-generation framework;
- a generic LLM serving platform;
- a workflow/policy engine;
- a claim that raw softmax values are calibrated probabilities;
- a fine-tuning framework in v1;
- a safety-critical decision authority without workload-specific validation.

## Reference model

The initial reference target is **Qwen 3.5 4B**. The architecture must not hard-code Decisio to one checkpoint: model/runtime adapters should allow additional compatible models once the reference path is proven.

Initial runtime priority:

1. PyTorch/CUDA reference implementation;
2. MLX/Apple Silicon after scoring semantics are stable;
3. quantized execution only after BF16 correctness/quality baselines exist.

## Core output semantics

A decision result should make the distinction between *relative model score* and *calibrated confidence* explicit.

Example:

```json
{
  "choice": "billing",
  "distribution": {
    "billing": 0.91,
    "technical": 0.07,
    "sales": 0.02
  },
  "answerability": 0.84,
  "probability_status": "uncalibrated_conditional_scores",
  "scorer": "semantic_binary_logodds",
  "generated_tokens": 0
}
```

Calibration may be added later as an optional workload-specific layer. Decisio must never silently label uncalibrated scores as probability of correctness.

## Success criteria for v1

Decisio v1 is successful if it provides reproducible evidence that the primary scorer:

- produces useful bounded decisions without generating answer tokens;
- is at least competitive with direct A/B/C logit scoring on decision quality;
- materially reduces option-order / verbalizer sensitivity;
- handles missing evidence better through explicit answerability;
- is materially faster than equivalent autoregressive structured-output generation;
- benefits measurably from shared-prefix execution when many decisions use the same state;
- exposes enough provenance to reproduce every benchmark result.

The project does **not** require beating Jev to succeed.

## Milestone 0 laboratory

The first executable slice is now implemented as a Python package with two zero-generation scorers:

- `semantic` — the primary candidate-by-candidate Yes/No log-odds scorer;
- `letters` — the direct A/B/C-style next-token baseline.

Install the reference Qwen runtime:

```bash
uv sync --extra qwen --extra dev
```

Score one request:

```bash
uv run decisio score --input request.json --scorer semantic --device cuda
```

Run the smoke harness:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-smoke.jsonl \
  --scorer semantic \
  --device cuda
```

Milestone 0 intentionally uses fresh inference for every candidate. Shared KV/state execution is a later optimization and must be validated against this reference path.

## Documentation

- [Product scope and durable objectives](docs/product.md)
- [Architecture and scoring model](docs/architecture.md)
- [Implementation roadmap](docs/roadmap.md)
- [Current state](docs/current-state.md)

## Status

The repository is in **product/architecture definition**. No production inference implementation is integrated yet.
