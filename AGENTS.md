# Decisio — Coding Agent Guide

Decisio is a training-free, zero-generation decision layer for compatible open-weight causal LLMs.

Before substantial product or architecture work, read:

1. `docs/product.md` — mission, scope, non-goals and success criteria.
2. `docs/architecture.md` — scoring semantics and proposed system boundaries.
3. `docs/roadmap.md` — evidence-driven implementation order.
4. `docs/current-state.md` — integrated/blocked/next truth.
5. `docs/repository-quality.md` — repository usability, reproducibility or documentation work.

## Product invariant

The initial project thesis is:

> Use a general-purpose causal LLM as a semantic decision scorer before using it as a text generator.

v1 is training-free. Do not add fine-tuning, adapters or learned heads without benchmark evidence and an explicit product-scope change.

## Core technical invariants

- Native Decisio scoring paths generate zero answer tokens.
- The primary experimental scorer is comparative semantic candidate log-odds; the original independent scorer remains a benchmark baseline.
- Direct answer-token scoring is a baseline for comparison.
- Deterministically invalid alternatives are filtered by the owning application/domain layer before model scoring; Decisio must not replace certain rules with probabilistic inference.
- Answerability is separate from candidate preference.
- Raw/normalized model scores are never described as calibrated probability of correctness unless a validated calibration artifact is active.
- No silent input truncation.
- Candidate IDs are independent of presentation order.
- Shared/cache-optimized execution must be compared against a fresh reference path.
- Benchmark claims carry exact model revision, scorer/compiler identity, precision/backend and timing scope.
- Qwen 3.5 4B is the initial reference model, not a hard-coded product boundary.
- Correctness and evidence precede backend proliferation, quantization and UI work.

## Implementation order

Follow `docs/roadmap.md`.

Do not add HTTP, MLX, quantization, UI or broad model support before Milestones 0–1 establish the scorer.

The first executable question is:

> On the same frozen workload and Qwen 3.5 4B checkpoint, does semantic candidate log-odds provide a useful quality/robustness trade-off against direct answer-token scoring and generated structured output?

## Validation priorities

For decision behavior, measure more than accuracy:

- balanced/task-appropriate accuracy;
- NLL/Brier where meaningful;
- option-order sensitivity;
- paraphrase/wrapper sensitivity;
- irrelevant context;
- missing/contradictory evidence;
- selective accuracy versus answerability/coverage;
- end-to-end latency;
- decisions/sec;
- peak memory;
- fresh versus shared execution differences.

Performance changes that alter outputs must report changed rows/argmaxes.

## Documentation ownership

- public identity and shortest explanation: `README.md`
- durable product truth: `docs/product.md`
- system/scoring boundaries: `docs/architecture.md`
- implementation milestones: `docs/roadmap.md`
- integrated/blocked/next: `docs/current-state.md`
- durable architectural rationale: `docs/adr/`
- benchmark methodology/results: `benchmarks/` and focused result docs once implemented
- repository usability/reproducibility hardening: `docs/repository-quality.md`

Root `.engineering/`, `skills/`, `scripts/`, workflows and Decisio docs are authoritative. `template/` is baseline source only.
