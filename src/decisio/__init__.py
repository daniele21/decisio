"""Decisio: stateful typed decisions for local causal LLMs."""

from .schema import Candidate, ChoiceRequest, DecisionResult
from .session import DecisionSession

__all__ = ["Candidate", "ChoiceRequest", "DecisionResult", "DecisionSession"]
__version__ = "0.1.0a0"
