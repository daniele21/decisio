"""Semantic candidate scorers."""

from __future__ import annotations

from collections.abc import Callable

from decisio.backends.base import LogitBackend
from decisio.compiler import (
    CompiledPrompt,
    compile_independent_semantic_candidate,
    compile_semantic_candidate,
)
from decisio.math import binary_log_odds, softmax, stable_argmax
from decisio.schema import ChoiceRequest, DecisionResult


def _score_compiled(
    backend: LogitBackend,
    compiled: list[CompiledPrompt],
) -> list[list[float]]:
    input_ids_batch = [item.input_ids for item in compiled]
    token_ids_batch = [
        [item.readout["yes"], item.readout["no"]]
        for item in compiled
    ]
    batch_method = getattr(backend, "batch_next_token_logits", None)
    if callable(batch_method):
        return batch_method(input_ids_batch, token_ids_batch)
    return [
        backend.next_token_logits(input_ids, token_ids)
        for input_ids, token_ids in zip(input_ids_batch, token_ids_batch, strict=True)
    ]


class _BaseSemanticScorer:
    name: str
    compiler: Callable

    def __init__(self, backend: LogitBackend):
        self.backend = backend

    def score(self, request: ChoiceRequest) -> DecisionResult:
        compiled = [
            self.compiler(self.backend.tokenizer, request, candidate)
            for candidate in request.candidates
        ]
        logits_batch = _score_compiled(self.backend, compiled)

        scores = {
            candidate.id: binary_log_odds(logits[0], logits[1])
            for candidate, logits in zip(request.candidates, logits_batch, strict=True)
        }
        binary_conditional_probability = {
            candidate.id: softmax([logits[0], logits[1]])[0]
            for candidate, logits in zip(request.candidates, logits_batch, strict=True)
        }
        prompt_hashes = {
            candidate.id: item.sha256
            for candidate, item in zip(request.candidates, compiled, strict=True)
        }

        ordered_scores = [scores[candidate.id] for candidate in request.candidates]
        probabilities = softmax(ordered_scores)
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
            binary_conditional_probability=binary_conditional_probability,
            prompt_sha256=prompt_hashes,
            model=self.backend.identity,
        )


class SemanticBinaryScorer(_BaseSemanticScorer):
    """Default v2 scorer: candidate judgment is comparative across all supplied alternatives."""

    name = "semantic_comparative_logodds_v2"
    compiler = staticmethod(compile_semantic_candidate)


class IndependentSemanticScorer(_BaseSemanticScorer):
    """Original v1 scorer retained as an experimental baseline."""

    name = "semantic_binary_logodds_v1"
    compiler = staticmethod(compile_independent_semantic_candidate)
