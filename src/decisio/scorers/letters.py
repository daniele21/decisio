"""A/B/C direct-logit benchmark baseline."""

from __future__ import annotations

from decisio.backends.base import LogitBackend
from decisio.compiler import compile_letter_choice
from decisio.math import softmax, stable_argmax
from decisio.schema import ChoiceRequest, DecisionResult


class LetterTokenScorer:
    name = "letter_token_baseline_v1"

    def __init__(self, backend: LogitBackend, *, reuse_prefix: bool = False):
        self.backend = backend
        self.reuse_prefix = reuse_prefix
        if reuse_prefix:
            self.name = "letter_question_prefix_v1"

    def score(self, request: ChoiceRequest) -> DecisionResult:
        compiled = compile_letter_choice(
            self.backend.tokenizer, request, reuse_prefix=self.reuse_prefix,
        )
        token_ids = [compiled.readout[candidate.id] for candidate in request.candidates]
        shared = getattr(self.backend, "shared_prefix_batch_next_token_logits", None)
        if (
            self.reuse_prefix and compiled.reusable_prefix_len is not None
            and getattr(self.backend, "supports_reusable_prefix_hint", False)
            and callable(shared)
        ):
            logits = shared(
                [compiled.input_ids], [token_ids],
                reusable_prefix_len=compiled.reusable_prefix_len,
            )[0]
        else:
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
