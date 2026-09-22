# Product

Status: active  
Owner: repository

## Mission

Decisio exists to make general-purpose open-weight language models directly useful as fast, typed decision engines when an application needs a bounded semantic judgment rather than generated text.

Its durable objective is to determine how much decision quality, robustness and efficiency can be obtained **without training a new model**, by changing the inference/readout strategy.

## Primary users / consumers

- AI/ML engineers building automation, routing, triage, agent control, policy checks or classification systems whose valid outputs are known at runtime.
- Application engineers who want local/open decision inference without parsing generated prose or trusting self-reported confidence.
- Researchers and practitioners comparing generative structured output with non-generative decision readouts.

The primary consumer is software, not a conversational end user.

## Core problems / jobs

Decisio owns the following job:

> Given state/evidence, a semantic question and a bounded set of valid runtime-defined alternatives, return a typed decision signal that software can consume directly without autoregressive answer generation.

The initial problem surface includes:

- boolean semantic judgments;
- single-choice decisions over runtime-defined candidates;
- explicit assessment of whether the supplied evidence is sufficient to answer;
- many decisions over the same state efficiently.

## Value proposition

For decision-shaped workloads, Decisio aims to provide:

- **zero answer generation** — no decoding loop for the final decision;
- **no mandatory training** — start from an existing open-weight causal LLM;
- **semantic candidates** — score the meaning of each candidate rather than an arbitrary A/B/C label;
- **shared computation** — reuse state/question work across candidates and related decisions;
- **typed outputs** — no JSON repair or free-form parsing on the decision path;
- **honest probability semantics** — distinguish conditional model scores from calibrated probability of correctness;
- **local/open execution** — inspect model, prompt, score path and benchmark artifacts.

## Core product hypothesis

A normal causal LLM already contains enough semantic information in its logits/hidden state to support useful bounded decisions without generating text.

Decisio's primary hypothesis is that **comparative candidate-level binary semantic scoring** is a better general decision primitive than arbitrary answer-token scoring or candidate-independent binary scoring.

For candidate `c_i`:

```text
state + question + all alternatives + candidate_i
                         |
                         v
                    YES / NO logits
              |
              v
score_i = logit(YES) - logit(NO)
```

Candidate scores are then normalized across the supplied alternatives.

A separate answerability judgment estimates whether the state contains enough information to answer at all.

## Reference runtime

v1 uses Qwen 3.5 4B Q4_K_M GGUF via llama.cpp on CPU. Promotion evidence pins the exact
artifact/runtime/host/scorer identity; BF16/Transformers is not equivalent. Scores remain
uncalibrated unless a calibration artifact matches that identity.

## Meaningful differentiation

Decisio is not differentiated merely by "reading logits"; that already exists in open projects.

Its intended differentiation combines:

1. **comparative semantic candidate scoring** rather than arbitrary answer tokens;
2. **separate answerability and honest probability status**;
3. **shared/parallel execution with reproducible strategy evidence**;
4. **training-free first**, adding training only if evidence shows a meaningful ceiling.

## Core outcomes

A successful Decisio user should be able to:

- replace a bounded generative classification/routing call with a typed non-generative decision call;
- define candidates dynamically at runtime;
- receive a ranked/normalized distribution plus answerability and provenance;
- process multiple candidates/questions without re-reading the same long state unnecessarily;
- understand whether returned values are raw/conditional/calibrated;
- benchmark the chosen model/scorer on their own workload before automation.

## Non-goals

Decisio deliberately does not own:

- general-purpose chat or free-form generation;
- chain-of-thought generation;
- workflow orchestration or business-rule execution;
- tool execution or agent planning;
- training/fine-tuning in the initial product milestone;
- reproducing Jev's private architecture or RLCD;
- claiming raw scores are calibrated confidence;
- hiding model/prompt/runtime identity behind an opaque API;
- supporting every model/backend before the reference implementation is validated;
- multimodal decision support in v1 even if the reference checkpoint is multimodal-capable.

## Product principles

- **Decisions, not strings.** If the valid output space is bounded, do not generate prose to recover it.
- **Training-free before trained.** Establish the inference-time ceiling before adding learned components.
- **Constrain before score.** Deterministic validity/safety/business constraints stay with the owning domain and remove impossible candidates before probabilistic scoring.
- **Semantic options over arbitrary verbalizers.** Candidate meaning should drive the score, not which letter represents it.
- **Answerability is separate from preference.** "Which option?" and "Can this be answered?" are different questions.
- **Scores are not confidence until calibrated.** API naming and metadata must preserve that distinction.
- **Share expensive context.** Long state should be processed once wherever model/runtime semantics safely allow it.
- **Benchmark the failure modes.** Accuracy alone is insufficient; permutation robustness, missing evidence, calibration, latency and memory matter.
- **Reference implementation before abstraction explosion.** Prove Qwen 3.5 4B Q4_K_M on llama.cpp before generalizing to other runtimes or quantizations.

## Product quality attributes

| Attribute | Importance | Product promise / principle | Technical owner |
| --- | --- | --- | --- |
| Decision correctness | critical | Scoring strategies are evaluated on frozen labeled workloads before claims are made | `benchmarks/`, `docs/roadmap.md` |
| Probability honesty | critical | Uncalibrated outputs are explicitly marked and never presented as probability of correctness | decision schema / scorer |
| Robustness | critical | Meaning-preserving option reordering/wrapping should not silently change semantics | perturbation benchmark |
| Performance | high | No answer generation; reuse shared state when it is safe and beneficial | runtime/backend |
| Reproducibility | high | Results carry model revision, scorer version, prompt hash and runtime metadata | evaluation/result schema |
| Local/open operation | high | Reference path uses inspectable open-weight models and local inference | model/backend |
| Extensibility | normal | Additional models/backends can be added behind explicit capability contracts | adapters |

## Success signals

### Acceptance

The reference implementation can execute boolean and choice decisions with zero generated answer tokens and a stable typed schema.

### Outcome

On frozen evaluation sets, semantic candidate scoring is compared against:

- direct A/B/C or equivalent answer-token scoring;
- autoregressive structured-output generation;
- optional external references when legally/reproducibly available.

The key question is not only "is it accurate?" but "does it improve the decision-specific trade-off?"

### Product impact

Before calling v1 successful, we should have evidence for:

- quality competitive with the strongest training-free baseline;
- lower sensitivity to option order/verbalizer artifacts;
- stronger missing-evidence behavior or a clearly useful answerability signal;
- meaningful latency/throughput improvement over generated structured output;
- measurable shared-state speedup;
- documented cases where the approach should not be used.

## Decision to introduce training

Training is not part of v1.

A training/fine-tuning track becomes justified only if benchmark evidence shows a material ceiling that inference-time methods cannot address, especially in:

- calibration;
- abstention/answerability;
- domain-specific accuracy;
- robust ordinal/numeric decisions.

If introduced, it should be an optional later layer rather than a prerequisite for using Decisio.
