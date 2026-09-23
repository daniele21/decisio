<p align="center">
  <img src="assets/brand/decisio-app-icon.svg" alt="Decisio" width="120" />
</p>

<h1 align="center">Decisio</h1>

<p align="center">
  <strong>A stateful decision runtime for local LLMs: compile stable context once, then make fast typed decisions over changing state.</strong>
</p>

<p align="center">
  Training-free · stateful context reuse · zero answer tokens · local GGUF + llama.cpp
</p>

<p align="center">
  <a href="https://github.com/daniele21/decisio/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/daniele21/decisio/actions/workflows/ci.yml/badge.svg" />
  </a>
  <a href="https://github.com/daniele21/decisio/actions/workflows/repository-health.yml">
    <img alt="Repository Health" src="https://github.com/daniele21/decisio/actions/workflows/repository-health.yml/badge.svg" />
  </a>
  <img alt="Python >= 3.11" src="https://img.shields.io/badge/Python-%E2%89%A53.11-112543?style=flat-square&logo=python&logoColor=white" />
  <img alt="Runtime: llama.cpp" src="https://img.shields.io/badge/runtime-llama.cpp-03C27E?style=flat-square" />
  <img alt="Model format: GGUF" src="https://img.shields.io/badge/models-GGUF-01C8F6?style=flat-square" />
  <img alt="Status: experimental" src="https://img.shields.io/badge/status-experimental-F59E0B?style=flat-square" />
  <a href="LICENSE">
    <img alt="License: Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-112543?style=flat-square" />
  </a>
</p>

<p align="center">
  <a href="docs/README.md">Docs</a>
  · <a href="docs/architecture.md">Architecture</a>
  · <a href="docs/current-state.md">Current state</a>
  · <a href="benchmarks/README.md">Benchmarks</a>
  · <a href="examples/README.md">Examples</a>
  · <a href="CONTRIBUTING.md">Contributing</a>
</p>

Decisio treats **stable decision context as a runtime resource**, not text to resend blindly on
every request. The intended loop is: prefill the stable task/policy context once, keep a reusable
llama.cpp model-context snapshot, then score only the changing application state, deterministic
sensors and valid actions. Native scoring generates **zero answer tokens** and requires **no
fine-tuning**.

The v1 runtime is deliberately opinionated: local **GGUF + llama.cpp**. Qwen3.5-2B Q4_K_M is the
reference evidence artifact, not a permanent model restriction.

## The product idea

```text
stable decision context
(task, policy, coordinate/sensor semantics)
              |
         prefill once
              |
     reusable model context
        /       |       \
       /        |        \
state t      state t+1   state t+2
+ sensors    + sensors   + sensors
+ valid      + valid     + valid
 actions      actions     actions
   |            |           |
direct logits direct logits direct logits
   |            |           |
typed action  typed action typed action
```

> **IMAGE PLACEHOLDER — Compile stable context once**
> Two panels. Left: a stateless loop repeats a large TASK/POLICY block together with STATE 1, STATE 2,
> STATE 3 and labels each pass “re-prefill”. Right: Decisio prefills TASK/POLICY once into “reusable
> llama.cpp model context”, then appends only changing state + deterministic sensors + valid actions.
> Show logical tokens vs physically evaluated tokens, cache hits and fresh-equivalence; do not print
> a speedup number unless it comes from a measured run.

Decisio separates three things that are often mixed together:

```text
deterministic facts        stable semantics             uncertain choice
-------------------        ----------------             ----------------
wall collision        ->   Snake decision policy   ->   RIGHT vs UP
authorization rule         sensor meanings              route A vs B
invalid transition         task objective               retry vs escalate
```

The application owns deterministic truth. Decisio only scores the remaining semantic trade-off.

> **IMAGE PLACEHOLDER — Constraints before probabilities**
> A funnel: application state -> deterministic constraints remove impossible actions -> stable
> decision context (cached) -> current state + sensors -> direct option logits -> typed action.
> Add a future side branch from confidence/answerability to ABSTAIN, clearly marked “planned”.

## How this differs from SemIf

[SemIf](https://github.com/TheoLeeCJ/SemIf) independently explores the same important low-level
primitive: use an open model's option logits directly instead of generating prose/JSON. It also
supports shared-state execution, several runtimes and workload calibration. **Decisio does not claim
direct logits themselves as the differentiator.**

The intended product boundary is different:

| | SemIf emphasis | Decisio emphasis |
| --- | --- | --- |
| Core primitive | direct typed option scoring | direct typed option scoring is an internal primitive |
| State | shared-state scoring/reuse | first-class persistent decision context + changing application state |
| Runtime breadth | multiple backends/model paths | opinionated local GGUF + llama.cpp reference runtime |
| Domain facts | supplied decision input | deterministic constraints are explicitly applied before scoring |
| Reuse contract | performance execution mode | fresh-equivalent model-context reuse is a product invariant |
| Output contract | option probabilities/scores | typed application action + provenance; answerability/abstention planned |

The shorthand is:

> **SemIf: score this decision efficiently.**  
> **Decisio: keep my application's decision context warm and make many bounded decisions as state changes.**

> **IMAGE PLACEHOLDER — Shared primitive, different boundary**
> Venn-style architecture graphic. Shared center: “open LLM + direct option logits + zero answer
> generation”. SemIf side: “multi-backend scoring / calibration / benchmarking”. Decisio side:
> “persistent decision context / deterministic constraints / current-state suffix / typed action /
> fresh-equivalence”. Avoid “better/worse” language.

<p align="center">
  <img src="brand/graphics/decisio-vs-generated-decisions.png" alt="Decisio vs generated decisions: generated JSON and parse/repair compared with direct llama.cpp logit scoring into a typed decision" width="100%" />
</p>

## Why

A lot of software does not need prose from an LLM. It needs a bounded decision:

- route a request;
- choose an action;
- classify into categories defined at runtime;
- interpret evidence against a small set of alternatives;
- eventually decide whether the supplied evidence is sufficient to answer.

The common pattern asks a model to generate JSON and immediately parses that text back into a
software decision.

Decisio explores a different primitive:

```text
state + question + valid candidates
                │
                ▼
      zero-generation scoring
         /              \
        /                \
direct option logits   semantic candidate scoring
        \                /
         \              /
          typed decision
```

The product hypothesis is simple:

> For bounded semantic decisions, use the LLM as a scorer before using it as a writer.

## Bring your own quantized Qwen

The runtime target is deliberately local and artifact-oriented:

```text
your compatible Qwen GGUF
        │
        ▼
     llama.cpp
        │
        ▼
      Decisio
        │
        ▼
typed semantic decision
```

You should be able to choose the quantized GGUF that makes sense for your machine instead of having
Decisio require one heavyweight model packaging stack.

For example, a user may prefer a smaller Q4 artifact for local CPU use or a higher-fidelity
quantization when memory allows. Decisio's scoring approach stays the same; the exact logits and
therefore quality, margins, latency and calibration can change with the artifact.

That distinction matters:

- **Q4_K_M is the v1 reference artifact**, not a permanent product restriction;
- other compatible Qwen GGUF quantizations are intended to be usable;
- quantizations are **not assumed equivalent**;
- benchmark evidence belongs to the exact GGUF/runtime identity that produced it;
- a calibration artifact must not silently transfer to a different GGUF/quantization.

This makes model choice a deployment decision while keeping scorer semantics and evidence explicit.

## Runtime status

Decisio has an in-process local-GGUF llama.cpp backend. The pinned Qwen3.5-2B Q4_K_M
reference gate has already produced a negative result for semantic v2 as a short/fresh
general-purpose default: scorer-gate v2 remains **FAIL**. The active experiment is the separately
frozen repeated-state gate v3.

Two native zero-generation choice readouts are implemented:

- **direct choice logits** — one prompt, A/B/C/... option-token logits, one model evaluation; used by
  the Snake demo as its default low-latency control path;
- **semantic v2** — comparative YES/NO scoring per candidate; still experimental and evaluated
  separately for repeated-state workloads.

The benchmark CLI remains experimental:

```bash
decisio compare \
  --input .artifacts/scorer-gate-v2.jsonl \
  --output-dir .artifacts/scorer-gate-v2 \
  --model /absolute/path/Qwen3.5-2B-Q4_K_M.gguf \
  --device cpu \
  --warmup-rounds 1 \
  --performance-rounds 4
```

Benchmark claims remain bound to the exact artifact, scorer and runtime identity that produced them.

See the active [llama.cpp runtime migration workstream](docs/workstreams/llama-cpp-reference-runtime.md)
and [current state](docs/current-state.md).

## What comes back

A native result contains a selected candidate plus raw/normalized model scores and provenance:

```json
{
  "choice": "billing",
  "distribution": {
    "billing": 0.91,
    "technical": 0.07,
    "sales": 0.02
  },
  "scores": {
    "billing": 4.2,
    "technical": 1.6,
    "sales": 0.3
  },
  "binary_conditional_probability": {
    "billing": 0.99,
    "technical": 0.83,
    "sales": 0.57
  },
  "probability_status": "uncalibrated_conditional_scores",
  "generated_tokens": 0
}
```

The numbers above illustrate the **output shape**, not a benchmark result.

The distribution means “relative preference among the supplied candidates under this scorer.” It is
**not** automatically a calibrated probability that the answer is correct.

GGUF/llama.cpp does not prevent calibration. A later calibration layer can be fitted over Decisio
scores, but the calibration artifact must match the exact model artifact, quantization,
scorer/compiler and runtime identity.

## From logits to calibrated probabilities

Decisio deliberately separates **model preference** from **probability of correctness**. The path is:

```text
Qwen GGUF
   │
   ▼
llama.cpp next-token logits
   │
   ▼
Decisio candidate scores
   │
   ▼
softmax across supplied candidates
   │
   ▼
uncalibrated conditional distribution
   │
   ▼
optional calibration artifact fitted on labeled validation data
   │
   ▼
calibrated probabilities
```

<p align="center">
  <img src="brand/graphics/decisio-logits-to-calibrated-probabilities.png" alt="From logits to calibrated probabilities: pipeline from Qwen GGUF through llama.cpp next-token logits, Decisio scoring, uncalibrated conditional distribution, to optional calibration layer and calibrated probability" width="100%" />
</p>

### 1. llama.cpp gives Decisio logits

For semantic scoring, Decisio asks the model to judge one candidate against the complete candidate
set and reads the next-token logits for the configured binary verbalizers:

```text
YES logit = 8.2
NO  logit = 6.7

candidate score = 8.2 - 6.7 = 1.5
```

No answer token needs to be generated on the native scoring path.

The same operation is repeated for the other valid candidates. Suppose the resulting scores are:

```text
billing   = 2.4
technical = 1.1
sales     = -0.2
```

The semantic scorers now preserve this quantity as `binary_conditional_probability`. It is the
YES probability after renormalizing the model's YES/NO logits for that candidate; it is not a
calibrated correctness probability.

### 2. Softmax turns scores into a relative distribution

Decisio can normalize those scores across the supplied candidate set:

```text
softmax(scores)

billing   = 0.73
technical = 0.20
sales     = 0.07
```

This is useful, but its interpretation is deliberately narrow:

> Given this scorer, model artifact, prompt/compiler and candidate set, `billing` receives 73% of
> the relative score mass.

It does **not** yet mean:

> `billing` has a 73% probability of being correct.

That is why the result is labeled:

```json
{
  "probability_status": "uncalibrated_conditional_scores"
}
```

<p align="center">
  <img src="brand/graphics/decisio-relative-distribution-vs-calibrated-probability.png" alt="Relative distribution vs calibrated probability: uncalibrated conditional distribution compared with calibrated probability after held-out calibration" width="100%" />
</p>

### 3. Calibration learns the mapping from scores to observed correctness

Calibration is a separate post-hoc step. It needs a **labeled validation set that was not used to
fit or select the calibration parameters**.

For each validation example:

```text
known correct answer
        │
        ├──────────────┐
        ▼              │
run Decisio            │
        │              │
        ▼              │
predicted scores       │
and distribution       │
        │              │
        └──── compare ─┘
               │
               ▼
predicted confidence vs observed correctness
```

For example, if predictions around `0.80` are correct only about 65% of the time, the system is
over-confident in that region.

A calibration method can then learn a correction. One simple candidate is **temperature scaling**:

```text
calibrated_distribution = softmax(scores / T)
```

where `T` is fitted on held-out labeled examples rather than chosen by hand. Other calibration
methods may be evaluated later if they provide better evidence.

Calibration quality should be measured with appropriate held-out metrics such as NLL, Brier score,
reliability/calibration error and task-appropriate accuracy/coverage diagnostics. Calibration must
not be declared successful merely because probabilities look smoother.

<p align="center">
  <img src="brand/graphics/decisio-calibration-fitting-workflow.png" alt="Calibration fitting workflow: step-by-step workflow from labeled validation set to saved calibration artifact with artifact fingerprint" width="100%" />
</p>

### 4. Calibration belongs to the exact decision engine identity

Calibration is not a generic property of “Qwen3.5-2B”. A Q4_K_M artifact and a Q8 artifact can
produce slightly different logits, margins and decision boundaries.

A future Decisio calibration artifact therefore needs to identify at least:

```text
GGUF SHA-256
quantization
scorer identity
compiler / prompt identity
readout verbalizers
llama.cpp runtime / build identity
calibration method
calibration dataset identity
```

Changing the GGUF or quantization does not prevent Decisio from running. It means the old calibration
must not automatically be treated as valid.

This is the intended model:

```text
                    Decisio scorer semantics
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
             Q4_K_M         Q6_K          Q8_0
                │             │             │
          own evidence   own evidence   own evidence
                │             │             │
      optional matching calibration artifacts
```

Qwen3.5-2B Q4_K_M is the first reference configuration so the project has one reproducible,
locally practical CPU baseline. The 2B choice is not a claim that it is universally better than 4B;
users remain free to choose another compatible quantized Qwen GGUF and measure the trade-off on
their own workload.

### 5. Calibrated output stays explicit

The current API exposes uncalibrated conditional scores. A future calibrated result should keep both
layers visible rather than overwrite one with the other:

```json
{
  "choice": "billing",
  "binary_conditional_probability": {
    "billing": 0.92,
    "technical": 0.71,
    "sales": 0.38
  },
  "distribution": {
    "billing": 0.73,
    "technical": 0.20,
    "sales": 0.07
  },
  "calibrated_probability": {
    "billing": 0.61,
    "technical": 0.25,
    "sales": 0.14
  },
  "probability_status": "temperature_scaled",
  "calibration_id": "qwen35-2b-q4km-semantic-v2-..."
}
```

This JSON is an **illustration of the intended future calibrated contract**, not implemented API or
benchmark evidence.

Calibration also does not solve every uncertainty problem. In particular, “which candidate is
preferred?” and “is there enough evidence to answer?” remain separate questions; Decisio plans to
treat answerability as its own signal rather than hide it inside candidate confidence.

## How scoring works

Decisio currently has two native zero-generation choice paths.

### Direct choice logits

For a small bounded action set, Decisio can render the valid options once as A/B/C/... and read those
option-token logits from a **single model evaluation**:

```text
state + question

A. UP
B. RIGHT
C. DOWN
      |
      v
one next-token logit readout
      |
      v
logit(A), logit(B), logit(C)
      |
      v
relative softmax + typed choice
```

This is the default Snake path. It is fast and generates zero answer tokens, but its scores remain
uncalibrated and direct option-token scoring can be sensitive to presentation order/verbalizers.
That is why it is still measured explicitly in benchmark comparisons.

### Comparative semantic v2

The primary semantic experiment evaluates every valid candidate against the complete alternative set:

```text
candidate score = logit(Yes) - logit(No)
```

Candidate scores are normalized across the supplied set.

Applications must remove choices that are already known to be invalid before calling Decisio:

```text
domain rules
    ↓
valid candidates
    ↓
Decisio
    ↓
semantic preference
```

A probabilistic model should not overrule facts such as a wall collision, an invalid state transition
or an explicit authorization rule.

## Why shared context state matters

Zero answer generation removes decoding work, but repeated **prefill** can still dominate CPU
latency. This is especially relevant to semantic v2, which evaluates candidate-specific suffixes,
and to many questions over one long unchanged state. Direct choice scoring already evaluates one
bounded choice prompt in one pass; it does not need candidate-by-candidate YES/NO branching.

```text
long state + question + alternatives
              │
         prefill once
              │
      reusable model state
       /       |       \
      A        B        C
      │        │        │
   YES/NO   YES/NO   YES/NO
```

For repeated decisions, the target is also to retain a bounded prefix state so a long unchanged
state is not recomputed for every new question.

<p align="center">
  <img src="brand/graphics/decisio-shared-context-state-reuse.png" alt="Shared context-state reuse: naive re-prefill execution compared with Decisio and llama.cpp shared context-state reuse across candidates and questions" width="100%" />
</p>

Fresh evaluation remains the oracle: the shared fast path becomes default only after it preserves
the same choice and keeps score/probability deltas within a declared tolerance.

## Target architecture

```mermaid
flowchart LR
    A[Application state] --> B[Deterministic constraints]
    B --> C[ChoiceRequest]
    C --> D[Prompt compiler]
    D --> E[Scorer]
    E --> F[LlamaCpp backend]
    F --> G[Qwen GGUF]
    G --> H[Required next-token logits]
    H --> I[DecisionResult]
```

llama.cpp owns model execution. Decisio owns the decision semantics: compilation, scorer behavior,
probability status, provenance and evidence.

See [Architecture](docs/architecture.md) for the current implementation and migration boundary.

## Evidence before API expansion

Decisio compares four inference strategies on the same frozen workload:

- **semantic v2** — comparative Yes/No log-odds;
- **semantic v1** — candidate-independent Yes/No log-odds;
- **letters** — direct A/B/C next-token scoring; benchmark baseline and the fast control path used by Snake;
- **generated JSON** — minimal autoregressive baseline.

The scorer gate measures quality, candidate-order sensitivity, invalid output and systems
performance. CPU runs use warm-up, repeated balanced trials, p50/p95 latency, throughput and process
peak-RSS reporting.

The original [scorer gate v1](benchmarks/scorer-gate-v1.md) is retained as the frozen
Transformers/BF16 methodology source, but it no longer authorizes scorer promotion. The llama.cpp
migration will freeze a gate-v2 GGUF/runtime identity before representative results are observed.

## Snake: the reference stateful loop

Snake is now the concrete reference for the product contract. A fixed controller context explains the
goal, coordinates, sensor semantics and decision priorities once. Every move supplies only the
current board plus deterministic candidate features. Immediate wall/body collisions are filtered in
code before Qwen sees the options. The direct scorer uses question-prefix context reuse by default;
`--fresh-prefix` keeps the same decision path without cache reuse for diagnostics.

```text
STATIC FOR THE EPISODE                 CHANGES EVERY STEP
----------------------                 ------------------
Snake objective                        head/body/food
coordinate convention        +         valid actions
sensor definitions                      projected exits
decision priorities                      reachable area
                                        recent-visit sensor
          |                                  |
          +------ reusable context ----------+
                          |
                       A/B/C logits
                          |
                       typed move
```

> **IMAGE PLACEHOLDER — Snake static vs dynamic**
> Show a cached left column named “Snake decision context” and a stream of Step 1 / Step 2 / Step 3
> cards containing only current board, food, valid moves and deterministic sensors. Under each step
> show one direct-logit readout. Highlight that full previous boards are not replayed.

## Examples

- [Support routing](examples/support-routing/) — runtime-defined support queues.
- [Policy gate](examples/policy-gate/) — bounded semantic interpretation without replacing deterministic policy.
- [Snake](examples/snake/) — branded live OBSERVE → DECIDE → ACT demo; unsafe moves are filtered, then direct choice logits select among the remaining actions in one forward pass.

Examples are behavioral probes, not benchmark claims.

The quickest visual path is the local Snake demo:

```bash
uv sync --frozen --extra llama --extra dev
uv run python -m examples.snake.web \
  --model /path/to/model.gguf \
  --scorer direct \
  --open
```

Snake filters deterministic invalid moves first, then presents the remaining actions as A/B/C/...
options and reads all option logits from one model evaluation. See
[examples/snake](examples/snake/) for the live decision UI, model notes and scorer comparisons.

## Status

Decisio is **experimental**.

Implemented now:

- in-process local GGUF + llama.cpp backend;
- comparative semantic v2, independent semantic v1 and direct A/B/C choice logits;
- zero-generation native scoring and generated-JSON comparison baseline;
- deterministic prompt/readout compilation and exact provenance;
- native-batch-safe shared candidate execution plus bounded repeated-state cache;
- frozen benchmark/evaluation tooling with candidate-order perturbation;
- branded live Snake demo with direct one-forward choice logits by default;
- real-model CPU smoke and trace/video evidence.

Evidence status:

- scorer-gate v2 is **FAIL** for semantic v2 as a short/fresh general-purpose default;
- repeated-state diagnostic v2 showed a useful latency signal on the pinned 2B runtime;
- repeated-state gate v3 is the active precommitted scope experiment;
- direct choice logits are implemented and useful as an application fast path, but are not being
  relabeled as the winner of the failed semantic scorer gate.

Still pending:

- repeated-state gate v3 decision and resulting scorer scope;
- broader perturbation coverage;
- answerability;
- scaled multi-question scheduling;
- calibration;
- stable high-level Python API;
- representative release evidence.

## What Decisio is not

Decisio is not:

- a chat framework;
- a generic LLM server;
- a workflow or authorization engine;
- a claim that raw model scores are calibrated confidence;
- a claim that different quantizations are interchangeable;
- a fine-tuning framework in v1;
- a safety-critical decision authority without workload-specific validation.

## Documentation

- [Product scope](docs/product.md)
- [Architecture](docs/architecture.md)
- [Current state](docs/current-state.md)
- [Active llama.cpp workstream](docs/workstreams/llama-cpp-reference-runtime.md)
- [Roadmap](docs/roadmap.md)
- [Repository quality plan](docs/repository-quality.md)
- [Benchmarks](benchmarks/README.md)
- [Examples](examples/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

Licensed under [Apache-2.0](LICENSE).
