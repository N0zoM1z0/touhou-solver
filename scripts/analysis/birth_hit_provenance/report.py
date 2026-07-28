"""Build the compact realized birth-to-hit provenance report."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from analysis.partial_witness_capsule.serialization import (
    canonical_sha256,
    file_sha256,
)

from .trace import scan_activation_evidence
from .types import ActivationEvidence

_KIND_BY_CODE = {
    2: "bootstrap_recent",
    3: "activation_edge",
    4: "timer_regression",
}


def _integer(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _finite_number(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _load_dossier(
    dossier: Path,
    *,
    stage_route_index: int | None,
) -> tuple[list[dict[str, object]], frozenset[int]]:
    try:
        payload = json.loads(dossier.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid dossier: {error}") from error
    if not isinstance(payload, dict) or not isinstance(
        payload.get("deaths"), list
    ):
        raise ValueError("dossier.deaths must be a list")

    hits: list[dict[str, object]] = []
    slots: set[int] = set()
    seen_frames: set[int] = set()
    for index, death in enumerate(payload["deaths"]):
        if not isinstance(death, dict):
            raise ValueError(f"dossier death {index} must be an object")
        if (
            stage_route_index is not None
            and death.get("stage_route_index") != stage_route_index
        ):
            continue
        frame = _integer(death.get("frame"), label=f"death {index} frame")
        if frame in seen_frames:
            raise ValueError(f"duplicate dossier hit frame {frame}")
        seen_frames.add(frame)
        exact = death.get("observed_bullet_contact_candidate")
        nearest = death.get("nearest_observed_bullet")
        if exact is not None:
            role = "exact_observed_overlap"
            candidate = exact
        elif nearest is not None:
            role = "nearest_only"
            candidate = nearest
        else:
            role = "missing"
            candidate = None
        slot: int | None = None
        candidate_record: dict[str, object] | None = None
        if candidate is not None:
            if not isinstance(candidate, dict):
                raise ValueError(
                    f"death {frame} bullet candidate must be an object"
                )
            slot = _integer(
                candidate.get("slot"),
                label=f"death {frame} candidate slot",
            )
            slots.add(slot)
            candidate_record = {
                "slot": slot,
                "x": _finite_number(
                    candidate.get("x"),
                    label=f"death {frame} candidate x",
                ),
                "y": _finite_number(
                    candidate.get("y"),
                    label=f"death {frame} candidate y",
                ),
                "velocity_x": _finite_number(
                    candidate.get("velocity_x"),
                    label=f"death {frame} candidate velocity_x",
                ),
                "velocity_y": _finite_number(
                    candidate.get("velocity_y"),
                    label=f"death {frame} candidate velocity_y",
                ),
                "half_width": _finite_number(
                    candidate.get("half_width"),
                    label=f"death {frame} candidate half_width",
                ),
                "half_height": _finite_number(
                    candidate.get("half_height"),
                    label=f"death {frame} candidate half_height",
                ),
                "aabb_clearance": _finite_number(
                    candidate.get("aabb_clearance"),
                    label=f"death {frame} candidate aabb_clearance",
                ),
            }
        loss = death.get("viability_kernel_exhausted_at_frame")
        if loss is not None:
            loss = _integer(loss, label=f"death {frame} viability loss")
            if loss > frame:
                raise ValueError(
                    f"death {frame} viability loss is after the hit"
                )
        hits.append(
            {
                "frame": frame,
                "stage_route_index": death.get("stage_route_index"),
                "sample_role": death.get("sample_role"),
                "primary_cause_class": death.get("primary_cause_class"),
                "spell_attribution": death.get("spell_attribution"),
                "viability_loss_frame": loss,
                "candidate_role": role,
                "candidate": candidate_record,
                "_slot": slot,
            }
        )
    return hits, frozenset(slots)


def _relation(
    activation: ActivationEvidence | None,
    *,
    loss_frame: int | None,
) -> str:
    if activation is None:
        return "activation_unresolved"
    if activation.code == 2:
        return "bootstrap_recent_activation_time_unresolved"
    if activation.code == 4:
        return "slot_reuse_ambiguous"
    if loss_frame is None:
        return "loss_boundary_unavailable"
    if (
        activation.support_start is not None
        and activation.support_start > loss_frame
    ):
        return "activation_after_loss"
    if activation.support_end <= loss_frame:
        return "activation_before_or_at_loss"
    return "activation_straddles_loss"


def _activation_record(
    activation: ActivationEvidence | None,
) -> dict[str, object] | None:
    if activation is None:
        return None
    x, y, velocity_x, velocity_y, half_width, half_height = (
        activation.geometry
    )
    return {
        "trace_line": activation.trace_line,
        "frame": activation.frame,
        "snapshot_frame": activation.snapshot_frame,
        "gameplay_epoch": activation.gameplay_epoch,
        "stage_route_index": activation.stage_route_index,
        "slot": activation.slot,
        "evidence_code": activation.code,
        "evidence_kind": _KIND_BY_CODE[activation.code],
        "status_code": activation.status_code,
        "state": activation.state,
        "age": activation.age,
        "previous_state": activation.previous_state,
        "previous_age": activation.previous_age,
        "support_start": activation.support_start,
        "support_end": activation.support_end,
        "geometry": {
            "x": x,
            "y": y,
            "velocity_x": velocity_x,
            "velocity_y": velocity_y,
            "half_width": half_width,
            "half_height": half_height,
            "transform_flags": activation.transform_flags,
        },
        "intent_available": activation.intent_available,
        "spell_enemy_pointer": activation.spell_enemy_pointer,
        "intent_scope": activation.intent_scope,
        "omitted_sources": list(activation.omitted_sources),
        "wave_evidence_count": activation.wave_evidence_count,
    }


def audit(
    *,
    trace: Path,
    dossier: Path,
    gameplay_epoch: int | None = None,
    stage_route_index: int | None = None,
) -> dict[str, object]:
    hits, target_slots = _load_dossier(
        dossier,
        stage_route_index=stage_route_index,
    )
    dossier_hit_count = len(hits)
    scan = scan_activation_evidence(
        trace,
        target_slots=target_slots,
        target_hit_frames=frozenset(hit["frame"] for hit in hits),
        gameplay_epoch=gameplay_epoch,
        stage_route_index=stage_route_index,
    )
    if gameplay_epoch is not None:
        hits = [
            hit
            for hit in hits
            if scan.hit_gameplay_epochs.get(hit["frame"]) == gameplay_epoch
        ]

    records: list[dict[str, object]] = []
    relation_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    exact_relation_counts: Counter[str] = Counter()
    for hit in hits:
        slot = hit.pop("_slot")
        hit_epoch = scan.hit_gameplay_epochs.get(hit["frame"])
        generations = scan.activations.get(slot, ()) if slot is not None else ()
        eligible = tuple(
            generation
            for generation in generations
            if (
                generation.support_end <= hit["frame"]
                and generation.gameplay_epoch == hit_epoch
            )
        )
        activation = eligible[-1] if eligible else None
        relation = _relation(
            activation,
            loss_frame=hit["viability_loss_frame"],
        )
        role = str(hit["candidate_role"])
        role_counts[role] += 1
        relation_counts[relation] += 1
        if role == "exact_observed_overlap":
            exact_relation_counts[relation] += 1
        hit["activation_relation"] = relation
        hit["activation"] = _activation_record(activation)
        hit["gameplay_epoch"] = hit_epoch
        hit["observed_generation_count_before_hit"] = len(eligible)
        if activation is not None and hit["viability_loss_frame"] is not None:
            hit["activation_support_minus_loss"] = {
                "start": (
                    None
                    if activation.support_start is None
                    else activation.support_start
                    - hit["viability_loss_frame"]
                ),
                "end": activation.support_end - hit["viability_loss_frame"],
            }
            hit["hit_minus_activation_support"] = {
                "start": (
                    None
                    if activation.support_start is None
                    else hit["frame"] - activation.support_start
                ),
                "end": hit["frame"] - activation.support_end,
            }
        else:
            hit["activation_support_minus_loss"] = None
            hit["hit_minus_activation_support"] = None
        records.append(hit)

    gates = {
        "filtered_scope_contains_hit": bool(hits),
        "all_filtered_dossier_hits_have_exact_trace_epoch": (
            len(scan.hit_gameplay_epochs) == len(hits)
        ),
        "all_filtered_dossier_hits_classified": len(records) == len(hits),
        "trace_contains_birth_rows": scan.birth_row_count > 0,
        "candidate_roles_preserved": sum(role_counts.values()) == len(records),
        "exact_overlap_not_inferred_from_nearest": all(
            record["candidate_role"] != "exact_observed_overlap"
            or record["primary_cause_class"] == "observed_bullet_overlap"
            for record in records
        ),
        "physical_action_authority_unchanged": True,
    }
    passed = all(gates.values())
    post_loss_exact = exact_relation_counts["activation_after_loss"]
    report: dict[str, object] = {
        "schema": "th08-g5-realized-birth-to-hit-provenance-v1",
        "scope": {
            "authority": "retrospective trace-only provenance",
            "gameplay_epoch_filter": gameplay_epoch,
            "stage_route_index_filter": stage_route_index,
            "candidate_roles": (
                "exact_observed_overlap is physical overlap evidence; "
                "nearest_only is noncausal diagnostics"
            ),
            "physical_action_authority": "none",
            "timing_authority": "none; retained files only",
        },
        "source": {
            "trace": str(trace),
            "trace_bytes": scan.trace_bytes,
            "trace_sha256": scan.trace_sha256,
            "trace_row_count": scan.row_count,
            "birth_row_count": scan.birth_row_count,
            "hit_decision_epoch_count": len(scan.hit_gameplay_epochs),
            "invalid_timer_evidence_count": (
                scan.invalid_timer_evidence_count
            ),
            "dossier": str(dossier),
            "dossier_bytes": dossier.stat().st_size,
            "dossier_sha256": file_sha256(dossier),
            "dossier_hit_count_before_epoch_filter": dossier_hit_count,
        },
        "counts": {
            "hit_count": len(records),
            "candidate_roles": dict(sorted(role_counts.items())),
            "activation_relations": dict(sorted(relation_counts.items())),
            "exact_overlap_activation_relations": dict(
                sorted(exact_relation_counts.items())
            ),
        },
        "hits": records,
        "gates": gates,
        "conclusions": {
            "audit_complete": passed,
            "observed_post_loss_exact_overlap_available": (
                post_loss_exact > 0
            ),
            "post_loss_exact_overlap_count": post_loss_exact,
            "canonical_first_hit_is_post_loss_birth": (
                bool(records)
                and records[0]["candidate_role"] == "exact_observed_overlap"
                and records[0]["activation_relation"]
                == "activation_after_loss"
            ),
            "future_hazard_coverage_complete": False,
            "physical_survival_claim_available": False,
            "strategy_promotion_available": False,
        },
        "passed": passed,
    }
    report["report_digest"] = canonical_sha256(report)
    return report


__all__ = ["audit"]
