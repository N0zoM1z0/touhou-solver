#!/usr/bin/env python3
"""Build the fixed V6 coalesced auxiliary-event physical report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analysis.auxiliary_ecl_event.physical_report_v6 import (  # noqa: E402
    build_physical_report_v6,
    write_report_v6,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the fixed V6 coalesced auxiliary-event physical report."
        )
    )
    parser.add_argument("trace", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("session", type=Path)
    parser.add_argument("ecl", type=Path)
    parser.add_argument("output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_physical_report_v6(
        args.trace,
        args.baseline,
        args.session,
        args.ecl,
    )
    write_report_v6(report, args.output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
