"""Minimal DecisionSession example for support routing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from decisio import Candidate, DecisionSession


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "metal"], default="cpu")
    parser.add_argument("--fresh", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request = json.loads(
        Path("examples/support-routing/request.json").read_text(encoding="utf-8")
    )
    candidates = tuple(Candidate.from_dict(item) for item in request["candidates"])

    with DecisionSession(
        args.model,
        request["question"],
        device=args.device,
    ) as session:
        result = session.choose(
            request_id=request["id"],
            state=request["state"],
            candidates=candidates,
            fresh=args.fresh,
        )

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
