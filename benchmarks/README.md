# Benchmarks

Decisio treats benchmark evidence as part of the product contract. The benchmark runner writes one JSON object per evaluated example and never rewrites model scores as calibrated confidence.

## Fixture format

Each JSONL row contains a normal choice request plus a ground-truth `label`:

```json
{
  "id": "routing-billing",
  "state": "My card was charged twice.",
  "question": "Which queue should handle this request?",
  "candidates": [
    {"id": "billing", "description": "Payments and invoices"},
    {"id": "technical", "description": "Software bugs"}
  ],
  "label": "billing"
}
```

`fixtures/smoke.jsonl` exists only to prove the harness. It is not a quality benchmark and must not be used for product claims.

## Run

Install the reference runtime:

```bash
uv sync --extra qwen --extra dev
```

Run the primary comparative semantic scorer:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-smoke.jsonl \
  --scorer semantic \
  --device cuda
```

Run the original independent semantic baseline:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-independent-smoke.jsonl \
  --scorer semantic-independent \
  --device cuda
```

Run the direct answer-token baseline:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/letters-smoke.jsonl \
  --scorer letters \
  --device cuda
```

The default Qwen checkpoint is pinned in `src/decisio/backends/qwen.py`. Override `--model` or `--revision` only when the resulting evidence records the changed model identity.

## Current benchmark boundary

The Qwen reference backend batches semantic candidate prompts in one forward and projects only requested readout vocabulary rows. This is a runtime optimization over the original sequential path. Shared-prefix/cache reuse and multi-question execution remain separate because they can affect model-state semantics and require equivalence evidence.


## Generated baseline

The autoregressive comparator is intentionally outside the native zero-generation path:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/generated-smoke.jsonl \
  --scorer generated \
  --device cuda
```

It requests the smallest valid JSON object, records the raw model text, counts generated tokens, and treats malformed or out-of-set output as an invalid decision rather than repairing it.

## Candidate-order perturbation

Run any scorer against the same frozen input with reversed candidate order:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-reversed.jsonl \
  --scorer semantic \
  --reverse-candidates \
  --device cuda
```

The benchmark summary includes the input SHA-256 and perturbation identity.
