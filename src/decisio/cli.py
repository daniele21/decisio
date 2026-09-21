"""Command-line entry point for the Decisio decision laboratory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import run_benchmark
from .comparison import SCORER_KEYS, run_comparison
from .schema import ChoiceRequest


def _backend(args: argparse.Namespace):
    from .backends.qwen import QwenBackendConfig, QwenTransformersBackend

    return QwenTransformersBackend(
        QwenBackendConfig(
            model=args.model,
            revision=args.revision,
            device=args.device,
            dtype=args.dtype,
            local_files_only=args.local_files_only,
        )
    )


def _scorer(name: str, backend: Any):
    if name == "semantic":
        from .scorers import SemanticBinaryScorer

        return SemanticBinaryScorer(backend)
    if name == "semantic-independent":
        from .scorers import IndependentSemanticScorer

        return IndependentSemanticScorer(backend)
    if name == "letters":
        from .scorers import LetterTokenScorer

        return LetterTokenScorer(backend)
    if name == "generated":
        from .baselines import GeneratedJsonScorer

        return GeneratedJsonScorer(backend)
    raise ValueError(f"unknown scorer {name!r}")


def _add_model_args(parser: argparse.ArgumentParser) -> None:
    from .backends.qwen import DEFAULT_MODEL, DEFAULT_REVISION

    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument(
        "--dtype", choices=["bfloat16", "float16", "float32"], default="bfloat16"
    )
    parser.add_argument("--local-files-only", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="decisio")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scorer_choices = list(SCORER_KEYS)

    score = subparsers.add_parser("score", help="score one choice request from JSON")
    score.add_argument("--input", type=Path, required=True)
    score.add_argument("--scorer", choices=scorer_choices, default="semantic")
    _add_model_args(score)

    benchmark = subparsers.add_parser("benchmark", help="run a labeled JSONL benchmark")
    benchmark.add_argument("--input", type=Path, required=True)
    benchmark.add_argument("--output", type=Path, required=True)
    benchmark.add_argument("--scorer", choices=scorer_choices, default="semantic")
    benchmark.add_argument("--reverse-candidates", action="store_true")
    _add_model_args(benchmark)

    compare = subparsers.add_parser(
        "compare",
        help="run the paired v2/v1/letters/generated scorer matrix",
    )
    compare.add_argument("--input", type=Path, required=True)
    compare.add_argument("--output-dir", type=Path, required=True)
    _add_model_args(compare)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    backend = _backend(args)

    if args.command == "score":
        scorer = _scorer(args.scorer, backend)
        data = json.loads(args.input.read_text(encoding="utf-8"))
        result = scorer.score(ChoiceRequest.from_dict(data))
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "benchmark":
        scorer = _scorer(args.scorer, backend)
        summary = run_benchmark(
            args.input,
            args.output,
            scorer,
            reverse_candidates=args.reverse_candidates,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    scorers = {name: _scorer(name, backend) for name in SCORER_KEYS}
    report = run_comparison(args.input, args.output_dir, scorers)
    print(
        json.dumps(
            {
                "input_sha256": report["input_sha256"],
                "examples": report["examples"],
                "report_json": str(args.output_dir / "comparison.json"),
                "report_markdown": str(args.output_dir / "comparison.md"),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
