#!/usr/bin/env python3
"""Compare Python and parity-gated native local hazard queries on replay roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
import time
from pathlib import Path

import th08_live_dodge_agent as live_agent
from analysis.local_beam_stability_audit import _beam_sample, _decision
from analysis.local_pipeline_certificate_audit import (
    _read_decisions,
    _reconstruct_roots,
)
from touhou_control import native_backend


SEGMENTS = (
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


def _finite_difference(left: float, right: float) -> float:
    if math.isinf(left) and math.isinf(right) and left == right:
        return 0.0
    return abs(left - right)


def _decision_differences(reference, native) -> dict[str, object]:
    exact_fields = (
        "mask",
        "action",
        "bomb",
        "robust_collisions",
        "robust_worst_delay",
        "terminal_threat_collisions",
        "viability_constrained",
        "viability_safe_action_count",
        "viability_repair_volume",
        "viability_survival_preferred",
        "viability_survival_frames",
    )
    exact = {
        field: getattr(reference, field) == getattr(native, field)
        for field in exact_fields
    }
    float_fields = (
        "min_clearance",
        "immediate_clearance",
        "pipeline_clearance",
        "robust_min_clearance",
        "robust_cvar_risk",
        "terminal_threat_min_clearance",
        "score",
    )
    float_differences = {
        field: _finite_difference(
            float(getattr(reference, field)),
            float(getattr(native, field)),
        )
        for field in float_fields
    }
    hard_fields = (
        "min_clearance",
        "immediate_clearance",
        "pipeline_clearance",
        "robust_min_clearance",
        "terminal_threat_min_clearance",
    )
    return {
        "exact": exact,
        "float_absolute": float_differences,
        "action_equal": (
            exact["mask"]
            and exact["action"]
            and exact["bomb"]
        ),
        "hard_label_equal": (
            all(exact.values())
            and all(float_differences[field] <= 1e-4 for field in hard_fields)
        ),
    }


def _segment_values(decision, outer_total_ms: float) -> dict[str, float]:
    timing = decision.local_certificate_timing
    return {
        "outer_total": outer_total_ms,
        "shared_laser_projection": timing.shared_laser_projection_ms,
        "certificate_total": timing.certificate_total_ms,
        "certificate_geometry": timing.geometry_kernel_ms,
        "control_prefix": timing.control_prefix_ms,
        "planning_bullet_projection": timing.planning_bullet_projection_ms,
        "beam_search": timing.beam_search_ms,
        "terminal_threat": timing.terminal_threat_ms,
        "selection_finalize": timing.selection_finalize_ms,
    }


def _run_decision(root, backend: str):
    original = live_agent._hazards_for_positions
    replacement = (
        live_agent._numpy_hazards_for_positions
        if backend == "numpy"
        else live_agent._native_hazards_for_positions
    )
    live_agent._hazards_for_positions = replacement
    started = time.perf_counter()
    try:
        decision = _decision(
            root,
            beam_dedup_mode="quantized",
            beam_width=24,
        )
    finally:
        outer_total_ms = (time.perf_counter() - started) * 1000.0
        live_agent._hazards_for_positions = original
    return decision, _segment_values(decision, outer_total_ms)


def _density(active_bullets: int) -> str:
    if active_bullets < 200:
        return "lt_200"
    if active_bullets < 600:
        return "200_599"
    if active_bullets < 1000:
        return "600_999"
    return "ge_1000"


def _empty_timing_store() -> dict[str, dict[str, list[float]]]:
    return {
        backend: {segment: [] for segment in SEGMENTS}
        for backend in ("numpy", "native")
    }


def _summarize_timing(
    timing: dict[str, dict[str, list[float]]],
) -> dict[str, object]:
    report: dict[str, object] = {}
    for segment in SEGMENTS:
        reference = timing["numpy"][segment]
        native = timing["native"][segment]
        speedup = [
            left / right
            for left, right in zip(reference, native)
            if right > 0.0
        ]
        native_change = [
            100.0 * (right - left) / left
            for left, right in zip(reference, native)
            if left > 0.0
        ]
        reference_summary = _timing(reference)
        native_summary = _timing(native)
        report[segment] = {
            "numpy": reference_summary,
            "native": native_summary,
            "paired": {
                "median_speedup_factor": statistics.median(speedup),
                "median_native_change_percent": statistics.median(
                    native_change
                ),
                "aggregate_p95_native_change_percent": (
                    100.0
                    * (
                        float(native_summary["p95_ms"])
                        - float(reference_summary["p95_ms"])
                    )
                    / float(reference_summary["p95_ms"])
                    if float(reference_summary["p95_ms"]) > 0.0
                    else 0.0
                ),
            },
        }
    return report


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_trace(
    trace: Path,
    *,
    samples_per_trace: int,
    repeats: int,
) -> dict[str, object]:
    rows, loader_digest = _read_decisions(trace)
    roots, population = _reconstruct_roots(rows)
    sampled = _beam_sample(roots, samples_per_trace)
    if not sampled:
        raise ValueError(f"{trace}: no replay roots sampled")

    # Load the DLL/SO and populate code/data caches outside the retained timing.
    for backend in ("numpy", "native"):
        _run_decision(sampled[0], backend)

    timing = _empty_timing_store()
    by_density = {
        density: _empty_timing_store()
        for density in ("lt_200", "200_599", "600_999", "ge_1000")
    }
    exact_mismatches = {
        field: 0
        for field in (
            "mask",
            "action",
            "bomb",
            "robust_collisions",
            "robust_worst_delay",
            "terminal_threat_collisions",
            "viability_constrained",
            "viability_safe_action_count",
            "viability_repair_volume",
            "viability_survival_preferred",
            "viability_survival_frames",
        )
    }
    maximum_float_difference = {
        field: 0.0
        for field in (
            "min_clearance",
            "immediate_clearance",
            "pipeline_clearance",
            "robust_min_clearance",
            "robust_cvar_risk",
            "terminal_threat_min_clearance",
            "score",
        )
    }
    action_mismatch_count = 0
    hard_label_mismatch_count = 0
    mismatch_examples: list[dict[str, object]] = []

    for repeat in range(repeats):
        for root_index, root in enumerate(sampled):
            order = (
                ("numpy", "native")
                if (repeat + root_index) % 2 == 0
                else ("native", "numpy")
            )
            results = {}
            segment_results = {}
            for backend in order:
                decision, segments = _run_decision(root, backend)
                results[backend] = decision
                segment_results[backend] = segments
            density = _density(int(root.row.get("active_bullets", 0)))
            for backend in ("numpy", "native"):
                for segment, value in segment_results[backend].items():
                    timing[backend][segment].append(value)
                    by_density[density][backend][segment].append(value)

            differences = _decision_differences(
                results["numpy"],
                results["native"],
            )
            for field, equal in differences["exact"].items():
                if not equal:
                    exact_mismatches[field] += 1
            for field, difference in differences["float_absolute"].items():
                maximum_float_difference[field] = max(
                    maximum_float_difference[field],
                    float(difference),
                )
            if not differences["action_equal"]:
                action_mismatch_count += 1
            if not differences["hard_label_equal"]:
                hard_label_mismatch_count += 1
            if (
                (
                    not differences["action_equal"]
                    or not differences["hard_label_equal"]
                )
                and len(mismatch_examples) < 12
            ):
                mismatch_examples.append(
                    {
                        "frame": int(root.row["frame"]),
                        "repeat": repeat,
                        "numpy_action": results["numpy"].action,
                        "native_action": results["native"].action,
                        "differences": differences,
                    }
                )

    pair_count = len(sampled) * repeats
    return {
        "trace": str(trace),
        "trace_sha256": _sha256(trace),
        "loader_trace_sha256": loader_digest,
        "population": population,
        "sample": {
            "unique_root_count": len(sampled),
            "repeat_count": repeats,
            "paired_evaluation_count": pair_count,
            "method": (
                "bounded union of Boolean-losing, 240-frame pre-hit, and "
                "full action-eligible roots"
            ),
            "explicit_pipeline_root": True,
            "alternating_backend_order": True,
            "beam_width": 24,
            "horizon": 10,
            "threat_horizon": 32,
        },
        "parity": {
            "action_mismatch_count": action_mismatch_count,
            "hard_label_mismatch_count": hard_label_mismatch_count,
            "exact_field_mismatch_count": exact_mismatches,
            "maximum_float_absolute_difference": maximum_float_difference,
            "mismatch_examples": mismatch_examples,
        },
        "timing": _summarize_timing(timing),
        "by_active_bullets": {
            density: {
                "paired_evaluation_count": len(
                    values["numpy"]["outer_total"]
                ),
                "timing": (
                    _summarize_timing(values)
                    if values["numpy"]["outer_total"]
                    else None
                ),
            }
            for density, values in by_density.items()
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--samples-per-trace", type=int, default=128)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples_per_trace <= 0 or args.repeats <= 0:
        raise ValueError("sample and repeat counts must be positive")
    if native_backend._load_local_hazards_function() is None:
        raise RuntimeError("native local hazard export is unavailable")
    report = {
        "schema": "th08-local-native-hazard-benchmark-v1",
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "native_library": str(native_backend._library_path()),
        },
        "claim_boundary": {
            "source": "offline replay of retained native hazards and roots",
            "substitution": (
                "parity-gated replacement of every local hazard query inside "
                "the existing planner; recurrence, beam, root, and action "
                "selection are unchanged"
            ),
            "authority": (
                "differential parity and performance evidence only; the "
                "default live controller does not call this export"
            ),
            "float_tolerance": (
                "hard clearances <= 1e-4; soft risk/score differences are "
                "reported without granting action authority"
            ),
        },
        "traces": [
            audit_trace(
                trace,
                samples_per_trace=args.samples_per_trace,
                repeats=args.repeats,
            )
            for trace in args.traces
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
