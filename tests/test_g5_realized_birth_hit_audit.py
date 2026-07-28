from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.birth_hit_provenance import audit


def _evidence(
    slot: int,
    *,
    code: int = 3,
    status: int = 2,
    finite: bool = True,
) -> dict[str, object]:
    return {
        "format": "columnar_v1",
        "slot": [slot],
        "code": [code],
        "status": [status],
        "state": [2],
        "age": [0],
        "previous_state": [0],
        "previous_age": [0],
        "geometry": [[10.0, 20.0, 1.0, 2.0, 4.0, 5.0]],
        "transform_flags": [0],
        "geometry_finite": [finite],
    }


def _birth_row(
    slot: int,
    *,
    frame: int,
    previous_frame: int | None,
    code: int = 3,
    status: int = 2,
) -> dict[str, object]:
    evidence = _evidence(slot, code=code, status=status)
    return {
        "kind": "bullet_birth_audit",
        "frame": frame,
        "snapshot_frame": frame - 1,
        "gameplay_epoch": 0,
        "stage_route_index": 5,
        "spell_enemy_pointer": 0,
        "intent": None,
        "scope": {
            "intent": "active_spell_enemy_main_vm_only",
            "omitted_sources": [
                "non_spell_enemy_main_vm",
                "child_enemy_or_auxiliary_vm",
            ],
        },
        "observation": {
            "frame_before": frame - 1,
            "frame_after": frame - 1,
            "previous_frame_before": previous_frame,
            "previous_frame_after": previous_frame,
            "evidence_count": 1,
            "evidence": evidence,
        },
    }


def _candidate(slot: int, *, clearance: float) -> dict[str, object]:
    return {
        "slot": slot,
        "x": 10.0,
        "y": 20.0,
        "velocity_x": 1.0,
        "velocity_y": 2.0,
        "half_width": 4.0,
        "half_height": 5.0,
        "aabb_clearance": clearance,
    }


def _death(
    frame: int,
    slot: int | None,
    *,
    loss: int | None,
    exact: bool,
) -> dict[str, object]:
    return {
        "frame": frame,
        "stage_route_index": 5,
        "sample_role": "canonical_fresh_attempt_causal_sample",
        "primary_cause_class": (
            "observed_bullet_overlap"
            if exact
            else "modeled_committed_prefix_collision"
        ),
        "spell_attribution": {"status": "no_active_spell_at_hit"},
        "viability_kernel_exhausted_at_frame": loss,
        "observed_bullet_contact_candidate": (
            _candidate(slot, clearance=-1.0)
            if exact and slot is not None
            else None
        ),
        "nearest_observed_bullet": (
            _candidate(slot, clearance=2.0)
            if not exact and slot is not None
            else None
        ),
    }


class RealizedBirthHitAuditTests(unittest.TestCase):
    def _audit(
        self,
        rows: list[dict[str, object]],
        deaths: list[dict[str, object]],
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace = root / "trace.jsonl"
            dossier = root / "dossier.json"
            decision_rows = [
                {
                    "kind": "decision",
                    "frame": death["frame"],
                    "gameplay_epoch": 0,
                    "stage_route_index": 5,
                    "hit_started": True,
                }
                for death in deaths
            ]
            trace.write_text(
                "".join(
                    json.dumps(row, allow_nan=False) + "\n"
                    for row in [*rows, *decision_rows]
                ),
                encoding="utf-8",
            )
            dossier.write_text(
                json.dumps({"deaths": deaths}, allow_nan=False),
                encoding="utf-8",
            )
            return audit(
                trace=trace,
                dossier=dossier,
                gameplay_epoch=0,
                stage_route_index=5,
            )

    def test_exact_edges_classify_before_after_and_straddling_loss(self) -> None:
        report = self._audit(
            [
                _birth_row(10, frame=11, previous_frame=9),
                _birth_row(20, frame=16, previous_frame=14),
                _birth_row(30, frame=17, previous_frame=12),
            ],
            [
                _death(40, 10, loss=12, exact=True),
                _death(41, 20, loss=12, exact=True),
                _death(42, 30, loss=15, exact=True),
            ],
        )
        self.assertTrue(report["passed"])
        self.assertEqual(
            [hit["activation_relation"] for hit in report["hits"]],
            [
                "activation_before_or_at_loss",
                "activation_after_loss",
                "activation_straddles_loss",
            ],
        )
        self.assertEqual(
            report["conclusions"]["post_loss_exact_overlap_count"],
            1,
        )

    def test_nearest_candidate_never_becomes_exact_overlap(self) -> None:
        report = self._audit(
            [_birth_row(10, frame=16, previous_frame=14)],
            [_death(40, 10, loss=12, exact=False)],
        )
        hit = report["hits"][0]
        self.assertEqual(hit["candidate_role"], "nearest_only")
        self.assertEqual(hit["activation_relation"], "activation_after_loss")
        self.assertEqual(
            report["conclusions"]["post_loss_exact_overlap_count"],
            0,
        )

    def test_latest_slot_generation_before_hit_is_selected(self) -> None:
        report = self._audit(
            [
                _birth_row(10, frame=8, previous_frame=6),
                _birth_row(10, frame=16, previous_frame=14),
                _birth_row(10, frame=60, previous_frame=58),
            ],
            [_death(40, 10, loss=12, exact=True)],
        )
        hit = report["hits"][0]
        self.assertEqual(hit["activation"]["frame"], 16)
        self.assertEqual(hit["observed_generation_count_before_hit"], 2)

    def test_bootstrap_and_timer_regression_remain_ambiguous(self) -> None:
        report = self._audit(
            [
                _birth_row(
                    10,
                    frame=16,
                    previous_frame=None,
                    code=2,
                    status=2,
                ),
                _birth_row(
                    20,
                    frame=16,
                    previous_frame=14,
                    code=4,
                    status=3,
                ),
            ],
            [
                _death(40, 10, loss=12, exact=True),
                _death(41, 20, loss=12, exact=True),
            ],
        )
        self.assertEqual(
            [hit["activation_relation"] for hit in report["hits"]],
            [
                "bootstrap_recent_activation_time_unresolved",
                "slot_reuse_ambiguous",
            ],
        )

    def test_missing_candidate_and_activation_are_explicit(self) -> None:
        report = self._audit(
            [_birth_row(10, frame=16, previous_frame=14)],
            [
                _death(40, None, loss=12, exact=False),
                _death(41, 20, loss=12, exact=True),
            ],
        )
        self.assertEqual(report["hits"][0]["candidate_role"], "missing")
        self.assertEqual(
            report["hits"][0]["activation_relation"],
            "activation_unresolved",
        )
        self.assertEqual(
            report["hits"][1]["activation_relation"],
            "activation_unresolved",
        )

    def test_source_scope_is_preserved_and_sorted(self) -> None:
        report = self._audit(
            [_birth_row(10, frame=16, previous_frame=14)],
            [_death(40, 10, loss=12, exact=True)],
        )
        activation = report["hits"][0]["activation"]
        self.assertEqual(
            activation["intent_scope"],
            "active_spell_enemy_main_vm_only",
        )
        self.assertEqual(
            activation["omitted_sources"],
            [
                "child_enemy_or_auxiliary_vm",
                "non_spell_enemy_main_vm",
            ],
        )
        self.assertFalse(activation["intent_available"])

    def test_slot_generation_is_matched_within_hit_gameplay_epoch(self) -> None:
        old = _birth_row(10, frame=16, previous_frame=14)
        current = _birth_row(10, frame=31, previous_frame=29)
        current["gameplay_epoch"] = 1
        death = _death(40, 10, loss=20, exact=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace = root / "trace.jsonl"
            dossier = root / "dossier.json"
            trace.write_text(
                "".join(
                    json.dumps(row, allow_nan=False) + "\n"
                    for row in [
                        old,
                        current,
                        {
                            "kind": "decision",
                            "frame": 40,
                            "gameplay_epoch": 1,
                            "stage_route_index": 5,
                            "hit_started": True,
                        },
                    ]
                ),
                encoding="utf-8",
            )
            dossier.write_text(
                json.dumps({"deaths": [death]}, allow_nan=False),
                encoding="utf-8",
            )
            report = audit(
                trace=trace,
                dossier=dossier,
                stage_route_index=5,
            )
        hit = report["hits"][0]
        self.assertEqual(hit["gameplay_epoch"], 1)
        self.assertEqual(hit["activation"]["frame"], 31)
        self.assertEqual(hit["observed_generation_count_before_hit"], 1)

    def test_malformed_column_lengths_fail_closed(self) -> None:
        row = _birth_row(10, frame=16, previous_frame=14)
        row["observation"]["evidence"]["age"] = []
        with self.assertRaisesRegex(ValueError, "column lengths"):
            self._audit([row], [_death(40, 10, loss=12, exact=True)])

    def test_invalid_code_status_pair_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid code/status"):
            self._audit(
                [
                    _birth_row(
                        10,
                        frame=16,
                        previous_frame=14,
                        code=4,
                        status=2,
                    )
                ],
                [_death(40, 10, loss=12, exact=True)],
            )

    def test_report_digest_is_deterministic(self) -> None:
        rows = [_birth_row(10, frame=16, previous_frame=14)]
        deaths = [_death(40, 10, loss=12, exact=True)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace = root / "trace.jsonl"
            dossier = root / "dossier.json"
            trace.write_text(
                "".join(
                    json.dumps(row, allow_nan=False) + "\n"
                    for row in [
                        *rows,
                        {
                            "kind": "decision",
                            "frame": 40,
                            "gameplay_epoch": 0,
                            "stage_route_index": 5,
                            "hit_started": True,
                        },
                    ]
                ),
                encoding="utf-8",
            )
            dossier.write_text(
                json.dumps({"deaths": deaths}, allow_nan=False),
                encoding="utf-8",
            )
            arguments = {
                "trace": trace,
                "dossier": dossier,
                "gameplay_epoch": 0,
                "stage_route_index": 5,
            }
            first = audit(**arguments)
            second = audit(**arguments)
            self.assertEqual(
                first["report_digest"],
                second["report_digest"],
            )


if __name__ == "__main__":
    unittest.main()
