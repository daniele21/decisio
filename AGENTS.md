# Decisio — Coding Agent Guide

Decisio is a training-free, stateful decision runtime for compatible local open-weight causal LLMs.
Read only the owners needed for the task: `docs/product.md`, `docs/architecture.md`,
`docs/roadmap.md`, `docs/current-state.md`, and `docs/repository-quality.md` when repository
quality/reproducibility is in scope.

## Product invariant

> Compile stable decision context once, reuse model context state, and make bounded typed decisions
> over changing application state without generating an answer.

v1 is training-free and local GGUF + llama.cpp. Qwen3.5-2B Q4_K_M is the pinned reference evidence
artifact, not a permanent product restriction.

## Core invariants

- Stable task policy belongs in the reusable prefix; changing world state and deterministic sensors
  belong in the dynamic suffix.
- Applications remove deterministic invalid alternatives before model scoring.
- Native scoring generates zero answer tokens.
- Direct A/B/C logits are a control primitive, not the product differentiator.
- Comparative semantic v2 remains experimental; its failed short/fresh gate must not be reinterpreted.
- Answerability is separate from candidate preference.
- Raw/normalized scores are not calibrated correctness probabilities.
- No silent truncation; candidate IDs are presentation-order independent.
- Shared/cache execution must match a fresh oracle; cache hits without output equivalence are failures.
- Claims carry exact model, artifact/quantization, scorer/compiler, runtime and timing scope.
- Quantizations are not assumed equivalent.

## Validation

Measure task quality independently from runtime efficiency. For stateful paths record fresh/shared
choice and score deltas, logical versus physically evaluated tokens, cache hits, latency and bounded
memory. Performance changes that alter outputs must report the changed rows; never weaken a
legitimate gate to obtain PASS. Use repository-owned validation selectors and exact-head evidence
when required by stage.

## Documentation ownership

Public identity: `README.md`; product truth: `docs/product.md`; architecture: `docs/architecture.md`;
milestones: `docs/roadmap.md`; integrated/blocked/next: `docs/current-state.md`; rationale:
`docs/adr/`; evidence: `benchmarks/`; repository hardening: `docs/repository-quality.md`.

Root `.engineering/`, local skills, scripts, workflows and repository docs are authoritative;
`template/` is baseline source only.
