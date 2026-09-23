# Snake controller benchmark v1

Status: active benchmark contract; diagnostic/product evidence, not a universal game-playing claim.

## Question

For one fixed GGUF/runtime identity, which Decisio Snake controller configuration gives the strongest
trade-off between local decision quality, full-episode outcome and inference cost?

This benchmark belongs to Decisio because it evaluates the in-process scorer/controller contract.
Externally served endpoint evaluation remains Performance Lab responsibility.

## Two evidence layers

### Fixed-state decision quality

The frozen fixture `benchmarks/fixtures/snake-controller-v1.jsonl` contains current Snake states with
body geometry, direction, food and optional bounded recent-head memory. Every configuration sees the
same state.

A versioned independent planner, `snake_dynamic_body_planner_v1`, performs bounded breadth-first
search over the **moving body**, not Manhattan distance alone. A food path counts as safe only when
post-food play survives a configurable minimum horizon (default four moves), unless eating fills the
board. Search exhaustion proves no safe path within the exact state graph reached under the configured
depth; reaching a node/depth budget is reported as `bounded_unknown`, never as false optimality.

Reported fixed-state metrics:

- `oracle_coverage`: fraction of states where every candidate is resolved without hitting a
  planner node/depth bound; bounded states stay in the ledger but are excluded from optimality
  denominators;
- `optimal_set_agreement`: on oracle-complete states, the chosen action is in the planner's
  best-action set;
- `mean_rank_regret`: on oracle-complete states, chosen planner rank minus one, so near-equivalent
  choices are distinguishable from large misses;
- `mean_extra_safe_food_steps`: extra proven-safe steps to the current food versus the shortest
  proven-safe candidate when both values are known;
- `catastrophic_miss_rate`: a proven non-safe-food action is chosen when another supplied action has
  a proven safe-food path;
- `order_change_rate`: choice changes when the same candidates are reversed;
- invalid-choice rate and p50/p95 decision latency.

The planner is a bounded reference policy, not a claim of globally perfect Snake play. Planner
version and bounds are part of evidence identity.

### Full episodes

Configurations also run deterministic seeded games. Episode evidence reports:

- food eaten and completion ratio;
- survival steps and board-filled rate;
- moves per food;
- revisit-step rate;
- maximum steps since food, stall rate and exact repeated-state loop rate;
- controller failures, generated-token count and model-decision latency.

`board_filled` is the strict solved condition. Completion ratio remains useful when no configuration
fills the board:

```text
food_eaten / (board_cells - initial_snake_length)
```

## Configuration matrix

The initial matrix isolates controller/readout choices before broad model tuning:

| ID | Scorer | Input | Prompt mode | Execution | Controller |
| --- | --- | --- | --- | --- | --- |
| `direct-stateful-verbose` | direct A/B/C logits | verbose | question-first stateful | shared | model |
| `direct-fresh-verbose` | direct A/B/C logits | verbose | question-first stateful | fresh | model |
| `direct-stateful-compact` | direct A/B/C logits | compact | question-first stateful | shared | model |
| `semantic-verbose` | semantic v2 | verbose | semantic comparative v2 | scorer default | model |
| `semantic-independent-verbose` | semantic v1 | verbose | semantic independent v1 | scorer default | model |
| `direct-adjacent-food` | direct A/B/C logits | verbose | question-first stateful | shared | adjacent-food |
| `generated-verbose` | generated JSON baseline | verbose | generated JSON v1 | generated | model (optional) |

The stateful-vs-fresh direct comparison is deliberately controlled: both variants compile the exact
same question-first stateful prompt and therefore the same prompt hash. Only execution changes:
`shared` may restore the reusable prefix; `fresh` evaluates the same compiled prompt without
shared-prefix execution. A prompt-order change is a different experiment and must not be attributed
to caching.

Do not expand into a model/quantization Cartesian product until this first matrix identifies useful
controller families. Different model artifacts are separate evidence identities.

## Append-only result ledger

Every run appends a `run_start` manifest **before GGUF backend construction**, a
`runtime_ready` row after the exact runtime identity is loaded, one terminal
`configuration_result` for every attempted configuration, and a `run_end` row from the runner's
finalization path. Rows are never overwritten. A model/runtime load failure therefore still leaves
the requested model path/runtime parameters plus a failed `run_end`; a handled configuration
failure keeps its partial evidence and error. An externally killed process can still leave an
incomplete run, but its earlier append-only rows remain available for diagnosis.

Each row records at least:

- benchmark schema/version and unique run ID;
- source commit/branch/dirty state when available;
- fixture path + SHA-256;
- planner version and search/survival bounds;
- configuration ID, scorer, input format, prompt mode, execution mode, effective prefix reuse and controller;
- GGUF filename/SHA/size/quantization, llama.cpp binding/runtime, CPU/context/batch/thread settings;
- selected fixed cases plus episode seeds/board/horizon/stall threshold, hashed as a protocol fingerprint;
- fixed-state metrics, oracle coverage, raw normal/reversed decision readouts and detailed
  per-case planner evidence;
- episode metrics and per-seed outcomes;
- runtime logical/physical tokens, cache metrics and physical/logical ratio;
- completed/failed status and error text.

Default local ledger:

```text
.artifacts/snake-controller/history.jsonl
```

CI uploads the ledger as a retained artifact. Multiple ledger files can be summarized together; the
history summarizer groups only comparable
`configuration + model SHA + fixture SHA + protocol SHA` identities.

## Run

```bash
uv run python -m benchmarks.run_snake_controller_benchmark \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --output .artifacts/snake-controller/latest.json \
  --ledger .artifacts/snake-controller/history.jsonl \
  --threads 2 --threads-batch 2
```

For a cheap smoke, reduce fixed states and episode length without relabelling it representative:

```bash
uv run python -m benchmarks.run_snake_controller_benchmark \
  --model /path/to/model.gguf \
  --output .artifacts/snake-controller/smoke.json \
  --ledger .artifacts/snake-controller/history.jsonl \
  --configs direct-stateful-verbose direct-fresh-verbose semantic-verbose \
  --fixed-limit 4 --episode-seeds 7 19 --episode-max-steps 12
```

Summarize one or more append-only ledgers:

```bash
uv run python -m benchmarks.summarize_snake_controller_history \
  --ledger .artifacts/snake-controller/history.jsonl \
  --output .artifacts/snake-controller/history.md \
  --json-output .artifacts/snake-controller/history-summary.json
```

## Interpretation

Do not collapse quality and latency into an arbitrary weighted score. Interpret in order:

1. oracle coverage, controller failures and catastrophic misses;
2. fixed-state agreement/rank regret/extra safe-food steps and order robustness;
3. full-episode food/completion/survival/stall/loop evidence;
4. latency, physical tokens and reuse among configurations with acceptable quality.

A screening result selects configurations for further evidence; it is not automatically a product
default. A later holdout fixture should be frozen before prompt/controller tuning is declared complete.
