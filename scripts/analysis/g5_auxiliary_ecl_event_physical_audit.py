#!/usr/bin/env python3
"""Audit replay-capable auxiliary ECL event delivery from a physical run."""

from __future__ import annotations

import argparse
from pathlib import Path

from auxiliary_ecl_event.physical_report import (
    build_physical_report,
    write_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--ecl", type=Path, required=True)
    parser.add_argument("--expected-ecl-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_physical_report(
        args.trace,
        args.baseline,
        args.session,
        args.ecl,
        expected_ecl_sha256=args.expected_ecl_sha256,
    )
    write_report(report, args.output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
