#!/usr/bin/env python3
"""Generate the retained G3 stationary partial-witness capsule report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.partial_witness_capsule import audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--cadence", default="4,5,6")
    parser.add_argument("--max-scanned-roots", type=int, default=16)
    arguments = parser.parse_args(argv)
    cadence = tuple(
        int(value) for value in arguments.cadence.split(",") if value
    )
    result = audit(
        horizon=arguments.horizon,
        decision_frame_support=cadence,
        max_scanned_roots=arguments.max_scanned_roots,
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
