# Support routing

A classic bounded semantic decision: choose one runtime-defined queue from a piece of evidence.

```bash
uv run decisio score \
  --input examples/support-routing/request.json \
  --scorer semantic \
  --device cuda
```

This use case demonstrates why candidate descriptions matter. The category IDs are software identifiers; the model scores the semantic descriptions rather than an arbitrary A/B/C mapping.

Try changing the ticket text, adding a new queue, or reversing candidate order.
