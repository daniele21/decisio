from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig


class FakeRuntime:
    binding_version = "0.3.35"
    metadata = {
        "general.architecture": "qwen35",
        "general.name": "Qwen3.5 test",
        "general.file_type": 15,
    }
    n_vocab = 256
    n_ctx = 4096
    n_batch = 128
    n_ubatch = 64
    n_threads = 4
    n_threads_batch = 4
    n_seq_max = 8

    def __init__(self, config):
        self.config = config
        self.closed = False
        self.logit_calls = []
        self.shared_calls = []
        self.generated = []
        self.metrics_reset = 0

    def encode(self, text, *, add_special_tokens):
        return ([1] if add_special_tokens else []) + [ord(char) % 200 for char in text]

    def format_chat(self, messages, *, add_generation_prompt, enable_thinking):
        body = "|".join(f"{item['role']}:{item['content']}" for item in messages)
        return f"{body}|gen={add_generation_prompt}|thinking={enable_thinking}"

    def next_token_logits(self, input_ids, token_ids):
        self.logit_calls.append((input_ids, token_ids))
        return [float(token_id) / 10.0 for token_id in token_ids]

    def shared_prefix_batch_next_token_logits(self, input_ids_batch, token_ids_batch):
        self.shared_calls.append((input_ids_batch, token_ids_batch))
        return [
            [float(token_id) / 10.0 for token_id in token_ids]
            for token_ids in token_ids_batch
        ]

    def generate(self, input_ids, *, max_new_tokens):
        self.generated.append((input_ids, max_new_tokens))
        return '{"choice":"a"}', 5

    def runtime_metrics(self):
        return {
            "logical_input_tokens": 10,
            "physically_evaluated_tokens": 6,
            "reused_prefix_tokens": 4,
            "fresh_calls": 0,
            "shared_prefix_calls": 1,
            "reuse_ratio": 0.4,
        }

    def reset_runtime_metrics(self):
        self.metrics_reset += 1

    def close(self):
        self.closed = True


def model_file(tmp_path: Path) -> Path:
    path = tmp_path / "Qwen3.5-4B-Q4_K_M.gguf"
    path.write_bytes(b"fake-gguf")
    return path


def build_backend(tmp_path: Path):
    runtimes = []

    def factory(config):
        runtime = FakeRuntime(config)
        runtimes.append(runtime)
        return runtime

    backend = LlamaCppBackend(
        LlamaCppBackendConfig(model=model_file(tmp_path)),
        _runtime_factory=factory,
    )
    return backend, runtimes[0]


def test_backend_requires_local_gguf(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        LlamaCppBackend(
            LlamaCppBackendConfig(model=tmp_path / "missing.gguf"),
            _runtime_factory=FakeRuntime,
        )
    wrong = tmp_path / "model.bin"
    wrong.write_bytes(b"x")
    with pytest.raises(ValueError, match=".gguf"):
        LlamaCppBackend(
            LlamaCppBackendConfig(model=wrong),
            _runtime_factory=FakeRuntime,
        )


def test_identity_is_path_free_and_hashes_artifact(tmp_path: Path):
    backend, _ = build_backend(tmp_path)
    identity = backend.identity
    assert identity["backend"] == "llama-cpp-python"
    assert identity["binding_version"] == "0.3.35"
    assert identity["model"] == "Qwen3.5-4B-Q4_K_M.gguf"
    assert identity["quantization"] == "Q4_K_M"
    assert identity["artifact_sha256"] == hashlib.sha256(b"fake-gguf").hexdigest()
    assert str(tmp_path) not in str(identity)
    assert identity["selected_vocab_projection"] is False
    assert identity["shared_context_state"] is True


def test_tokenizer_uses_runtime_chat_template_and_no_implicit_bos(tmp_path: Path):
    backend, _ = build_backend(tmp_path)
    prompt = backend.tokenizer.apply_chat_template(
        [{"role": "user", "content": "hello"}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    assert "user:hello" in prompt
    assert "thinking=False" in prompt
    plain = backend.tokenizer.encode("ab", add_special_tokens=False)
    with_bos = backend.tokenizer.encode("ab", add_special_tokens=True)
    assert with_bos[1:] == plain


def test_backend_delegates_fresh_shared_and_generation(tmp_path: Path):
    backend, runtime = build_backend(tmp_path)
    assert backend.next_token_logits((1, 2), [10, 11]) == [1.0, 1.1]
    rows = backend.shared_prefix_batch_next_token_logits(
        [(1, 2, 3), (1, 2, 4)],
        [[10, 11], [10, 11]],
    )
    assert rows == [[1.0, 1.1], [1.0, 1.1]]
    assert len(runtime.shared_calls) == 1
    assert backend.generate((1, 2), max_new_tokens=8) == ('{"choice":"a"}', 5)
    assert backend.runtime_metrics()["reuse_ratio"] == 0.4
    backend.reset_runtime_metrics()
    assert runtime.metrics_reset == 1


def test_close_is_idempotent_and_invalidates_runtime(tmp_path: Path):
    backend, runtime = build_backend(tmp_path)
    backend.close()
    backend.close()
    assert runtime.closed is True
    with pytest.raises(RuntimeError, match="closed"):
        backend.next_token_logits((1,), [2])
