"""Supported high-level stateful decision session."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any

from .backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from .schema import Candidate, ChoiceRequest, DecisionResult
from .scorers import LetterTokenScorer

BackendFactory = Callable[[LlamaCppBackendConfig], Any]


class DecisionSession:
    """Own one local GGUF runtime and a stable direct-choice decision context.

    The supported v1 session intentionally exposes one evidence-backed readout: direct
    A/B/C/... option logits with zero generated answer tokens. The stable decision context is
    compiled into the reusable question prefix; each choose call supplies only changing state
    and the currently valid candidates.
    """

    def __init__(
        self,
        model: str | Path,
        decision_context: str,
        *,
        device: str = "cpu",
        n_ctx: int = 8192,
        n_batch: int = 512,
        n_ubatch: int = 512,
        threads: int | None = None,
        threads_batch: int | None = None,
        _backend_factory: BackendFactory = LlamaCppBackend,
    ) -> None:
        if not isinstance(decision_context, str) or not decision_context.strip():
            raise ValueError("decision_context must be a non-empty string")

        config = LlamaCppBackendConfig(
            model=model,
            device=device,
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_ubatch=n_ubatch,
            n_threads=threads,
            n_threads_batch=threads_batch,
        )
        self.decision_context = decision_context
        self._backend = _backend_factory(config)
        self._identity = dict(self._backend.identity)
        self._reuse_scorer = LetterTokenScorer(
            self._backend,
            reuse_prefix=True,
            shared_prefix_execution=True,
        )
        self._fresh_scorer = LetterTokenScorer(
            self._backend,
            reuse_prefix=True,
            shared_prefix_execution=False,
        )
        self._closed = False

    @property
    def identity(self) -> dict[str, Any]:
        """Return a copy of the loaded model/runtime provenance."""
        return dict(self._identity)

    @property
    def closed(self) -> bool:
        return self._closed

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("DecisionSession is closed")

    def choose(
        self,
        *,
        state: Any,
        candidates: Iterable[Candidate],
        request_id: str | None = None,
        fresh: bool = False,
    ) -> DecisionResult:
        """Choose one valid candidate for the current state.

        fresh=True evaluates the exact same stateful prompt without shared-prefix execution.
        It is the supported oracle/debug path, not a different prompt or scorer.
        """
        self._require_open()
        candidate_tuple = tuple(candidates)
        if any(not isinstance(candidate, Candidate) for candidate in candidate_tuple):
            raise TypeError("candidates must contain Candidate objects")

        request = ChoiceRequest(
            id=request_id,
            state=state,
            question=self.decision_context,
            candidates=candidate_tuple,
        )
        self._backend.reset_runtime_metrics()
        scorer = self._fresh_scorer if fresh else self._reuse_scorer
        result = scorer.score(request)
        return replace(
            result,
            execution_mode="fresh" if fresh else "reuse",
            runtime_metrics=dict(self._backend.runtime_metrics()),
        )

    def clear_cache(self) -> None:
        """Drop reusable repeated-state model context owned by this session."""
        self._require_open()
        self._backend.clear_repeated_state_cache()

    def close(self) -> None:
        """Release the underlying llama.cpp runtime. Safe to call more than once."""
        if self._closed:
            return
        self._closed = True
        self._backend.close()

    shutdown = close

    def __enter__(self) -> "DecisionSession":
        self._require_open()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback
        self.close()
