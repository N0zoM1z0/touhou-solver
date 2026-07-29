#!/usr/bin/env python3
"""Audit epoch-safe schema-v6 auxiliary event delivery."""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.auxiliary_ecl_event.physical_report_v3 import (
    build_physical_report_v3,
    write_report_v3,
)
from analysis.th08_runtime_ecl_identity_audit import STAGE5_STATIC_SHA256


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--ecl", type=Path, required=True)
    parser.add_argument(
        "--expected-ecl-sha256",
        default=STAGE5_STATIC_SHA256,
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_physical_report_v3(
        args.trace,
        args.baseline,
        args.session,
        args.ecl,
        expected_ecl_sha256=args.expected_ecl_sha256,
    )
    write_report_v3(report, args.output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
