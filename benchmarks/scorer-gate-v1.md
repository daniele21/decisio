# Scorer gate v1

Status: active methodology  
Owner: Decisio

## Question

This benchmark answers one product question:

> On the same frozen workload and pinned Qwen3.5-4B checkpoint, is comparative semantic
> log-odds v2 strong and robust enough to become Decisio's stable default scorer?

This is an internal scorer-semantics experiment. It does not move externally served endpoint
evaluation, device evidence, or regression ownership out of Performance Lab.

## Frozen workload

The owned workload contains 64 examples, 16 in each family:

- `support_routing` — runtime-defined semantic routing;
- `rule_application` — explicit rule application with approve/deny/manual-review choices;
- `evidence_entailment` — choose the conclusion supported by supplied evidence;
- `comparative_nuance` — distinguish closely related operational categories.

Materialize it with:

```bash
python benchmarks/build_scorer_gate_fixture.py \
  --output .artifacts/scorer-gate-v1.jsonl
```

Expected full-workload SHA-256:

```text
087ee8bbec3393609689046ea9c5d8219d0f39562e322180ca8f1e08eb368d3a
```

The generator checks this digest before writing. Any case change therefore requires an explicit
fixture-version decision rather than silently changing the evidence base.

The workload is synthetic and repository-owned. It is designed to expose Decisio failure modes; it
is not evidence of broad real-world generalization.

## Compared scorers

The matrix is fixed:

1. `semantic` — comparative candidate Yes/No log-odds v2;
2. `semantic-independent` — candidate-independent Yes/No log-odds v1;
3. `letters` — direct A/B/C/... next-token baseline;
4. `generated` — minimal autoregressive JSON baseline.

Every scorer runs on the same examples twice:

- original candidate order;
- fully reversed candidate order.

The comparison command loads one backend and executes the complete matrix:

```bash
uv run decisio compare \
  --input .artifacts/scorer-gate-v1.jsonl \
  --output-dir .artifacts/scorer-gate-v1 \
  --device cuda \
  --dtype bfloat16
```

Outputs include the eight raw JSONL result files plus `comparison.json` and
`comparison.md`.

## Primary evidence

The report records:

- overall and per-family accuracy;
- invalid output count/rate;
- median/mean/total wall-clock scorer latency;
- generated-token count;
- candidate-order choice-change rate;
- order-induced correctness regressions/recoveries;
- paired v2-only versus baseline-only correct rows;
- exact two-sided McNemar/binomial p-value for paired correctness.

Latency is an in-process comparison for this exact backend/run. It is not a general hardware claim.

## Representative execution contract

A scorer-stability decision requires all of the following in one run:

- model: `Qwen/Qwen3.5-4B`;
- revision: the exact default revision pinned in `src/decisio/backends/qwen.py`;
- dtype: BF16;
- device: CUDA on representative hardware;
- one exact Decisio commit for all four scorers;
- the full frozen 64-example input SHA above;
- both original and reversed candidate order;
- retained raw JSONL plus JSON/Markdown comparison reports.

Hosted CPU and Qwen3.5-0.8B CI runs are integration/directional evidence only.

## Precommitted v2 promotion gate

The thresholds below are fixed before the representative run. They are product gate margins, not a
claim of universal statistical significance.

Comparative semantic v2 may become the Milestone-1 stable default only when all are true:

1. **Overall quality:** normal-order v2 accuracy is no more than 5 percentage points below the
   strongest baseline, and no baseline significantly beats v2 in the exact paired test at
   `p < 0.05`.
2. **Family guardrail:** in every 16-example family, v2 is no more than 2 examples worse than the
   strongest baseline for that family.
3. **Order robustness:** v2 changes choice on at most 1 of 64 examples after reversal and is not
   more order-sensitive than the strongest baseline.
4. **Native invariant:** v2 reports zero generated answer tokens on every row.
5. **Generation trade-off:** total v2 scorer latency is lower than the generated JSON baseline on
   the same run. If not, the zero-generation path is not promoted until the discrepancy is
   understood.

Passing this gate promotes v2 only as Decisio's current default scorer. It does not establish broad
task generalization, calibration, answerability quality, or representative deployment performance.

If any condition fails, v2 remains experimental and the discordant rows become the next diagnostic
workload instead of weakening the gate after seeing the results.

## CI subset

For functional CI only:

```bash
python benchmarks/build_scorer_gate_fixture.py \
  --ci \
  --output .artifacts/scorer-gate-ci.jsonl
```

The CI subset has 8 examples, two from each family, with SHA-256:

```text
360a972d7732cc0039113f4a41fbb3d51630439e4084631dbf4d1b60c63c1d17
```

It verifies the real-model matrix and artifact format with Qwen3.5-0.8B on hosted CPU. It must never
be used to pass the stable-scorer decision gate.
