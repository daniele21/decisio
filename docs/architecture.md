# Architecture

Status: active  
Owner: repository

## System intent

Decisio converts a compatible causal language model into a bounded semantic decision engine without running an autoregressive answer-generation loop.

Qwen 3.5 4B remains the reference model and is treated as a semantic scorer. The v1 target runtime is now a pinned Q4_K_M GGUF executed through llama.cpp on CPU for representative scorer evidence. Applications provide only alternatives that remain valid after deterministic domain constraints. The runtime compiles state, question and candidates into comparative scoring prompts, reads the required next-token logits, and post-processes them into an explicitly typed result.

## Constraint boundary

Decisio chooses among **valid alternatives**; it does not replace deterministic rules.

```text
raw domain state + raw actions
            |
            v
 deterministic/domain constraints
            |
            v
       valid candidates
            |
            v
          Decisio
            |
            v
  semantic preference among them
```

Examples include geometry, schema validity, hard policy requirements, resource bounds, and other conditions whose truth is already known deterministically. The owning application is responsible for those constraints. If exactly one valid alternative remains, callers may resolve it without model inference.

This boundary avoids spending model compute on impossible options and prevents a probabilistic scorer from overruling facts such as "this move hits a wall."

## Reference-runtime migration

The repository currently contains a PyTorch/Transformers reference backend. That implementation
established scorer/compiler semantics but is being replaced as the product reference path by an
in-process llama.cpp backend over local GGUF artifacts.

The target boundary is:

```mermaid
flowchart LR
    A[Application state] --> B[Deterministic constraints]
    B --> C[ChoiceRequest]
    C --> D[Prompt compiler]
    D --> E[Semantic or letter scorer]
    E --> F[LlamaCpp backend]
    F --> G[Qwen3.5 GGUF]
    G --> H[Requested next-token logits]
    H --> I[Log-odds / softmax]
    I --> J[DecisionResult]
```

llama.cpp owns model execution, quantized kernels, context/batch/sequence mechanics and device
support. Decisio owns prompt/scorer semantics, deterministic constraints boundary, probability
status, provenance, evaluation and the eventual calibration layer.

Representative evidence must bind to the exact GGUF SHA-256, quantization and llama.cpp
runtime/build identity. BF16/Transformers results are not treated as equivalent to Q4_K_M results.

## Current implementation architecture

```mermaid
flowchart LR
    A[Application state] --> B[Deterministic constraints]
    B --> C[ChoiceRequest]
    C --> D[Prompt compiler]
    D --> E[Semantic or letter scorer]
    E --> F[Qwen Transformers backend]
    F --> G[Selected next-token logits]
    G --> H[Log-odds / softmax]
    H --> I[DecisionResult]
```

Current code owners:

| Concern | Current owner |
| --- | --- |
| Request/result contracts | `src/decisio/schema.py` |
| Prompt compilation | `src/decisio/compiler.py` |
| Semantic and letter scoring | `src/decisio/scorers/` |
| Current Qwen/Transformers loading, batching and selected-vocabulary projection (migration source) | `src/decisio/backends/qwen.py` |
| Benchmark execution | `src/decisio/benchmark.py` |
| Paired scorer comparison | `src/decisio/comparison.py` |
| CLI | `src/decisio/cli.py` |

Answerability, shared-prefix reuse and a stable high-level Python engine are **not implemented yet**.

## Target decision flow (planned)

The target shape below is conditional on benchmark evidence and includes planned answerability/shared execution.

```text
Request
  |
  +-- state/evidence
  +-- question
  +-- candidates
          |
          v
   deterministic compiler
          |
          v
 shared state/question prefill
          |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
     candidate A        candidate B        candidate C
          |                  |                  |
      YES / NO           YES / NO           YES / NO
        logits             logits             logits
          |                  |                  |
       log-odds           log-odds           log-odds
          +------------------+------------------+
                             |
                             v
                      relative softmax
                             |
                             +--> choice distribution
                             |
 separate answerability ----+
                             |
                             v
                     typed decision result
```

No answer token needs to be sampled or appended to the sequence.

## Primary scoring method

For each candidate `c_i`, compile a binary comparative judgment whose valid readout is `YES` versus `NO`. The prompt includes the complete alternative set and asks whether `c_i` is the best answer among those alternatives.

The raw candidate score is:

```text
score_i = logit(YES | state, question, alternatives, candidate_i)
        - logit(NO  | state, question, alternatives, candidate_i)
```

For mutually exclusive choice candidates, derive a conditional distribution:

```text
P_i = softmax(score_1 ... score_n)
```

This distribution is conditional on the supplied candidates and **must not be described as calibrated probability of correctness** unless a validated calibration layer is explicitly active.

## Answerability (planned)

Answerability is intended to be modeled separately:

```text
Does the supplied evidence contain enough information to answer this question?
YES / NO
```

The result exposes the answerability signal independently from the choice distribution.

This avoids forcing "insufficient evidence" to compete semantically with ordinary candidates and enables downstream policies such as:

```text
if answerability < threshold:
    escalate / request more evidence
else:
    use candidate distribution
```

Thresholds are application policy, not universal Decisio truth.

## Baselines

The benchmark harness should implement at least two baselines:

### Direct answer-token scoring

Map candidates to answer slots such as A/B/C and read their next-token logits. This establishes comparability with existing zero-generation approaches.

### Autoregressive structured output

Ask the same reference model to generate the smallest valid structured answer. This measures the systems cost and semantic differences introduced by generation.

Baselines are evaluation paths first; Decisio's public runtime should default to the primary semantic scorer rather than expose every experimental method as permanent API surface.

## Shared execution (planned)

The target optimization is hierarchical reuse:

```text
state
  -> reusable state cache/representation
      -> question branch
          -> candidate micro-batch
```

Implementation should initially prefer the simplest cache boundary proven correct for Qwen 3.5.

Correctness comes before maximum cache reuse: shared execution must be continuously compared against fresh execution, because low-level cache/batching differences can move borderline logits.

## Target component map

The following owners are planned, not current public API commitments.

| Concern | Proposed owner | Responsibility |
| --- | --- | --- |
| Public schemas | `src/decisio/schema.py` | requests, candidates, decisions, metadata |
| Prompt/scoring compiler | `src/decisio/compiler.py` | deterministic scoring text/tokens and readout tokens |
| Scorer interface | `src/decisio/scorers/` | semantic binary scorer and experimental baselines |
| Model adapters | `src/decisio/models/` | model-specific load/token/cache/logit capabilities |
| Runtime engine | `src/decisio/engine.py` | orchestration, batching, cache reuse |
| Post-processing | `src/decisio/decision.py` | log-odds, normalization, answerability, policies |
| API/CLI | `src/decisio/api.py`, `cli.py` | stable user entry points |
| Evaluation | `benchmarks/` | frozen data, runners, metrics, reports |
| Calibration | `src/decisio/calibration.py` | later optional post-hoc calibration |

Names are proposed. Implemented owners are listed in **Current implementation architecture** above.

## Public decision primitives

### v1

- `boolean`
- `choice`
- answerability for both

### later, only after semantics are validated

- ordinal `score`
- numeric/distributional estimates
- ranking/top-k
- multi-label decisions

Do not implement every type by disguising it as choice unless the semantics and evaluation support that decision.

## Probability semantics

Every result must carry a status such as:

- `uncalibrated_conditional_scores`
- `temperature_scaled`
- a future validated calibration identifier

The API should expose raw candidate scores in debug/audit mode and always expose the scorer identity.

## Model abstraction

The model adapter must describe capabilities explicitly rather than assume every causal LM supports identical optimizations. llama.cpp/GGUF is the canonical v1 path; additional runtimes remain optional future adapters.

Relevant capabilities include:

- next-token logits;
- exact readout-token verification;
- prefix/state cache creation;
- cache branching/batching;
- selected-vocabulary projection if available;
- quantization mode;
- maximum context;
- backend/device.

Qwen 3.5 4B is the reference implementation, not a permanent dependency boundary.

## Runtime priorities

1. correctness-stable comparative semantic scoring on the pinned Q4_K_M llama.cpp path;
2. explicit GGUF/runtime provenance and local model loading;
3. candidate batching using llama.cpp-supported execution semantics;
4. shared state/question reuse with fresh-path equivalence evidence;
5. multi-question reuse;
6. additional backend/quantization portability only after the reference path is proven.

## Trust and data boundaries

The initial product is local-first. State/evidence is processed by the locally loaded model/runtime and is not sent to a hosted Decisio service.

External model downloads remain governed by the upstream model host and cache tooling.

Benchmark artifacts must avoid embedding sensitive user data.

## Key invariants

- generated answer tokens = 0 on native Decisio scoring paths;
- no silent input truncation;
- deterministic invalid candidates are excluded before semantic scoring when the caller can know validity exactly;
- candidate IDs remain independent from their rendered order;
- scoring/readout tokens are validated against the tokenizer;
- uncalibrated values are labeled as such;
- every benchmark record includes model revision, scorer version, prompt/compiler hash, runtime/backend and timing scope;
- optimized shared execution is compared against a fresh reference path;
- deterministic post-processing for identical logits.

## Architecture questions intentionally left open

These should be answered by evidence rather than preference:

- best binary verbalizer pair (`YES/NO`, alternatives, or multi-verbalizer aggregation);
- whether state-only versus state+question prefix reuse gives the best quality/throughput trade-off;
- whether option scoring should include explicit negative framing or pairwise comparisons;
- whether hidden-state scoring can improve over logit verbalizers without training;
- how much post-hoc calibration helps without task-specific training;
- when an optional trained adapter becomes justified.


## Current implementation boundary

The current code path implements comparative semantic scoring and PyTorch/Transformers candidate batching, but it is no longer the target reference runtime. All candidate prompts are padded into one model batch, final hidden states are selected at each real sequence end, and only requested vocabulary rows are projected. This removes sequential full forwards and full-vocabulary projection without changing the zero-generation contract.

The batch still duplicates the common state/question tokens across rows. Qwen3.5 uses a hybrid 3:1 Gated DeltaNet/full-attention text stack, so true shared-prefix/cache branching requires model-specific equivalence work rather than assuming a conventional KV-only decoder cache. Shared-prefix and multi-question reuse therefore remain pending.
