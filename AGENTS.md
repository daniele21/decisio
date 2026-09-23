# Decisio — Coding Agent Guide

Decisio is a training-free, zero-generation decision layer for compatible open-weight causal LLMs.

For substantial work, read only the relevant owners: `docs/product.md`, `docs/architecture.md`,
`docs/roadmap.md`, `docs/current-state.md`, and `docs/repository-quality.md` when repository
usability/reproducibility is in scope.

## Product invariant

> Use a general-purpose causal LLM as a typed decision scorer before using it as a text generator.

v1 is training-free. Do not add fine-tuning, adapters or learned heads without benchmark evidence and
an explicit scope change. The reference evidence path is Qwen3.5-2B Q4_K_M GGUF via llama.cpp; exact
artifact/runtime identity is pinned.

## Core invariants

- Native scoring generates zero answer tokens.
- Comparative semantic v2 is experimental; semantic v1 remains a baseline.
- Direct A/B/C option-token scoring is a measured native path and benchmark baseline; no scorer is a
  universal default without scope-specific evidence.
- Applications remove deterministic invalid alternatives before model scoring.
- Answerability is separate from candidate preference.
- Raw/normalized scores are not calibrated correctness probabilities.
- No silent truncation; candidate IDs are independent of presentation order.
- Cache/shared execution is checked against a fresh oracle.
- Claims carry model, scorer/compiler, backend/precision and timing scope.
- Qwen3.5-2B is a reference, not a hard-coded product boundary.
- GGUF + llama.cpp is canonical for v1; quantizations are not assumed equivalent.

## Active evidence question

Scorer-gate v2 failed for short/fresh general semantic-v2 use; do not weaken or reinterpret it.

> On frozen repeated-state gate v3, does semantic v2 keep comparable quality while materially beating
> generated JSON through exact shared-state reuse?

Contract: `benchmarks/repeated-state-gate-v3.md`. PASS can support only `NARROW_SCOPE`.

## Validation

Measure task quality plus option-order sensitivity, missing/irrelevant evidence, latency, throughput,
memory and fresh/shared differences. Performance changes that alter outputs must report changed
rows/argmaxes. Use repository-owned validation selectors and exact-head evidence.

## Documentation ownership

- public identity: `README.md`
- product truth: `docs/product.md`
- architecture/scoring: `docs/architecture.md`
- milestones: `docs/roadmap.md`
- integrated/blocked/next: `docs/current-state.md`
- durable rationale: `docs/adr/`
- benchmarks/evidence: `benchmarks/`
- repository hardening: `docs/repository-quality.md`

Root `.engineering/`, local skills, scripts, workflows and repository docs are authoritative;
`template/` is baseline source only.
