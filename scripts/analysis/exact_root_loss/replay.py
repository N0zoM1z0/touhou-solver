"""Deterministically recompute exact-root variants from dossier contracts."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any

from analysis.viability_differential_audit import (
    BASE,
    NO_GROWTH_UNCERTAINTY,
    NO_UNCERTAINTY,
    QUERY_DELAY_SUPPORT,
    SHORT_HORIZONS,
    SPACE_4,
    SPACE_8,
    TIME_4_CLIPPED,
    AuditSolver,
    _query_payload,
)

from .model import COMPLETE, solve_result
from .source import sha256_file


VARIANTS = {
    variant.name: variant
    for variant in (
        BASE,
        SPACE_8,
        SPACE_4,
        TIME_4_CLIPPED,
        NO_GROWTH_UNCERTAINTY,
        NO_UNCERTAINTY,
        *SHORT_HORIZONS,
    )
}

CORE_QUERY_FIELDS = (
    "available",
    "state_viable",
    "safe_action_count",
    "layer",
    "row",
    "column",
    "position_error",
)
SURVIVAL_FIELDS = (
    "survival_frames",
    "bottleneck_margin",
    "best_action_mask",
    "best_actions",
    "remaining_frames",
)


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def compare_query_results(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> list[str]:
    mismatches = []
    for field in (*CORE_QUERY_FIELDS, *SURVIVAL_FIELDS):
        if field not in expected and field not in actual:
            continue
        left = expected.get(field)
        right = actual.get(field)
        if isinstance(left, float) or isinstance(right, float):
            equal = (
                isinstance(left, (int, float))
                and isinstance(right, (int, float))
                and math.isclose(
                    float(left),
                    float(right),
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
            )
        else:
            equal = left == right
        if not equal:
            mismatches.append(f"{field}: expected {left!r}, got {right!r}")
    return mismatches


def _synthetic_row(root: dict[str, Any]) -> dict[str, Any]:
    query = root["query"]
    return {
        "corridor": {
            "source_frame": root["capsule"]["contract"]["source_frame"],
            "viability": {
                "query_frame": query["query_frame"],
                "active_action": query["active_action"],
            },
        },
        "player": {
            "projected_x": float.fromhex(query["projected_x_hex"]),
            "projected_y": float.fromhex(query["projected_y_hex"]),
        },
    }


def replay_dossier(
    *,
    dossier_path: Path,
    capsule_dir: Path,
    root_limit: int | None = None,
    selected_variants: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    dossier = _load(dossier_path)
    roots = list(dossier.get("roots", ()))
    if root_limit is not None:
        if root_limit <= 0:
            raise ValueError("root_limit must be positive")
        roots = roots[:root_limit]
    variant_names = (
        tuple(VARIANTS) if selected_variants is None else selected_variants
    )
    unknown = set(variant_names) - VARIANTS.keys()
    if unknown:
        raise ValueError(
            "unknown replay variants: " + ", ".join(sorted(unknown))
        )
    solver = AuditSolver(maximum_cached_solutions=2)
    results = []
    mismatch_count = 0
    digest_mismatch_count = 0
    dependency_digest_mismatch_count = 0
    incomplete_source_count = 0
    pipeline_mismatch_count = 0
    pipeline_incomplete_source_count = 0
    for root in roots:
        capsule_path = capsule_dir / root["capsule"]["name"]
        digest = sha256_file(capsule_path)
        digest_matches = digest == root["capsule"]["sha256"]
        if not digest_matches:
            digest_mismatch_count += 1
        row = _synthetic_row(root)
        variant_results = []
        for name in variant_names:
            expected = root["variants"].get(name)
            if expected is None or expected.get("completion") != COMPLETE:
                incomplete_source_count += 1
                variant_results.append(
                    {
                        "name": name,
                        "status": "source_unresolved",
                        "mismatches": [],
                    }
                )
                continue
            variant = VARIANTS[name]
            if name == QUERY_DELAY_SUPPORT.name:
                variant = replace(
                    variant,
                    delay_frames=tuple(
                        int(value)
                        for value in root["query"][
                            "current_delay_support"
                        ]
                    ),
                )
            solved = solver.solve(
                capsule_path,
                variant,
                survival_shadow=(name == BASE.name),
            )
            actual_payload = _query_payload(solved, row)
            actual = solve_result(actual_payload)
            mismatches = compare_query_results(
                expected["query"],
                actual["query"],
            )
            mismatch_count += len(mismatches)
            variant_results.append(
                {
                    "name": name,
                    "status": "matched" if not mismatches else "mismatch",
                    "mismatches": mismatches,
                }
            )
        pipeline_results = []
        pipeline = root["pipeline_comparison"]
        for label, dependency_field, continuation in (
            ("fresh_pipeline_root", "capsule", False),
            ("terminal_contract", "continuation_capsule", True),
        ):
            expected = pipeline[label]
            identity = expected.get("capsule_identity")
            if expected.get("completion") != COMPLETE or not isinstance(
                identity, dict
            ):
                pipeline_incomplete_source_count += 1
                pipeline_results.append(
                    {
                        "name": label,
                        "status": "source_unresolved",
                        "mismatches": [],
                    }
                )
                continue
            dependency_path = capsule_dir / identity["name"]
            dependency_digest_matches = (
                sha256_file(dependency_path) == identity["sha256"]
            )
            if not dependency_digest_matches:
                dependency_digest_mismatch_count += 1
            if continuation:
                solved = solver.solve(
                    capsule_path,
                    BASE,
                    continuation_path=dependency_path,
                )
            else:
                solved = solver.solve(dependency_path, BASE)
            actual_payload = _query_payload(solved, row)
            mismatches = compare_query_results(
                expected["query"],
                actual_payload,
            )
            pipeline_mismatch_count += len(mismatches)
            pipeline_results.append(
                {
                    "name": label,
                    "dependency_field": dependency_field,
                    "capsule_sha256_matches": (
                        dependency_digest_matches
                    ),
                    "status": "matched" if not mismatches else "mismatch",
                    "mismatches": mismatches,
                }
            )
        results.append(
            {
                "root_id": root["root_id"],
                "capsule_sha256_matches": digest_matches,
                "variants": variant_results,
                "pipeline_variants": pipeline_results,
            }
        )
    return {
        "schema": "th08-exact-root-loss-replay-v1",
        "scope": {
            "dossier": str(dossier_path),
            "capsule_dir": str(capsule_dir),
            "root_count": len(roots),
            "variant_names": list(variant_names),
        },
        "gate": {
            "passed": (
                mismatch_count == 0
                and digest_mismatch_count == 0
                and dependency_digest_mismatch_count == 0
                and incomplete_source_count == 0
                and pipeline_mismatch_count == 0
                and pipeline_incomplete_source_count == 0
            ),
            "query_field_mismatch_count": mismatch_count,
            "capsule_digest_mismatch_count": digest_mismatch_count,
            "dependency_capsule_digest_mismatch_count": (
                dependency_digest_mismatch_count
            ),
            "incomplete_source_variant_count": incomplete_source_count,
            "pipeline_query_field_mismatch_count": pipeline_mismatch_count,
            "pipeline_incomplete_source_variant_count": (
                pipeline_incomplete_source_count
            ),
        },
        "roots": results,
    }
