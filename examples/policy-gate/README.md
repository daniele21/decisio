# Policy gate

A bounded allow/deny decision over explicit evidence and policy.

```bash
uv run decisio score \
  --input examples/policy-gate/request.json \
  --scorer semantic \
  --device cuda
```

The returned values are conditional model scores, **not authorization by themselves**. In a real system the authoritative policy engine remains the source of truth; Decisio can be evaluated as a semantic interpretation layer where rules contain natural-language evidence.

This example deliberately illustrates the product boundary: Decisio returns a decision signal but does not execute the action or replace deterministic business rules.
