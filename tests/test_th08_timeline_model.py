#!/usr/bin/env python3
"""Regression tests for the recovered TH08 stage-timeline scheduler."""

from __future__ import annotations

import struct
import unittest
from pathlib import Path

from th08_ecl import (
    EclFile,
    EclHeader,
    Timeline,
    TimelineInstruction,
    parse_ecl,
)
from th08_simulator import (
    Th08Route2FrameControl,
    initial_route2_stage_simulation_state,
    route2_stage_executor,
)
from th08_timeline_model import (
    IndexedEnemyView,
    StageTimelineState,
    TimelineClock,
    TimelineExternalState,
    initial_stage_timeline_state,
    step_stage_timelines,
)


ROOT = Path(__file__).resolve().parent.parent


def _word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _instruction(
    offset: int,
    time: int,
    opcode: int,
    arguments: tuple[int, ...] = (),
    difficulty_mask: int = 0xFF,
) -> TimelineInstruction:
    return TimelineInstruction(
        offset,
        time,
        opcode,
        8 + 4 * len(arguments),
        difficulty_mask,
        arguments,
    )


def _ecl(*instruction_groups: tuple[TimelineInstruction, ...]) -> EclFile:
    timelines = tuple(
        Timeline(index, 0, 0, instructions, 0, 0)
        for index, instructions in enumerate(instruction_groups)
    )
    header = EclHeader(1, len(timelines), (), 0, (0,))
    return EclFile(Path("synthetic.ecl"), "synthetic", header, (), timelines)


SPAWN_ARGS = (3, _word(100.0), _word(-20.0), 10, 1, 1000)


class TimelineModelTests(unittest.TestCase):
    def test_same_frame_marker_is_visible_to_later_timeline(self) -> None:
        program = _ecl(
            (_instruction(0x10, 0, 0x0E, (1,)),),
            (
                _instruction(0x20, 0, 0x0D, (1,)),
                _instruction(0x2C, 0, 0x00, SPAWN_ARGS),
            ),
        )
        result = step_stage_timelines(
            program,
            initial_stage_timeline_state(program, rng_seed=0x1234),
            active_difficulty_mask=0x0F,
        )
        self.assertEqual(result.state.markers, (-1, -1, -1, -1))
        self.assertEqual(len(result.spawns), 1)
        self.assertEqual(result.spawns[0].timeline_index, 1)
        self.assertEqual(result.spawns[0].subroutine, 3)
        self.assertEqual((result.spawns[0].x, result.spawns[0].y), (100.0, -20.0))

    def test_wait_holds_clock_and_spawn_suppression_still_consumes_record(self) -> None:
        wait_program = _ecl((_instruction(0x10, 0, 0x0D, (7,)),))
        state = initial_stage_timeline_state(wait_program, rng_seed=0)
        first = step_stage_timelines(wait_program, state, active_difficulty_mask=1)
        self.assertEqual(first.state.clocks[0].elapsed, 0)
        self.assertEqual(first.state.clocks[0].blocked_reason, "marker_7")

        spawn_program = _ecl((_instruction(0x20, 0, 0x00, SPAWN_ARGS),))
        suppressed = step_stage_timelines(
            spawn_program,
            initial_stage_timeline_state(spawn_program, rng_seed=0),
            active_difficulty_mask=1,
            external=TimelineExternalState(spawn_suppressed=True),
        )
        self.assertFalse(suppressed.spawns)
        self.assertTrue(suppressed.state.clocks[0].stopped)

    def test_indexed_enemy_wait_and_field_write_boundary(self) -> None:
        program = _ecl(
            (
                _instruction(0x10, 0, 0x08, (0, 0x12345)),
                _instruction(0x20, 0, 0x0A, (0,)),
            )
        )
        indexed = (IndexedEnemyView(active=True),) + (None,) * 7
        result = step_stage_timelines(
            program,
            initial_stage_timeline_state(program, rng_seed=0),
            active_difficulty_mask=1,
            external=TimelineExternalState(indexed_enemies=indexed),
        )
        self.assertEqual(result.external.indexed_enemies[0].field_2d30, 0x2345)
        self.assertEqual(result.state.clocks[0].blocked_reason, "indexed_enemy_0_active")
        self.assertEqual(result.state.clocks[0].elapsed, 0)

    def test_extra_first_cross_timeline_release_at_stage_frame_400(self) -> None:
        program = parse_ecl(ROOT / "artifacts/decoded/ecldata8.ecl")
        state = initial_stage_timeline_state(program, rng_seed=0xC0A4)
        result = None
        for _ in range(401):
            result = step_stage_timelines(
                program, state, active_difficulty_mask=0x0F
            )
            state = result.state
        assert result is not None
        self.assertEqual(
            [(spawn.timeline_index, spawn.instruction_offset) for spawn in result.spawns],
            [(0, 75076), (1, 86888)],
        )
        self.assertEqual(state.clocks[0].elapsed, 401)
        self.assertEqual(state.clocks[1].elapsed, 21)

    def test_integrated_executor_places_player_before_timeline(self) -> None:
        program = _ecl((_instruction(0x10, 0, 0x00, SPAWN_ARGS),))
        state = initial_route2_stage_simulation_state(
            program,
            rng_seed=0,
            active_timeline_difficulty_mask=1,
            short_spawn_mode=True,
        )
        executor = route2_stage_executor()
        self.assertEqual(
            executor.event_order,
            ("replay_publish_input", "player_input_movement", "stage_timeline_step"),
        )
        result = executor.step(state, Th08Route2FrameControl(0), frame_index=0)
        self.assertEqual(result.state.player.frame_index, 1)
        self.assertEqual(len(result.state.last_timeline_step.spawns), 1)


if __name__ == "__main__":
    unittest.main()
