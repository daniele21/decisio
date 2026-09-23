# Calibration and probability semantics

Decisio separates **model preference** from **probability of correctness**.

Native scoring reads selected logits from the unchanged causal language-model head. Those values can
be normalized into a distribution over the supplied candidates, but that distribution is not
automatically a calibrated estimate that the selected candidate is correct.

## Native score path

```text
Qwen GGUF
   |
   v
llama.cpp next-token logits
   |
   v
Decisio candidate scores
   |
   v
softmax across supplied candidates
   |
   v
uncalibrated conditional distribution
```

For comparative semantic scoring, one candidate can be represented by a binary verbalizer pair:

```text
YES logit = 8.2
NO  logit = 6.7

candidate score = 8.2 - 6.7 = 1.5
```

The semantic scorer may preserve the renormalized YES/NO quantity as
`binary_conditional_probability`. That is still conditional on the model, prompt/compiler,
verbalizers and supplied candidate set; it is not a calibrated correctness probability.

Likewise, if candidate scores are:

```text
billing   = 2.4
technical = 1.1
sales     = -0.2
```

then a softmax may produce:

```text
billing   = 0.73
technical = 0.20
sales     = 0.07
```

The correct interpretation is:

> Under this exact scorer/model/prompt/candidate set, `billing` receives 73% of the relative score
> mass.

It does **not** mean that `billing` has a 73% probability of being correct.

## Post-hoc calibration

Calibration is a separate evidence step. It requires a labeled validation set that was not used to
fit or select the calibration parameters.

```text
labeled validation examples
        |
        v
run exact Decisio scorer identity
        |
        v
scores / relative distribution
        |
        v
compare predicted confidence with observed correctness
        |
        v
fit calibration mapping
        |
        v
held-out calibration evaluation
```

A simple candidate is temperature scaling:

```text
calibrated_distribution = softmax(scores / T)
```

where `T` is fitted on held-out labeled examples rather than chosen manually. Other methods may be
used when supported by stronger evidence.

Useful held-out measurements include NLL, Brier score, reliability/calibration error and
task-appropriate accuracy/coverage diagnostics. Smoother-looking probabilities are not sufficient
evidence of calibration quality.

## Calibration identity

Calibration belongs to an exact decision-engine identity, not to a model family name such as
“Qwen3.5-2B”.

A calibration artifact should bind at least:

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

Changing the GGUF or quantization does not prevent Decisio from running, but an older calibration
artifact must not silently be treated as valid for the new identity.

Qwen3.5-2B Q4_K_M is the current reference evidence artifact. It is not a claim that it is
universally better than other compatible quantizations.

## Intended calibrated output

The current API exposes uncalibrated scores. A future calibrated contract should preserve both the
raw/native layer and the calibrated layer rather than overwrite one with the other:

```json
{
  "choice": "billing",
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
  "calibration_id": "qwen35-2b-q4km-direct-v1-..."
}
```

This is an intended future shape, not a currently promoted calibrated API.

## Answerability is separate

Calibration does not answer every uncertainty question. In particular:

- “Which supplied candidate is preferred?”
- “Is there enough evidence to answer at all?”

are separate decisions.

Decisio plans to treat answerability/abstention as an explicit signal rather than infer it from the
largest softmax value alone.
