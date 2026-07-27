#!/usr/bin/env python3
"""Run the fixed physical stationary-witness Windows delivery gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from benchmarks.stationary_witness_delivery.abi import (
    verify_production_abi,
)
from benchmarks.stationary_witness_delivery.gate import evaluate_gate
from benchmarks.stationary_witness_delivery.native import (
    NativeStationaryWitnessLibrary,
)
from benchmarks.stationary_witness_delivery.runner import run_all
from benchmarks.stationary_witness_delivery.workload import (
    SOURCE_RUN,
    preparation_record,
    prepare_physical_reservoir,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACE = (
    ROOT / "artifacts" / "runtime_reports" / f"{SOURCE_RUN}.jsonl"
)
DEFAULT_CAPSULE_DIR = (
    ROOT / "artifacts" / "viability_audit" / "raw" / SOURCE_RUN
)


def _canonical_sha256(record: dict[str, object]) -> str:
    encoded = json.dumps(
        record,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument(
        "--capsule-dir",
        type=Path,
        default=DEFAULT_CAPSULE_DIR,
    )
    parser.add_argument(
        "--minimum-background-solves",
        type=int,
        default=24,
    )
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="return nonzero when the fixed gate does not pass",
    )
    args = parser.parse_args(argv)
    if args.minimum_background_solves < 1:
        parser.error("--minimum-background-solves must be positive")

    reservoir = prepare_physical_reservoir(
        trace=args.trace,
        capsule_dir=args.capsule_dir,
    )
    preparation = preparation_record(reservoir)
    library = NativeStationaryWitnessLibrary.default(ROOT)
    measurements = run_all(
        reservoir=reservoir,
        library=library,
        minimum_background_solves=args.minimum_background_solves,
    )
    abi = verify_production_abi(ROOT)
    authoritative_windows_run = os.name == "nt"
    gate = evaluate_gate(
        preparation=preparation,
        measurements=measurements,
        abi=abi,
        authoritative_windows_run=authoritative_windows_run,
    )
    report: dict[str, object] = {
        "schema": "touhou-stationary-witness-windows-delivery-gate-v1",
        "contract": (
            "notes/STATIONARY_WITNESS_WINDOWS_DELIVERY_CONTRACT_20260728.md"
        ),
        "classification": {
            "physical_roots": "observed",
            "finite_model_labels_and_paths": "observed",
            "delivery_and_contention_timings": "observed",
            "future_physical_survival": "unknown",
        },
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "os_name": os.name,
            "authoritative_windows_run": authoritative_windows_run,
        },
        "preparation": preparation,
        "measurements": measurements,
        "production_abi": abi,
        "gate": gate,
        "physical_action_authority": "none",
    }
    report["report_sha256"] = _canonical_sha256(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(
        {
            "output": str(args.output),
            "report_sha256": report["report_sha256"],
            "gate_passed": gate["passed"],
        },
        sort_keys=True,
    ))
    return 1 if args.require_pass and not gate["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
