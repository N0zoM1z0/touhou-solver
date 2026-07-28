#!/usr/bin/env python3
"""Build a compact auxiliary-ECL event inventory from one retained trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auxiliary_ecl_event.report import (
    build_auxiliary_ecl_event_inventory_report,
    write_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--ecl", type=Path, required=True)
    parser.add_argument("--expected-ecl-sha256", required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_auxiliary_ecl_event_inventory_report(
        args.trace,
        args.ecl,
        expected_ecl_sha256=args.expected_ecl_sha256,
    )
    if args.output is None:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        write_report(report, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
