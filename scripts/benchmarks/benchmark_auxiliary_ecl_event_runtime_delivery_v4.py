#!/usr/bin/env python3
"""Benchmark compact V4 delivery against a retained raw-state trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from benchmarks.auxiliary_ecl_event.runtime_delivery_replay import (  # noqa: E402
    benchmark_runtime_delivery_v4,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--ecl", type=Path, required=True)
    parser.add_argument("--expected-ecl-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    arguments = parser.parse_args(argv)
    report = benchmark_runtime_delivery_v4(
        arguments.trace,
        arguments.ecl,
        expected_static_sha256=arguments.expected_ecl_sha256,
        repeats=arguments.repeats,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0 if all(report["gates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
