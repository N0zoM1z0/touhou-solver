"""Shared planner-consistency summary for dossier reports."""

from __future__ import annotations


def _planner_consistency_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    """Cross-tab distinct global-horizon and local-prefix safety contracts.

    A global winning state promises a policy over the remaining corridor
    horizon.  The local certificate only checks the selected action over its
    delay-plus-hold prefix.  Those Boolean values are useful together, but
    disagreement is not itself a contradiction.  The action-level
    contradiction is narrower: an action in the global winning set that the
    fresh local tube checker finds unsafe.
    """

    comparable = []
    excluded_hazard_version_change_count = 0
    excluded_deadline_hold_count = 0
    for row in decisions:
        player = row.get("player")
        if isinstance(player, dict) and (
            int(player.get("phase", 0)) != 0
            or int(player.get("phase_at_action", 0)) != 0
        ):
            continue
        viability = row.get("viability")
        robust = row.get("robust_control")
        if (
            not isinstance(viability, dict)
            or not bool(viability.get("available"))
            or not bool(viability.get("support_covers_current", True))
            or not isinstance(robust, dict)
        ):
            continue
        issue_guard = row.get("issue_time_enemy_guard")
        if (
            isinstance(issue_guard, dict)
            and bool(issue_guard.get("changes"))
        ):
            # The global policy and its action mask belong to the pre-issue
            # hazard version.  The issue guard deliberately invalidates that
            # version and recertifies against a newer local snapshot.
            excluded_hazard_version_change_count += 1
            continue
        deadline_guard = row.get("deadline_guard")
        if (
            isinstance(deadline_guard, dict)
            and bool(deadline_guard.get("input_suppressed"))
        ):
            # The traced action is the already-active input, not the newly
            # planned action whose global membership was queried.
            excluded_deadline_hold_count += 1
            continue
        global_safe = (
            bool(viability.get("state_viable"))
            and int(viability.get("safe_action_count", 0)) > 0
        )
        local_safe = (
            int(robust.get("worst_collisions", 0)) == 0
            and float(robust.get("min_clearance", 0.0)) >= 0.0
        )
        safe_actions = {
            str(action) for action in viability.get("safe_actions", ())
        }
        comparable.append(
            {
                "global_winning": global_safe,
                "local_prefix_safe": local_safe,
                "selected_in_winning_set": (
                    str(row.get("action", "")) in safe_actions
                ),
            }
        )
    count = len(comparable)

    def count_where(predicate) -> int:
        return sum(bool(predicate(item)) for item in comparable)

    global_winning_local_prefix_unsafe = count_where(
        lambda item: (
            item["global_winning"] and not item["local_prefix_safe"]
        )
    )
    global_losing_local_prefix_safe = count_where(
        lambda item: (
            not item["global_winning"] and item["local_prefix_safe"]
        )
    )
    certified_action_local_prefix_unsafe = count_where(
        lambda item: (
            item["global_winning"]
            and item["selected_in_winning_set"]
            and not item["local_prefix_safe"]
        )
    )
    selected_outside = count_where(
        lambda item: (
            item["global_winning"]
            and not item["selected_in_winning_set"]
        )
    )
    return {
        "comparable_decision_count": count,
        "global_winning_local_prefix_safe_count": count_where(
            lambda item: (
                item["global_winning"] and item["local_prefix_safe"]
            )
        ),
        "global_winning_local_prefix_unsafe_count": (
            global_winning_local_prefix_unsafe
        ),
        "global_losing_local_prefix_safe_count": (
            global_losing_local_prefix_safe
        ),
        "global_losing_local_prefix_unsafe_count": count_where(
            lambda item: (
                not item["global_winning"]
                and not item["local_prefix_safe"]
            )
        ),
        "selected_certified_action_local_prefix_unsafe_count": (
            certified_action_local_prefix_unsafe
        ),
        "selected_certified_action_local_prefix_unsafe_fraction": (
            certified_action_local_prefix_unsafe / count
            if count
            else None
        ),
        "selected_action_outside_global_winning_set_count": selected_outside,
        "excluded_hazard_version_change_count": (
            excluded_hazard_version_change_count
        ),
        "excluded_deadline_hold_count": excluded_deadline_hold_count,
        "semantics": (
            "global is a remaining-horizon winning-set claim; local is a "
            "delay-plus-hold prefix claim. After excluding observed "
            "issue-time invalidations, a selected cached-policy action that "
            "the fresh local prefix finds unsafe is a forecast/version "
            "contradiction; future births can still make the cached hazard "
            "set older than the local one. Deadline holds are excluded "
            "because their final input is not governed by that policy query."
        ),
    }


planner_consistency_summary = _planner_consistency_summary


__all__ = ["planner_consistency_summary"]
