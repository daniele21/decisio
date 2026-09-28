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
| Repeated-state gate v3 | FAILED | cache/runtime criteria passed strongly, but semantic-v2 quality and p95 latency criteria failed on the pinned 2B local run |
| Product foundation | ACTIVE | supported direct-choice DecisionSession integrated; answerability/calibration remain planned |
| Snake stateful reference loop | ACTIVE | fixed decision context + current-only dynamic state + direct logits + fresh/cache oracle |
| Snake controller quality benchmark | ACTIVE | first pinned-2B direct v1 screening completed; stateful/fresh matched exactly but quality/order robustness were insufficient; direct v2 remediation requires rerun |
| Repository adoption hardening | DONE | one-command demo, docs, package metadata and public intake integrated; GitHub settings remain external (#9) |

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

The frozen repeated-state gate v3 was then executed locally on the pinned Qwen3.5-2B Q4_K_M CPU
identity and **FAILED** without changing the fixture or thresholds. Cache reuse passed exactly:
8 cold misses, 40 hits, zero fallbacks, zero semantic order changes and 94,244 physical versus
1,058,852 logical input tokens (~8.9%). Semantic-v2 nevertheless scored 32/48 versus generated
JSON 39/48, failing overall quality, evidence-entailment/rule-application family guardrails and the
4-candidate guardrail. Group latency narrowly passed the 2x p50 target (93.34 s vs 187.42 s) but
missed the 2x p95 target (226.43 s vs 438.35 s). This closes semantic-v2 promotion for the scoped
repeated-state path while preserving the runtime/cache evidence. See
`benchmarks/repeated-state-gate-v3.md`.

## Snake direct screening evidence

The first complete pinned-2B direct screening ran on clean `main` commit
`263f7ba1274f6f798d7a93a3c0cf4fcfffeae92f`. Stateful and fresh direct execution produced the
same fixed-state choices/scores and the same four episode outcomes, proving cache execution did not
change semantics. Both variants achieved only 5/10 fixed-state optimal-set agreement, 20%
catastrophic misses and 30% candidate-order changes; median episode food was 16 with 50% loop rate,
75% stall rate and 25% controller-failure rate.

The stateful path reused 151,808 of 503,070 logical input tokens (~30.2%) with 593 cache hits and one
miss. Fixed-state p50 latency improved from 40.44 s fresh to 5.11 s stateful, but long episodes did
not retain that advantage because the runtime snapshotted roughly 23 MB of prefix state on each
shared call in addition to restoring cached state. Direct v2 therefore canonicalizes candidates by
stable ID before A/B/C lettering and reuses the existing cached prefix snapshot instead of capturing
it again on cache hits. The representative 2B screening must be rerun before holdout selection.

## Product direction

Semantic-v2 now has two failed promotion gates and remains an experimental comparison path. The
primary product hypothesis is stateful direct choice: canonical candidate ordering, one
zero-generation option-logit readout, deterministic constraints first, and exact fresh equivalence.

## Next

1. Rerun the unchanged Snake controller screening on the pinned 2B model with direct v2 and compare stateful vs fresh exact outputs, quality, physical tokens, snapshot/restore bytes and latency.
2. If the remediated direct controller has acceptable screening quality, freeze a separate holdout fixture before any further prompt/controller tuning.
3. Exercise the supported DecisionSession contract on the pinned 2B model without treating API stability as a quality/performance endorsement.
4. Protect `main` and add GitHub description/topics/social preview through repository settings; source-controlled checks cannot substitute for those settings.
