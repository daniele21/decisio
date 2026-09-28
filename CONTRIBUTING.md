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
uv run ruff check src tests examples
uv run pytest
uv run python -m compileall -q src tests examples
```

Repository/governance checks are owned by `scripts/verify_*.py` and run in the Repository health
workflow. Canonical command intent lives in `.engineering/commands.json`.

To try the real local runtime without choosing a model first:

```bash
uv sync --frozen --extra llama --extra dev
uv run python -m examples.snake.demo --open
```

That path uses the pinned 0.8B smoke artifact and proves integration only.

The `qwen` extra exists only to reproduce the superseded Transformers/BF16 scorer-gate-v1 history.
New runtime work must use the `llama` extra unless a new evidence contract explicitly says otherwise.

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
`llama-cpp-python==0.3.35` on CPU. Full 2B reference gates are run locally/manual and must retain the
exact host/runtime identity; PR CI is limited to cheaper 0.8B mechanism smoke. Smaller models and
Metal runs are separate evidence identities.

Both semantic-v2 promotion gates are recorded **FAIL** results and must not be reinterpreted; the repeated-state run still retains strong cache-mechanism evidence. Snake controller quality is governed by `benchmarks/snake-controller-benchmark-v1.md` and remains deliberately separate from cache efficiency. Direct-v1 screening evidence is append-only; direct-v2 reruns use a distinct protocol fingerprint.

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
