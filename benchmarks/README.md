# Benchmarks

Decisio treats benchmark evidence as part of the product contract. The benchmark runner writes one
JSON object per evaluated example and never rewrites model scores as calibrated confidence.

## Fixture format

Each JSONL row contains a normal choice request plus a ground-truth `label`:

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

`fixtures/smoke.jsonl` exists only to prove the single-scorer harness. It is not a quality
benchmark and must not be used for product claims.

## Scorer decision gate

The first product decision benchmark is defined in
[`scorer-gate-v1.md`](scorer-gate-v1.md). It compares the four current inference strategies on one
frozen 64-example workload and candidate-order reversal.

Materialize the frozen input:

```bash
python benchmarks/build_scorer_gate_fixture.py \
  --output .artifacts/scorer-gate-v1.jsonl
```

Run the complete paired matrix with one backend instance:

```bash
uv sync --frozen --extra qwen --extra dev

uv run decisio compare \
  --input .artifacts/scorer-gate-v1.jsonl \
  --output-dir .artifacts/scorer-gate-v1 \
  --device cpu \
  --dtype bfloat16 \
  --warmup-rounds 1 \
  --performance-rounds 8
```

The output directory contains raw JSONL evidence for v2, v1, letters and generated JSON in original
and reversed candidate order, plus `comparison.json` and `comparison.md`. Scorer-gate runs
also include repeated CPU full-workload timing with balanced scorer order, throughput and process
peak-RSS evidence. Omit the performance flags for cheap functional smoke runs.

The stable-scorer decision requires the pinned Qwen3.5-4B BF16 CPU execution contract and the
precommitted margins in the methodology. Smaller-model or reduced-workload results are directional only.

## Run one scorer

Install the reference runtime:

```bash
uv sync --frozen --extra qwen --extra dev
```

Run the primary comparative semantic scorer:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-smoke.jsonl \
  --scorer semantic \
  --device cpu
```

Run the original independent semantic baseline:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-independent-smoke.jsonl \
  --scorer semantic-independent \
  --device cpu
```

Run the direct answer-token baseline:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/letters-smoke.jsonl \
  --scorer letters \
  --device cpu
```

The default Qwen checkpoint is pinned in `src/decisio/backends/qwen.py`. Override `--model` or
`--revision` only when the resulting evidence records the changed model identity.

## Generated baseline

The autoregressive comparator is intentionally outside the native zero-generation path:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/generated-smoke.jsonl \
  --scorer generated \
  --device cpu
```

It requests the smallest valid JSON object, records the raw model text, counts generated tokens, and
treats malformed or out-of-set output as an invalid decision rather than repairing it.

## Candidate-order perturbation

Run any scorer against the same frozen input with reversed candidate order:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-reversed.jsonl \
  --scorer semantic \
  --reverse-candidates \
  --device cpu
```

The benchmark summary includes input SHA-256, perturbation identity, invalid-rate and per-family
metrics when a `family` field is present.

## Runtime boundary

The Qwen reference backend batches semantic candidate prompts in one forward and projects only
requested readout vocabulary rows. This is a runtime optimization over the original sequential path.
Shared-prefix/cache reuse and multi-question execution remain separate because they can affect
model-state semantics and require equivalence evidence.
