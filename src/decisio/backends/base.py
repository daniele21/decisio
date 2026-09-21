"""Backend capability contract."""

from __future__ import annotations

from typing import Any, Protocol

from decisio.compiler import Tokenizer


class LogitBackend(Protocol):
    tokenizer: Tokenizer

    @property
    def identity(self) -> dict[str, Any]: ...

    def next_token_logits(self, input_ids: tuple[int, ...], token_ids: list[int]) -> list[float]:
        """Return next-token logits for exactly the requested vocabulary token ids."""
        ...

    def batch_next_token_logits(
        self,
        input_ids_batch: list[tuple[int, ...]],
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]:
        """Score multiple prompts in one backend batch."""
        ...
