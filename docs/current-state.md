# Current state

Status: active  
Owner: repository

## Current milestone

Make Decisio a stateful local decision runtime: keep stable task context reusable, score changing application state with typed zero-generation choices, and prove cache reuse against fresh execution on the pinned llama.cpp/GGUF path.

Active plans: [llama.cpp reference runtime evidence closure](workstreams/llama-cpp-reference-runtime.md) and [repository quality/adoption](repository-quality.md).

## Active workstreams

| Workstream | State | Blocker |
| --- | --- | --- |
| llama.cpp reference runtime | DONE | local-GGUF backend/CLI and scorer primitives implemented |
| Shared context-state fast path | DONE | native-batch-safe branching + bounded repeated-state cache |
| Scorer gate v2 | FAILED | short independent workload does not justify v2 promotion |
| Repeated-state gate v3 | ACTIVE | frozen 48-case/8-state scoped experiment; 2B reference execution is local/manual, not PR CI |
| Product foundation | ACTIVE | supported direct-choice DecisionSession integrated; answerability/calibration remain planned |
| Snake stateful reference loop | ACTIVE | fixed decision context + current-only dynamic state + direct logits + fresh/cache oracle |
| Snake controller quality benchmark | ACTIVE | bounded dynamic-body oracle + append-only fixed/episode matrix implemented; reference 2B screening evidence pending |
| Repository adoption hardening | ACTIVE | one-command demo, current docs and public intake/package metadata are being integrated; GitHub settings remain external |

## Reference identity

The canonical evidence artifact remains Qwen3.5-2B Q4_K_M from
`unsloth/Qwen3.5-2B-GGUF` revision
`1c466474d208da1a7c4b8cb87ebcdac78f160e34`, SHA-256
`aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223`,
with `llama-cpp-python==0.3.35` on CPU.

The integrated backend also exposes optional Apple Metal execution through `--device metal`. It
uses the same GGUF scoring and reusable sequence-state path, records its offload configuration in
runtime identity, and requires a Metal-enabled `llama-cpp-python` build. This is an operational
runtime option, not evidence equivalent to the pinned CPU reference.

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

Repeated-state gate v3 is frozen before representative execution. The 2B reference run is intentionally local/manual rather than automatic PR CI; its fixture, scorer semantics and precommitted thresholds remain unchanged. Fixture SHA
`f9e5f56128f93efb952f1fc3f4f38441150cb0c29906f688977ffa69ea61338a` covers 48 unique decisions
in eight shared-state groups, four families, 2/4/8 candidates, short/medium/long state tiers and
normal/reversed candidate order. Its precommitted gate requires comparable quality, zero semantic
order changes, exact cache behavior, <=50% physical/logical tokens, and at least 2x p50/p95 group
latency advantage over generated JSON. See `benchmarks/repeated-state-gate-v3.md`.

## Product direction

The general semantic-v2 gate remains valid evidence about that scorer, but it no longer defines the
whole product thesis. The primary direction is the stateful runtime contract demonstrated by Snake:
fixed decision context, current-only dynamic state, deterministic candidate sensors, direct
zero-generation choice readout and observable context reuse.

## Next

1. Validate the exact-head Snake stateful direct path on real-model smoke: cached and fresh stateful prompts must return identical choices/scores and cached execution must reduce physical token work.
2. Run repeated-state gate v3 locally on the unchanged pinned 2B CPU identity and record PASS/FAIL with host/runtime identity, without broadening the semantic-v2 claim.
3. Run the Snake controller screening matrix on the pinned reference 2B model; require oracle coverage, fixed-state quality, episode outcomes and append-only evidence before selecting a controller family.
4. Freeze a holdout Snake fixture before prompt/controller tuning is treated as validated; cache efficiency is not controller quality.
5. Exercise the supported DecisionSession contract in local 2B evidence without treating API stability as a quality/performance endorsement.
6. Protect `main` and add GitHub description/topics/social preview through repository settings; source-controlled checks cannot substitute for those settings.
