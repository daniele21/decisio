# Current state

Status: active  
Owner: repository

## Current milestone

Make Decisio a stateful local decision runtime: reuse stable model context across changing
application state and return bounded typed actions with zero answer generation.

Active plan: [llama.cpp reference runtime evidence closure](workstreams/llama-cpp-reference-runtime.md).

## Workstreams

| Workstream | State | Current boundary |
| --- | --- | --- |
| llama.cpp reference runtime | DONE | local GGUF backend, direct logits and provenance implemented |
| Shared context-state fast path | DONE | exact single-sequence snapshot/restore + bounded prefix cache |
| Semantic scorer gate v2 | FAILED | short/fresh semantic-v2 is not promoted |
| Repeated-state gate v3 | FAILED | cache mechanics passed; semantic-v2 quality and global p95 promotion criteria failed |
| DecisionSession | ACTIVE | supported direct-choice API; answerability/calibration remain planned |
| Snake controller benchmark | ACTIVE | direct-v1 2B screening retained; direct-v2 remediation requires rerun |
| Repository adoption hardening | DONE | source-controlled onboarding/docs/intake integrated; GitHub settings remain #9 |

## Reference identity

Representative evidence pins Qwen3.5-2B Q4_K_M from
`unsloth/Qwen3.5-2B-GGUF` revision
`1c466474d208da1a7c4b8cb87ebcdac78f160e34`, SHA-256
`aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223`,
with `llama-cpp-python==0.3.35` on CPU. Metal is supported operationally but is a separate evidence
identity.

## Evidence

**Semantic-v2.** The frozen short/fresh scorer gate remains FAIL. The later pinned-2B repeated-state
gate also **FAILED** without changing thresholds: cache behavior passed with 8 misses, 40 hits, zero
fallbacks/order changes and 94,244 physical versus 1,058,852 logical tokens (~8.9%), but semantic-v2
scored 32/48 versus generated JSON 39/48. Group p50 met the 2x target (93.34 s vs 187.42 s); p95
missed it (226.43 s vs 438.35 s). Semantic-v2 is therefore experimental, not promoted. See
`benchmarks/repeated-state-gate-v3.md`.

**Direct Snake v1.** Clean `main` commit
`263f7ba1274f6f798d7a93a3c0cf4fcfffeae92f` proved stateful and fresh direct execution returned
identical choices/scores and identical four-episode outcomes. Quality was insufficient for holdout:
5/10 optimal-set agreement, 20% catastrophic misses and 30% candidate-order changes. Stateful reused
151,808/503,070 logical tokens (~30.2%) with 593 hits/1 miss; fixed-state p50 improved from 40.44 s
fresh to 5.11 s stateful. Long episodes lost that advantage because each shared call also
re-snapshotted roughly 23 MB of prefix state.

**Direct v2 remediation.** Candidate IDs are canonicalized before A/B/C lettering so caller order
compiles to the same one-pass direct prompt/readout mapping. On cache hits the runtime reuses the
existing prefix snapshot instead of serializing it again. Prompt version and ordering strategy are
part of the Snake benchmark protocol fingerprint, so v1 evidence remains separate.

## Product direction

The promoted v1 hypothesis is stateful direct choice: deterministic constraints first, canonical
candidate ordering, one zero-generation option-logit readout, stable-context reuse and exact fresh
equivalence.

## Next

1. Rerun the unchanged Snake screening locally on the pinned 2B identity with direct v2; compare
   exact stateful/fresh outputs, quality, physical tokens, snapshot/restore bytes and latency.
2. Freeze a separate holdout only if the remediated screening quality is acceptable.
3. Exercise `DecisionSession` on the pinned 2B identity without turning API stability into a
   quality/performance claim.
4. Complete repository settings tracked by #9.
