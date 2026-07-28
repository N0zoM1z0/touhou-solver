#!/usr/bin/env python3
"""Audit the exact loss bracket containing the canonical first hit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.first_loss_capsule import audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--capsule-dir", type=Path, required=True)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--cadence", default="4,5,6")
    parser.add_argument("--gameplay-epoch", type=int)
    parser.add_argument("--stage-route-index", type=int)
    arguments = parser.parse_args(argv)
    report = audit(
        trace=arguments.trace,
        capsule_dir=arguments.capsule_dir,
        horizon=arguments.horizon,
        decision_frame_support=tuple(
            int(value)
            for value in arguments.cadence.split(",")
            if value
        ),
        gameplay_epoch=arguments.gameplay_epoch,
        stage_route_index=arguments.stage_route_index,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["report_digest"]))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
