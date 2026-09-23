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
| Repeated-state gate v3 | ACTIVE | frozen 48-case/8-state scoped promotion experiment |
| Product foundation | ACTIVE | PR #1 remains draft until the scorer scope is decided |
| Snake live demo | DONE | branded local OBSERVE → DECIDE → ACT UI over the existing example controller |

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

The 2B runtime oracle proved exact cached-vs-fresh scoring with 526 physical tokens versus 2574 fresh
and ~4.45x observed speedup.

Diagnostic v2 then replicated the product signal on remote run `35840582210`: semantic and generated
both scored 12/14 across two rounds (6/7 unique cases), both missed only the same
performance-regression case, semantic p50 was 14.98 s versus 68.40 s generated (~4.57x), semantic
generated zero answer tokens, and the semantic path evaluated 9,226 physical versus 181,258 logical
tokens. This is diagnostic evidence, not promotion evidence.

Repeated-state gate v3 is now frozen before representative execution. Fixture SHA
`f9e5f56128f93efb952f1fc3f4f38441150cb0c29906f688977ffa69ea61338a` covers 48 unique decisions
in eight shared-state groups, four families, 2/4/8 candidates, short/medium/long state tiers and
normal/reversed candidate order. Its precommitted gate requires comparable quality, zero semantic
order changes, exact cache behavior, <=50% physical/logical tokens, and at least 2x p50/p95 group
latency advantage over generated JSON. See `benchmarks/repeated-state-gate-v3.md`.

## Next

1. Run repeated-state gate v3 on the exact pinned 2B CPU runtime.
2. If PASS, adopt `NARROW_SCOPE` for repeated-state decisions only; scorer-gate v2 remains FAIL.
3. If FAIL, preserve the failed criterion and choose a narrower/new scorer experiment or alternative.
4. Keep PR #1 draft until product scope, docs and exact-head integration evidence agree.
