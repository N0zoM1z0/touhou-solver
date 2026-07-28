"""Build the compact G3/G4 first-loss capsule report."""

from __future__ import annotations

from pathlib import Path

from analysis.complete_mask_capsule.solve import audit_root
from analysis.partial_witness_capsule.serialization import (
    canonical_sha256,
    file_sha256,
)

from .selection import select_first_loss_bracket


def _selection_record(selection) -> dict[str, object]:
    record: dict[str, object] = {
        "status": selection.status,
        "interruption_counts": dict(selection.interruption_counts),
        "root_validation_failure_count": len(
            selection.root_validation_failures
        ),
        "root_validation_failure_samples": (
            selection.root_validation_failures[:6]
        ),
        "recovered_loss_episodes": selection.recovered_loss_episodes,
        "target_hit_frame": selection.target_hit_frame,
        "unresolved": selection.unresolved,
    }
    if selection.bracket is not None:
        record["bracket"] = {
            "last_viable": {
                "line": selection.bracket.last_viable.trace_line,
                "decision_frame": (
                    selection.bracket.last_viable.decision_frame
                ),
                "query_frame": selection.bracket.last_viable.query_frame,
                "identity_sha256": (
                    selection.bracket.last_viable.identity.digest
                ),
            },
            "first_losing": {
                "line": selection.bracket.first_losing.trace_line,
                "decision_frame": (
                    selection.bracket.first_losing.decision_frame
                ),
                "query_frame": selection.bracket.first_losing.query_frame,
                "identity_sha256": (
                    selection.bracket.first_losing.identity.digest
                ),
            },
        }
    return record


def audit(
    *,
    trace: Path,
    capsule_dir: Path,
    horizon: int,
    decision_frame_support: tuple[int, ...],
    gameplay_epoch: int | None = None,
    stage_route_index: int | None = None,
) -> dict[str, object]:
    if not 1 <= horizon <= 80:
        raise ValueError("horizon must be in [1, 80]")
    if (
        not decision_frame_support
        or any(value <= 0 for value in decision_frame_support)
    ):
        raise ValueError("decision-frame support must be positive")
    selection = select_first_loss_bracket(
        trace=trace,
        capsule_dir=capsule_dir,
        gameplay_epoch=gameplay_epoch,
        stage_route_index=stage_route_index,
    )
    observations: dict[str, object] = {}
    solve_error: str | None = None
    if selection.bracket is not None:
        try:
            observations = {
                "g4_last_viable": audit_root(
                    selection.bracket.last_viable,
                    capsule_dir=capsule_dir,
                    horizon=horizon,
                    decision_frame_support=decision_frame_support,
                    continuation_mode="all_actions",
                ),
                "g3_first_losing": audit_root(
                    selection.bracket.first_losing,
                    capsule_dir=capsule_dir,
                    horizon=horizon,
                    decision_frame_support=decision_frame_support,
                    continuation_mode="all_actions",
                ),
            }
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            solve_error = f"{type(error).__name__}: {error}"

    gates = {
        "exact_uninterrupted_bracket_selected": (
            selection.status == "selected"
        ),
        "root_stream_has_no_validation_failure": (
            not selection.root_validation_failures
        ),
        "both_restricted_portfolios_complete": (
            len(observations) == 2 and solve_error is None
        ),
        "physical_action_authority_unchanged": all(
            observation.get("physical_action_authority") == "none"
            for observation in observations.values()
            if isinstance(observation, dict)
        ),
    }
    finite_model_passed = all(gates.values())
    physical_survival_claim_available = (
        finite_model_passed
        and len(observations) == 2
        and all(
            observation.get("physical_model_status")
            == "coverage_complete"
            for observation in observations.values()
            if isinstance(observation, dict)
        )
    )
    report = {
        "schema": "th08-g3-g4-first-loss-capsule-audit-v1",
        "scope": {
            "authority": (
                "offline restricted attainable lower witnesses only"
            ),
            "root_actions": (
                "all 36 canonical no-Bomb complete-mask actions"
            ),
            "continuations": (
                "all 36 stationary complete-mask candidates"
            ),
            "horizon_frames": horizon,
            "decision_frame_support": decision_frame_support,
            "gameplay_epoch_filter": gameplay_epoch,
            "stage_route_index_filter": stage_route_index,
            "timing_authority": (
                "none; viability capsule I/O contaminates B4 timing"
            ),
        },
        "source": {
            "trace": str(trace),
            "trace_bytes": trace.stat().st_size,
            "trace_sha256": file_sha256(trace),
            "capsule_dir": str(capsule_dir),
        },
        "selection": _selection_record(selection),
        "observations": observations,
        "solve_error": solve_error,
        "gates": gates,
        "conclusions": {
            "finite_model_audit_passed": finite_model_passed,
            "physical_survival_claim_available": (
                physical_survival_claim_available
            ),
            "strategy_promotion_available": False,
        },
        "passed": finite_model_passed,
    }
    report["report_digest"] = canonical_sha256(report)
    return report


__all__ = ["audit"]
