# Benchmarks

Decisio treats benchmark evidence as part of the product contract. Benchmark outputs never relabel
model scores as calibrated probability of correctness.

## Fixture format

Each JSONL row contains a choice request plus ground truth:

```json
{
  "id": "routing-billing",
  "family": "support_routing",
  "state": "My card was charged twice.",
  "question": "Which queue should handle this request?",
  "candidates": [
    {"id": "billing", "description": "Payments and invoices"},
    {"id": "technical", "description": "Software bugs"}
  ],
  "label": "billing"
}
```

`fixtures/smoke.jsonl` is a harness smoke only; it is not quality evidence.

## Stable-scorer gate v2

The active decision contract is [`scorer-gate-v2.md`](scorer-gate-v2.md). Historical
Transformers/BF16 methodology remains in [`scorer-gate-v1.md`](scorer-gate-v1.md) but cannot
promote the scorer.

The v2 reference evidence artifact is Qwen3.5-2B Q4_K_M GGUF through the pinned llama.cpp binding.
This pin is for reproducible product evidence, not a model-selection restriction: Decisio users can
point the runtime at another compatible GGUF and produce evidence under that artifact's identity.

Materialize the frozen 64-case workload:

```bash
python benchmarks/build_scorer_gate_fixture.py \
  --output .artifacts/scorer-gate-v2.jsonl
```

Expected input SHA-256:

```text
087ee8bbec3393609689046ea9c5d8219d0f39562e322180ca8f1e08eb368d3a
```

Install the canonical runtime and run the paired matrix:

```bash
uv sync --frozen --extra llama --extra dev

uv run decisio compare \
  --input .artifacts/scorer-gate-v2.jsonl \
  --output-dir .artifacts/scorer-gate-v2 \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --device cpu \
  --n-ctx 8192 \
  --n-batch 512 \
  --n-ubatch 512 \
  --threads 2 \
  --threads-batch 2 \
  --warmup-rounds 1 \
  --performance-rounds 4

uv run python benchmarks/evaluate_scorer_gate.py \
  --comparison .artifacts/scorer-gate-v2/comparison.json \
  --output-dir .artifacts/scorer-gate-v2 \
  --require-pass
```

The evaluator checks the frozen runtime/artifact identity as well as the precommitted quality,
family, option-order, zero-generation and generated-baseline latency criteria.

Before the paired matrix, the CPU workflow also runs
`benchmarks/verify_llama_runtime_gate.py`. It compares semantic v2 shared execution against the
fresh oracle over all 64 cases, then proves a bounded same-state/different-question cache hit against
fresh evaluation. Output equality is blocking; cache latency is recorded but is not a precommitted
2B speed threshold.

## Repeated-state gate v3

The scoped repeated-state contract is
[`repeated-state-gate-v3.md`](repeated-state-gate-v3.md). It does not replace scorer-gate v2.

Materialize and run the frozen 48-case / 8-state workload:

```bash
uv run python -m benchmarks.build_repeated_state_gate_fixture \
  --output .artifacts/repeated-state-gate-v3/fixture.json

uv run python -m benchmarks.run_repeated_state_gate \
  --fixture .artifacts/repeated-state-gate-v3/fixture.json \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --output .artifacts/repeated-state-gate-v3/report.json \
  --n-ctx 8192 --n-batch 512 --n-ubatch 512 \
  --threads 2 --threads-batch 2

uv run python -m benchmarks.evaluate_repeated_state_gate \
  --report .artifacts/repeated-state-gate-v3/report.json \
  --output-dir .artifacts/repeated-state-gate-v3 \
  --require-pass
```

Expected fixture SHA-256:
`f9e5f56128f93efb952f1fc3f4f38441150cb0c29906f688977ffa69ea61338a`.

The runner prints live progress/ETA. The evaluator includes the cold decision in each six-decision
group and applies the quality, order, cache/token and >=2x p50/p95 latency criteria frozen in the
methodology document.

## Snake controller benchmark v1

[Snake controller benchmark v1](snake-controller-benchmark-v1.md) evaluates the Snake application
at two levels: fixed-state decisions against a bounded dynamic-body planner, and deterministic
seeded episodes. It is the controller-quality benchmark; it is separate from scorer promotion gates
and from the smaller input/cache diagnostic.

The initial matrix compares the same stateful direct prompt under shared versus fresh execution,
compact input, semantic v2/v1 and the adjacent-food application policy. Every run appends a
`run_start` manifest plus terminal configuration results to a JSONL ledger. Evidence binds source
commit, fixture/protocol hashes, exact GGUF/runtime identity, prompt/execution mode, controller
parameters, decision-quality metrics, episode outcomes and runtime/token/cache metrics.

```bash
uv run python -m benchmarks.run_snake_controller_benchmark \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --output .artifacts/snake-controller/latest.json \
  --ledger .artifacts/snake-controller/history.jsonl \
  --threads 2 --threads-batch 2

uv run python -m benchmarks.summarize_snake_controller_history \
  --ledger .artifacts/snake-controller/history.jsonl \
  --output .artifacts/snake-controller/history.md
```

Reduced 0.8B CI runs are mechanism/directional smokes only. Do not mix them with a full 2B matrix:
the history groups by model SHA, fixture SHA and protocol SHA.

## Run one scorer

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-smoke.jsonl \
  --scorer semantic \
  --model /path/to/model.gguf \
  --device cpu
```

Use `semantic-independent`, `letters` or `generated` for the comparison baselines. Add
`--reverse-candidates` to exercise option-order perturbation.

The generated comparator is intentionally outside the native zero-generation path: it emits the
smallest structured answer it can, records generated-token count and treats malformed/out-of-set
output as invalid instead of repairing it.

## Evidence boundary

The full gate is internal scorer/runtime evidence owned by Decisio. Smaller models, reduced
workloads or different GGUF/runtime identities are directional unless their own contract says
otherwise. Externally served endpoint evaluation and regression remain Performance Lab
responsibilities.
