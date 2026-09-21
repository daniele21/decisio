"""Deterministic numerical post-processing."""

from __future__ import annotations

import math


def softmax(values: list[float]) -> list[float]:
    if len(values) < 2:
        raise ValueError("softmax requires at least two values")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("softmax values must be finite")
    maximum = max(values)
    weights = [math.exp(value - maximum) for value in values]
    total = math.fsum(weights)
    return [weight / total for weight in weights]


def binary_log_odds(positive_logit: float, negative_logit: float) -> float:
    if not math.isfinite(positive_logit) or not math.isfinite(negative_logit):
        raise ValueError("binary logits must be finite")
    return positive_logit - negative_logit
