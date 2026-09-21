# Current state

Status: active  
Owner: repository

## Current milestone

Validate the Milestone 0 scoring hypothesis on the pinned Qwen 3.5 4B reference model.

## Active workstreams

| Workstream | Current executable slice | State | Blocker |
| --- | --- | --- | --- |
| Product foundation | Scope, architecture, scorer hypothesis and roadmap | ACTIVE | pending merge |
| Decision laboratory | Semantic + letter-token + generated JSON baselines with JSONL harness | ACTIVE | representative Qwen/CUDA evidence not run yet |
| Examples | Snake, support routing and policy gate | ACTIVE | behavioral quality not benchmarked |

## Integrated on the product branch

- dependency-free decision schema and deterministic compiler;
- semantic candidate scorer using Yes/No log-odds;
- A/B/C direct-logit baseline;
- tokenizer verification for one-token readout slots;
- Qwen 3.5 4B Transformers backend pinned to an exact model revision;
- CLI for single scoring and JSONL benchmarks;
- auditable result records with scorer/model/prompt provenance;
- smoke fixtures and deterministic unit tests;
- generated JSON comparison baseline with invalid-output accounting;
- candidate-order reversal perturbation and input SHA-256 tracking;
- project CI for lint/test/compile;
- runnable Snake, support-routing and policy-gate examples.

## Repository blockers

- The repository still contains inherited `repo-template-sw` material that should be removed after the project-specific engineering baseline is specialized.
- Real Qwen 3.5 4B BF16/CUDA benchmark evidence is still required before Milestone 1 conclusions.
- Shared-prefix execution and answerability are intentionally not implemented yet; the generated-output baseline is available only for comparison.
- Example behavior remains exploratory until promoted into frozen benchmark/regression evidence.

## Next

- Run the pinned reference model on the frozen smoke/initial evaluation set.
- Expand Milestone 1 perturbations beyond candidate reversal and run all three scorers on representative Qwen/CUDA.
- Use Snake traces to identify repeated failure patterns worth promoting into fixed regression fixtures.
- Decide from evidence whether semantic binary log-odds remains the default scorer before implementing shared execution.
