"""PyTorch/Transformers reference backend for Qwen 3.5 text-only scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_MODEL = "Qwen/Qwen3.5-4B"
DEFAULT_REVISION = "1eef1f4e0bc57dec8f814d1e4c714c8e0065d261"


@dataclass(frozen=True, slots=True)
class QwenBackendConfig:
    model: str = DEFAULT_MODEL
    revision: str = DEFAULT_REVISION
    device: str = "auto"
    dtype: str = "bfloat16"
    local_files_only: bool = False


class QwenTransformersBackend:
    """Reference backend with selected-vocabulary projection and prompt batching."""

    def __init__(self, config: QwenBackendConfig | None = None):
        config = config or QwenBackendConfig()
        try:
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Qwen backend requires the 'qwen' extra: uv sync --extra qwen"
            ) from exc

        self._torch = torch
        self._transformers_version = transformers.__version__
        self.config = config
        self.device = self._resolve_device(config.device)
        self.dtype = self._resolve_dtype(config.dtype)

        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model,
            revision=config.revision,
            trust_remote_code=False,
            local_files_only=config.local_files_only,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            config.model,
            revision=config.revision,
            dtype=self.dtype,
            trust_remote_code=False,
            local_files_only=config.local_files_only,
        )
        self.model.to(self.device)
        self.model.eval()

        model_type = getattr(self.model.config, "model_type", None)
        if model_type != "qwen3_5_text":
            raise ValueError(f"expected qwen3_5_text causal LM, got {model_type!r}")
        if not hasattr(self.model, "model"):
            raise ValueError("Qwen causal LM does not expose the expected text backbone")

    def _resolve_device(self, requested: str) -> str:
        if requested == "auto":
            return "cuda" if self._torch.cuda.is_available() else "cpu"
        if requested == "cuda" and not self._torch.cuda.is_available():
            raise RuntimeError("CUDA requested but torch.cuda.is_available() is false")
        if requested not in {"cuda", "cpu"}:
            raise ValueError("device must be auto, cuda, or cpu")
        return requested

    def _resolve_dtype(self, requested: str):
        supported = {
            "bfloat16": self._torch.bfloat16,
            "float16": self._torch.float16,
            "float32": self._torch.float32,
        }
        try:
            return supported[requested]
        except KeyError as exc:
            raise ValueError(f"unsupported dtype {requested!r}") from exc

    @property
    def identity(self) -> dict[str, Any]:
        resolved_revision = getattr(self.model.config, "_commit_hash", None) or self.config.revision
        cuda_device_name = (
            self._torch.cuda.get_device_name() if self.device == "cuda" else None
        )
        cuda_device_capability = (
            list(self._torch.cuda.get_device_capability()) if self.device == "cuda" else None
        )
        cuda_total_memory_bytes = (
            int(self._torch.cuda.get_device_properties(0).total_memory)
            if self.device == "cuda"
            else None
        )
        return {
            "backend": "transformers",
            "model": self.config.model,
            "requested_revision": self.config.revision,
            "resolved_revision": resolved_revision,
            "model_type": getattr(self.model.config, "model_type", None),
            "device": self.device,
            "dtype": str(self.dtype).removeprefix("torch."),
            "transformers": self._transformers_version,
            "torch": self._torch.__version__,
            "cuda_runtime": self._torch.version.cuda,
            "cuda_device_name": cuda_device_name,
            "cuda_device_capability": cuda_device_capability,
            "cuda_total_memory_bytes": cuda_total_memory_bytes,
            "batched_candidate_scoring": True,
            "selected_vocab_projection": True,
        }

    def synchronize(self) -> None:
        """Synchronize accelerator work before or after wall-clock timing."""
        if self.device == "cuda":
            self._torch.cuda.synchronize()

    def reset_peak_memory(self) -> None:
        """Reset CUDA peak-memory accounting for one measured trial."""
        if self.device == "cuda":
            self._torch.cuda.reset_peak_memory_stats()

    def peak_memory_bytes(self) -> int | None:
        """Return CUDA peak allocated memory since the last reset."""
        if self.device != "cuda":
            return None
        return int(self._torch.cuda.max_memory_allocated())

    def _project_selected(
        self,
        hidden_states,
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]:
        torch = self._torch
        output_head = self.model.get_output_embeddings()
        unique_ids = sorted({token_id for row in token_ids_batch for token_id in row})
        unique_tensor = torch.tensor(unique_ids, dtype=torch.long, device=self.device)

        with torch.inference_mode():
            weight = getattr(output_head, "weight", None)
            if weight is not None:
                selected_weight = weight.index_select(0, unique_tensor)
                bias = getattr(output_head, "bias", None)
                selected_bias = None if bias is None else bias.index_select(0, unique_tensor)
                logits = torch.nn.functional.linear(hidden_states, selected_weight, selected_bias)
            else:  # pragma: no cover - defensive compatibility fallback
                logits = output_head(hidden_states).index_select(-1, unique_tensor)
            values = logits.float().cpu()

        offsets = {token_id: index for index, token_id in enumerate(unique_ids)}
        return [
            [float(values[row_index, offsets[token_id]]) for token_id in token_ids]
            for row_index, token_ids in enumerate(token_ids_batch)
        ]

    def batch_next_token_logits(
        self,
        input_ids_batch: list[tuple[int, ...]],
        token_ids_batch: list[list[int]],
    ) -> list[list[float]]:
        if not input_ids_batch:
            raise ValueError("input_ids_batch must not be empty")
        if len(input_ids_batch) != len(token_ids_batch):
            raise ValueError("input and token-id batch sizes must match")
        if any(not input_ids for input_ids in input_ids_batch):
            raise ValueError("input sequences must not be empty")
        if any(not token_ids for token_ids in token_ids_batch):
            raise ValueError("token-id rows must not be empty")

        torch = self._torch
        lengths = [len(input_ids) for input_ids in input_ids_batch]
        max_length = max(lengths)
        pad_token_id = self.tokenizer.pad_token_id
        if pad_token_id is None:
            pad_token_id = self.tokenizer.eos_token_id
        if pad_token_id is None:
            raise ValueError("tokenizer must expose pad_token_id or eos_token_id")

        ids = torch.full(
            (len(input_ids_batch), max_length),
            fill_value=pad_token_id,
            dtype=torch.long,
            device=self.device,
        )
        mask = torch.zeros_like(ids)
        for row_index, input_ids in enumerate(input_ids_batch):
            length = len(input_ids)
            ids[row_index, :length] = torch.tensor(
                input_ids,
                dtype=torch.long,
                device=self.device,
            )
            mask[row_index, :length] = 1

        with torch.inference_mode():
            outputs = self.model.model(
                input_ids=ids,
                attention_mask=mask,
                use_cache=False,
            )
            hidden = outputs.last_hidden_state
            row_indices = torch.arange(len(lengths), device=self.device)
            last_indices = torch.tensor(lengths, dtype=torch.long, device=self.device) - 1
            final_hidden = hidden[row_indices, last_indices]

        return self._project_selected(final_hidden, token_ids_batch)

    def next_token_logits(self, input_ids: tuple[int, ...], token_ids: list[int]) -> list[float]:
        return self.batch_next_token_logits([input_ids], [token_ids])[0]

    def generate(self, input_ids: tuple[int, ...], *, max_new_tokens: int) -> tuple[str, int]:
        if not input_ids:
            raise ValueError("input_ids must not be empty")
        if max_new_tokens < 1:
            raise ValueError("max_new_tokens must be positive")
        torch = self._torch
        ids = torch.tensor([input_ids], dtype=torch.long, device=self.device)
        mask = torch.ones_like(ids)
        eos = self.tokenizer.eos_token_id
        with torch.inference_mode():
            output = self.model.generate(
                input_ids=ids,
                attention_mask=mask,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=eos,
            )
        new_ids = output[0, ids.shape[1] :]
        text = self.tokenizer.decode(new_ids, skip_special_tokens=True)
        return text, int(new_ids.numel())
