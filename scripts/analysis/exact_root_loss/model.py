"""Authority-safe result semantics for the exact-root loss dossier."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


COMPLETE = "complete"
INCOMPLETE = "incomplete"
NOT_RUN = "not_run"

VIABLE = "viable"
EMPTY = "empty"
UNRESOLVED = "unresolved"

EXPECTED_CLASSIFICATION_COUNTS = {
    "SPATIAL_AMBIGUITY": 6,
    "SHORT_HORIZON_ONLY": 8,
    "MODELED_LOSING_UNRESOLVED": 47,
}
EXPECTED_FUTURE_BIRTH_GAP_COUNT = 7
EXPECTED_ROOT_COUNT = 61

PRIMARY_CODE = {
    "spatial_coarse_false_empty": "SPATIAL_AMBIGUITY",
    "finite_horizon_collapse": "SHORT_HORIZON_ONLY",
    "modeled_losing_unresolved": "MODELED_LOSING_UNRESOLVED",
    "policy_reconstruction_or_version_mismatch": "PUBLICATION_MISMATCH",
    "stale_policy_version": "PUBLICATION_MISMATCH",
}

FACTOR_CODE = {
    "full_async_delay_envelope": "DELAY_SUPPORT_SENSITIVE",
    "spatial_quantization": "SPATIAL_AMBIGUITY",
    "forecast_uncertainty_growth": "UNCERTAINTY_SENSITIVE",
    "base_or_forecast_uncertainty": "UNCERTAINTY_SENSITIVE",
    "finite_horizon_requirement": "SHORT_HORIZON_ONLY",
}

FACTOR_VARIANTS = {
    "full_async_delay_envelope": (
        "space16_time8_h80_delay_current_query",
    ),
    "spatial_quantization": (
        "space8_time8_h80",
        "space4_time8_h80",
    ),
    "forecast_uncertainty_growth": (
        "space16_time8_h80_uncertainty_no_growth",
    ),
    "base_or_forecast_uncertainty": (
        "space16_time8_h80_uncertainty_none",
    ),
    "finite_horizon_requirement": (
        "space16_time8_h32",
        "space16_time8_h48",
        "space16_time8_h64",
    ),
}


def solve_result(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize completion separately from the finite-model outcome."""

    if payload is None:
        return {
            "completion": NOT_RUN,
            "outcome": UNRESOLVED,
            "reason": "variant absent from source audit",
        }
    if payload.get("available") is True:
        outcome = VIABLE if payload.get("state_viable") is True else EMPTY
        return {
            "completion": COMPLETE,
            "outcome": outcome,
            "query": dict(payload),
        }
    reason = str(payload.get("reason", "query result unavailable"))
    completion = (
        NOT_RUN
        if reason == "query age exceeds short horizon"
        else INCOMPLETE
    )
    return {
        "completion": completion,
        "outcome": UNRESOLVED,
        "reason": reason,
        "query": dict(payload),
    }


def primary_code(source_classification: str) -> str:
    try:
        return PRIMARY_CODE[source_classification]
    except KeyError as exc:
        raise ValueError(
            f"unknown source classification {source_classification!r}"
        ) from exc


def minimal_rescue_combinations(
    factors: Sequence[str],
) -> list[dict[str, Any]]:
    """Return the singleton interventions proved sufficient by the audit.

    Each source factor is emitted only when its corresponding one-factor
    counterfactual solved viable.  Multiple entries therefore overlap at one
    root, but no untested multi-factor interaction is invented.
    """

    combinations = []
    for factor in factors:
        if factor not in FACTOR_CODE or factor not in FACTOR_VARIANTS:
            raise ValueError(f"unknown rescue factor {factor!r}")
        combinations.append(
            {
                "factors": [FACTOR_CODE[factor]],
                "source_factor": factor,
                "witness_variants": list(FACTOR_VARIANTS[factor]),
                "evidence_level": "observed",
                "claim_scope": "finite-model counterfactual only",
            }
        )
    return combinations


def root_conclusions(
    *,
    source_classification: str,
    evidence_flags: Sequence[str],
    rescue_factors: Sequence[str],
) -> list[dict[str, str]]:
    code = primary_code(source_classification)
    conclusions = [
        {
            "code": code,
            "evidence_level": "observed",
            "claim": (
                "The retained complete finite solves reproduce this "
                "classification at the immutable query root."
            ),
        }
    ]
    if "hazard_model_future_birth_gap" in evidence_flags:
        conclusions.extend(
            [
                {
                    "code": "FUTURE_BIRTH_GAP",
                    "evidence_level": "observed",
                    "claim": (
                        "The later contact projectile slot is absent from "
                        "the source capsule."
                    ),
                },
                {
                    "code": "FUTURE_BIRTH_GAP",
                    "evidence_level": "inferred",
                    "claim": (
                        "The source model is incomplete for the later "
                        "contact; this does not explain or rescue an empty "
                        "kernel."
                    ),
                },
                {
                    "code": "PHYSICAL_CAUSE_UNRESOLVED",
                    "evidence_level": "hypothesized",
                    "claim": (
                        "The missing future birth may affect physical "
                        "soundness, but no physical causal attribution is "
                        "proved by this finite audit."
                    ),
                },
            ]
        )
    for factor in rescue_factors:
        conclusions.append(
            {
                "code": FACTOR_CODE[factor],
                "evidence_level": "inferred",
                "claim": (
                    f"The single-factor {factor!r} counterfactual is viable; "
                    "live safety authority is unchanged."
                ),
            }
        )
    return conclusions


def _error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_dossier(dossier: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the G0 exit gate without converting unresolved work to empty."""

    errors: list[str] = []
    roots = dossier.get("roots")
    _error(errors, isinstance(roots, list), "roots must be a list")
    if not isinstance(roots, list):
        roots = []
    _error(
        errors,
        len(roots) == EXPECTED_ROOT_COUNT,
        f"expected {EXPECTED_ROOT_COUNT} roots, found {len(roots)}",
    )
    root_ids = [root.get("root_id") for root in roots]
    _error(
        errors,
        len(root_ids) == len(set(root_ids)),
        "root identifiers are not unique",
    )

    classifications = Counter()
    future_birth_count = 0
    incomplete_labeled_empty = 0
    digest_ready_count = 0
    replay_ready_count = 0
    pipeline_match_count = 0
    for root in roots:
        classification = root.get("primary_classification")
        if isinstance(classification, Mapping):
            classifications[str(classification.get("code"))] += 1
        conclusions = root.get("conclusions", ())
        if any(
            item.get("code") == "FUTURE_BIRTH_GAP"
            and item.get("evidence_level") == "observed"
            for item in conclusions
            if isinstance(item, Mapping)
        ):
            future_birth_count += 1
        capsule = root.get("capsule", {})
        if (
            isinstance(capsule, Mapping)
            and capsule.get("sha256")
            and capsule.get("bytes")
            and capsule.get("decoded") is True
        ):
            digest_ready_count += 1
        variants = root.get("variants", {})
        all_complete = bool(variants)
        for name, result in variants.items():
            completion = result.get("completion")
            outcome = result.get("outcome")
            if completion != COMPLETE:
                all_complete = False
            if completion != COMPLETE and outcome == EMPTY:
                incomplete_labeled_empty += 1
                errors.append(
                    f"{root.get('root_id')}:{name} labels an "
                    "incomplete result empty"
                )
        if all_complete:
            replay_ready_count += 1
        pipeline = root.get("pipeline_comparison", {})
        if isinstance(pipeline, Mapping) and pipeline.get("base_matches_trace"):
            pipeline_match_count += 1

    _error(
        errors,
        dict(classifications) == EXPECTED_CLASSIFICATION_COUNTS,
        "classification counts do not reproduce 6 spatial, 8 short-horizon, "
        "and 47 unresolved roots",
    )
    _error(
        errors,
        future_birth_count == EXPECTED_FUTURE_BIRTH_GAP_COUNT,
        f"expected {EXPECTED_FUTURE_BIRTH_GAP_COUNT} future-birth gaps, "
        f"found {future_birth_count}",
    )
    _error(
        errors,
        digest_ready_count == len(roots),
        "not every root capsule is decoded and content-addressed",
    )
    _error(
        errors,
        replay_ready_count == len(roots),
        "not every root has complete source solve results",
    )
    _error(
        errors,
        pipeline_match_count == len(roots),
        "not every reconstructed base result matches the published pipeline",
    )
    _error(
        errors,
        incomplete_labeled_empty == 0,
        "an incomplete or unvisited variant was labeled empty",
    )
    transitions = dossier.get("transitions", [])
    hit_count = int(dossier.get("scope", {}).get("hit_count", 0))
    _error(
        errors,
        isinstance(transitions, list) and len(transitions) == hit_count,
        "transition coverage does not match hit count",
    )

    return {
        "passed": not errors,
        "errors": errors,
        "root_count": len(roots),
        "classification_counts": dict(classifications),
        "future_birth_gap_count": future_birth_count,
        "content_addressed_root_count": digest_ready_count,
        "source_complete_root_count": replay_ready_count,
        "pipeline_match_count": pipeline_match_count,
        "incomplete_labeled_empty_count": incomplete_labeled_empty,
        "transition_count": len(transitions)
        if isinstance(transitions, list)
        else 0,
    }
