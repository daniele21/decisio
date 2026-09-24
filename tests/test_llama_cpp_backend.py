from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from decisio.backends.llama_cpp import (
    LlamaCppBackend,
    LlamaCppBackendConfig,
    _device_options,
    _NativeLlamaCppRuntime,
    _require_device_support,
    _shared_prefix_plan,
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


def test_device_configuration_maps_cpu_and_metal_to_llama_cpp_offload():
    assert _device_options("cpu") == (0, False)
    assert _device_options("metal") == (-1, True)


def test_device_configuration_rejects_unknown_device(tmp_path: Path):
    with pytest.raises(ValueError, match="cpu.*metal"):
        LlamaCppBackendConfig(model=model_file(tmp_path), device="cuda")


def test_metal_requires_macos_and_gpu_enabled_binding():
    class CpuOnlyBinding:
        @staticmethod
        def llama_supports_gpu_offload():
            return False

    class GpuBinding:
        @staticmethod
        def llama_supports_gpu_offload():
            return True

    with pytest.raises(RuntimeError, match="requires macOS"):
        _require_device_support("metal", GpuBinding(), platform_name="linux")
    with pytest.raises(RuntimeError, match="Metal-enabled"):
        _require_device_support("metal", CpuOnlyBinding(), platform_name="darwin")
    _require_device_support("metal", GpuBinding(), platform_name="darwin")
    _require_device_support("cpu", CpuOnlyBinding(), platform_name="linux")


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
    assert identity["device"] == "cpu"
    assert identity["n_gpu_layers"] == 0
    assert identity["offload_kqv"] is False
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


def test_metal_identity_records_offload_configuration(tmp_path: Path):
    path = model_file(tmp_path)
    backend = LlamaCppBackend(
        LlamaCppBackendConfig(model=path, device="metal"),
        _runtime_factory=FakeRuntime,
    )

    assert backend.identity["device"] == "metal"
    assert backend.identity["n_gpu_layers"] == -1
    assert backend.identity["offload_kqv"] is True


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


def test_shared_prefix_plan_falls_back_when_prefix_has_no_native_batch_boundary():
    assert _shared_prefix_plan(
        common_prefix_len=152,
        reusable_prefix_len=93,
        max_input_len=188,
        n_batch=512,
    ) == (0, None)


def test_shared_prefix_plan_accepts_exact_native_batch_boundary():
    assert _shared_prefix_plan(
        common_prefix_len=512,
        reusable_prefix_len=None,
        max_input_len=540,
        n_batch=512,
    ) == (512, None)


def test_shared_prefix_plan_aligns_long_reusable_state_to_native_batch_boundary():
    assert _shared_prefix_plan(
        common_prefix_len=1260,
        reusable_prefix_len=1207,
        max_input_len=1288,
        n_batch=512,
    ) == (1024, 1024)


def test_shared_prefix_plan_uses_aligned_common_prefix_without_cache_hint():
    assert _shared_prefix_plan(
        common_prefix_len=1260,
        reusable_prefix_len=None,
        max_input_len=1288,
        n_batch=512,
    ) == (1024, None)


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

@pytest.mark.parametrize("count", [1, 8, 9, 77])
def test_serial_candidate_reuse_is_independent_of_sequence_capacity(count):
    from collections import defaultdict

    runtime = object.__new__(_NativeLlamaCppRuntime)
    runtime.n_seq_max = 8
    runtime.n_batch = 4
    runtime.n_ctx = 128
    runtime.n_vocab = 256
    runtime._metrics = defaultdict(int)
    runtime._require_open = lambda: None
    state = []
    decoded = []
    runtime._clear_scoring_state = state.clear

    def decode(tokens, *, seq_id, n_past):
        assert seq_id == 0
        assert len(state) == n_past
        state.extend(tokens)
        decoded.append(tuple(tokens))

    def restore(snapshot, seq_id):
        assert seq_id == 0
        state[:] = snapshot
        return len(snapshot)

    runtime._decode_tokens = decode
    runtime._capture_sequence_state = lambda seq_id: tuple(state)
    runtime._restore_sequence_state = restore
    runtime._repeated_cache_key = lambda *args: None
    runtime._selected_logits = lambda ids: [float(sum(state) + token) for token in ids]
    inputs = [(1, 2, 3, 4, 10 + i) for i in range(count)]
    readouts = [[1, 2] for _ in inputs]
    expected = [
        runtime.next_token_logits(row, ids)
        for row, ids in zip(inputs, readouts, strict=True)
    ]
    runtime._metrics.clear()
    decoded.clear()

    actual = runtime.shared_prefix_batch_next_token_logits(inputs, readouts)

    assert actual == expected
    assert runtime._metrics["shared_prefix_fallbacks"] == 0
    assert runtime._metrics["shared_prefix_calls"] == 1
    assert runtime._metrics["fresh_calls"] == 0
    assert runtime._metrics["physically_evaluated_tokens"] == 4 + count
    assert runtime._metrics["logical_input_tokens"] == 5 * count
    assert decoded == [(1, 2, 3, 4)] + [(10 + i,) for i in range(count)]
