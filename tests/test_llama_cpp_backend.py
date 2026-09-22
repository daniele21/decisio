from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from decisio.backends.llama_cpp import (
    LlamaCppBackend,
    LlamaCppBackendConfig,
    _NativeLlamaCppRuntime,
)


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
        self.cache_clears = 0

    def encode(self, text, *, add_special_tokens):
        return ([1] if add_special_tokens else []) + [ord(char) % 200 for char in text]

    def format_chat(self, messages, *, add_generation_prompt, enable_thinking):
        body = "|".join(f"{item['role']}:{item['content']}" for item in messages)
        return f"{body}|gen={add_generation_prompt}|thinking={enable_thinking}"

    def next_token_logits(self, input_ids, token_ids):
        self.logit_calls.append((input_ids, token_ids))
        return [float(token_id) / 10.0 for token_id in token_ids]

    def shared_prefix_batch_next_token_logits(
        self,
        input_ids_batch,
        token_ids_batch,
        *,
        reusable_prefix_len=None,
    ):
        self.shared_calls.append(
            (input_ids_batch, token_ids_batch, reusable_prefix_len)
        )
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

    def clear_repeated_state_cache(self):
        self.cache_clears += 1

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


def test_cache_bounds_must_not_be_negative(tmp_path: Path):
    path = model_file(tmp_path)
    with pytest.raises(ValueError, match="repeated_state_cache_max_entries"):
        LlamaCppBackendConfig(model=path, repeated_state_cache_max_entries=-1)
    with pytest.raises(ValueError, match="repeated_state_cache_max_bytes"):
        LlamaCppBackendConfig(model=path, repeated_state_cache_max_bytes=-1)


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
    assert (
        identity["shared_prefix_primitive"]
        == "single_sequence_state_snapshot_restore"
    )
    assert identity["repeated_state_cache"] == "exact_compiler_token_prefix_lru"
    assert identity["repeated_state_cache_max_entries"] == 2
    assert identity["repeated_state_cache_max_bytes"] == 256 * 1024 * 1024


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


def test_fresh_view_disables_shared_prefix_capability(tmp_path: Path):
    backend, runtime = build_backend(tmp_path)
    view = backend.fresh_view()
    assert not hasattr(view, "shared_prefix_batch_next_token_logits")
    assert view.identity["execution_path"] == "fresh"
    rows = view.batch_next_token_logits(
        [(1, 2, 3), (1, 2, 4)],
        [[10, 11], [10, 11]],
    )
    assert rows == [[1.0, 1.1], [1.0, 1.1]]
    assert len(runtime.logit_calls) == 2
    assert runtime.shared_calls == []


def test_backend_delegates_fresh_shared_and_generation(tmp_path: Path):
    backend, runtime = build_backend(tmp_path)
    assert backend.next_token_logits((1, 2), [10, 11]) == [1.0, 1.1]
    rows = backend.shared_prefix_batch_next_token_logits(
        [(1, 2, 3), (1, 2, 4)],
        [[10, 11], [10, 11]],
        reusable_prefix_len=2,
    )
    assert rows == [[1.0, 1.1], [1.0, 1.1]]
    assert runtime.shared_calls == [
        ([(1, 2, 3), (1, 2, 4)], [[10, 11], [10, 11]], 2)
    ]
    backend.clear_repeated_state_cache()
    assert runtime.cache_clears == 1
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


class _FakeBatchData:
    def __init__(self, *, n_tokens: int, n_seq_max: int):
        self.n_tokens = 0
        self.token = [0] * n_tokens
        self.pos = [0] * n_tokens
        self.seq_id = [[0] * n_seq_max for _ in range(n_tokens)]
        self.n_seq_id = [0] * n_tokens
        self.logits = [False] * n_tokens


class _FakeBatchOwner:
    def __init__(self, *, n_tokens: int, n_seq_max: int):
        self.batch = _FakeBatchData(n_tokens=n_tokens, n_seq_max=n_seq_max)


def test_native_batch_is_single_sequence():
    runtime = object.__new__(_NativeLlamaCppRuntime)
    runtime.n_seq_max = 4
    runtime._batch = _FakeBatchOwner(n_tokens=8, n_seq_max=4)

    runtime._set_batch((11, 12, 13), seq_id=0, n_past=7)

    batch = runtime._batch.batch
    assert batch.n_tokens == 3
    assert batch.token[:3] == [11, 12, 13]
    assert batch.pos[:3] == [7, 8, 9]
    assert batch.n_seq_id[:3] == [1, 1, 1]
    assert [row[0] for row in batch.seq_id[:3]] == [0, 0, 0]
    assert batch.logits[:3] == [False, False, True]


class _FakeSequenceStateApi:
    def __init__(self):
        self.restored = []

    def llama_state_seq_get_size(self, ctx, seq_id):
        del ctx, seq_id
        return 4

    def llama_state_seq_get_data(self, ctx, dst, size, seq_id):
        del ctx, seq_id
        payload = b"test"
        assert size == len(payload)
        for index, value in enumerate(payload):
            dst[index] = value
        return size

    def llama_state_seq_set_data(self, ctx, src, size, seq_id):
        del ctx
        self.restored.append((bytes(src[:size]), seq_id))
        return size


class _FakeScoreContext:
    ctx = object()


def test_native_sequence_state_round_trip_uses_llama_state_api():
    runtime = object.__new__(_NativeLlamaCppRuntime)
    runtime._llama_cpp = _FakeSequenceStateApi()
    runtime._score_ctx = _FakeScoreContext()

    state = runtime._capture_sequence_state(0)
    restored = runtime._restore_sequence_state(state, 0)

    assert bytes(state) == b"test"
    assert restored == 4
    assert runtime._llama_cpp.restored == [(b"test", 0)]

