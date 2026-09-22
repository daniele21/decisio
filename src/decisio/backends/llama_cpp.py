"""In-process llama.cpp backend for local GGUF decision scoring."""

from __future__ import annotations

import ctypes
import hashlib
import os
import platform
import re
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

LLAMA_CPP_PYTHON_VERSION = "0.3.35"


@dataclass(frozen=True, slots=True)
class LlamaCppBackendConfig:
    """Pinned CPU reference configuration for one local GGUF."""

    model: str | Path
    device: str = "cpu"
    n_ctx: int = 8192
    n_batch: int = 512
    n_ubatch: int = 512
    n_threads: int | None = None
    n_threads_batch: int | None = None
    max_sequences: int = 8
    use_mmap: bool = True
    use_mlock: bool = False
    seed: int = 0
    verbose: bool = False

    def __post_init__(self) -> None:
        if self.device != "cpu":
            raise ValueError("the v1 reference backend currently supports device='cpu' only")
        for name in ("n_ctx", "n_batch", "n_ubatch", "max_sequences"):
            if int(getattr(self, name)) < 1:
                raise ValueError(f"{name} must be positive")
        for name in ("n_threads", "n_threads_batch"):
            value = getattr(self, name)
            if value is not None and int(value) < 1:
                raise ValueError(f"{name} must be positive when set")


class _Runtime(Protocol):
    binding_version: str
    metadata: Mapping[str, Any]
    n_vocab: int
    n_ctx: int
    n_batch: int
    n_ubatch: int
    n_threads: int
    n_threads_batch: int
    n_seq_max: int

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]: ...

    def format_chat(
        self,
        messages: list[dict[str, str]],
        *,
        add_generation_prompt: bool,
        enable_thinking: bool,
    ) -> str: ...

    def next_token_logits(
        self, input_ids: tuple[int, ...], token_ids: list[int]
    ) -> list[float]: ...

    def shared_prefix_batch_next_token_logits(
        self,
        input_ids_batch: list[tuple[int, ...]],
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]: ...

    def generate(
        self, input_ids: tuple[int, ...], *, max_new_tokens: int
    ) -> tuple[str, int]: ...

    def runtime_metrics(self) -> dict[str, int | float]: ...

    def reset_runtime_metrics(self) -> None: ...

    def close(self) -> None: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quantization_from_name(name: str) -> str | None:
    match = re.search(r"(?:IQ\d(?:_[A-Z0-9]+)+|Q\d(?:_[A-Z0-9]+)+)", name.upper())
    return None if match is None else match.group(0)


def _process_peak_rss_bytes() -> int | None:
    try:
        import resource
    except ImportError:  # pragma: no cover - non-POSIX platform
        return None
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _longest_common_prefix(rows: Sequence[tuple[int, ...]]) -> int:
    if not rows:
        return 0
    limit = min(len(row) for row in rows)
    first = rows[0]
    for index in range(limit):
        token = first[index]
        if any(row[index] != token for row in rows[1:]):
            return index
    return limit



class _NativeLlamaCppRuntime:
    """Pinned adapter over llama-cpp-python plus one low-level scoring context."""

    def __init__(self, config: LlamaCppBackendConfig):
        try:
            import llama_cpp
            from llama_cpp import Llama, _internals
            from llama_cpp.llama_chat_format import Jinja2ChatFormatter
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "llama.cpp backend requires the 'llama' extra: uv sync --extra llama"
            ) from exc

        if llama_cpp.__version__ != LLAMA_CPP_PYTHON_VERSION:
            raise RuntimeError(
                "unsupported llama-cpp-python version: "
                f"{llama_cpp.__version__!r}; expected {LLAMA_CPP_PYTHON_VERSION!r}"
            )

        self._llama_cpp = llama_cpp
        self._formatter_type = Jinja2ChatFormatter
        self.binding_version = llama_cpp.__version__
        self.n_threads = config.n_threads or max(1, os.cpu_count() or 1)
        self.n_threads_batch = config.n_threads_batch or self.n_threads
        self.n_batch = config.n_batch
        self.n_ubatch = config.n_ubatch
        self._metrics = {
            "logical_input_tokens": 0,
            "physically_evaluated_tokens": 0,
            "reused_prefix_tokens": 0,
            "fresh_calls": 0,
            "shared_prefix_calls": 0,
            "prefix_state_snapshot_bytes": 0,
            "prefix_state_restore_bytes": 0,
            "prefix_state_restores": 0,
        }

        self._llm = Llama(
            model_path=str(Path(config.model)),
            n_gpu_layers=0,
            n_ctx=config.n_ctx,
            n_batch=config.n_batch,
            n_ubatch=config.n_ubatch,
            n_threads=self.n_threads,
            n_threads_batch=self.n_threads_batch,
            seed=config.seed,
            logits_all=False,
            embedding=False,
            offload_kqv=False,
            flash_attn=False,
            use_mmap=config.use_mmap,
            use_mlock=config.use_mlock,
            verbose=config.verbose,
        )
        self.metadata = dict(getattr(self._llm, "metadata", {}) or {})
        self.n_vocab = int(self._llm.n_vocab())
        self.n_ctx = int(self._llm.n_ctx())

        max_parallel = int(llama_cpp.llama_max_parallel_sequences())
        self.n_seq_max = min(config.max_sequences, max_parallel)
        if self.n_seq_max < 1:
            raise RuntimeError("llama.cpp reported no usable sequence slots")

        params = llama_cpp.llama_context_default_params()
        params.n_ctx = self.n_ctx
        params.n_batch = config.n_batch
        params.n_ubatch = config.n_ubatch
        params.n_seq_max = self.n_seq_max
        params.embeddings = False
        params.offload_kqv = False
        params.flash_attn_type = llama_cpp.LLAMA_FLASH_ATTN_TYPE_DISABLED
        params.kv_unified = True

        self._score_ctx = _internals.LlamaContext(
            model=self._llm._model,
            params=params,
            verbose=config.verbose,
        )
        self._score_ctx.set_n_threads(self.n_threads, self.n_threads_batch)
        self._batch = _internals.LlamaBatch(
            n_tokens=config.n_batch,
            embd=0,
            n_seq_max=self.n_seq_max,
            verbose=config.verbose,
        )
        self._closed = False

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("llama.cpp runtime is closed")

    def _special_text(self, token_id: int) -> str:
        if token_id < 0:
            return ""
        return self._llm.detokenize([token_id], special=True).decode(
            "utf-8", errors="replace"
        )

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        self._require_open()
        return list(
            self._llm.tokenize(
                text.encode("utf-8"),
                add_bos=add_special_tokens,
                special=True,
            )
        )

    def format_chat(
        self,
        messages: list[dict[str, str]],
        *,
        add_generation_prompt: bool,
        enable_thinking: bool,
    ) -> str:
        self._require_open()
        template = self.metadata.get("tokenizer.chat_template")
        if not isinstance(template, str) or not template.strip():
            raise RuntimeError("GGUF does not expose tokenizer.chat_template metadata")
        formatter = self._formatter_type(
            template=template,
            eos_token=self._special_text(int(self._llm.token_eos())),
            bos_token=self._special_text(int(self._llm.token_bos())),
            add_generation_prompt=add_generation_prompt,
            stop_token_ids=[int(self._llm.token_eos())],
        )
        return formatter(
            messages=messages,
            enable_thinking=enable_thinking,
        ).prompt

    def _clear_scoring_state(self) -> None:
        self._score_ctx.kv_cache_clear()

    def _set_batch(
        self,
        tokens: Sequence[int],
        *,
        seq_id: int,
        n_past: int,
    ) -> None:
        if seq_id < 0 or seq_id >= self.n_seq_max:
            raise ValueError("seq_id is outside the configured sequence capacity")

        batch = self._batch.batch
        batch.n_tokens = len(tokens)
        for index, token in enumerate(tokens):
            batch.token[index] = int(token)
            batch.pos[index] = n_past + index
            batch.seq_id[index][0] = seq_id
            batch.n_seq_id[index] = 1
            batch.logits[index] = False
        batch.logits[len(tokens) - 1] = True

    def _decode_tokens(
        self,
        tokens: Sequence[int],
        *,
        seq_id: int,
        n_past: int,
    ) -> None:
        offset = 0
        while offset < len(tokens):
            chunk = tokens[offset : offset + self.n_batch]
            self._set_batch(chunk, seq_id=seq_id, n_past=n_past + offset)
            self._score_ctx.decode(self._batch)
            offset += len(chunk)

    def _selected_logits(self, token_ids: list[int]) -> list[float]:
        logits = self._score_ctx.get_logits_ith(-1)
        if not logits:
            raise RuntimeError("llama.cpp did not expose final-token logits")
        return [float(logits[token_id]) for token_id in token_ids]

    def _capture_sequence_state(self, seq_id: int) -> Any:
        size = int(
            self._llama_cpp.llama_state_seq_get_size(self._score_ctx.ctx, seq_id)
        )
        if size < 1:
            raise RuntimeError("llama.cpp returned an empty sequence state")
        state = (ctypes.c_uint8 * size)()
        copied = int(
            self._llama_cpp.llama_state_seq_get_data(
                self._score_ctx.ctx,
                state,
                size,
                seq_id,
            )
        )
        if copied != size:
            raise RuntimeError(
                f"llama.cpp copied {copied} sequence-state bytes; expected {size}"
            )
        return state

    def _restore_sequence_state(self, state: Any, seq_id: int) -> int:
        size = len(state)
        restored = int(
            self._llama_cpp.llama_state_seq_set_data(
                self._score_ctx.ctx,
                state,
                size,
                seq_id,
            )
        )
        if restored != size:
            raise RuntimeError(
                f"llama.cpp restored {restored} sequence-state bytes; expected {size}"
            )
        return restored

    def _validate(
        self,
        input_ids: tuple[int, ...],
        token_ids: list[int],
    ) -> None:
        if not input_ids:
            raise ValueError("input_ids must not be empty")
        if len(input_ids) > self.n_ctx:
            raise ValueError(
                f"input has {len(input_ids)} tokens but context supports {self.n_ctx}"
            )
        if not token_ids:
            raise ValueError("token_ids must not be empty")
        if any(token_id < 0 or token_id >= self.n_vocab for token_id in token_ids):
            raise ValueError("token_ids contain an id outside the model vocabulary")

    def next_token_logits(
        self,
        input_ids: tuple[int, ...],
        token_ids: list[int],
    ) -> list[float]:
        self._require_open()
        self._validate(input_ids, token_ids)
        self._clear_scoring_state()
        self._decode_tokens(input_ids, seq_id=0, n_past=0)
        self._metrics["logical_input_tokens"] += len(input_ids)
        self._metrics["physically_evaluated_tokens"] += len(input_ids)
        self._metrics["fresh_calls"] += 1
        return self._selected_logits(token_ids)

    def shared_prefix_batch_next_token_logits(
        self,
        input_ids_batch: list[tuple[int, ...]],
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]:
        self._require_open()
        if not input_ids_batch:
            raise ValueError("input_ids_batch must not be empty")
        if len(input_ids_batch) != len(token_ids_batch):
            raise ValueError("input and token-id batch sizes must match")
        if len(input_ids_batch) > self.n_seq_max:
            return [
                self.next_token_logits(input_ids, token_ids)
                for input_ids, token_ids in zip(
                    input_ids_batch, token_ids_batch, strict=True
                )
            ]
        for input_ids, token_ids in zip(
            input_ids_batch, token_ids_batch, strict=True
        ):
            self._validate(input_ids, token_ids)

        prefix_len = _longest_common_prefix(input_ids_batch)
        if prefix_len < 1:
            return [
                self.next_token_logits(input_ids, token_ids)
                for input_ids, token_ids in zip(
                    input_ids_batch, token_ids_batch, strict=True
                )
            ]

        prefix = input_ids_batch[0][:prefix_len]
        physical = prefix_len + sum(
            len(input_ids) - prefix_len for input_ids in input_ids_batch
        )

        # Multi-sequence prefix sharing is not fresh-equivalent for the pinned
        # Qwen3.5 hybrid runtime. Keep one canonical sequence instead: prefill the
        # common prefix once, snapshot llama.cpp's complete sequence memory, and
        # restore that snapshot before each later candidate suffix.
        self._clear_scoring_state()
        self._decode_tokens(prefix, seq_id=0, n_past=0)
        result: list[list[float] | None] = [None] * len(input_ids_batch)

        for candidate_index, input_ids in enumerate(input_ids_batch):
            if len(input_ids) == prefix_len:
                result[candidate_index] = self._selected_logits(
                    token_ids_batch[candidate_index]
                )

        prefix_state = self._capture_sequence_state(0)
        snapshot_size = len(prefix_state)
        restore_count = 0
        live_prefix_state = True

        for candidate_index, input_ids in enumerate(input_ids_batch):
            suffix = input_ids[prefix_len:]
            if not suffix:
                continue
            if not live_prefix_state:
                self._clear_scoring_state()
                self._restore_sequence_state(prefix_state, 0)
                restore_count += 1

            self._decode_tokens(suffix, seq_id=0, n_past=prefix_len)
            result[candidate_index] = self._selected_logits(
                token_ids_batch[candidate_index]
            )
            live_prefix_state = False

        if any(row is None for row in result):
            raise RuntimeError(
                "llama.cpp sequence-state reuse did not produce all candidate logits"
            )

        logical = sum(len(row) for row in input_ids_batch)
        self._metrics["logical_input_tokens"] += logical
        self._metrics["physically_evaluated_tokens"] += physical
        self._metrics["reused_prefix_tokens"] += logical - physical
        self._metrics["shared_prefix_calls"] += 1
        self._metrics["prefix_state_snapshot_bytes"] += snapshot_size
        self._metrics["prefix_state_restore_bytes"] += snapshot_size * restore_count
        self._metrics["prefix_state_restores"] += restore_count
        return [row for row in result if row is not None]

    def generate(
        self,
        input_ids: tuple[int, ...],
        *,
        max_new_tokens: int,
    ) -> tuple[str, int]:
        self._require_open()
        if not input_ids:
            raise ValueError("input_ids must not be empty")
        if max_new_tokens < 1:
            raise ValueError("max_new_tokens must be positive")
        if len(input_ids) > self.n_ctx:
            raise ValueError(
                f"input has {len(input_ids)} tokens but context supports {self.n_ctx}"
            )
        response = self._llm.create_completion(
            prompt=list(input_ids),
            max_tokens=max_new_tokens,
            temperature=0.0,
            top_p=1.0,
            min_p=0.0,
            top_k=1,
            repeat_penalty=1.0,
            seed=0,
            stream=False,
        )
        if not isinstance(response, dict):
            raise RuntimeError("llama.cpp completion returned an unexpected stream")
        choices = response.get("choices")
        usage = response.get("usage")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("llama.cpp completion returned no choices")
        text = choices[0].get("text")
        if not isinstance(text, str):
            raise RuntimeError("llama.cpp completion returned non-text output")
        generated_tokens = (
            int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
        )
        return text, generated_tokens

    def runtime_metrics(self) -> dict[str, int | float]:
        logical = int(self._metrics["logical_input_tokens"])
        physical = int(self._metrics["physically_evaluated_tokens"])
        return {
            **self._metrics,
            "reuse_ratio": 0.0 if logical == 0 else (logical - physical) / logical,
        }

    def reset_runtime_metrics(self) -> None:
        for key in self._metrics:
            self._metrics[key] = 0

    def close(self) -> None:
        if self._closed:
            return
        self._batch.close()
        self._score_ctx.close()
        self._llm.close()
        self._closed = True


class _TokenizerAdapter:
    def __init__(self, backend: LlamaCppBackend):
        self._backend = backend

    def encode(self, text: str, *, add_special_tokens: bool = False) -> list[int]:
        with self._backend._lock:
            return self._backend._runtime_or_raise().encode(
                text, add_special_tokens=add_special_tokens
            )

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool = False,
        add_generation_prompt: bool = True,
        enable_thinking: bool = False,
        **kwargs: Any,
    ) -> str:
        del kwargs
        if tokenize:
            raise ValueError("Decisio requests text chat templates before tokenization")
        with self._backend._lock:
            return self._backend._runtime_or_raise().format_chat(
                messages,
                add_generation_prompt=add_generation_prompt,
                enable_thinking=enable_thinking,
            )


RuntimeFactory = Callable[[LlamaCppBackendConfig], _Runtime]


class FreshLlamaCppBackendView:
    """Diagnostic view that disables shared-prefix scoring without reloading the model."""

    def __init__(self, backend: LlamaCppBackend):
        self._backend = backend
        self.tokenizer = backend.tokenizer

    @property
    def identity(self) -> dict[str, Any]:
        return {**self._backend.identity, "execution_path": "fresh"}

    def next_token_logits(
        self,
        input_ids: tuple[int, ...],
        token_ids: list[int],
    ) -> list[float]:
        return self._backend.next_token_logits(input_ids, token_ids)

    def batch_next_token_logits(
        self,
        input_ids_batch: list[tuple[int, ...]],
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]:
        return self._backend.batch_next_token_logits(input_ids_batch, token_ids_batch)


class LlamaCppBackend:
    """Canonical v1 backend: local GGUF + pinned llama.cpp, CPU reference path."""

    def __init__(
        self,
        config: LlamaCppBackendConfig,
        *,
        _runtime_factory: RuntimeFactory | None = None,
    ):
        model_path = Path(config.model).expanduser()
        if not model_path.is_file():
            raise FileNotFoundError(f"GGUF model does not exist: {model_path}")
        if model_path.suffix.lower() != ".gguf":
            raise ValueError("model must be a .gguf file")

        self.config = config
        self._model_path = model_path
        self._lock = threading.RLock()
        self._closed = False
        factory = _runtime_factory or _NativeLlamaCppRuntime
        self._runtime: _Runtime | None = factory(config)
        self.tokenizer = _TokenizerAdapter(self)

        runtime = self._runtime_or_raise()
        metadata = runtime.metadata
        self._identity = {
            "backend": "llama-cpp-python",
            "runtime": "llama.cpp",
            "binding_version": runtime.binding_version,
            "model": model_path.name,
            "artifact_filename": model_path.name,
            "artifact_sha256": _sha256(model_path),
            "artifact_size_bytes": model_path.stat().st_size,
            "quantization": _quantization_from_name(model_path.name),
            "gguf_architecture": metadata.get("general.architecture"),
            "gguf_name": metadata.get("general.name"),
            "gguf_file_type": metadata.get("general.file_type"),
            "device": "cpu",
            "n_ctx": runtime.n_ctx,
            "n_batch": runtime.n_batch,
            "n_ubatch": runtime.n_ubatch,
            "n_threads": runtime.n_threads,
            "n_threads_batch": runtime.n_threads_batch,
            "n_seq_max": runtime.n_seq_max,
            "use_mmap": config.use_mmap,
            "use_mlock": config.use_mlock,
            "cpu_machine": platform.machine(),
            "cpu_processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "memory_metric": "process_max_rss",
            "zero_generation_native_scoring": True,
            "shared_context_state": True,
            "shared_prefix_primitive": "single_sequence_state_snapshot_restore",
            "selected_vocab_projection": False,
            "logit_readout": "full_final_position_vocab_then_select",
        }

    def _runtime_or_raise(self) -> _Runtime:
        if self._runtime is None or self._closed:
            raise RuntimeError("llama.cpp backend is closed")
        return self._runtime

    @property
    def identity(self) -> dict[str, Any]:
        return dict(self._identity)

    def fresh_view(self) -> FreshLlamaCppBackendView:
        """Return a scorer-compatible fresh-evaluation view for equivalence diagnostics."""
        return FreshLlamaCppBackendView(self)

    def next_token_logits(
        self,
        input_ids: tuple[int, ...],
        token_ids: list[int],
    ) -> list[float]:
        with self._lock:
            return self._runtime_or_raise().next_token_logits(input_ids, token_ids)

    def batch_next_token_logits(
        self,
        input_ids_batch: list[tuple[int, ...]],
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]:
        if len(input_ids_batch) != len(token_ids_batch):
            raise ValueError("input and token-id batch sizes must match")
        with self._lock:
            runtime = self._runtime_or_raise()
            return [
                runtime.next_token_logits(input_ids, token_ids)
                for input_ids, token_ids in zip(
                    input_ids_batch, token_ids_batch, strict=True
                )
            ]

    def shared_prefix_batch_next_token_logits(
        self,
        input_ids_batch: list[tuple[int, ...]],
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]:
        with self._lock:
            return self._runtime_or_raise().shared_prefix_batch_next_token_logits(
                input_ids_batch, token_ids_batch
            )

    def generate(
        self,
        input_ids: tuple[int, ...],
        *,
        max_new_tokens: int,
    ) -> tuple[str, int]:
        with self._lock:
            return self._runtime_or_raise().generate(
                input_ids, max_new_tokens=max_new_tokens
            )

    def runtime_metrics(self) -> dict[str, int | float]:
        with self._lock:
            return dict(self._runtime_or_raise().runtime_metrics())

    def reset_runtime_metrics(self) -> None:
        with self._lock:
            self._runtime_or_raise().reset_runtime_metrics()

    def synchronize(self) -> None:
        return None

    def reset_peak_memory(self) -> None:
        return None

    def peak_memory_bytes(self) -> int | None:
        return _process_peak_rss_bytes()

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            runtime = self._runtime
            self._runtime = None
            self._closed = True
            if runtime is not None:
                runtime.close()

    shutdown = close

    def __enter__(self) -> LlamaCppBackend:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback
        self.close()
