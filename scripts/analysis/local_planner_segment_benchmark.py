#!/usr/bin/env python3
"""Benchmark full local planning segments with an explicit pipeline root."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path

from analysis.local_beam_stability_audit import (
    _beam_sample,
    _decision,
)
from analysis.local_pipeline_certificate_audit import (
    _read_decisions,
    _reconstruct_roots,
)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _timing(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "median_ms": statistics.median(values),
        "p95_ms": _p95(values),
        "max_ms": max(values),
    }


def audit_trace(
    trace: Path,
    *,
    samples_per_trace: int,
) -> dict[str, object]:
    rows, digest = _read_decisions(trace)
    roots, population = _reconstruct_roots(rows)
    sampled = _beam_sample(roots, samples_per_trace)
    values = {
        name: []
        for name in (
            "outer_total",
            "shared_laser_projection",
            "certificate_total",
            "certificate_geometry",
            "control_prefix",
            "planning_bullet_projection",
            "beam_search",
            "terminal_threat",
            "selection_finalize",
        )
    }
    by_density = {
        name: {segment: [] for segment in values}
        for name in ("lt_200", "200_599", "600_999", "ge_1000")
    }
    for root in sampled:
        started = time.perf_counter()
        decision = _decision(
            root,
            beam_dedup_mode="quantized",
            beam_width=24,
        )
        outer_total = (time.perf_counter() - started) * 1000.0
        timing = decision.local_certificate_timing
        sample_values = {
            "outer_total": outer_total,
            "shared_laser_projection": (
                timing.shared_laser_projection_ms
            ),
            "certificate_total": timing.certificate_total_ms,
            "certificate_geometry": timing.geometry_kernel_ms,
            "control_prefix": timing.control_prefix_ms,
            "planning_bullet_projection": (
                timing.planning_bullet_projection_ms
            ),
            "beam_search": timing.beam_search_ms,
            "terminal_threat": timing.terminal_threat_ms,
            "selection_finalize": timing.selection_finalize_ms,
        }
        active_bullets = int(root.row.get("active_bullets", 0))
        density = (
            "lt_200"
            if active_bullets < 200
            else (
                "200_599"
                if active_bullets < 600
                else (
                    "600_999"
                    if active_bullets < 1000
                    else "ge_1000"
                )
            )
        )
        for name, value in sample_values.items():
            values[name].append(value)
            by_density[density][name].append(value)
    return {
        "trace": str(trace),
        "trace_sha256": digest,
        "population": population,
        "sample": {
            "count": len(sampled),
            "method": (
                "bounded union of Boolean-losing, 240-frame pre-hit, and "
                "full action-eligible roots"
            ),
            "explicit_pipeline_root": True,
            "beam_width": 24,
            "horizon": 10,
            "threat_horizon": 32,
        },
        "timing": {
            name: _timing(segment_values)
            for name, segment_values in values.items()
        },
        "by_active_bullets": {
            density: {
                "count": len(segment_values["outer_total"]),
                "timing": {
                    name: (
                        _timing(timings)
                        if timings
                        else None
                    )
                    for name, timings in segment_values.items()
                },
            }
            for density, segment_values in by_density.items()
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--samples-per-trace", type=int, default=128)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples_per_trace <= 0:
        raise ValueError("samples per trace must be positive")
    report = {
        "schema": "th08-local-planner-segment-benchmark-v1",
        "claim_boundary": {
            "source": "offline replay of retained native hazards and roots",
            "authority": "performance evidence only; no live action authority",
            "root": (
                "explicit active/held/pending root reconstructed or read from "
                "trace and checked by the audit loader"
            ),
        },
        "traces": [
            audit_trace(
                trace,
                samples_per_trace=args.samples_per_trace,
            )
            for trace in args.traces
        ],
    }
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
