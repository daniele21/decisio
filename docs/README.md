# Decisio documentation

Start here:

- [Product](product.md) — why Decisio exists, who it serves, non-goals and success criteria.
- [Architecture](architecture.md) — zero-generation readout paths, runtime boundaries and current system shape.
- [Current state](current-state.md) — what is integrated, blocked and next.
- [Calibration](calibration.md) — why native score distributions are not calibrated correctness probabilities and how future calibration artifacts are scoped.
- [Roadmap](roadmap.md) — evidence-driven implementation order.
- [Repository quality](repository-quality.md) — usability, reproducibility, documentation and hardening plan.
- [Benchmarks](../benchmarks/README.md) — frozen scorer comparisons, perturbations and evidence rules.
- [Examples](../examples/README.md) — live Snake decision UI plus support-routing and policy-gate scenarios.
- [ADR 0001](adr/0001-training-free-semantic-scoring.md) — why v1 is training-free and semantic-scoring-first.
- [ADR 0002](adr/0002-constrain-before-score.md) — why deterministic constraints precede semantic scoring and why v2 is comparative.

## Documentation rule

Keep product truth, current implementation and benchmark evidence distinct.

Product documents define the intended outcome and boundaries. `docs/current-state.md` records what is true now. Benchmark artifacts determine whether hypotheses are supported by evidence. If evidence contradicts an architectural hypothesis, update the architecture and roadmap rather than preserving the original idea for consistency.

Prefer one canonical explanation, executable examples and diagrams over repeated prose.
