"""Build the compact exact-root loss dossier from retained evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .model import (
    minimal_rescue_combinations,
    primary_code,
    root_conclusions,
    solve_result,
    validate_dossier,
)
from .source import (
    canonical_sha256,
    capsule_dependency_identity,
    capsule_identity,
    read_trace_evidence,
    sha256_file,
    transition_evidence,
)


SOURCE_SCHEMA = "touhou-viability-differential-audit-v1"
DOSSIER_SCHEMA = "th08-exact-root-loss-dossier-v1"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _pipeline_comparison(observation: dict[str, Any]) -> dict[str, Any]:
    trace_viable = bool(observation["trace_state_viable"])
    base = observation["variants"]["space16_time8_h80"]
    return {
        "published_trace": {
            "completion": "complete",
            "outcome": "viable" if trace_viable else "empty",
            "query_frame": int(observation["query_frame"]),
            "layer": int(observation["trace_layer"]),
            "position_error": float(observation["trace_position_error"]),
        },
        "reconstructed_exact_root": solve_result(base),
        "base_matches_trace": (
            bool(base["state_viable"]) == trace_viable
            and int(base["layer"]) == int(observation["trace_layer"])
        ),
        "fresh_pipeline_root": solve_result(
            observation.get("fresh_policy")
        ),
        "terminal_contract": solve_result(
            observation.get("next_policy_overlap_terminal")
        ),
        "evidence_level": "observed",
    }


def _root_record(
    *,
    observation: dict[str, Any],
    trace_sample: Any,
    capsule_dir: Path,
) -> dict[str, Any]:
    capsule_name = str(observation["capsule"])
    if trace_sample.capsule != capsule_name:
        raise ValueError(
            f"frame {trace_sample.decision_frame}: trace capsule "
            f"{trace_sample.capsule} != audit capsule {capsule_name}"
        )
    if trace_sample.query_frame != int(observation["query_frame"]):
        raise ValueError(
            f"frame {trace_sample.decision_frame}: query frame mismatch"
        )
    identity = capsule_identity(
        capsule_dir / capsule_name,
        expected_source_frame=int(observation["capsule_source_frame"]),
        expected_snapshot_frame=int(observation["capsule_snapshot_frame"]),
    )
    source_classification = str(observation["primary_classification"])
    evidence_flags = tuple(str(v) for v in observation["evidence_flags"])
    rescue_factors = tuple(
        str(value) for value in observation["empty_rescue_factors"]
    )
    root_id = (
        f"h{int(observation['hit_frame']):05d}_"
        f"q{int(observation['query_frame']):05d}_"
        f"{Path(capsule_name).stem}"
    )
    query = trace_sample.payload()
    query.update(
        {
            "hit_frame": int(observation["hit_frame"]),
            "time_to_hit": int(observation["time_to_hit"]),
            "trace_layer": int(observation["trace_layer"]),
            "trace_position_error": float(
                observation["trace_position_error"]
            ),
        }
    )
    variants = {
        name: solve_result(result)
        for name, result in observation["variants"].items()
    }
    birth = dict(observation["birth_evidence"])
    birth["classification"] = (
        "FUTURE_BIRTH_GAP"
        if "hazard_model_future_birth_gap" in evidence_flags
        else "SOURCE_COVERS_CONTACT_SLOT"
    )
    birth["evidence_level"] = "observed"
    pipeline = _pipeline_comparison(observation)
    fresh_query = pipeline["fresh_pipeline_root"].get("query", {})
    fresh_name = str(fresh_query.get("capsule", ""))
    if fresh_name:
        pipeline["fresh_pipeline_root"]["capsule_identity"] = (
            capsule_dependency_identity(
                capsule_dir / fresh_name,
                expected_source_frame=int(fresh_query["source_frame"]),
            )
        )
    terminal_query = pipeline["terminal_contract"].get("query", {})
    terminal_name = str(
        terminal_query.get("continuation_capsule", "")
    )
    if terminal_name:
        pipeline["terminal_contract"]["capsule_identity"] = (
            capsule_dependency_identity(
                capsule_dir / terminal_name,
                expected_source_frame=int(
                    terminal_query["continuation_source_frame"]
                ),
            )
        )
    record = {
        "root_id": root_id,
        "query": query,
        "capsule": identity,
        "primary_classification": {
            "code": primary_code(source_classification),
            "source_label": source_classification,
            "evidence_level": "observed",
        },
        "variants": variants,
        "pipeline_comparison": pipeline,
        "minimal_sufficient_rescue_combinations": (
            minimal_rescue_combinations(rescue_factors)
        ),
        "future_birth": birth,
        "conclusions": root_conclusions(
            source_classification=source_classification,
            evidence_flags=evidence_flags,
            rescue_factors=rescue_factors,
        ),
    }
    record["root_contract_sha256"] = canonical_sha256(record)
    return record


def build_dossier(
    *,
    source_report_path: Path,
    trace_path: Path,
    capsule_dir: Path,
    bundle_audit_path: Path | None,
    minimum_pre_hit_frames: int = 240,
) -> dict[str, Any]:
    source = _load_json(source_report_path)
    if source.get("schema") != SOURCE_SCHEMA:
        raise ValueError(
            f"{source_report_path}: expected schema {SOURCE_SCHEMA!r}"
        )
    observations = [
        observation
        for observation in source.get("observations", ())
        if observation.get("trace_state_viable") is False
    ]
    target_frames = {
        int(observation["decision_frame"]) for observation in observations
    }
    trace = read_trace_evidence(
        trace_path,
        target_decision_frames=target_frames,
    )
    roots = [
        _root_record(
            observation=observation,
            trace_sample=trace.target_samples[
                int(observation["decision_frame"])
            ],
            capsule_dir=capsule_dir,
        )
        for observation in observations
    ]
    roots.sort(key=lambda root: (root["query"]["hit_frame"], root["root_id"]))
    bundle = _load_json(bundle_audit_path) if bundle_audit_path else None
    if bundle is not None:
        expected_trace_hash = bundle.get("trace", {}).get("sha256")
        actual_trace_hash = sha256_file(trace_path)
        if actual_trace_hash != expected_trace_hash:
            raise ValueError(
                f"{trace_path}: SHA-256 does not match bundle audit"
            )
    else:
        actual_trace_hash = sha256_file(trace_path)
    classification_counts = Counter(
        root["primary_classification"]["code"] for root in roots
    )
    rescue_counts = Counter(
        "+".join(
            combination["factors"][0]
            for combination in root[
                "minimal_sufficient_rescue_combinations"
            ]
        )
        or "none"
        for root in roots
    )
    dossier = {
        "schema": DOSSIER_SCHEMA,
        "scope": {
            "workload": "Hard Stage 4A",
            "source_report": str(source_report_path),
            "source_report_sha256": sha256_file(source_report_path),
            "trace": str(trace_path),
            "trace_sha256": actual_trace_hash,
            "capsule_dir": str(capsule_dir),
            "bundle_sha256": (
                bundle.get("bundle_sha256") if bundle is not None else None
            ),
            "hit_count": len(trace.hit_frames),
            "minimum_pre_hit_frames": minimum_pre_hit_frames,
            "root_count": len(roots),
            "authority": (
                "offline/shadow diagnosis only; no live action authority"
            ),
        },
        "semantics": {
            "completion": (
                "Only a returned exact solve is complete. Timeout, error, "
                "unvisited, unavailable, and absent variants are unresolved "
                "and cannot be labeled empty."
            ),
            "empty": (
                "Empty means the completed finite recurrence has no viable "
                "action at the declared immutable query root."
            ),
            "future_birth": (
                "FUTURE_BIRTH_GAP is orthogonal soundness evidence. Adding a "
                "missing future hazard cannot rescue an empty kernel."
            ),
            "rescue": (
                "Minimal rescue combinations are singleton finite-model "
                "counterfactuals actually solved viable. No untested combined "
                "intervention is claimed."
            ),
            "evidence_levels": {
                "observed": (
                    "Retained trace, capsule, or completed finite-solve output."
                ),
                "inferred": (
                    "Interpretation entailed by observed finite comparisons."
                ),
                "hypothesized": (
                    "Possible physical implication not established here."
                ),
            },
        },
        "classification_counts": dict(classification_counts),
        "rescue_combination_counts": dict(rescue_counts),
        "transitions": transition_evidence(
            trace,
            minimum_pre_hit_frames=minimum_pre_hit_frames,
        ),
        "roots": roots,
    }
    dossier["gate"] = validate_dossier(dossier)
    dossier["dossier_content_sha256"] = canonical_sha256(dossier)
    return dossier


def render_markdown(dossier: dict[str, Any]) -> str:
    gate = dossier["gate"]
    lines = [
        "# Exact-Root Loss Dossier",
        "",
        "This is an offline/shadow diagnosis. It changes no live action "
        "authority.",
        "",
        "## Exit gate",
        "",
        f"- Gate: **{'PASS' if gate['passed'] else 'FAIL'}**",
        f"- Content-addressed exact roots: {gate['root_count']}",
        f"- Published/base parity: {gate['pipeline_match_count']}",
        f"- Incomplete results mislabeled empty: "
        f"{gate['incomplete_labeled_empty_count']}",
        f"- Retained pre-hit transitions: {gate['transition_count']}",
        "",
        "## Orthogonal classifications",
        "",
    ]
    for code, count in sorted(gate["classification_counts"].items()):
        lines.append(f"- `{code}`: {count}")
    lines.extend(
        [
            f"- `FUTURE_BIRTH_GAP`: "
            f"{gate['future_birth_gap_count']} (orthogonal evidence)",
            "",
            "## Completion contract",
            "",
            dossier["semantics"]["completion"],
            "",
            dossier["semantics"]["future_birth"],
            "",
            "## Minimal sufficient rescue combinations",
            "",
        ]
    )
    for combination, count in sorted(
        dossier["rescue_combination_counts"].items()
    ):
        lines.append(f"- `{combination}`: {count}")
    lines.extend(
        [
            "",
            "Every listed factor is a singleton intervention whose complete "
            "finite solve is viable. Multiple singleton witnesses may overlap "
            "at one root. Untested multi-factor combinations are not reported.",
            "",
            "## Root witnesses",
            "",
            "| Root | Hit | Query | Primary | Future birth | Rescue witnesses |",
            "| --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for root in dossier["roots"]:
        query = root["query"]
        rescue = ", ".join(
            combination["factors"][0]
            for combination in root[
                "minimal_sufficient_rescue_combinations"
            ]
        )
        lines.append(
            f"| `{root['root_id']}` | {query['hit_frame']} | "
            f"{query['query_frame']} | "
            f"`{root['primary_classification']['code']}` | "
            f"`{root['future_birth']['classification']}` | "
            f"{rescue or 'none'} |"
        )
    if gate["errors"]:
        lines.extend(["", "## Gate failures", ""])
        lines.extend(f"- {error}" for error in gate["errors"])
    lines.append("")
    return "\n".join(lines)
