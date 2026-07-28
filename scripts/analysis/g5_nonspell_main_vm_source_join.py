#!/usr/bin/env python3
"""Join ordinary-enemy main-VM histories to realized bullet activations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.main_vm_source_join import (
    build_main_vm_source_join_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--ecl", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    report = build_main_vm_source_join_report(
        trace_path=arguments.trace,
        ecl_path=arguments.ecl,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["report_digest"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
