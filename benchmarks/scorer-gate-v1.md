# Scorer gate v1

Status: superseded for scorer promotion; retained as Transformers/BF16 historical methodology  
Owner: Decisio

> **Runtime migration note (2026-09-22):** Decisio v1 now targets a pinned Qwen3.5-2B Q4_K_M GGUF
> through llama.cpp. This v1 gate remains useful as the frozen workload, evaluator-threshold and
> historical Transformers/BF16 methodology source, but a PASS here can no longer promote the stable
> scorer. The active migration plan is
> [`docs/workstreams/llama-cpp-reference-runtime.md`](../docs/workstreams/llama-cpp-reference-runtime.md).
> Scorer-gate v2 will freeze the exact GGUF SHA-256 and llama.cpp runtime/build identity before the
> representative result is observed.

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
  --device cpu \
  --dtype bfloat16 \
  --warmup-rounds 1 \
  --performance-rounds 4
```

Outputs include the eight raw JSONL result files plus `comparison.json`,
`comparison.md`, `gate-evaluation.json` and `gate-evaluation.md`. The last two are produced
by `benchmarks/evaluate_scorer_gate.py`, which applies the precommitted criteria below without
manual scorer selection.

## Primary evidence

The report records:

- overall and per-family accuracy;
- invalid output count/rate;
- single-pass per-example latency for diagnostics only;
- repeated full-workload p50/p95 latency with balanced scorer position;
- repeated decisions/second;
- process peak RSS on CPU;
- generated-token count;
- candidate-order choice-change rate;
- order-induced correctness regressions/recoveries;
- paired v2-only versus baseline-only correct rows;
- exact two-sided McNemar/binomial p-value for paired correctness.

The performance phase runs after correctness collection. It performs one full-workload warm-up round
followed by four measured full-workload rounds. Scorer order rotates so every scorer occupies each
execution position once. The CPU path uses in-process wall-clock timing; the report records process
max RSS as a high-water mark rather than pretending it is scorer-isolated allocator memory. The
report retains execution order, CPU/runtime identity, p50/p95 total-workload latency,
decisions/second and peak RSS.

Single-pass per-example timings are diagnostic only. Stable performance decisions use the repeated
performance trials. All timing remains specific to the exact backend, hardware and runtime identity
recorded by the report; it is not a general hardware claim.

## Representative execution contract

A scorer-stability decision requires all of the following in one run:

- model: `Qwen/Qwen3.5-4B`;
- revision: the exact default revision pinned in `src/decisio/backends/qwen.py`;
- dtype: BF16;
- device: CPU on Linux;
- one exact Decisio commit for all four scorers;
- the full frozen 64-example input SHA above;
- both original and reversed candidate order;
- retained raw JSONL plus JSON/Markdown comparison reports.

Qwen3.5-0.8B and reduced-workload CI runs are integration/directional evidence only. A hosted CPU
run may satisfy the scorer gate only when it uses the pinned 4B checkpoint, the full frozen workload,
the required repeated trials, and retains the exact CPU/thread/runtime identity with the artifacts.

## Precommitted v2 promotion gate

The thresholds below are fixed before the full CPU run. They are product gate margins, not a
claim of universal statistical significance.

Comparative semantic v2 may become the Milestone-1 stable default only when all are true:

1. **Overall quality:** normal-order v2 accuracy is no more than 5 percentage points below the
   strongest baseline, and no baseline significantly beats v2 in the exact paired test at
   `p < 0.05`.
2. **Family guardrail:** in every 16-example family, v2 is no more than 2 examples worse than the
   strongest baseline for that family.
3. **Order robustness:** v2 changes choice on at most 1 of 64 examples after reversal and is not
   more order-sensitive than the strongest baseline. "Strongest baseline" means highest normal-order
   accuracy. If multiple baselines tie, the strict comparator is the tied baseline with the fewest
   order changes; any remaining tie uses the fixed baseline order
   `semantic-independent → letters → generated`.
4. **Native invariant:** v2 reports zero generated answer tokens on every row.
5. **Generation trade-off:** in the repeated CPU performance phase, v2 has lower p50 and p95
   full-workload latency than generated JSON on the same run. The measured round count must be
   position-balanced across all four scorers. If not, the zero-generation path is not promoted
   until the discrepancy is understood. Peak RSS is diagnostic and is not a promotion threshold.

Under the original v1 contract, passing this gate would have promoted v2 as Decisio's current
default scorer. After the llama.cpp/GGUF runtime decision, this gate is non-authoritative for
promotion and must not be used to merge that conclusion into product truth. It does not establish broad
task generalization, calibration, answerability quality, or representative deployment performance.

If any condition fails, v2 remains experimental and the discordant rows become the next diagnostic
workload instead of weakening the gate after seeing the results. The CPU workflow runs the evaluator
with `--require-pass`: a scientific gate failure therefore leaves the comparison artifacts available
for diagnosis but blocks promotion of v2 on that candidate.

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
be used to pass the stable-scorer decision gate because it changes both model scale and workload size.
