# Contributing to Decisio

Decisio is still experimental. Contributions should make the scoring hypothesis easier to test, the runtime easier to trust, or the developer experience simpler without expanding the product surface prematurely.

## Start here

Read only the context relevant to your change:

- `AGENTS.md` for repository invariants and routing;
- `docs/current-state.md` for what is integrated, blocked and next;
- `docs/product.md` for product scope;
- `docs/architecture.md` for system boundaries;
- `docs/repository-quality.md` for repository hardening work;
- `benchmarks/` when changing scorer semantics or evidence.

## Setup

The supported development runtime is Python 3.11+.

```bash
uv sync --frozen --extra qwen --extra dev
```

For the cheap deterministic loop:

```bash
uv sync --frozen --extra dev
uv run ruff check src tests examples
uv run pytest
uv run python -m compileall -q src tests examples
```

Repository/governance checks are owned by `scripts/verify_*.py` and run in the Repository health workflow. Canonical command intent lives in `.engineering/commands.json`.

## Change rules

- Keep deterministic/domain constraints outside probabilistic scoring.
- Native Decisio scoring must generate zero answer tokens.
- Do not describe raw normalized scores as calibrated correctness probabilities.
- Do not silently truncate input.
- Keep candidate IDs independent of presentation order.
- Preserve exact model/scorer/compiler/runtime provenance for benchmark evidence.
- Do not weaken a frozen benchmark or test to obtain a passing result.

Changes to scorer behavior should include direct tests and, when material, updated frozen evidence.

## Benchmark evidence

Functional CPU or small-model smoke runs prove integration only.

Representative claims about Qwen3.5-4B quality, CUDA latency, throughput or memory require the execution contract in `benchmarks/scorer-gate-v1.md`.

Do not edit a frozen fixture silently. A fixture change requires a new explicit dataset identity or version decision.

## Pull requests

Keep changes narrow and explain:

- the problem or invariant being addressed;
- the canonical owner changed;
- behavior or evidence affected;
- validation performed;
- any representative-hardware evidence still pending.

Code written is not completion if affected tests, docs or evidence disagree with the new behavior.
