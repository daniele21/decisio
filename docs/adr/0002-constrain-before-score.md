# ADR 0002 — Constrain before score; compare candidates explicitly

Status: accepted  
Date: 2026-09-21

## Context

The first real Snake rollout exposed two independent problems in the original semantic scorer.

First, the application offered moves to the LLM even when their immediate invalidity was already known deterministically. In the observed Qwen3.5-0.8B smoke, the model repeatedly selected RIGHT and eventually selected it again at the board edge, producing a wall collision with a high relative score.

Second, the v1 semantic scorer judged each candidate in isolation and executed one full model forward per candidate. The normalized output therefore forced a relative winner among independently judged options while paying repeated compute for nearly identical prompts.

## Decision

Decisio adopts two rules.

### 1. Constrain before score

The owning application/domain layer removes alternatives whose invalidity is known exactly before invoking Decisio.

Examples include:

- geometry and collision rules;
- schema/type validity;
- hard resource limits;
- deterministic authorization or policy predicates;
- mutually impossible lifecycle transitions.

If only one valid alternative remains, the caller may resolve it deterministically without model inference.

Decisio remains responsible for semantic preference among the valid alternatives, not for overruling facts already known by the system.

### 2. Comparative semantic scoring is the default hypothesis

The default scorer now evaluates each candidate with the complete alternative set in context:

```text
state + question + all valid alternatives + candidate_i
                         |
                         v
                    YES / NO logits
                         |
                         v
                  candidate log-odds
```

The original candidate-independent binary scorer remains available as an experimental baseline.

Candidate descriptions in the comparative prompt are rendered in a stable semantic order so caller presentation order does not become an accidental ranking signal.

### 3. Batch before shared-cache specialization

All candidate prompts are executed in one backend batch when supported. The Qwen backend selects each row's final hidden state and projects only the requested readout vocabulary rows.

This removes sequential candidate forwards and full-vocabulary projection while preserving a simple reference semantics.

True shared-prefix/cache branching remains a separate optimization. Qwen3.5's hybrid Gated DeltaNet/full-attention text stack makes cache reuse more model-specific than a conventional KV-only decoder, so shared-prefix execution requires explicit fresh-vs-shared equivalence evidence.

## Consequences

### Positive

- deterministic impossibilities cannot win a probabilistic ranking;
- fewer model calls when constraints reduce the candidate set;
- no model call when exactly one candidate remains;
- comparative prompts expose mutual competition among alternatives;
- candidate scoring uses one backend batch instead of N sequential forwards;
- selected-vocabulary projection avoids computing unused output rows;
- v1 semantics remain measurable as a baseline.

### Costs / risks

- filtering correctness becomes part of the caller/domain contract;
- comparative prompts are longer because each candidate sees the alternative set;
- batch execution repeats the shared prefix physically and may increase peak memory;
- comparative Yes/No scoring can still be biased or uncalibrated;
- batch execution is not equivalent to true shared-prefix computation;
- Qwen3.5 CPU inference remains unsuitable for latency claims.

## Evidence required

Before promoting the v2 scorer beyond experimental status:

- compare comparative v2, independent v1, letter-token scoring and generated output on frozen workloads;
- measure candidate-order perturbations;
- measure batched versus sequential output equivalence and latency on representative hardware;
- verify deterministic filters cannot be bypassed by the scorer;
- add fixed Snake-state evaluations rather than relying only on divergent rollouts.

## Reconsider when

Revisit this ADR if benchmark evidence shows that comparative binary scoring is consistently worse than a simpler direct-logit method, or if a backend-specific shared-prefix implementation can be proven equivalent and materially faster.
