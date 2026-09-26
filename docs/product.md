# Product

Status: active  
Owner: repository

## Mission

Decisio exists to turn a local open-weight causal LLM into a **stateful decision runtime** for applications that repeatedly need bounded typed actions while their world state changes.

Its durable objective is to compile stable decision context once, safely reuse the model context state, and evaluate only the changing state/action suffix wherever runtime semantics allow it — while remaining training-free and generating zero answer tokens on the native path.

## Primary users / consumers

- AI/ML engineers building automation, routing, triage, agent control, policy checks or classification systems whose valid outputs are known at runtime.
- Application engineers who want local/open decision inference without parsing generated prose or trusting self-reported confidence.
- Researchers and practitioners comparing generative structured output with non-generative decision readouts.

The primary consumer is software, not a conversational end user.

## Core problems / jobs

Decisio owns the following job:

> Given a stable decision contract, changing application state and a bounded set of valid runtime-defined alternatives, return repeated typed decisions while reusing the stable model context instead of re-prefilling it on every step.

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

The initial scorer hypothesis was that **comparative candidate-level binary semantic scoring**
would be a better general decision primitive than arbitrary answer-token scoring or
candidate-independent binary scoring.

The first representative 2B short/fresh scorer gate did **not** support that as a general default.
Semantic v2 therefore remains experimental, with the active question narrowed to repeated-state
workloads. Direct A/B/C option-token scoring remains an explicit benchmark baseline and is also a
legitimate low-latency application path for small bounded controls such as Snake.

For semantic candidate `c_i`:

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

v1 uses Qwen 3.5 2B Q4_K_M GGUF via llama.cpp on CPU. Promotion evidence pins the exact
artifact/runtime/host/scorer identity; BF16/Transformers is not equivalent. The 2B reference keeps
the local CPU path practical; it is not a claim that 2B is universally better than larger compatible
GGUFs. Scores remain uncalibrated unless a calibration artifact matches that identity.

## Supported Python boundary

The first supported high-level library contract is `DecisionSession`. It deliberately freezes only
the stateful direct-choice path already exercised by the reference loop:

- one local GGUF/llama.cpp runtime owned for the session lifetime;
- one stable decision context per session;
- changing JSON-serializable state plus runtime-defined valid `Candidate` objects per decision;
- direct A/B/C/... option-logit readout with zero generated answer tokens;
- explicit `fresh=True` execution of the identical prompt as the correctness/debug oracle;
- typed `DecisionResult` carrying scorer identity, model provenance, execution mode and runtime reuse
  metrics;
- deterministic `close()` and context-manager lifecycle.

This is a **software contract**, not a model-quality or latency endorsement. Pinned 2B controller and
repeated-state evidence remains a separate evidence obligation. The high-level API does not expose a
generic scorer selector, calibration, answerability, hosted execution or workflow orchestration.

## Meaningful differentiation

Reading option logits is **not** the differentiator. SemIf independently demonstrates direct typed
option scoring, shared-state execution, multiple backends and calibration. Decisio deliberately
builds on the same broad primitive but chooses a different product boundary:

- **state is a runtime resource, not just request text** — stable decision context is compiled/prefilled once and reused across many changing decisions;
- **constraints before probabilities** — deterministic domain facts remove impossible actions before the model sees the candidate set;
- **static context vs dynamic state is explicit** — policy/task semantics stay in the reusable prefix; current world state and deterministic sensors stay in the changing suffix;
- **fresh equivalence is the oracle** — an optimization is not accepted merely because it records a cache hit;
- **local GGUF + llama.cpp is the opinionated v1 runtime** rather than a multi-backend research matrix;
- **typed action, provenance and later abstention/answerability** are part of the decision contract.

The product shorthand is: **compile stable context once; make many typed local decisions.**

## Core outcomes

A successful Decisio user should be able to replace bounded generation with typed decisions over
runtime-defined candidates, reuse shared context, inspect probability/provenance status, and
benchmark the chosen model/scorer before automation.

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
- **Choose the readout deliberately.** Prefer semantic candidate readouts when evidence supports them; direct option-token logits are valid for latency-oriented bounded controls, but scorer identity and order/verbalizer sensitivity must stay explicit.
- **Answerability is separate from preference.** "Which option?" and "Can this be answered?" are different questions.
- **Scores are not confidence until calibrated.** API naming and metadata must preserve that distinction.
- **State is first-class.** Split stable decision context from changing world state; process the stable prefix once wherever model/runtime semantics safely allow it.
- **Benchmark the failure modes.** Accuracy alone is insufficient; permutation robustness, missing evidence, calibration, latency and memory matter.
- **Reference implementation before abstraction explosion.** Prove Qwen 3.5 2B Q4_K_M on llama.cpp before generalizing to other runtimes or quantizations.

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
- measurable physical-token reduction and latency benefit from stable-context reuse;
- documented cases where the approach should not be used.

## Decision to introduce training

Training is not part of v1.

A training/fine-tuning track becomes justified only if benchmark evidence shows a material ceiling that inference-time methods cannot address, especially in:

- calibration;
- abstention/answerability;
- domain-specific accuracy;
- robust ordinal/numeric decisions.

If introduced, it should be an optional later layer rather than a prerequisite for using Decisio.
