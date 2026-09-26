# Contributing to Decisio

Decisio is experimental. Contributions should make the stateful runtime easier to trust, the
decision contract easier to use, or the evidence easier to reproduce without expanding the product
surface prematurely.

## Start here

Read only the context relevant to your change:

- `AGENTS.md` for repository invariants and routing;
- `docs/current-state.md` for what is integrated, blocked and next;
- `docs/product.md` for product scope;
- `docs/architecture.md` for system boundaries;
- `docs/repository-quality.md` for repository hardening work;
- `benchmarks/` when changing scorer, controller or runtime evidence.

## Setup

Python 3.11+ is supported. The canonical local runtime is GGUF + llama.cpp:

```bash
uv sync --frozen --extra llama --extra dev
```

For the cheap deterministic loop:

```bash
uv sync --frozen --extra dev
uv run ruff check src tests examples scripts
uv run pytest
uv run python -m compileall -q src tests examples scripts
```

Repository/governance checks are owned by `scripts/verify_*.py` and run in the Repository health
workflow. Canonical command intent lives in `.engineering/commands.json`.

To try the real local runtime without choosing a model first:

```bash
uv sync --frozen --extra llama --extra dev
uv run python scripts/run_snake_demo.py --open
```

That path uses the pinned 0.8B smoke artifact and proves integration only.

## Change rules

- Keep deterministic/domain constraints outside probabilistic scoring.
- Native Decisio scoring must generate zero answer tokens.
- Stable task/policy belongs in the reusable prefix; changing state/sensors belong in the suffix.
- Shared/cache execution must match the fresh oracle before a reuse claim is accepted.
- Do not describe raw normalized scores as calibrated correctness probabilities.
- Do not silently truncate input.
- Keep candidate IDs independent of presentation order.
- Preserve exact model/GGUF/scorer/compiler/runtime provenance for benchmark evidence.
- Do not weaken a frozen benchmark or test to obtain a passing result.

Changes to scorer, compiler, cache or controller behavior should include direct tests and, when
material, updated frozen evidence.

## Benchmark evidence

The pinned reference identity is Qwen3.5-2B Q4_K_M GGUF through
`llama-cpp-python==0.3.35` on CPU. Smaller models and Metal runs are separate evidence identities.

The general short/fresh semantic-v2 gate is a recorded **FAIL** and must not be reinterpreted.
Repeated-state semantic evidence is governed separately by
`benchmarks/repeated-state-gate-v3.md`. Snake controller quality is governed by
`benchmarks/snake-controller-benchmark-v1.md` and is deliberately separate from cache efficiency.

Do not edit a frozen fixture silently. A fixture change requires a new explicit dataset/protocol
identity or version decision.

## Pull requests

Keep changes coherent and explain:

- the user/system outcome or invariant being addressed;
- the canonical owner changed;
- behavior or evidence affected;
- validation performed;
- any representative-environment evidence still pending.

Code written is not completion if affected tests, docs or evidence disagree with the new behavior.
