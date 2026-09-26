from __future__ import annotations

import pytest

from decisio import Candidate, DecisionSession


class FakeTokenizer:
    SPECIAL = {"A": 100, "B": 101, "C": 102}

    def apply_chat_template(
        self,
        messages,
        *,
        tokenize=False,
        add_generation_prompt=True,
        **kwargs,
    ):
        del kwargs
        assert tokenize is False
        body = "".join(f"<{item['role']}>\n{item['content']}\n" for item in messages)
        return body + ("<assistant>\n" if add_generation_prompt else "")

    def encode(self, text, *, add_special_tokens=False):
        del add_special_tokens
        for literal, token_id in self.SPECIAL.items():
            if text.endswith(literal):
                prefix = text[:-1]
                return [1000 + ord(char) for char in prefix] + [token_id]
        return [1000 + ord(char) for char in text]


class FakeBackend:
    supports_reusable_prefix_hint = True

    def __init__(self, config):
        self.config = config
        self.tokenizer = FakeTokenizer()
        self.closed = False
        self.shared_calls = []
        self.fresh_calls = []
        self.cache_clears = 0
        self._metrics = {}

    @property
    def identity(self):
        return {
            "backend": "fake-llama",
            "model": str(self.config.model),
            "device": self.config.device,
        }

    @staticmethod
    def _logits(token_ids):
        table = {100: 1.0, 101: 4.0, 102: -1.0}
        return [table[token_id] for token_id in token_ids]

    def reset_runtime_metrics(self):
        self._metrics = {}

    def runtime_metrics(self):
        return dict(self._metrics)

    def shared_prefix_batch_next_token_logits(
        self,
        input_ids_batch,
        token_ids_batch,
        *,
        reusable_prefix_len=None,
    ):
        self.shared_calls.append((input_ids_batch, token_ids_batch, reusable_prefix_len))
        logical = sum(len(row) for row in input_ids_batch)
        reused = reusable_prefix_len or 0
        self._metrics = {
            "logical_input_tokens": logical,
            "physically_evaluated_tokens": max(0, logical - reused),
            "reused_prefix_tokens": reused,
            "shared_prefix_calls": 1,
            "fresh_calls": 0,
        }
        return [self._logits(token_ids) for token_ids in token_ids_batch]

    def next_token_logits(self, input_ids, token_ids):
        self.fresh_calls.append((input_ids, token_ids))
        self._metrics = {
            "logical_input_tokens": len(input_ids),
            "physically_evaluated_tokens": len(input_ids),
            "reused_prefix_tokens": 0,
            "shared_prefix_calls": 0,
            "fresh_calls": 1,
        }
        return self._logits(token_ids)

    def clear_repeated_state_cache(self):
        self.cache_clears += 1

    def close(self):
        self.closed = True


def candidates():
    return (
        Candidate("billing", "Payments and refunds"),
        Candidate("technical", "Software troubleshooting"),
    )


def test_session_reuses_stable_context_and_returns_runtime_metadata():
    backend = None

    def factory(config):
        nonlocal backend
        backend = FakeBackend(config)
        return backend

    session = DecisionSession(
        "model.gguf",
        "Which support queue should own this ticket?",
        _backend_factory=factory,
    )
    first = session.choose(
        state={"ticket": "duplicate charge"},
        candidates=candidates(),
        request_id="one",
    )
    second = session.choose(
        state={"ticket": "login failure"},
        candidates=candidates(),
        request_id="two",
    )

    assert first.choice == "technical"
    assert first.execution_mode == "reuse"
    assert first.generated_tokens == 0
    assert first.runtime_metrics["shared_prefix_calls"] == 1
    assert first.runtime_metrics["reused_prefix_tokens"] > 0
    assert first.model["backend"] == "fake-llama"
    assert first.to_dict()["execution_mode"] == "reuse"
    assert "runtime_metrics" in first.to_dict()

    assert backend is not None
    left_inputs, _, left_hint = backend.shared_calls[0]
    right_inputs, _, right_hint = backend.shared_calls[1]
    assert left_hint == right_hint
    assert left_hint is not None and left_hint > 0
    assert left_inputs[0][:left_hint] == right_inputs[0][:right_hint]
    assert left_inputs[0][left_hint:] != right_inputs[0][right_hint:]
    assert second.choice == "technical"

    session.close()
    assert backend.closed is True
    assert session.closed is True


def test_fresh_mode_uses_identical_prompt_but_bypasses_shared_execution():
    backend = None

    def factory(config):
        nonlocal backend
        backend = FakeBackend(config)
        return backend

    with DecisionSession(
        "model.gguf",
        "Which support queue should own this ticket?",
        _backend_factory=factory,
    ) as session:
        reused = session.choose(state={"ticket": "x"}, candidates=candidates())
        fresh = session.choose(
            state={"ticket": "x"},
            candidates=candidates(),
            fresh=True,
        )

    assert backend is not None
    assert reused.prompt_sha256 == fresh.prompt_sha256
    assert reused.scores == fresh.scores
    assert reused.choice == fresh.choice
    assert reused.execution_mode == "reuse"
    assert fresh.execution_mode == "fresh"
    assert fresh.runtime_metrics["fresh_calls"] == 1
    assert len(backend.shared_calls) == 1
    assert len(backend.fresh_calls) == 1
    assert backend.closed is True


def test_session_lifecycle_and_explicit_cache_clear():
    backend = None

    def factory(config):
        nonlocal backend
        backend = FakeBackend(config)
        return backend

    session = DecisionSession("model.gguf", "Choose.", _backend_factory=factory)
    session.clear_cache()
    session.close()
    session.close()

    assert backend is not None
    assert backend.cache_clears == 1
    with pytest.raises(RuntimeError, match="closed"):
        session.choose(state={}, candidates=candidates())


def test_session_rejects_invalid_context_and_untyped_candidates():
    with pytest.raises(ValueError, match="decision_context"):
        DecisionSession("model.gguf", "   ", _backend_factory=FakeBackend)

    session = DecisionSession("model.gguf", "Choose.", _backend_factory=FakeBackend)
    try:
        with pytest.raises(TypeError, match="Candidate"):
            session.choose(
                state={},
                candidates=(
                    {"id": "a", "description": "A"},
                    {"id": "b", "description": "B"},
                ),
            )
    finally:
        session.close()
