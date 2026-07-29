#!/usr/bin/env python3
"""Compare SEM-SCALE product, raw oracle, and native x87 probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path

from analysis.th08_scale_transition_raw_oracle import (
    ORACLE_SEMANTICS_VERSION,
    RawLaserState,
    oracle_step_laser_raw,
    oracle_step_route2_movement_raw,
)
from movement_model import MovementBounds
from th08_ecl_vm_state import float32_bits, float32_from_bits
from th08_laser_model import (
    TH08_LASER_SCALE_SEMANTICS_VERSION,
    LaserPhase,
    LaserState,
    step_laser,
)
from th08_movement_model import (
    TH08_ROUTE2_MOVEMENT_SCALE_SEMANTICS_VERSION,
    step_route2_movement,
)
from th08_time_scale import TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION


SCHEMA = "th08-player-laser-scale-differential-v1"
_BOUNDS = MovementBounds(8.0, 16.0, 376.0, 432.0)
_BOUND_BITS = tuple(
    float32_bits(value)
    for value in (
        _BOUNDS.left,
        _BOUNDS.top,
        _BOUNDS.right,
        _BOUNDS.bottom,
    )
)


def _hex_dword(value: int) -> str:
    return f"0x{value & 0xFFFFFFFF:08x}"


def _probe_words(probe: Path, *arguments: str) -> tuple[int, ...]:
    completed = subprocess.run(
        (str(probe), *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    words = completed.stdout.strip().split()
    if not words:
        raise ValueError(f"empty probe output: {completed.stdout!r}")
    return tuple(int(word, 0) for word in words)


@dataclass(frozen=True)
class MovementCase:
    label: str
    x_bits: int
    y_bits: int
    input_masks: tuple[int, ...]
    scale_bits: tuple[int, ...]
    axis_scale_x_bits: int = 0x3F800000
    axis_scale_y_bits: int = 0x3F800000


def _movement_cases() -> tuple[MovementCase, ...]:
    f32 = float32_bits
    return (
        MovementCase(
            "unit_focused_cardinal",
            f32(192.125),
            f32(400.25),
            (0x84,) * 3,
            (f32(1.0),) * 3,
        ),
        MovementCase(
            "finalb_quarter_unfocused_right_four",
            f32(192.0),
            f32(400.0),
            (0x80,) * 4,
            (f32(0.25),) * 4,
        ),
        MovementCase(
            "one_third_direction_and_focus_changes",
            f32(160.75),
            f32(320.5),
            (0x80, 0xA4, 0x54, 0x20, 0),
            (f32(1.0 / 3.0),) * 5,
        ),
        MovementCase(
            "stop_resume_and_quarter_transition",
            f32(200.0),
            f32(300.0),
            (0x10, 0x10, 0x90, 0x94, 0x84),
            tuple(f32(value) for value in (1.0, 0.0, 0.0, 0.25, 1.0)),
        ),
        MovementCase(
            "one_twelfth_diagonal",
            f32(100.5),
            f32(100.5),
            (0xA0,) * 12,
            (f32(1.0 / 12.0),) * 12,
        ),
        MovementCase(
            "axis_scale_and_float32_store",
            f32(123.03125),
            f32(222.0625),
            (0x54, 0x94, 0x64),
            (f32(0.5), f32(0.25), f32(1.0)),
            axis_scale_x_bits=f32(0.75),
            axis_scale_y_bits=f32(1.25),
        ),
        MovementCase(
            "contradictory_direction_native_priority",
            f32(200.0),
            f32(200.0),
            (0xF4,),
            (f32(0.5),),
        ),
        MovementCase(
            "physical_clamp_each_store",
            f32(375.75),
            f32(16.25),
            (0x94, 0x94, 0x94),
            (f32(1.0), f32(0.5), f32(0.25)),
        ),
    )


def _movement_record(probe: Path, case: MovementCase) -> dict[str, object]:
    if len(case.input_masks) != len(case.scale_bits):
        raise ValueError("movement case schedules must have equal length")
    product_x_bits = case.x_bits
    product_y_bits = case.y_bits
    oracle_x_bits = case.x_bits
    oracle_y_bits = case.y_bits
    native_x_bits = case.x_bits
    native_y_bits = case.y_bits
    steps: list[dict[str, object]] = []
    for index, (input_mask, scale_bits) in enumerate(
        zip(case.input_masks, case.scale_bits),
        start=1,
    ):
        product = step_route2_movement(
            x=float32_from_bits(product_x_bits),
            y=float32_from_bits(product_y_bits),
            input_mask=input_mask,
            axis_scale_x=float32_from_bits(case.axis_scale_x_bits),
            axis_scale_y=float32_from_bits(case.axis_scale_y_bits),
            time_scale_bits=scale_bits,
            bounds=_BOUNDS,
        )
        product_words = tuple(
            float32_bits(value)
            for value in (
                product.x,
                product.y,
                product.velocity_x,
                product.velocity_y,
            )
        )
        oracle_words = oracle_step_route2_movement_raw(
            x_bits=oracle_x_bits,
            y_bits=oracle_y_bits,
            input_mask=input_mask,
            axis_scale_x_bits=case.axis_scale_x_bits,
            axis_scale_y_bits=case.axis_scale_y_bits,
            time_scale_bits=scale_bits,
            left_bits=_BOUND_BITS[0],
            top_bits=_BOUND_BITS[1],
            right_bits=_BOUND_BITS[2],
            bottom_bits=_BOUND_BITS[3],
        )
        native_words = _probe_words(
            probe,
            "movement",
            _hex_dword(native_x_bits),
            _hex_dword(native_y_bits),
            _hex_dword(input_mask),
            _hex_dword(case.axis_scale_x_bits),
            _hex_dword(case.axis_scale_y_bits),
            _hex_dword(scale_bits),
            *(_hex_dword(bits) for bits in _BOUND_BITS),
        )
        passed = product_words == oracle_words == native_words
        steps.append(
            {
                "step": index,
                "input_mask": _hex_dword(input_mask),
                "time_scale_bits": _hex_dword(scale_bits),
                "product": [_hex_dword(word) for word in product_words],
                "oracle": [_hex_dword(word) for word in oracle_words],
                "native_probe": [_hex_dword(word) for word in native_words],
                "passed": passed,
            }
        )
        product_x_bits, product_y_bits = product_words[:2]
        oracle_x_bits, oracle_y_bits = oracle_words[:2]
        native_x_bits, native_y_bits = native_words[:2]
    return {
        "label": case.label,
        "operation": "movement",
        "initial": {
            "x_bits": _hex_dword(case.x_bits),
            "y_bits": _hex_dword(case.y_bits),
            "axis_scale_x_bits": _hex_dword(case.axis_scale_x_bits),
            "axis_scale_y_bits": _hex_dword(case.axis_scale_y_bits),
        },
        "steps": steps,
        "passed": all(bool(step["passed"]) for step in steps),
    }


@dataclass(frozen=True)
class LaserCase:
    label: str
    state: RawLaserState
    scale_bits: tuple[int, ...]


def _raw_laser(
    *,
    tail: float = 0.0,
    head: float = 10.125,
    maximum_length: float = 12.5,
    width: float = 16.0,
    current_width: float = 1.2,
    speed: float = 3.25,
    warmup_frames: int = 3,
    active_frames: int = 4,
    fade_frames: int = 3,
    collision_enable_frame: int = 1,
    collision_disable_frame: int = 2,
    flags: int = 0,
    phase: int = 0,
    timer: int = 0,
    timer_fraction: float = 0.0,
    active: bool = True,
) -> RawLaserState:
    return RawLaserState(
        tail_bits=float32_bits(tail),
        head_bits=float32_bits(head),
        maximum_length_bits=float32_bits(maximum_length),
        width_bits=float32_bits(width),
        current_width_bits=float32_bits(current_width),
        speed_bits=float32_bits(speed),
        warmup_frames=warmup_frames,
        active_frames=active_frames,
        fade_frames=fade_frames,
        collision_enable_frame=collision_enable_frame,
        collision_disable_frame=collision_disable_frame,
        flags=flags,
        phase=phase,
        timer=timer,
        timer_fraction_bits=float32_bits(timer_fraction),
        active=active,
    )


def _laser_cases() -> tuple[LaserCase, ...]:
    f32 = float32_bits
    return (
        LaserCase(
            "unit_active_motion",
            _raw_laser(phase=1, timer=1),
            (f32(1.0),) * 3,
        ),
        LaserCase(
            "quarter_fractional_timer_and_length_clamp",
            _raw_laser(
                tail=2.0,
                head=13.0,
                phase=1,
                timer=1,
                timer_fraction=0.75,
            ),
            (f32(0.25),) * 4,
        ),
        LaserCase(
            "stop_resume_warmup",
            _raw_laser(warmup_frames=4),
            tuple(f32(value) for value in (0.0, 0.0, 0.5, 0.5, 1.0)),
        ),
        LaserCase(
            "warmup_same_update_active_fallthrough",
            _raw_laser(timer=3, timer_fraction=0.75),
            (f32(0.25), f32(1.0)),
        ),
        LaserCase(
            "active_same_update_fade_fallthrough",
            _raw_laser(phase=1, timer=4, timer_fraction=0.5),
            (f32(0.5), f32(0.5), f32(1.0)),
        ),
        LaserCase(
            "one_third_fade_width_and_disable",
            _raw_laser(
                phase=2,
                timer=0,
                timer_fraction=2.0 / 3.0,
                fade_frames=4,
                collision_disable_frame=2,
            ),
            (f32(1.0 / 3.0),) * 8,
        ),
        LaserCase(
            "alpha_flag_keeps_width",
            _raw_laser(flags=1, timer=1),
            (f32(0.25),) * 5,
        ),
        LaserCase(
            "one_twelfth_head_and_timer",
            _raw_laser(speed=17.125, warmup_frames=20),
            (f32(1.0 / 12.0),) * 13,
        ),
        LaserCase(
            "tail_cull_after_collision_phase",
            _raw_laser(
                tail=639.5,
                head=640.0,
                maximum_length=0.5,
                speed=4.0,
                phase=1,
                timer=1,
            ),
            (f32(0.25),),
        ),
    )


def _product_laser(raw: RawLaserState) -> LaserState:
    return LaserState(
        origin_x=0.0,
        origin_y=0.0,
        angle=0.0,
        tail_distance=float32_from_bits(raw.tail_bits),
        head_distance=float32_from_bits(raw.head_bits),
        maximum_length=float32_from_bits(raw.maximum_length_bits),
        width=float32_from_bits(raw.width_bits),
        speed=float32_from_bits(raw.speed_bits),
        warmup_frames=raw.warmup_frames,
        active_frames=raw.active_frames,
        fade_frames=raw.fade_frames,
        collision_enable_frame=raw.collision_enable_frame,
        collision_disable_frame=raw.collision_disable_frame,
        flags=raw.flags,
        current_width=float32_from_bits(raw.current_width_bits),
        phase=LaserPhase(raw.phase),
        timer=raw.timer,
        timer_fraction=float32_from_bits(raw.timer_fraction_bits),
        active=raw.active,
    )


def _encode_checks(checks: tuple[tuple[int, bool], ...]) -> int:
    code = len(checks)
    for index, (phase, graze) in enumerate(checks):
        code |= ((phase & 3) | (4 if graze else 0)) << (4 + index * 4)
    return code


def _product_laser_words(
    state: LaserState,
    checks: tuple[tuple[int, bool], ...],
) -> tuple[int, ...]:
    return (
        float32_bits(state.tail_distance),
        float32_bits(state.head_distance),
        float32_bits(state.current_width),
        int(state.phase),
        state.timer & 0xFFFFFFFF,
        float32_bits(state.timer_fraction),
        int(state.active),
        _encode_checks(checks),
    )


def _raw_laser_words(
    state: RawLaserState,
    checks: tuple[tuple[int, bool], ...],
) -> tuple[int, ...]:
    return (
        state.tail_bits,
        state.head_bits,
        state.current_width_bits,
        state.phase,
        state.timer & 0xFFFFFFFF,
        state.timer_fraction_bits,
        int(state.active),
        _encode_checks(checks),
    )


def _laser_probe_arguments(
    state: RawLaserState,
    scale_bits: int,
) -> tuple[str, ...]:
    return tuple(
        _hex_dword(value)
        for value in (
            state.tail_bits,
            state.head_bits,
            state.maximum_length_bits,
            state.width_bits,
            state.current_width_bits,
            state.speed_bits,
            state.warmup_frames,
            state.active_frames,
            state.fade_frames,
            state.collision_enable_frame,
            state.collision_disable_frame,
            state.flags,
            state.phase,
            state.timer,
            state.timer_fraction_bits,
            int(state.active),
            scale_bits,
        )
    )


def _laser_record(probe: Path, case: LaserCase) -> dict[str, object]:
    product_state = _product_laser(case.state)
    oracle_state = case.state
    native_state = case.state
    steps: list[dict[str, object]] = []
    for index, scale_bits in enumerate(case.scale_bits, start=1):
        product = step_laser(
            product_state,
            time_scale_bits=scale_bits,
        )
        product_checks = tuple(
            (int(check.phase), check.graze_enabled)
            for check in product.checks
        )
        product_words = _product_laser_words(
            product.laser,
            product_checks,
        )
        oracle = oracle_step_laser_raw(
            oracle_state,
            time_scale_bits=scale_bits,
        )
        oracle_words = _raw_laser_words(oracle.state, oracle.checks)
        native_words = _probe_words(
            probe,
            "laser",
            *_laser_probe_arguments(native_state, scale_bits),
        )
        passed = product_words == oracle_words == native_words
        steps.append(
            {
                "step": index,
                "time_scale_bits": _hex_dword(scale_bits),
                "product": [_hex_dword(word) for word in product_words],
                "oracle": [_hex_dword(word) for word in oracle_words],
                "native_probe": [_hex_dword(word) for word in native_words],
                "passed": passed,
            }
        )
        product_state = product.laser
        oracle_state = oracle.state
        native_state = RawLaserState(
            tail_bits=native_words[0],
            head_bits=native_words[1],
            maximum_length_bits=native_state.maximum_length_bits,
            width_bits=native_state.width_bits,
            current_width_bits=native_words[2],
            speed_bits=native_state.speed_bits,
            warmup_frames=native_state.warmup_frames,
            active_frames=native_state.active_frames,
            fade_frames=native_state.fade_frames,
            collision_enable_frame=native_state.collision_enable_frame,
            collision_disable_frame=native_state.collision_disable_frame,
            flags=native_state.flags,
            phase=native_words[3],
            timer=(
                native_words[4] - (1 << 32)
                if native_words[4] & 0x80000000
                else native_words[4]
            ),
            timer_fraction_bits=native_words[5],
            active=bool(native_words[6]),
        )
    return {
        "label": case.label,
        "operation": "laser",
        "initial": {
            "tail_bits": _hex_dword(case.state.tail_bits),
            "head_bits": _hex_dword(case.state.head_bits),
            "phase": case.state.phase,
            "timer": case.state.timer,
            "timer_fraction_bits": _hex_dword(
                case.state.timer_fraction_bits
            ),
        },
        "steps": steps,
        "passed": all(bool(step["passed"]) for step in steps),
    }


def _seeded_product_oracle_sweep() -> dict[str, object]:
    """Exercise broad physical-domain values without native subprocess cost."""

    generator = random.Random(0x5CA1E)
    scales = (0.0, 1.0 / 12.0, 0.25, 1.0 / 3.0, 0.5, 0.75, 1.0)
    digest = hashlib.sha256()
    movement_cases = 4096
    laser_cases = 2048
    movement_mismatches = 0
    laser_mismatches = 0

    def retain(words: tuple[int, ...]) -> None:
        for word in words:
            digest.update((word & 0xFFFFFFFF).to_bytes(4, "little"))

    for _ in range(movement_cases):
        x = float32_from_bits(float32_bits(generator.uniform(8.0, 376.0)))
        y = float32_from_bits(float32_bits(generator.uniform(16.0, 432.0)))
        input_mask = generator.randrange(256)
        axis_scale_x = float32_from_bits(
            float32_bits(generator.uniform(0.0, 2.0))
        )
        axis_scale_y = float32_from_bits(
            float32_bits(generator.uniform(0.0, 2.0))
        )
        scale_bits = float32_bits(generator.choice(scales))
        product = step_route2_movement(
            x=x,
            y=y,
            input_mask=input_mask,
            axis_scale_x=axis_scale_x,
            axis_scale_y=axis_scale_y,
            time_scale_bits=scale_bits,
            bounds=_BOUNDS,
        )
        product_words = tuple(
            float32_bits(value)
            for value in (
                product.x,
                product.y,
                product.velocity_x,
                product.velocity_y,
            )
        )
        oracle_words = oracle_step_route2_movement_raw(
            x_bits=float32_bits(x),
            y_bits=float32_bits(y),
            input_mask=input_mask,
            axis_scale_x_bits=float32_bits(axis_scale_x),
            axis_scale_y_bits=float32_bits(axis_scale_y),
            time_scale_bits=scale_bits,
            left_bits=_BOUND_BITS[0],
            top_bits=_BOUND_BITS[1],
            right_bits=_BOUND_BITS[2],
            bottom_bits=_BOUND_BITS[3],
        )
        movement_mismatches += product_words != oracle_words
        retain(
            (
                float32_bits(x),
                float32_bits(y),
                input_mask,
                float32_bits(axis_scale_x),
                float32_bits(axis_scale_y),
                scale_bits,
                *product_words,
                *oracle_words,
            )
        )

    for _ in range(laser_cases):
        phase = generator.randrange(3)
        warmup_frames = generator.randrange(0, 35)
        active_frames = generator.randrange(0, 20)
        fade_frames = generator.randrange(0, 12)
        phase_limit = (warmup_frames, active_frames, fade_frames)[phase]
        timer = generator.randrange(0, max(phase_limit + 3, 3))
        fraction = float32_from_bits(float32_bits(generator.random()))
        product_state = LaserState(
            origin_x=0.0,
            origin_y=0.0,
            angle=0.0,
            tail_distance=float32_from_bits(
                float32_bits(generator.uniform(0.0, 650.0))
            ),
            head_distance=float32_from_bits(
                float32_bits(generator.uniform(0.0, 650.0))
            ),
            maximum_length=float32_from_bits(
                float32_bits(generator.uniform(0.0, 100.0))
            ),
            width=float32_from_bits(
                float32_bits(generator.uniform(0.0, 64.0))
            ),
            speed=float32_from_bits(
                float32_bits(generator.uniform(-20.0, 20.0))
            ),
            warmup_frames=warmup_frames,
            active_frames=active_frames,
            fade_frames=fade_frames,
            collision_enable_frame=generator.randrange(0, 35),
            collision_disable_frame=generator.randrange(0, 12),
            flags=generator.randrange(2),
            current_width=float32_from_bits(
                float32_bits(generator.uniform(0.0, 64.0))
            ),
            phase=LaserPhase(phase),
            timer=timer,
            timer_fraction=fraction,
            active=True,
        )
        oracle_state = RawLaserState(
            tail_bits=float32_bits(product_state.tail_distance),
            head_bits=float32_bits(product_state.head_distance),
            maximum_length_bits=float32_bits(product_state.maximum_length),
            width_bits=float32_bits(product_state.width),
            current_width_bits=float32_bits(product_state.current_width),
            speed_bits=float32_bits(product_state.speed),
            warmup_frames=warmup_frames,
            active_frames=active_frames,
            fade_frames=fade_frames,
            collision_enable_frame=product_state.collision_enable_frame,
            collision_disable_frame=product_state.collision_disable_frame,
            flags=product_state.flags,
            phase=phase,
            timer=timer,
            timer_fraction_bits=float32_bits(fraction),
            active=True,
        )
        scale_bits = float32_bits(generator.choice(scales))
        product = step_laser(
            product_state,
            time_scale_bits=scale_bits,
        )
        oracle = oracle_step_laser_raw(
            oracle_state,
            time_scale_bits=scale_bits,
        )
        product_words = _product_laser_words(
            product.laser,
            tuple(
                (int(check.phase), check.graze_enabled)
                for check in product.checks
            ),
        )
        oracle_words = _raw_laser_words(oracle.state, oracle.checks)
        laser_mismatches += product_words != oracle_words
        retain(
            (
                oracle_state.tail_bits,
                oracle_state.head_bits,
                oracle_state.maximum_length_bits,
                oracle_state.width_bits,
                oracle_state.current_width_bits,
                oracle_state.speed_bits,
                phase,
                timer,
                oracle_state.timer_fraction_bits,
                scale_bits,
                *product_words,
                *oracle_words,
            )
        )

    return {
        "seed": "0x5ca1e",
        "movement_cases": movement_cases,
        "laser_cases": laser_cases,
        "movement_mismatches": movement_mismatches,
        "laser_mismatches": laser_mismatches,
        "sha256": digest.hexdigest(),
        "passed": movement_mismatches == 0 and laser_mismatches == 0,
    }


def build_report(probe: Path) -> dict[str, object]:
    records = [
        *(_movement_record(probe, case) for case in _movement_cases()),
        *(_laser_record(probe, case) for case in _laser_cases()),
    ]
    probe_bytes = probe.read_bytes()
    passed_cases = sum(bool(record["passed"]) for record in records)
    scale_bits = {
        step["time_scale_bits"]
        for record in records
        for step in record["steps"]
    }
    movement_steps = sum(
        len(record["steps"])
        for record in records
        if record["operation"] == "movement"
    )
    laser_steps = sum(
        len(record["steps"])
        for record in records
        if record["operation"] == "laser"
    )
    seeded_sweep = _seeded_product_oracle_sweep()
    return {
        "schema": SCHEMA,
        "semantics_version": TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
        "movement_version": TH08_ROUTE2_MOVEMENT_SCALE_SEMANTICS_VERSION,
        "laser_version": TH08_LASER_SCALE_SEMANTICS_VERSION,
        "oracle_version": ORACLE_SEMANTICS_VERSION,
        "native_probe": {
            "name": probe.name,
            "sha256": hashlib.sha256(probe_bytes).hexdigest(),
            "size": len(probe_bytes),
            "rounding": "FE_TONEAREST",
            "stores": "explicit_x87_fstp_dword",
        },
        "counts": {
            "cases": len(records),
            "passed": passed_cases,
            "failed": len(records) - passed_cases,
            "movement_steps": movement_steps,
            "laser_steps": laser_steps,
            "seeded_product_oracle_cases": (
                seeded_sweep["movement_cases"]
                + seeded_sweep["laser_cases"]
            ),
        },
        "gates": {
            "all_product_oracle_native_bitwise_equal": (
                passed_cases == len(records)
            ),
            "unit_nonunit_stop_present": {
                "0x3f800000",
                "0x3e800000",
                "0x00000000",
            }
            <= scale_bits,
            "one_third_present": _hex_dword(float32_bits(1.0 / 3.0))
            in scale_bits,
            "one_twelfth_present": _hex_dword(float32_bits(1.0 / 12.0))
            in scale_bits,
            "direction_and_focus_change_present": any(
                record["label"] == "one_third_direction_and_focus_changes"
                for record in records
            ),
            "laser_phase_fallthrough_present": {
                "warmup_same_update_active_fallthrough",
                "active_same_update_fade_fallthrough",
            }
            <= {str(record["label"]) for record in records},
            "seeded_product_oracle_zero_mismatch": bool(
                seeded_sweep["passed"]
            ),
        },
        "seeded_product_oracle_sweep": seeded_sweep,
        "cases": records,
        "passed": all(bool(record["passed"]) for record in records),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = build_report(arguments.probe)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if report["passed"] and all(report["gates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
