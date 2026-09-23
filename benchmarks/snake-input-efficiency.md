# Snake input and prefix-reuse diagnostic

Status: diagnostic only; no scorer promotion or default change.

Local working-tree experiment based on `461aa54e104363a191f569a6d3bcaf6e68180f8e`
with uncommitted Snake input and opt-in letter-prefix changes. This is not exact-head integration
or frozen scorer-gate evidence. Exact requests, prompt hashes and scores are in local artifacts
under `.artifacts/snake-efficiency/`; rerun using `examples.snake.benchmark_inputs`.

## Scope and identity

- Qwen3.5-0.8B Q4_K_M GGUF, SHA-256
  `f5b14da98939b60bbe1019a964eba656407e1e0b64f1fe3003ff6d650e93bfec`.
- llama-cpp-python 0.3.35, local arm64 CPU; context 8192, 5 execution threads,
  11 batch threads, batch and microbatch both 128 or both 64.
- Direct letter baseline versus opt-in `letter_question_prefix_v1`; zero generated tokens.
- Six easy states with food above/right/below the head, adjacent or two cells away;
  normal/reversed option order. Batch 128: two rounds, 24 rows per variant.
  Batch 64: one round, 12 rows per variant. Repetitions are not independent examples.
- Warmup and model load excluded. Timings include request compilation and scoring; game/UI
  roundtrip excluded. Shared rows include the first cache miss. Runtime configurations ran
  sequentially, not concurrently. These small runs do not establish stable hardware tuning.

## Results

| Batch | Input / execution | Correct rows | Median seconds | Physical / logical tokens |
| --- | --- | --- | --- | --- |
| 128 | verbose fresh | 16/24 | 3.210 | 15684/15684 |
| 128 | compact fresh | 8/24 | 1.726 | 8640/8640 |
| 128 | question-first compact fresh | 10/24 | 1.739 | 8640/8640 |
| 128 | question-first compact shared | 10/24 | 1.575 | 8640/8640 |
| 64 | compact fresh | 4/12 | 1.700 | 4320/4320 |
| 64 | question-first compact fresh | 5/12 | 1.904 | 4320/4320 |
| 64 | question-first compact shared | 5/12 | 1.448 | 3616/4320 |

The shared label at batch 128 does **not** imply token reuse: the fixed prefix is shorter than a
native checkpoint boundary, so cache hits were zero. Its timing difference is not evidence of
cache acceleration. At batch 64 there were 11 hits out of 12 requests; each warm request processed
296 rather than 360 tokens. Cached sequence state occupied 20,989,804 bytes.

Fresh/shared logits were exactly equal at each batch size (maximum difference 0, no changed
argmaxes). Pairing batch 64 against batch 128 round zero also gave zero logit differences and zero
changed argmaxes across all 36 comparable rows.

Compaction changes behavior: it always selected RIGHT in these six states. Compared with verbose,
10 of the 12 state/order combinations changed argmax (20/24 including repetitions). Only the two
orders with adjacent food on the right retained the same choice. Verbose input changed choice
under reversal in 3/6 states; question-first compact changed in 1/6; ordinary compact changed in
0/6 but was inaccurate. Order stability alone is not quality.

## Decision and limits

Keep verbose input, fresh direct scoring and the model controller as defaults. Expose compact
input and question-prefix reuse as separate opt-in experiments. Reuse is correct on this measured
scope, but the reordered/compacted prompt has worse task quality. Do not promote the combination
as an improved controller.

An independently selectable `adjacent-food` application policy skips scoring when eating leaves
at least one immediate exit. Unit tests cover skipping the model and rejecting an immediate dead
end; no episode success or latency claim is made for this policy. It is not a route planner.

Remaining evidence: representative episodes, body traps, leftward routes, loop states,
missing/irrelevant evidence perturbations, other models/precisions, and repeatable timing/memory
measurements. Peak RSS is recorded per process in the raw rows, but is not an isolated per-variant
memory measurement. The canonical 2B CPU scorer gates remain unchanged.
