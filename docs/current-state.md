# Current state

Status: active  
Owner: repository

## Current milestone

Validate the scoring hypothesis and runtime shape on the pinned Qwen 3.5 4B reference model while hardening the repository enough that the resulting evidence is reproducible and understandable.

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| Product foundation | Scope, architecture, scorer hypothesis, constraint boundary and roadmap | ACTIVE | pending merge |
| Decision laboratory | Frozen paired v2/v1/letters/generated scorer gate + order reversal | ACTIVE | representative Qwen3.5-4B/CUDA gate not run yet |
| Runtime | One-batch candidate execution + selected-vocabulary projection | ACTIVE | shared-prefix/cache reuse not implemented |
| Examples | Constraint-first Snake, support routing and policy gate | ACTIVE | behavioral quality not benchmarked |
| Repository quality | Vertical hardening plan for onboarding, trust, reproducibility and maintainability | ACTIVE | P0 items tracked in `docs/repository-quality.md` |

## Integrated on the product / benchmark branches

- dependency-free decision schema and deterministic compiler;
- comparative semantic v2 scorer using Yes/No log-odds across the complete alternative set;
- original candidate-independent semantic v1 scorer retained as a baseline;
- one-batch candidate execution in the Qwen backend;
- selected-vocabulary projection for requested readout tokens;
- A/B/C direct-logit baseline;
- generated JSON comparison baseline with invalid-output accounting;
- tokenizer verification for one-token readout slots;
- Qwen 3.5 4B Transformers backend pinned to an exact model revision;
- CLI for single scoring, one-scorer JSONL benchmarks and the paired four-scorer comparison matrix;
- frozen 64-example scorer-gate v1 workload with per-family metrics and exact input SHA-256;
- paired v2-vs-baseline correctness, exact McNemar/binomial evidence and candidate-order sensitivity reporting;
- auditable result records with scorer/model/prompt provenance;
- candidate-order reversal perturbation and input SHA-256 tracking;
- fixed-state Snake scorer fixtures;
- constraint-first Snake controller that removes deterministic reverse/wall/body failures before model scoring;
- no-model fast path when exactly one safe Snake action remains;
- runnable Snake, support-routing and policy-gate examples;
- CI-generated Snake video and JSONL trace;
- project CI for lint/test/compile;
- real-model Qwen3.5-0.8B CPU integration smoke;
- real-model four-scorer directional matrix smoke.

## Last validated implementation evidence

Implementation head `be12009660f7bd9c22cef3d7e7979a9cfe36371f`:

- Decisio CI: PASS — https://github.com/daniele21/decisio/actions/runs/35641019755
- Scorer matrix smoke: PASS — https://github.com/daniele21/decisio/actions/runs/35641019750

The scorer-matrix smoke uses official Qwen3.5-0.8B on a hosted CPU runner. It proves real-model integration and evidence-format behavior only; it does **not** establish representative latency or quality.

Directional 8-case matrix at that head:

- semantic v2: 7/8 correct, 0/8 order changes, zero generated answer tokens;
- semantic v1: 7/8 correct, 0/8 order changes, zero generated answer tokens;
- letters: 7/8 correct, 1/8 order changes, zero generated answer tokens;
- generated JSON: 7/8 correct, 2/8 order changes, 74 generated tokens.

Hosted-CPU latency from that run is explicitly non-representative.

## Repository blockers

### Scorer decision

- Real Qwen 3.5 4B BF16/CUDA benchmark evidence is still required before Milestone 1 conclusions.
- Comparative semantic v2 has not yet been shown to provide the required quality/robustness/performance trade-off against v1, direct answer-token scoring and generated structured output.
- Representative performance methodology needs warm-up, repeated runs, CUDA synchronization and stronger systems metrics before latency is used as a stable promotion signal.

### Product capability

- Shared-prefix/cache execution and multi-question reuse are not implemented; candidate batching still physically repeats shared prompt tokens across batch rows.
- Answerability is not implemented.
- Example behavior remains exploratory until promoted into frozen benchmark/regression evidence.

### Repository quality

The canonical hardening backlog is `docs/repository-quality.md`. Current P0 gaps include:

- default `main` still presents inherited `repo-template-sw` product identity;
- engineering-template specialization is incomplete;
- dependency environment is not locked with `uv.lock`;
- `LICENSE` is missing;
- public request/result contracts still need edge-case hardening where they can affect benchmark correctness.

## Next

1. Harden representative benchmark timing according to RQ-01 before using CUDA latency as a scorer promotion gate.
2. Run the frozen 64-example v2/v1/letters/generated gate on pinned Qwen3.5-4B BF16/CUDA and retain raw + JSON/Markdown reports.
3. Decide from evidence whether comparative semantic log-odds remains the default scorer.
4. Converge the product/scorer branches onto the default branch and complete the P0 repository-specialization work.
5. Expand perturbations beyond candidate reversal: paraphrase/wrapping, irrelevant context, missing evidence and candidate-count scaling.
6. Compare batched versus sequential execution for output equivalence, latency and peak memory on representative hardware.
7. Implement answerability only after the scorer decision gate.
8. Implement Qwen3.5-aware shared-prefix/cache reuse only with fresh-vs-shared equivalence evidence.
