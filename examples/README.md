# Decisio examples

These examples show where a bounded decision engine is a better fit than free-form text generation.

| Example | Decision shape | Why it matters |
| --- | --- | --- |
| [Snake](snake/) | sequential action choice | live OBSERVE → DECIDE → ACT loop with deterministic constraints and one-forward direct choice logits |
| [Support routing](support-routing/) | dynamic multiclass choice | runtime-defined semantic categories |
| [Policy gate](policy-gate/) | bounded allow/deny choice | software decision over explicit evidence and policy |

All examples use the same public decision shape:

```text
state/evidence + question + valid candidates
                  |
                  v
               Decisio
                  |
                  v
       typed choice + distribution
```

The scorer can differ by workload. Snake defaults to direct A/B/C option-token logits because its
action set is small and latency-sensitive; semantic v2 remains available for explicit comparison.
Returned distributions are **uncalibrated conditional model scores**, not calibrated probability of
correctness.

## Install

For real local GGUF inference:

```bash
uv sync --frozen --extra llama --extra dev
```

Qwen3.5-2B Q4_K_M is the pinned reference artifact for repository evidence, not the only compatible
model users may try. A compatible smaller GGUF such as Qwen3.5-0.8B can be useful for cheaper local
demo/smoke runs, but its quality and latency are separate evidence and must not be presented as the
2B reference result.

## Snake live UI

```bash
uv run python -m examples.snake.web \
  --model /path/to/model.gguf \
  --scorer direct \
  --open
```

The UI shows the board state, valid/filtered actions, direct option scores, selected move, model
identity and per-decision timing. The HTTP surface exists only inside the example; Decisio core does
not become a general-purpose web server.

## What the examples are for

Examples are not benchmark evidence by themselves. They are executable scenarios for understanding
behavior and discovering failure modes. Product claims come from frozen benchmark datasets and
reproducible evaluation.
