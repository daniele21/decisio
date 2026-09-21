# ADR 0001 — Training-free semantic scoring first

Status: accepted  
Date: 2026-09-21

## Context

Decisio is exploring whether a general-purpose open-weight causal LLM can serve as a useful software decision engine without generating answer text.

Existing zero-generation approaches demonstrate that next-token logits and shared-state execution can produce typed option scores efficiently. However, mapping runtime candidates to arbitrary answer tokens such as A/B/C introduces a verbalizer/position abstraction that is not part of the semantic problem itself.

A more specialized trained decision model could potentially improve calibration and robustness, but adding training immediately would make it difficult to determine how much value comes from inference/readout design versus learned specialization.

## Decision

Decisio v1 will be **training-free**.

The primary experimental path will score each semantic candidate using a binary Yes/No judgment and derive a raw candidate score from the logit difference:

```text
score(candidate) = logit(YES) - logit(NO)
```

For mutually exclusive choices, candidate scores may be normalized across the supplied candidate set.

Answerability will be evaluated separately rather than represented as an ordinary candidate.

Direct A/B/C-style answer-token scoring and minimal autoregressive structured output will be maintained as benchmark baselines.

## Consequences

### Positive

- isolates inference-time innovation;
- works with an existing open checkpoint;
- removes the 26-letter-style candidate limit from the product abstraction;
- reduces dependence on arbitrary candidate-to-letter mapping;
- keeps later fine-tuning optional;
- enables a clean benchmark of whether the new readout is actually useful.

### Costs / risks

- Yes/No verbalizers can still introduce token/prompt bias;
- normalized candidate scores are not calibrated probability of correctness;
- scoring each candidate increases suffix compute;
- the semantic scorer may be worse than direct logits;
- answerability may remain overconfident without training/calibration.

These are benchmark questions, not assumptions to hide.

## Reconsider when

Revisit this ADR if frozen benchmark evidence shows that inference-time scoring cannot achieve acceptable calibration, abstention, robustness or domain accuracy and a trained component offers a clearly measurable benefit.
