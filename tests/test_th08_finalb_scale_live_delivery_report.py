from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.th08_finalb_scale_live_delivery_report import build_report
from th08_live.scale_schedule_authority import (
    FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA,
)
from th08_live.scale_source_trace import (
    FINAL_B_ECL_STATIC_SHA256,
    FINAL_B_QUARTER_SCALE_BITS,
    FINAL_B_SCALE_SOURCE_TRACE_SCHEMA,
)
from th08_runtime.game_state import EXPECTED_EXE_SHA256
from th08_time_scale import (
    SCALE_COVERAGE_COMPLETE,
    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
    TH08_UNIT_TIME_SCALE_BITS,
)


ORIGIN = 74787


def _authority(offset: int, scale_bits: int) -> dict[str, object]:
    return {
        "kind": "finalb_live_scale_schedule_authority",
        "schema": FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA,
        "status": "complete_exact_source_schedule",
        "reason": None,
        "planner_scale_schedule_authority": True,
        "experimental_pretarget_transport": False,
        "hard_action_authority": False,
        "semantics_version": TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
        "origin_source_frame": ORIGIN,
        "current_source_frame": ORIGIN + offset,
        "frame_offset": offset,
        "baseline_predeath_counter": 0,
        "source_player_phase": 0,
        "root_scale_bits": scale_bits,
        "coverage": SCALE_COVERAGE_COMPLETE,
        "complete_horizon": 300 - offset,
        "provenance": "physical:live_exact_rebase",
        "fallback": None,
    }


def _decision(offset: int, scale_bits: int) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": ORIGIN + offset,
        "mask": 0x11,
        "bomb": False,
        "hit_started": False,
        "time_scale": {
            "semantics_version": TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
            "root_scale_bits": scale_bits,
            "coverage": SCALE_COVERAGE_COMPLETE,
            "provenance": "physical:live_exact_rebase",
            "source_frame": ORIGIN + offset,
            "complete_horizon": 300 - offset,
            "hard_authority": True,
        },
    }


def _transport_decision() -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": ORIGIN - 1,
        "mask": 0x11,
        "bomb": False,
        "hit_started": False,
        "time_scale": {
            "semantics_version": TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
            "root_scale_bits": TH08_UNIT_TIME_SCALE_BITS,
            "coverage": SCALE_COVERAGE_COMPLETE,
            "provenance": (
                "experimental_pretarget_unit_transport_unknown_direction"
            ),
            "source_frame": ORIGIN - 1,
            "complete_horizon": 256,
            "hard_authority": False,
            "phase_schedule_omitted": True,
        },
    }


def _fixture() -> list[dict[str, object]]:
    return [
        {"kind": "identity", "sha256": EXPECTED_EXE_SHA256},
        {
            "kind": "controller_config",
            "bomb_policy": "disabled",
            "finalb_scale_source_authority": True,
            "finalb_scale_pretarget_transport": (
                "experimental_unit_unknown_direction"
            ),
            "finalb_scale_delivery_auto_stop": True,
            "runtime_ecl_static_sha256": FINAL_B_ECL_STATIC_SHA256,
        },
        _transport_decision(),
        {
            "kind": "finalb_scale_source_trace",
            "schema": FINAL_B_SCALE_SOURCE_TRACE_SCHEMA,
            "status": "accepted_complete_source_trace",
            "route_id": 2,
            "difficulty_index": 3,
            "stage_route_index": 7,
            "spell_id": 190,
            "decision_frame": ORIGIN,
            "capture_manager_frame": ORIGIN,
            "expected_manager_frame": ORIGIN,
            "runtime_ecl_identity": {
                "exact_match": True,
                "static_sha256": FINAL_B_ECL_STATIC_SHA256,
            },
            "source_capture": {
                "coherent": True,
                "manager_frame_before": ORIGIN,
                "manager_frame_after": ORIGIN,
                "phase_before": {
                    "route_id": 2,
                    "difficulty_index": 3,
                    "stage_route_index": 7,
                    "spell_id": 190,
                    "scale_bits": FINAL_B_QUARTER_SCALE_BITS,
                    "player_bomb_active": 0,
                    "player_predeath_counter": 0,
                    "player_phase": 0,
                },
            },
            "schedule": {
                "semantics_version": (
                    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION
                ),
                "coverage": SCALE_COVERAGE_COMPLETE,
                "root_scale_bits": FINAL_B_QUARTER_SCALE_BITS,
                "source_frame": ORIGIN,
                "complete_horizon": 300,
                "player_scale_bits": (
                    [FINAL_B_QUARTER_SCALE_BITS] * 240
                    + [TH08_UNIT_TIME_SCALE_BITS] * 60
                ),
                "laser_scale_bits": (
                    [FINAL_B_QUARTER_SCALE_BITS] * 239
                    + [TH08_UNIT_TIME_SCALE_BITS] * 61
                ),
                "writes": [
                    {
                        "frame": 240,
                        "callback_index": 18,
                        "scale_bits_before": FINAL_B_QUARTER_SCALE_BITS,
                        "scale_bits_after": TH08_UNIT_TIME_SCALE_BITS,
                        "scales_active_bullet_velocity": False,
                    }
                ],
            },
        },
        _authority(0, FINAL_B_QUARTER_SCALE_BITS),
        _decision(0, FINAL_B_QUARTER_SCALE_BITS),
        _authority(239, FINAL_B_QUARTER_SCALE_BITS),
        _decision(239, FINAL_B_QUARTER_SCALE_BITS),
        _authority(240, TH08_UNIT_TIME_SCALE_BITS),
        _decision(240, TH08_UNIT_TIME_SCALE_BITS),
        {
            "kind": "run_summary",
            "termination_reason": "finalb_scale_delivery_complete",
            "hit_count": 3,
        },
    ]


def _terminal_unload_fixture() -> list[dict[str, object]]:
    records = _fixture()
    records[1]["finalb_scale_delivery_auto_stop"] = False
    source = records[3]
    source["decision_frame"] = ORIGIN - 1
    source["expected_manager_frame"] = ORIGIN - 1
    source["capture_manager_frame"] = ORIGIN
    source_capture = source["source_capture"]
    source_capture["manager_frame_before"] = ORIGIN
    source_capture["manager_frame_after"] = ORIGIN
    source_capture["phase_before"]["player_predeath_counter"] = 7
    source_capture["phase_before"]["player_phase"] = 3
    schedule = source["schedule"]
    schedule["player_scale_bits"] = (
        [FINAL_B_QUARTER_SCALE_BITS] * 239
        + [TH08_UNIT_TIME_SCALE_BITS] * 61
    )
    schedule["laser_scale_bits"] = (
        [FINAL_B_QUARTER_SCALE_BITS] * 238
        + [TH08_UNIT_TIME_SCALE_BITS] * 62
    )
    schedule["writes"][0]["frame"] = 239
    exact_rows = [
        _authority(1, FINAL_B_QUARTER_SCALE_BITS),
        _decision(1, FINAL_B_QUARTER_SCALE_BITS),
        _authority(238, FINAL_B_QUARTER_SCALE_BITS),
        _decision(238, FINAL_B_QUARTER_SCALE_BITS),
    ]
    for record in exact_rows:
        if record["kind"] == "finalb_live_scale_schedule_authority":
            record["baseline_predeath_counter"] = 7
            record["source_player_phase"] = 3
    records[4:] = [
        *exact_rows,
        {
            "kind": "finalb_live_scale_schedule_authority",
            "schema": FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA,
            "status": "root_only_context_mismatch",
            "reason": "immutable_context_mismatch",
            "planner_scale_schedule_authority": False,
            "experimental_pretarget_transport": False,
            "hard_action_authority": False,
            "origin_source_frame": ORIGIN,
            "current_source_frame": ORIGIN + 240,
            "frame_offset": 240,
            "baseline_predeath_counter": 7,
            "source_player_phase": 3,
            "root_scale_bits": TH08_UNIT_TIME_SCALE_BITS,
            "coverage": "root_only",
        },
        {
            "kind": "scene_inactive",
            "frame": ORIGIN + 240,
            "stage_route_index": 7,
            "transition_from_stage": 7,
            "expected_stage": None,
            "status": "terminal_unload",
        },
        {
            "kind": "run_summary",
            "termination_reason": "route_complete",
            "hit_count": 22,
        },
    ]
    return records


class FinalBScaleLiveDeliveryReportTests(unittest.TestCase):
    def _report(
        self,
        records: list[dict[str, object]],
    ) -> dict[str, object]:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "trace.jsonl"
            path.write_text(
                "".join(
                    json.dumps(record, sort_keys=True) + "\n"
                    for record in records
                ),
                encoding="utf-8",
            )
            return build_report(path)

    def test_clean_restore_scope_passes(self) -> None:
        report = self._report(_fixture())

        self.assertTrue(report["gate"]["passed"])
        self.assertEqual(report["observed"]["first_unit_offset"], 240)
        self.assertEqual(report["observed"]["hit_count"], 0)
        self.assertEqual(report["observed"]["bomb_decision_count"], 0)
        self.assertEqual(report["observed"]["entire_trial_hit_count"], 3)
        self.assertEqual(report["observed"]["source_player_phase"], 0)

    def test_stable_predeath_residue_is_reported_without_becoming_clean(
        self,
    ) -> None:
        records = _fixture()
        records[3]["source_capture"]["phase_before"][
            "player_predeath_counter"
        ] = 7
        for record in records:
            if record.get("kind") == "finalb_live_scale_schedule_authority":
                record["baseline_predeath_counter"] = 7

        report = self._report(records)

        self.assertTrue(report["gate"]["passed"])
        self.assertEqual(report["observed"]["baseline_predeath_counter"], 7)

    def test_phase_three_source_is_explicit_contamination_not_rejection(
        self,
    ) -> None:
        records = _fixture()
        records[3]["source_capture"]["phase_before"]["player_phase"] = 3
        for record in records:
            if record.get("kind") == "finalb_live_scale_schedule_authority":
                record["source_player_phase"] = 3

        report = self._report(records)

        self.assertTrue(report["gate"]["passed"])
        self.assertEqual(report["observed"]["source_player_phase"], 3)
        self.assertIn(
            "normal player-phase",
            report["authority"]["not_proved"],
        )

    def test_native_summary_kind_is_consumed(self) -> None:
        records = _fixture()
        records[-1]["kind"] = "summary"

        report = self._report(records)

        self.assertTrue(report["gate"]["passed"])
        self.assertEqual(
            report["observed"]["termination_reason"],
            "finalb_scale_delivery_complete",
        )

    def test_complete_route_can_retain_the_exact_gate_without_auto_stop(
        self,
    ) -> None:
        records = _fixture()
        records[1]["finalb_scale_delivery_auto_stop"] = False
        records[-1]["termination_reason"] = "route_complete"

        report = self._report(records)

        self.assertTrue(report["gate"]["passed"])

    def test_terminal_unload_can_physically_bracket_restore(self) -> None:
        report = self._report(_terminal_unload_fixture())

        self.assertTrue(report["gate"]["passed"])
        self.assertEqual(report["observed"]["capture_frame_delta"], 1)
        self.assertEqual(report["observed"]["first_authority_offset"], 1)
        self.assertEqual(report["observed"]["scheduled_restore_offset"], 239)
        self.assertEqual(report["observed"]["restore_observation_offset"], 240)
        self.assertEqual(
            report["observed"]["restore_observation"],
            "terminal_unload_root",
        )
        self.assertEqual(report["observed"]["source_player_phase"], 3)
        self.assertEqual(report["observed"]["baseline_predeath_counter"], 7)

    def test_terminal_restore_requires_matching_native_unload(self) -> None:
        records = [
            record
            for record in _terminal_unload_fixture()
            if record.get("kind") != "scene_inactive"
        ]

        report = self._report(records)

        self.assertFalse(
            report["gate"]["checks"]["physical_restore_bracket"]
        )

    def test_hit_bomb_predeath_and_authority_fallback_fail(self) -> None:
        cases = {
            "hit": lambda records: records[7].update(hit_started=True),
            "bomb": lambda records: records[9].update(mask=0x13),
            "predeath": lambda records: records[3]["source_capture"][
                "phase_before"
            ].update(player_predeath_counter=7),
            "fallback": lambda records: records.append(
                {"kind": "time_scale_authority_unknown"}
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                records = _fixture()
                mutate(records)
                report = self._report(records)
                self.assertFalse(report["gate"]["passed"])

    def test_restore_must_be_physically_bracketed(self) -> None:
        records = [
            record
            for record in _fixture()
            if not (
                record.get("kind")
                == "finalb_live_scale_schedule_authority"
                and record.get("frame_offset") == 240
            )
        ]

        report = self._report(records)

        self.assertFalse(
            report["gate"]["checks"]["physical_restore_bracket"]
        )

    def test_wrong_scope_hidden_origin_or_runtime_error_fails(self) -> None:
        cases = {
            "wrong_spell": lambda records: records[3].update(spell_id=189),
            "second_origin": lambda records: records.insert(
                -1,
                {
                    **_authority(241, TH08_UNIT_TIME_SCALE_BITS),
                    "origin_source_frame": ORIGIN + 1,
                    "current_source_frame": ORIGIN + 242,
                },
            ),
            "runtime_error": lambda records: records.insert(
                -1,
                {"kind": "runtime_error", "message": "foreground lost"},
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                records = _fixture()
                mutate(records)
                self.assertFalse(self._report(records)["gate"]["passed"])


if __name__ == "__main__":
    unittest.main()
