#!/usr/bin/env python3
"""Audit exact complete-mask roots joined to retained hazard capsules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.complete_mask_capsule import audit
from analysis.complete_mask_capsule.types import CompleteMaskWorkload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--capsule-dir", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--cadence", default="4,5,6")
    parser.add_argument("--root-limit", type=int, default=1)
    arguments = parser.parse_args(argv)
    result = audit(
        workloads=(
            CompleteMaskWorkload(
                name=arguments.name,
                stage=arguments.stage,
                trace=arguments.trace,
                capsule_dir=arguments.capsule_dir,
                physical_interpretation=(
                    "physical trace supplies exact complete-mask roots; "
                    "current future-event coverage remains fail-closed"
                ),
            ),
        ),
        horizon=arguments.horizon,
        decision_frame_support=tuple(
            int(value)
            for value in arguments.cadence.split(",")
            if value
        ),
        root_limit=arguments.root_limit,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["report_digest"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
