# Current state

Status: active  
Owner: repository

## Current milestone

Make local GGUF + llama.cpp the Decisio v1 reference runtime, then decide the scorer on the same
artifact/runtime class users run.

Active plan: [llama.cpp reference runtime migration](workstreams/llama-cpp-reference-runtime.md).

## Active workstreams

| Workstream | State | Blocker |
| --- | --- | --- |
| llama.cpp reference runtime | DONE | local-GGUF backend/CLI and scorer primitives implemented |
| Shared context-state fast path | DONE | native-batch-safe branching + bounded repeated-state cache |
| Scorer decision | ACTIVE | frozen 64-case gate-v2 on pinned 2B Q4_K_M pending |
| Product foundation | ACTIVE | PR #1 remains draft until representative evidence |
| Repository quality | ACTIVE | final exact-head integration evidence |

## Product/runtime decision

The v1 canonical evidence target is Qwen3.5-2B Q4_K_M GGUF through llama.cpp on CPU.

Scorer-gate v2 is pinned to:

- source: `unsloth/Qwen3.5-2B-GGUF`;
- revision: `1c466474d208da1a7c4b8cb87ebcdac78f160e34`;
- file: `Qwen3.5-2B-Q4_K_M.gguf`;
- SHA-256: `aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223`;
- size: `1280835840` bytes;
- runtime: `llama-cpp-python==0.3.35`, CPU.

The reference changed from 4B to 2B on 2026-09-22 so the canonical local CPU workflow is materially
easier to run. The switch happened before accepting any 2B scorer-matrix result. Workload, scorer
semantics, numerical tolerances and promotion criteria remain unchanged. Earlier 4B runtime
experiments are diagnostic history, not promotion evidence.

## Implemented today

- strict typed request/result contracts and deterministic compiler;
- semantic v2, semantic v1, letters and generated JSON comparison paths;
- zero answer generation on native scoring paths with explicit uncalibrated probability semantics;
- in-process local-GGUF `LlamaCppBackend` with exact artifact/runtime provenance;
- native-batch-safe candidate branching with conservative fresh fallback;
- byte/entry-bounded repeated-state LRU with physical-token and state-copy metrics;
- frozen 64-case workload, normal/reversed comparison and deterministic gate evaluator;
- CPU timing/p50/p95/throughput/RSS, real-model smoke and Snake evidence.

## Evidence status

Pinned 0.8B llama.cpp smoke established the state-reuse mechanism before the reference-model switch.
Run `35717350247` proved exact shared-vs-fresh scorer equivalence on its smoke fixture. Run
`35726724805` proved a same-state/different-question cache hit with zero score/probability drift,
526 physical tokens versus 2574 fresh, and deterministic cache clear.

Those runs prove the mechanism, not the 2B scorer decision.

## Remaining gate

W5 must run on the exact 2B artifact above with the frozen workload SHA
`087ee8bbec3393609689046ea9c5d8219d0f39562e322180ca8f1e08eb368d3a`, unchanged runtime
settings and unchanged criteria:

- full-workload shared-vs-fresh equivalence;
- long repeated-state cache oracle;
- semantic v2, v1, letters and generated JSON in normal/reversed order;
- quality, family, order, zero-generation and generated-latency checks;
- one warm-up plus four position-balanced performance rounds.

A quality or equivalence failure keeps semantic v2 experimental. No cache-speed threshold is invented
from earlier smaller-model observations.

## Next

1. Run scorer-gate v2 on the frozen Qwen3.5-2B Q4_K_M reference artifact.
2. Diagnose any failed criterion without weakening the precommitted gate.
3. Record exact-head 2B evidence.
4. If the gate passes, return PR #1 to ready and run exact-head integration preflight.
