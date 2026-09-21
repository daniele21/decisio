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
    """Fresh single-sequence scorer; cache sharing belongs to a later runtime milestone."""

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
        }

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

    def next_token_logits(self, input_ids: tuple[int, ...], token_ids: list[int]) -> list[float]:
        if not input_ids:
            raise ValueError("input_ids must not be empty")
        if not token_ids:
            raise ValueError("token_ids must not be empty")
        torch = self._torch
        ids = torch.tensor([input_ids], dtype=torch.long, device=self.device)
        mask = torch.ones_like(ids)
        with torch.inference_mode():
            output = self.model(
                input_ids=ids,
                attention_mask=mask,
                use_cache=False,
                logits_to_keep=1,
            )
            final = output.logits[0, -1]
            selected = final[torch.tensor(token_ids, dtype=torch.long, device=self.device)]
        return selected.float().cpu().tolist()
