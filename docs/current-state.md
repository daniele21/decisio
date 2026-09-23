# Current state

Status: active  
Owner: repository

## Current milestone

Make local GGUF + llama.cpp the Decisio v1 reference runtime and decide where zero-generation
semantic scoring is actually useful on the pinned Qwen3.5-2B Q4_K_M CPU path.

Active plan: [llama.cpp reference runtime migration](workstreams/llama-cpp-reference-runtime.md).

## Active workstreams

| Workstream | State | Blocker |
| --- | --- | --- |
| llama.cpp reference runtime | DONE | local-GGUF backend/CLI and scorer primitives implemented |
| Shared context-state fast path | DONE | native-batch-safe branching + bounded repeated-state cache |
| Scorer gate v2 | FAILED | short independent workload does not justify v2 promotion |
| Repeated-state diagnostic | ACTIVE | compare cached v2 against generated JSON on one long shared state |
| Product foundation | ACTIVE | PR #1 remains draft until the scorer scope is decided |

## Reference identity

The canonical evidence artifact remains Qwen3.5-2B Q4_K_M from
`unsloth/Qwen3.5-2B-GGUF` revision
`1c466474d208da1a7c4b8cb87ebcdac78f160e34`, SHA-256
`aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223`,
with `llama-cpp-python==0.3.35` on CPU.

## Scorer-gate v2 result

Exact-head run `35788235063` completed the full 64-case matrix and **FAILED** without weakening any
precommitted criterion.

Passed: runtime identity; shared/fresh and repeated-state correctness; overall quality
(`50/64` versus strongest baseline `53/64`); order robustness (`0/64` changes); native zero
generation.

Failed: `evidence_entailment` was `12/16` versus `16/16` for the strongest baseline, and
short-workload latency was semantic p50 `829.39 s` versus generated JSON `199.38 s`.

The four missed entailment cases are exact arithmetic/time conclusions (team size, storage, schedule,
budget). They are diagnostic evidence; the prompt is not tuned against these observed failures.

All 64 short rows used conservative fresh fallback. Semantic v2 made 240 fresh candidate evaluations
and processed 53,333 physical input tokens per measured round.

## Repeated-state evidence

The same 2B run proved the long-state cache mechanism independently: cached scoring matched fresh
exactly, evaluated 526 physical tokens versus 2574 fresh, and observed 8.998 s versus 40.009 s
(~4.45x fresh-path speedup).

Diagnostic v1 confirmed the performance mechanism but exposed a workload confound: semantic v2 was
~4.75x faster than generated JSON (18.12 s versus 86.00 s p50) with 95.2% token reuse, but scored
2/14 because questions referenced opaque case IDs inside the long state. Generated JSON scored 14/14.
That mixes decision quality with ID dereferencing, so it is not accepted as product evidence.

Diagnostic v2 is predeclared to keep the same long shared state/cache while putting the relevant case
evidence directly in each question. It remains diagnostic-only with no post-hoc promotion threshold.

## Next

1. Run repeated-state diagnostic v2 on the pinned 2B runtime.
2. Choose BUILD, NARROW_SCOPE, CHOOSE_ALTERNATIVE or DO_NOT_BUILD for v2 from that evidence.
3. Freeze any replacement promotion experiment before observing its result.
4. Keep PR #1 draft until scorer scope, durable docs and exact-head integration evidence agree.
