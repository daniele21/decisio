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

Run the primary semantic scorer:

```bash
uv run decisio benchmark \
  --input benchmarks/fixtures/smoke.jsonl \
  --output .artifacts/semantic-smoke.jsonl \
  --scorer semantic \
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

Milestone 0 uses **fresh inference** for every semantic candidate. Candidate batching, shared KV/state reuse and multi-question execution deliberately belong to a later milestone so optimized execution can be compared against a simple semantic reference path.
