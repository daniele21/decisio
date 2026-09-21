# Current state

Status: active  
Owner: repository

## Current milestone

Validate the scoring hypothesis and runtime shape on the pinned Qwen 3.5 4B reference model.

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| Product foundation | Scope, architecture, scorer hypothesis, constraint boundary and roadmap | ACTIVE | pending merge |
| Decision laboratory | Comparative semantic v2 + independent semantic v1 + letters + generated JSON | ACTIVE | representative Qwen3.5-4B/CUDA evidence not run yet |
| Runtime | One-batch candidate execution + selected-vocabulary projection | ACTIVE | shared-prefix/cache reuse not implemented |
| Examples | Constraint-first Snake, support routing and policy gate | ACTIVE | behavioral quality not benchmarked |

## Integrated on the product branch

- dependency-free decision schema and deterministic compiler;
- comparative semantic v2 scorer using Yes/No log-odds across the complete alternative set;
- original candidate-independent semantic v1 scorer retained as a baseline;
- one-batch candidate execution in the Qwen backend;
- selected-vocabulary projection for requested readout tokens;
- A/B/C direct-logit baseline;
- generated JSON comparison baseline with invalid-output accounting;
- tokenizer verification for one-token readout slots;
- Qwen 3.5 4B Transformers backend pinned to an exact model revision;
- CLI for single scoring and JSONL benchmarks;
- auditable result records with scorer/model/prompt provenance;
- candidate-order reversal perturbation and input SHA-256 tracking;
- fixed-state Snake scorer fixtures;
- constraint-first Snake controller that removes deterministic reverse/wall/body failures before model scoring;
- no-model fast path when exactly one safe Snake action remains;
- runnable Snake, support-routing and policy-gate examples;
- CI-generated Snake video and JSONL trace;
- project CI for lint/test/compile;
- real-model Qwen3.5-0.8B CPU integration smoke.

## Exact-head automated evidence

Head `d966a5538e3fc8c55469bfd7624757bf66683e84`:

- Decisio CI: PASS — https://github.com/daniele21/decisio/actions/runs/35636206905
- Real model smoke: PASS — https://github.com/daniele21/decisio/actions/runs/35636206906

The real-model smoke is functional integration evidence only. It uses official Qwen3.5-0.8B on a hosted CPU runner and does **not** establish representative latency or quality.

Observed five-step Snake smoke after the constraint/batching changes:

- step 1: RIGHT, 2.529 s, alive;
- step 2: RIGHT, 2.475 s, alive;
- step 3: RIGHT, 2.495 s, alive;
- step 4: RIGHT is deterministically filtered as `wall_collision`; DOWN chosen in 1.672 s, alive;
- step 5: DOWN chosen in 1.603 s, alive.

All native decisions reported zero generated answer tokens. The previous wall-collision regression is therefore blocked by the domain constraint layer in the current smoke.

## Repository blockers

- Real Qwen 3.5 4B BF16/CUDA benchmark evidence is still required before Milestone 1 conclusions.
- Comparative semantic v2 has not yet been shown to outperform independent v1, direct answer-token scoring or generated structured output on a representative frozen workload.
- Shared-prefix/cache execution and multi-question reuse are not implemented; candidate batching still physically repeats shared prompt tokens across batch rows.
- Answerability is not implemented.
- Qwen3.5 hosted CPU inference uses slow fallback kernels and is not representative performance evidence.
- The repository still contains inherited `repo-template-sw` material that should be removed after the project-specific engineering baseline is specialized.
- Example behavior remains exploratory until promoted into frozen benchmark/regression evidence.

## Next

- Run comparative v2, independent v1, letters and generated output on the same frozen Qwen3.5-4B/CUDA workload.
- Expand perturbations beyond candidate reversal: paraphrase/wrapping, irrelevant context, missing evidence and candidate-count scaling.
- Compare batched versus sequential execution for output equivalence, latency and peak memory on representative hardware.
- Decide from evidence whether comparative semantic log-odds remains the default scorer.
- Implement answerability only after the scorer decision gate.
- Implement Qwen3.5-aware shared-prefix/cache reuse only with fresh-vs-shared equivalence evidence.
