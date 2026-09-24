# Decisio examples

These examples show where a stateful bounded-decision runtime is a better fit than repeatedly
generating free-form text.

| Example | Stable context | Changing state | Typed decision |
| --- | --- | --- | --- |
| [Snake](snake/) | objective, policy, sensor meanings | current board and valid moves | next move |
| [Support routing](support-routing/) | routing semantics | new request | queue ID |
| [Policy gate](policy-gate/) | policy semantics | current evidence | bounded policy action |

The repeated-state shape is:

```text
stable task / policy  ->  reusable model state
                               |
current state + valid candidates
                               |
                               v
                       direct typed decision
```

Snake is the clearest demonstration because its stable decision context can remain warm while only
the board, sensors and valid moves change.

## Install

For real local GGUF inference:

```bash
uv sync --frozen --extra llama --extra dev
```

The root [README](../README.md#try-it) includes a copy/paste Snake setup using the small pinned
Qwen3.5-0.8B Q4_K_M smoke artifact. Qwen3.5-2B Q4_K_M remains the primary reference artifact for
repository evidence.

## Snake live UI

```bash
uv run python -m examples.snake.web \
  --model /path/to/model.gguf \
  --scorer direct \
  --open
```

The UI shows the current model input, valid/filtered actions, direct option scores, selected move,
model identity, timing and context-reuse metrics. Snake direct scoring reuses the fixed decision
context by default; use `--fresh-prefix` to compare against fresh execution.

The HTTP surface exists only inside the example; Decisio core does not become a general-purpose web
server.

## Scoring note

The scorer can differ by workload. Snake defaults to direct A/B/C option-token logits because its
action set is small and latency-sensitive. Semantic v2 remains available for explicit comparison.

Returned distributions are **uncalibrated conditional model scores**, not calibrated probability of
correctness.

## What the examples are for

Examples are executable scenarios for understanding behavior and discovering failure modes. They are
not benchmark evidence by themselves. Product claims come from frozen benchmark datasets and
reproducible evaluation tied to exact model/runtime identities.
