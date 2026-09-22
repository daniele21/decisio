# Scorer gate v2 — Qwen3.5-2B Q4_K_M + llama.cpp

Status: FROZEN before representative result  
Frozen: 2026-09-22  
Owner: repository

## Decision question

> On the frozen 64-case workload and the same local GGUF/runtime class users run, is comparative
> semantic log-odds v2 useful and robust enough to become Decisio's stable default scorer?

This gate is a product decision experiment, not a claim of broad model quality.

## Reference evidence identity

The representative v2 run is pinned to:

- source: `unsloth/Qwen3.5-2B-GGUF`;
- source revision: `1c466474d208da1a7c4b8cb87ebcdac78f160e34`;
- file: `Qwen3.5-2B-Q4_K_M.gguf`;
- file size: `1280835840` bytes;
- file SHA-256: `aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223`;
- runtime/binding: `llama-cpp-python==0.3.35` CPU wheel;
- device: CPU;
- `n_ctx=8192`, `n_batch=512`, `n_ubatch=512`;
- `n_threads=2`, `n_threads_batch=2`;
- mmap enabled, mlock disabled;
- shared prefix primitive: `single_sequence_state_snapshot_restore`;
- repeated-state cache: `exact_compiler_token_prefix_lru`;
- repeated cache bounds: 2 entries / 256 MiB.

The workflow downloads from the exact source revision and independently verifies the file SHA before
loading it.
The revision pin is intentional: do not substitute `main` or a newer revision merely because the
filename matches; artifact bytes and SHA are part of the evidence identity.

**Reference-artifact amendment — 2026-09-22, before any 2B scorer matrix executed.** The canonical
CPU evidence artifact changed from Qwen3.5-4B Q4_K_M to Qwen3.5-2B Q4_K_M to make the local-first
reference path materially easier to run. The frozen workload, scorer semantics, numerical tolerances
and promotion criteria are unchanged. Earlier 4B runtime experiments remain diagnostic history.

This identity is the reproducible reference artifact only. Decisio remains model-file driven: users
may choose another compatible quantized Qwen GGUF. Such a choice creates a different evidence and
future calibration identity; it does not invalidate the product path.

## Frozen workload

The owned workload has 64 synthetic examples, 16 per family:

- `support_routing`;
- `rule_application`;
- `evidence_entailment`;
- `comparative_nuance`.

Input SHA-256:

```text
087ee8bbec3393609689046ea9c5d8219d0f39562e322180ca8f1e08eb368d3a
```

The same rows are run in original and fully reversed candidate order.

## Compared strategies

1. `semantic` — comparative candidate YES/NO log-odds v2;
2. `semantic-independent` — independent YES/NO log-odds v1;
3. `letters` — direct A/B/C/... next-token baseline;
4. `generated` — minimal autoregressive JSON baseline.

Native semantic/letter paths must report zero generated answer tokens.

## Runtime correctness gate

Representative scoring is blocked unless both runtime oracles pass.

### Full-workload shared vs fresh

For semantic v2 on every frozen case:

- selected choice must match fresh evaluation;
- max absolute score delta <= `1e-3`;
- max binary conditional probability delta <= `1e-4`;
- max cross-candidate distribution delta <= `1e-4`;
- candidate-prefix reuse may checkpoint only at a boundary also reached by fresh native batching;
- when the common prefix is shorter than that safe boundary, execution must fall back to fresh;
- aggregate physical input tokens on the optimized path must never exceed fresh.

The frozen 64-case fixture is therefore a correctness oracle, not a requirement to force reuse on
short prompts. Physical-token reduction remains blocking on the dedicated long-state fixture below.

**Runtime-gate amendment — 2026-09-22, before the scorer matrix executed.** The first 4B runtime
oracle showed that snapshotting an arbitrary common prefix inside a single native decode batch can
preserve argmax while materially changing logits. The runtime contract was narrowed to native-batch
boundaries plus conservative fresh fallback. Numerical tolerances and every scorer-promotion
criterion below remain unchanged.

### Repeated-state cache

A long same-state/different-question fixture must prove:

- same choice as fresh;
- the same numerical tolerances above;
- at least one cache miss/storage on prime;
- at least one cache hit on the second question;
- positive repeated-state reused-token count;
- fewer physical input tokens than fresh;
- cache entries/bytes remain within the frozen bounds;
- explicit clear returns entries and bytes to zero.

Latency and speedup are recorded. No blocking cache-speed threshold is introduced in v2 before
the first representative result.

## Precommitted scorer criteria

The v1 scientific margins are carried forward unchanged.

1. **Overall quality:** normal-order v2 accuracy is no more than 5 percentage points below the
   strongest baseline, and no baseline significantly beats v2 at `p < 0.05` in the exact paired
   test.
2. **Family guardrail:** in every 16-case family, v2 is no more than 2 correct examples worse than
   the strongest baseline for that family.
3. **Order robustness:** v2 changes choice on at most 1/64 examples and is not more order-sensitive
   than the strongest baseline. Ties use highest normal accuracy, then fewer order changes, then the
   fixed order `semantic-independent -> letters -> generated`.
4. **Native invariant:** v2 reports zero generated answer tokens in normal and reversed runs.
5. **Generation trade-off:** after one warm-up and four position-balanced measured rounds, v2 must
   have lower full-workload p50 and p95 latency than generated JSON in the same run. Peak RSS is
   diagnostic only.
6. **Runtime identity:** the comparison report must match every frozen artifact/runtime/cache field
   listed above.

A failed criterion keeps semantic v2 experimental. Do not loosen a threshold after observing the
representative result; diagnose the violated assumption/invariant instead.

## Evidence interpretation

A PASS supports the stable scorer only for this pinned reference configuration and workload. It
does not establish calibrated probability of correctness, universal task generalization, endpoint
deployment performance or all user-selected GGUFs.

The Qwen3.5-0.8B real-model smoke remains mechanism/integration evidence only.
