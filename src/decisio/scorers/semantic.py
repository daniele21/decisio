"""Primary semantic candidate scorer."""

from __future__ import annotations

from decisio.backends.base import LogitBackend
from decisio.compiler import compile_semantic_candidate
from decisio.math import binary_log_odds, softmax
from decisio.schema import ChoiceRequest, DecisionResult


class SemanticBinaryScorer:
    name = "semantic_binary_logodds_v1"

    def __init__(self, backend: LogitBackend):
        self.backend = backend

    def score(self, request: ChoiceRequest) -> DecisionResult:
        scores: dict[str, float] = {}
        prompt_hashes: dict[str, str] = {}
        for candidate in request.candidates:
            compiled = compile_semantic_candidate(self.backend.tokenizer, request, candidate)
            logits = self.backend.next_token_logits(
                compiled.input_ids,
                [compiled.readout["yes"], compiled.readout["no"]],
            )
            scores[candidate.id] = binary_log_odds(logits[0], logits[1])
            prompt_hashes[candidate.id] = compiled.sha256

        ordered_scores = [scores[candidate.id] for candidate in request.candidates]
        probabilities = softmax(ordered_scores)
        distribution = {
            candidate.id: probability
            for candidate, probability in zip(request.candidates, probabilities, strict=True)
        }
        choice = max(distribution, key=distribution.__getitem__)
        return DecisionResult(
            choice=choice,
            distribution=distribution,
            scores=scores,
            scorer=self.name,
            prompt_sha256=prompt_hashes,
            model=self.backend.identity,
        )
