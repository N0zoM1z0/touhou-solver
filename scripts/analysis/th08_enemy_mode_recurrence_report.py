#!/usr/bin/env python3
"""Audit the TH08 player-mode recurrence over retained physical intervals."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from th08_enemy_mode import step_route2_enemy_mode_state

REPORT_SCHEMA = "th08-enemy-mode-recurrence-report-v1"
_FOCUS_INPUT_BIT = 0x04
_MAX_RETAINED_MISMATCHES = 32


def _records(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"line {line_number}: trace row is not an object")
            yield line_number, record


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _integer(
    value: object,
    *,
    line_number: int,
    field: str,
) -> int:
    if type(value) is not int:
        raise ValueError(f"line {line_number}: {field} must be an integer")
    return value


def _boolean(
    value: object,
    *,
    line_number: int,
    field: str,
) -> bool:
    if type(value) is not bool:
        raise ValueError(f"line {line_number}: {field} must be a Boolean")
    return value


def _capture_state(
    capture: dict[str, object],
    *,
    line_number: int,
) -> dict[str, object]:
    player = capture.get("player_after")
    if not isinstance(player, dict):
        raise ValueError(f"line {line_number}: mode capture lacks player_after object")
    state = (
        _integer(
            player.get("focus_logic"),
            line_number=line_number,
            field="player_after.focus_logic",
        ),
        _boolean(
            player.get("secondary_character_active"),
            line_number=line_number,
            field="player_after.secondary_character_active",
        ),
        _integer(
            player.get("focus_transition_counter"),
            line_number=line_number,
            field="player_after.focus_transition_counter",
        ),
    )
    if not 0 <= state[0] <= 0xFF or state[2] < 0:
        raise ValueError(f"line {line_number}: invalid native mode state")
    return {
        "state": state,
        "input_current": _integer(
            player.get("input_current"),
            line_number=line_number,
            field="player_after.input_current",
        ),
        "phase": _integer(
            player.get("phase"),
            line_number=line_number,
            field="player_after.phase",
        ),
        "bomb_active": _integer(
            player.get("bomb_active"),
            line_number=line_number,
            field="player_after.bomb_active",
        ),
        "effective_focus": _boolean(
            player.get("effective_focus"),
            line_number=line_number,
            field="player_after.effective_focus",
        ),
    }


def _focus(mask: int) -> bool:
    return bool(mask & _FOCUS_INPUT_BIT)


def _eligible_interval(
    previous: dict[str, object],
    current: dict[str, object],
) -> tuple[str | None, int | None]:
    if (
        previous["gameplay_epoch"] != current["gameplay_epoch"]
        or previous["stage_route_index"] != current["stage_route_index"]
    ):
        return "epoch_or_stage_changed", None

    manager_delta = int(current["enemy_frame"]) - int(previous["enemy_frame"])
    if manager_delta <= 0:
        return "nonpositive_manager_delta", None

    previous_player = previous["player"]
    current_player = current["player"]
    assert isinstance(previous_player, dict)
    assert isinstance(current_player, dict)
    if previous_player["phase"] != current_player["phase"]:
        return "player_phase_changed", None
    if previous_player["phase"] in (1, 2):
        return "mode_update_suppressed_player_phase", None
    if previous_player["bomb_active"] or current_player["bomb_active"]:
        return "bomb_active", None

    effective_focus = bool(previous_player["effective_focus"])
    if effective_focus != bool(current_player["effective_focus"]):
        return "effective_focus_changed", None

    root = previous["pipeline_root"]
    if (
        not isinstance(root, dict)
        or root.get("canonical_status") != "available"
        or root.get("estimator_consistent") is not True
    ):
        return "pipeline_root_unavailable_or_inconsistent", None
    for field in ("active_mask", "held_desired_mask"):
        mask = root.get(field)
        if type(mask) is not int:
            return f"{field}_missing", None
        if _focus(mask) != effective_focus:
            return f"{field}_focus_mismatch", None
    pending_mask = root.get("pending_mask")
    if pending_mask is not None:
        if type(pending_mask) is not int:
            return "pending_mask_malformed", None
        if _focus(pending_mask) != effective_focus:
            return "pending_mask_focus_mismatch", None

    dispatch = previous["input_dispatch"]
    if not isinstance(dispatch, dict):
        return "input_dispatch_missing", None
    target_mask = dispatch.get("target_mask")
    if type(target_mask) is not int:
        return "dispatch_target_mask_missing", None
    if _focus(target_mask) != effective_focus:
        return "dispatch_target_focus_mismatch", None

    if _focus(int(previous_player["input_current"])) != effective_focus:
        return "capture_input_focus_mismatch", None
    return None, manager_delta


def build_report(path: Path) -> dict[str, object]:
    """Build a source-hashed physical recurrence audit."""

    total_rows = 0
    decision_rows = 0
    capture_rows = 0
    coherent_rows = 0
    adjacent_coherent_intervals = 0
    eligible_intervals = 0
    matched_intervals = 0
    mismatch_count = 0
    exclusion_counts: Counter[str] = Counter()
    manager_delta_counts: Counter[str] = Counter()
    intervening_nondecision_kind_counts: Counter[str] = Counter()
    retained_clock_boundary_intervals: list[dict[str, object]] = []
    retained_mismatches: list[dict[str, object]] = []
    capture_authority_violations: list[int] = []
    capture_role_violations: list[int] = []
    previous: dict[str, object] | None = None
    intervening_nondecision_kinds: Counter[str] = Counter()

    for line_number, record in _records(path):
        total_rows += 1
        kind = record.get("kind")
        if kind != "decision":
            if previous is not None:
                label = str(kind)
                intervening_nondecision_kinds[label] += 1
                intervening_nondecision_kind_counts[label] += 1
            continue
        decision_rows += 1
        capture = record.get("player_enemy_mode_capture")
        if capture is None:
            previous = None
            intervening_nondecision_kinds.clear()
            continue
        if not isinstance(capture, dict):
            raise ValueError(
                f"line {line_number}: player_enemy_mode_capture is not an object"
            )
        capture_rows += 1
        if capture.get("action_authority") is not False:
            capture_authority_violations.append(line_number)
        if capture.get("role") != "diagnostic_shadow":
            capture_role_violations.append(line_number)
        if capture.get("coherent") is not True:
            previous = None
            intervening_nondecision_kinds.clear()
            continue

        coherent_rows += 1
        enemy_frame = _integer(
            capture.get("enemy_frame_after"),
            line_number=line_number,
            field="enemy_frame_after",
        )
        frame = _integer(
            record.get("frame"),
            line_number=line_number,
            field="frame",
        )
        current = {
            "line": line_number,
            "frame": frame,
            "enemy_frame": enemy_frame,
            "gameplay_epoch": record.get("gameplay_epoch"),
            "stage_route_index": record.get("stage_route_index"),
            "player": _capture_state(capture, line_number=line_number),
            "pipeline_root": record.get("local_pipeline_root"),
            "input_dispatch": record.get("input_dispatch"),
        }
        if previous is not None:
            adjacent_coherent_intervals += 1
            if intervening_nondecision_kinds:
                exclusion = "intervening_nondecision_trace_record"
                manager_delta = None
                if len(retained_clock_boundary_intervals) < _MAX_RETAINED_MISMATCHES:
                    previous_player = previous["player"]
                    current_player = current["player"]
                    assert isinstance(previous_player, dict)
                    assert isinstance(current_player, dict)
                    retained_clock_boundary_intervals.append(
                        {
                            "previous_line": previous["line"],
                            "line": line_number,
                            "previous_frame": previous["frame"],
                            "frame": frame,
                            "previous_enemy_frame": (previous["enemy_frame"]),
                            "enemy_frame": enemy_frame,
                            "manager_delta": (
                                enemy_frame - int(previous["enemy_frame"])
                            ),
                            "intervening_kind_counts": dict(
                                sorted(intervening_nondecision_kinds.items())
                            ),
                            "initial_state": list(previous_player["state"]),
                            "observed_state": list(current_player["state"]),
                        }
                    )
            else:
                exclusion, manager_delta = _eligible_interval(
                    previous,
                    current,
                )
            if exclusion is not None:
                exclusion_counts[exclusion] += 1
            else:
                assert manager_delta is not None
                eligible_intervals += 1
                manager_delta_counts[str(manager_delta)] += 1
                previous_player = previous["player"]
                current_player = current["player"]
                assert isinstance(previous_player, dict)
                assert isinstance(current_player, dict)
                predicted = previous_player["state"]
                assert isinstance(predicted, tuple)
                effective_focus = bool(previous_player["effective_focus"])
                for _ in range(manager_delta):
                    predicted = step_route2_enemy_mode_state(
                        predicted,
                        focused=effective_focus,
                    )
                observed = current_player["state"]
                if predicted == observed:
                    matched_intervals += 1
                else:
                    mismatch_count += 1
                    if len(retained_mismatches) < _MAX_RETAINED_MISMATCHES:
                        retained_mismatches.append(
                            {
                                "previous_line": previous["line"],
                                "line": line_number,
                                "previous_frame": previous["frame"],
                                "frame": frame,
                                "previous_enemy_frame": (previous["enemy_frame"]),
                                "enemy_frame": enemy_frame,
                                "manager_delta": manager_delta,
                                "effective_focus": effective_focus,
                                "initial_state": list(previous_player["state"]),
                                "predicted_state": list(predicted),
                                "observed_state": list(observed),
                            }
                        )
        previous = current
        intervening_nondecision_kinds.clear()

    integrity_errors = {
        "capture_action_authority_true_or_missing_lines": (
            capture_authority_violations
        ),
        "capture_non_diagnostic_role_lines": capture_role_violations,
        "recurrence_mismatch_count": mismatch_count,
        "eligible_interval_count_zero": int(eligible_intervals == 0),
    }
    return {
        "schema": REPORT_SCHEMA,
        "source": {
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        },
        "scope": {
            "classification": "observed_physical_posthoc_recurrence",
            "eligible_interval_contract": (
                "adjacent coherent captures with no intervening non-decision "
                "trace record, in the same stage/epoch and player phase "
                "other than native suppressed phases 1/2, with no Bomb and "
                "captured active, held desired, pending, and newly "
                "dispatched target masks that all preserve one "
                "effective-focus value"
            ),
            "manager_delta_interpretation": (
                "tested update count only inside each eligible interval"
            ),
            "manager_frame_universal_physical_clock_authority": False,
            "action_authority": False,
            "hard_survival_authority": False,
            "physical_survival_authority": False,
        },
        "rows": {
            "total": total_rows,
            "decision": decision_rows,
            "capture": capture_rows,
            "coherent": coherent_rows,
        },
        "intervals": {
            "adjacent_coherent": adjacent_coherent_intervals,
            "eligible": eligible_intervals,
            "matched": matched_intervals,
            "mismatched": mismatch_count,
            "excluded": (adjacent_coherent_intervals - eligible_intervals),
            "exclusion_counts": dict(sorted(exclusion_counts.items())),
            "manager_delta_counts": dict(
                sorted(
                    manager_delta_counts.items(),
                    key=lambda item: int(item[0]),
                )
            ),
            "intervening_nondecision_kind_counts": dict(
                sorted(intervening_nondecision_kind_counts.items())
            ),
        },
        "retained_clock_boundary_intervals": (retained_clock_boundary_intervals),
        "retained_mismatches": retained_mismatches,
        "integrity": {
            "passed": bool(not any(integrity_errors.values())),
            "errors": integrity_errors,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.trace)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if report["integrity"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
