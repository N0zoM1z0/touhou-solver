from __future__ import annotations

import struct
import unittest
from copy import deepcopy
from pathlib import Path

from th08_ecl_tool.core import parse_ecl
from th08_ordinary_future_sources import project_ordinary_future_sources


REPO_ROOT = Path(__file__).resolve().parents[1]
ECL = parse_ecl(REPO_ROOT / "artifacts" / "decoded" / "ecldata5.ecl")
ECL_BASE = 0x10000000
SOURCE_POINTER = 0x0057D2F0


def _bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _inventory(rows: list[list[object]]) -> dict[str, object]:
    return {
        "invalid_active_vms": 0,
        "invalid_auxiliary_contexts": 0,
        "invalid_auxiliary_context_rows": [],
        "rows": rows,
    }


def _empty_source_group() -> dict[str, object]:
    return {
        "enemy_bodies": [],
        "main_ecl_vm_inventory": _inventory([]),
        "main_ecl_installed_callbacks": {"rows": []},
        "periodic_emission_state": {"rows": []},
        "emission_state": {"rows": []},
        "motion_state": {"rows": []},
        "phase_transition_state": {"rows": []},
        "auxiliary_ecl_contexts": {"rows": []},
    }


def _payload() -> dict[str, object]:
    first_timeline = ECL.timelines[0].instructions[0]
    main_row = [
        0,
        SOURCE_POINTER,
        0x01000049,
        ECL_BASE + 11480,
        0,
        0,
        [0] * 8,
        [0] * 8,
        [0] * 4,
    ]
    callback = {
        "enemy_pointer": SOURCE_POINTER,
        "installed_callback": {"function_pointer": 0},
    }
    periodic = {
        "enemy_pointer": SOURCE_POINTER,
        "enabled": False,
    }
    emission = {
        "enemy_pointer": SOURCE_POINTER,
        "emission_offset": [0.0, 0.0, 0.0],
        "rank_speed_interval": [-0.15, 0.15],
        "rank_count_interval": [0, 0, 0, 0],
        "descriptor": {
            "transform_program_hex": (b"\0" * (18 * 24)).hex(),
        },
    }
    motion = {
        "enemy_pointer": SOURCE_POINTER,
        "movement_state": 0,
        "mirror_x": False,
        "base_position": [60.0, 32.0, 0.0],
        "relative_position": [0.0, 0.0, 0.0],
        "velocity": [0.0, 0.0, 0.0],
        "world_position": [60.0, 32.0, 0.0],
        "angle": 0.0,
        "angular_velocity": 0.0,
        "speed": 0.0,
        "speed_acceleration": 0.0,
        "orbit_angle": 0.0,
        "orbit_angular_velocity": 0.0,
        "orbit_radius": 0.0,
        "orbit_radius_acceleration": 0.0,
        "orbit_center_position": [0.0, 0.0, 0.0],
        "motion_timer_elapsed": 0,
        "motion_duration": 0,
    }
    auxiliary = {
        "enemy_pointer": SOURCE_POINTER,
        "auxiliary_index": 0,
        "call_depth": 0,
        "installed_callback": {"function_pointer": 0},
        "state": {
            "instruction_pointer": ECL_BASE + 11812,
            "timer_elapsed": 0,
            "timer_fraction_bits": 0,
            "timer_previous": -1,
            "local_projection": {
                "integer_locals": [0] * 8,
                "float_local_bits": [
                    _bits(0.0),
                    _bits(1.0),
                    _bits(1.0),
                    0,
                    0,
                    0,
                    0,
                    0,
                ],
                "scratch_integers": [0, 0, 2, 0],
            },
        },
    }
    manager = {
        "source_role": "enemy_manager_template_or_special_singleton",
        "enemy_bodies": [
            {
                "pointer": SOURCE_POINTER,
                "flags": 0x01000049,
                "half_width": 18.0,
                "half_height": 18.0,
            }
        ],
        "main_ecl_vm_inventory": _inventory([main_row]),
        "main_ecl_installed_callbacks": {"rows": [callback]},
        "periodic_emission_state": {"rows": [periodic]},
        "emission_state": {"rows": [emission]},
        "motion_state": {"rows": [motion]},
        "phase_transition_state": {
            "rows": [
                {
                    "enemy_pointer": SOURCE_POINTER,
                    "health_thresholds": [-1, -1, -1, -1],
                    "timeout_frame": -1,
                    "timeout_subroutine": -1,
                }
            ]
        },
        "auxiliary_ecl_contexts": {"rows": [auxiliary]},
    }
    ordinary = _empty_source_group()
    return {
        "schema": "th08-native-snapshot-collision-control-projection-v12",
        "compact_state": {
            "manager_frame": 2129,
            "time_scale_bits": 0x3F800000,
            "rng_state": 1,
            "rng_calls": 0,
            "player_x": 192.0,
            "player_y": 432.0,
            "player_phase": 0,
            "predeath_counter": 10,
            "spell_id": None,
        },
        "enemy_manager_template_source": manager,
        "enemy_main_ecl_vm_inventory": ordinary[
            "main_ecl_vm_inventory"
        ],
        "enemy_bodies": ordinary["enemy_bodies"],
        "enemy_main_ecl_installed_callbacks": ordinary[
            "main_ecl_installed_callbacks"
        ],
        "enemy_periodic_emission_state": ordinary[
            "periodic_emission_state"
        ],
        "enemy_emission_state": ordinary["emission_state"],
        "enemy_motion_state": ordinary["motion_state"],
        "enemy_phase_transition_state": ordinary[
            "phase_transition_state"
        ],
        "enemy_auxiliary_ecl_contexts": ordinary[
            "auxiliary_ecl_contexts"
        ],
        "bullet_template_geometry": {
            "rows": [
                {
                    "type": 2,
                    "half_width": 2.0,
                    "half_height": 2.0,
                }
            ]
        },
        "stage_timeline_runtime": {
            "difficulty_mask": 8,
            "stage_flag_10": False,
            "ecl_file": {
                "magic": 0x800,
                "file_base": ECL_BASE,
                "subroutine_count": len(ECL.subroutines),
                "timeline_count": len(ECL.timelines),
                "static_data_end_offset": ECL.header.data_end_offset,
                "canonical_sha256": ECL.sha256,
            },
            "rows": [
                {
                    "elapsed": 0,
                    "fraction_bits": 0,
                    "current_instruction": {
                        "static_offset": first_timeline.offset,
                        "terminal": True,
                    },
                }
            ],
            "external": {
                "markers": [-1, -1, -1, -1],
                "stage_transition_busy": False,
                "spawn_suppressed": False,
                "conditional_gate_blocked": False,
                "indexed_enemies": [None] * 8,
            },
        },
    }


class OrdinaryFutureSourceTests(unittest.TestCase):
    def test_auxiliary_fire_is_complete_and_consumed(self) -> None:
        closure = project_ordinary_future_sources(
            _payload(),
            ECL,
            horizon_frames=1,
        )
        self.assertTrue(closure.projection.source_closure_complete)
        self.assertEqual(closure.source_count, 1)
        self.assertEqual(closure.auxiliary_count, 1)
        self.assertEqual(len(closure.direct_fire_events), 1)
        event = closure.direct_fire_events[0]
        self.assertGreater(event.angle1.upper, event.angle1.lower)
        self.assertEqual(
            len(closure.projection.trajectories),
            len(closure.direct_fire_events),
        )
        self.assertTrue(closure.projection.coverage.complete)

    def test_installed_callback_fails_closed(self) -> None:
        payload = _payload()
        payload["enemy_manager_template_source"][
            "main_ecl_installed_callbacks"
        ]["rows"][0]["installed_callback"]["function_pointer"] = 0x401000
        closure = project_ordinary_future_sources(
            payload,
            ECL,
            horizon_frames=1,
        )
        self.assertFalse(closure.projection.source_closure_complete)
        self.assertIn(
            "installed callback",
            closure.projection.source_closure_reason,
        )
        self.assertFalse(closure.projection.coverage.complete)

    def test_reached_random_x_timeline_spawn_is_lowered(self) -> None:
        payload = deepcopy(_payload())
        spawn = next(
            instruction
            for instruction in ECL.timelines[0].instructions
            if instruction.offset == 43348
        )
        row = payload["stage_timeline_runtime"]["rows"][0]
        row["elapsed"] = spawn.time
        row["current_instruction"]["static_offset"] = spawn.offset
        row["current_instruction"]["terminal"] = False
        closure = project_ordinary_future_sources(
            payload,
            ECL,
            horizon_frames=1,
        )
        self.assertTrue(closure.projection.source_closure_complete)
        self.assertEqual(closure.timeline_spawn_count, 1)
        self.assertEqual(closure.source_count, 2)
        timeline_events = [
            event
            for event in closure.direct_fire_events
            if event.source.startswith("timeline:")
        ]
        self.assertEqual(len(timeline_events), 2)
        self.assertEqual(timeline_events[0].origin_x.lower, 48.0)
        self.assertEqual(timeline_events[0].origin_x.upper, 160.0)

    def test_spawn_wave_remains_closed_through_timed_motion(self) -> None:
        payload = deepcopy(_payload())
        spawn = next(
            instruction
            for instruction in ECL.timelines[0].instructions
            if instruction.offset == 43348
        )
        row = payload["stage_timeline_runtime"]["rows"][0]
        row["elapsed"] = spawn.time
        row["current_instruction"]["static_offset"] = spawn.offset
        row["current_instruction"]["terminal"] = False
        closure = project_ordinary_future_sources(
            payload,
            ECL,
            horizon_frames=180,
        )
        self.assertTrue(closure.projection.source_closure_complete)
        self.assertEqual(closure.timeline_spawn_count, 9)
        self.assertGreater(len(closure.direct_fire_events), 1000)
        self.assertTrue(closure.projection.coverage.complete)

    def test_runtime_program_identity_mismatch_fails_closed(self) -> None:
        payload = _payload()
        payload["stage_timeline_runtime"]["ecl_file"][
            "canonical_sha256"
        ] = "0" * 64
        closure = project_ordinary_future_sources(
            payload,
            ECL,
            horizon_frames=1,
        )
        self.assertFalse(closure.projection.source_closure_complete)
        self.assertIn("SHA-256", closure.projection.source_closure_reason)


if __name__ == "__main__":
    unittest.main()
