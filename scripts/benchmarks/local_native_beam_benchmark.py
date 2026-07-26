#!/usr/bin/env python3
"""Paired replay benchmark of Python and native quantized beam reduction."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import time
from pathlib import Path

import th08_live_dodge_agent as live
from analysis.local_beam_stability_audit import _beam_sample, _decision
from analysis.local_pipeline_certificate_audit import (
    _read_decisions,
    _reconstruct_roots,
)
from benchmarks.local_native_hazard_benchmark import (
    SEGMENTS,
    _decision_differences,
    _segment_values,
    _timing,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(root, reducer: str):
    original_hazards = live._hazards_for_positions
    original_reducer = live._LOCAL_BEAM_REDUCER
    live._hazards_for_positions = live._native_hazards_for_positions
    live._configure_local_beam_reducer(reducer)
    started = time.perf_counter()
    try:
        decision = _decision(
            root,
            beam_dedup_mode="quantized",
            beam_width=24,
        )
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        live._hazards_for_positions = original_hazards
        live._configure_local_beam_reducer(original_reducer)
    return decision, _segment_values(decision, elapsed_ms)


def _summaries(
    timing: dict[str, dict[str, list[float]]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for segment in SEGMENTS:
        python_values = timing["python"][segment]
        native_values = timing["native"][segment]
        python_summary = _timing(python_values)
        native_summary = _timing(native_values)
        paired_change = [
            100.0 * (native - reference) / reference
            for reference, native in zip(python_values, native_values)
            if reference > 0.0
        ]
        result[segment] = {
            "python": python_summary,
            "native": native_summary,
            "paired_median_native_change_percent": statistics.median(
                paired_change
            ),
            "aggregate_p95_native_change_percent": (
                100.0
                * (
                    float(native_summary["p95_ms"])
                    - float(python_summary["p95_ms"])
                )
                / float(python_summary["p95_ms"])
                if float(python_summary["p95_ms"]) > 0.0
                else 0.0
            ),
        }
    return result


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

    _run(sampled[0], "python")
    _run(sampled[0], "native")
    timing = {
        reducer: {segment: [] for segment in SEGMENTS}
        for reducer in ("python", "native")
    }
    action_mismatches = 0
    hard_label_mismatches = 0
    maximum_float_difference = 0.0
    mismatch_examples: list[dict[str, object]] = []
    pair_ordinal = 0
    for repetition in range(repeats):
        for root in sampled:
            order = (
                ("python", "native")
                if pair_ordinal % 2 == 0
                else ("native", "python")
            )
            results = {}
            for reducer in order:
                decision, segments = _run(root, reducer)
                results[reducer] = decision
                for segment, value in segments.items():
                    timing[reducer][segment].append(value)
            difference = _decision_differences(
                results["python"],
                results["native"],
            )
            action_mismatches += int(not difference["action_equal"])
            hard_label_mismatches += int(
                not difference["hard_label_equal"]
            )
            maximum_float_difference = max(
                maximum_float_difference,
                *difference["float_absolute"].values(),
            )
            if (
                not difference["action_equal"]
                or not difference["hard_label_equal"]
            ) and len(mismatch_examples) < 12:
                mismatch_examples.append(
                    {
                        "frame": int(root.row["frame"]),
                        "difference": difference,
                    }
                )
            pair_ordinal += 1
    return {
        "trace": str(trace),
        "trace_sha256": _sha256(trace),
        "loader_sha256": loader_digest,
        "population": population,
        "sample_count": len(sampled),
        "repeat_count": repeats,
        "pair_count": len(sampled) * repeats,
        "timing": _summaries(timing),
        "parity": {
            "action_mismatches": action_mismatches,
            "hard_label_mismatches": hard_label_mismatches,
            "maximum_float_absolute_difference": maximum_float_difference,
            "examples": mismatch_examples,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--samples-per-trace", type=int, default=128)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if min(args.samples_per_trace, args.repeats) <= 0:
        raise ValueError("sample and repeat counts must be positive")

    report = {
        "schema": "th08-local-native-beam-benchmark-v1",
        "platform": platform.platform(),
        "claim_boundary": {
            "hazards": "native parity-gated local hazard kernel in both arms",
            "difference": (
                "only quantized deduplication, pruning-key evaluation, "
                "stable ordering, and beam truncation"
            ),
            "authority": (
                "implementation parity and performance only; the finite beam "
                "remains proposal logic below the hard certificate"
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
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
