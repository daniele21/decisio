"""A/B/C direct-logit benchmark baseline."""

from __future__ import annotations

from decisio.backends.base import LogitBackend
from decisio.compiler import compile_letter_choice
from decisio.math import softmax, stable_argmax
from decisio.schema import ChoiceRequest, DecisionResult


class LetterTokenScorer:
    name = "letter_token_baseline_v1"

    def __init__(self, backend: LogitBackend):
        self.backend = backend

    def score(self, request: ChoiceRequest) -> DecisionResult:
        compiled = compile_letter_choice(self.backend.tokenizer, request)
        token_ids = [compiled.readout[candidate.id] for candidate in request.candidates]
        logits = self.backend.next_token_logits(compiled.input_ids, token_ids)
        scores = {
            candidate.id: logit
            for candidate, logit in zip(request.candidates, logits, strict=True)
        }
        probabilities = softmax(logits)
        distribution = {
            candidate.id: probability
            for candidate, probability in zip(request.candidates, probabilities, strict=True)
        }
        choice = stable_argmax(distribution)
        return DecisionResult(
            choice=choice,
            distribution=distribution,
            scores=scores,
            scorer=self.name,
            prompt_sha256={"choice": compiled.sha256},
            model=self.backend.identity,
        )
