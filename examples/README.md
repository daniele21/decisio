# Decisio examples

These examples show where a bounded decision engine is a better fit than free-form text generation.

| Example | Decision shape | Why it matters |
| --- | --- | --- |
| [Snake](snake/) | sequential action choice | exercises Decisio repeatedly in a closed control loop |
| [Support routing](support-routing/) | dynamic multiclass choice | shows runtime-defined semantic categories |
| [Policy gate](policy-gate/) | bounded allow/deny choice | shows a software decision over explicit evidence and policy |

All examples use the same public decision contract:

```text
state/evidence + question + candidates
                  |
                  v
               Decisio
                  |
                  v
       typed choice + distribution
```

The returned distribution is an **uncalibrated conditional model score**, not a calibrated probability of correctness.

## Install

For real Qwen inference:

```bash
uv sync --extra qwen --extra dev
```

The reference model is Qwen3.5-4B. For a cheaper functional smoke, the same backend can be pointed at the official Qwen3.5-0.8B checkpoint, as used by the GitHub Actions real-model smoke.

## What the examples are for

Examples are not benchmark evidence by themselves. They are executable scenarios for understanding behavior and discovering failure modes. Product claims should come from frozen benchmark datasets and reproducible evaluation.
