#!/usr/bin/env python3
"""Game-neutral frame-synchronized input playback protocol.

The platform adapter owns process observation and physical input delivery.
This module owns the fail-closed handshake: prepare frame N+1 immediately
after observing frame N, then require the target to report exactly that input
on the next frame before advancing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InputTransition:
    bit: int
    pressed: bool


@dataclass(frozen=True)
class PlaybackAdvance:
    completed_frame_index: int
    target_counter: int
    transitions: tuple[InputTransition, ...]
    finished: bool


def input_transitions(
    previous_mask: int, target_mask: int, *, supported_mask: int
) -> tuple[InputTransition, ...]:
    previous_mask &= 0xFFFF
    target_mask &= 0xFFFF
    unsupported = (previous_mask | target_mask) & ~supported_mask
    if unsupported:
        raise ValueError(f"unsupported input bits {unsupported:#06x}")
    changed = previous_mask ^ target_mask
    releases = tuple(
        InputTransition(bit, False)
        for bit in _individual_bits(changed & previous_mask)
    )
    presses = tuple(
        InputTransition(bit, True)
        for bit in _individual_bits(changed & target_mask)
    )
    return releases + presses


def _individual_bits(mask: int) -> tuple[int, ...]:
    return tuple(1 << index for index in range(16) if mask & (1 << index))


def load_input_masks(path: Path) -> tuple[int, ...]:
    """Load either a flat mask list or a compact replay ``runs`` artifact."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        masks = tuple(int(value) for value in payload)
    elif isinstance(payload, dict) and "masks" in payload:
        masks = tuple(int(value) for value in payload["masks"])
    elif isinstance(payload, dict) and "runs" in payload:
        frame_count = int(payload["frame_count"])
        expanded = [None] * frame_count
        for run in payload["runs"]:
            start = int(run["start_frame"])
            end = int(run["end_frame_exclusive"])
            mask = int(run["input_mask"])
            if not 0 <= start < end <= frame_count:
                raise ValueError(f"invalid input run [{start}, {end})")
            if any(value is not None for value in expanded[start:end]):
                raise ValueError(f"overlapping input run [{start}, {end})")
            expanded[start:end] = [mask] * (end - start)
        if any(value is None for value in expanded):
            raise ValueError("input runs do not cover the complete frame extent")
        masks = tuple(int(value) for value in expanded)
    else:
        raise ValueError("input trace must be a list, contain masks, or contain runs")
    if any(not 0 <= mask <= 0xFFFF for mask in masks):
        raise ValueError("input masks must fit in 16 bits")
    return masks


class FrameSynchronizedPlayback:
    """One-frame-ahead coordinator with exact counter and input readback."""

    def __init__(self, masks: tuple[int, ...], *, supported_mask: int) -> None:
        if not masks:
            raise ValueError("playback requires at least one input frame")
        if any(mask & ~supported_mask for mask in masks):
            raise ValueError("playback trace contains unsupported input bits")
        self._masks = masks
        self._supported_mask = supported_mask
        self._armed_counter: int | None = None
        self._prepared_index = -1
        self._prepared_mask = 0

    @property
    def prepared_frame_index(self) -> int:
        return self._prepared_index

    def arm(self, observed_counter: int) -> tuple[InputTransition, ...]:
        if self._armed_counter is not None:
            raise RuntimeError("playback is already armed")
        self._armed_counter = observed_counter
        self._prepared_index = 0
        target = self._masks[0]
        transitions = input_transitions(
            0, target, supported_mask=self._supported_mask
        )
        self._prepared_mask = target
        return transitions

    def observe(self, counter: int, observed_mask: int) -> PlaybackAdvance:
        if self._armed_counter is None or self._prepared_index < 0:
            raise RuntimeError("playback is not armed")
        expected_counter = self._armed_counter + self._prepared_index + 1
        if counter != expected_counter:
            raise RuntimeError(
                f"target frame discontinuity: expected {expected_counter}, got {counter}"
            )
        if observed_mask & self._supported_mask != self._prepared_mask:
            raise RuntimeError(
                "target input readback mismatch at trace frame "
                f"{self._prepared_index}: expected {self._prepared_mask:#06x}, "
                f"got {observed_mask & self._supported_mask:#06x}"
            )

        completed = self._prepared_index
        next_index = completed + 1
        if next_index >= len(self._masks):
            transitions = input_transitions(
                self._prepared_mask, 0, supported_mask=self._supported_mask
            )
            return PlaybackAdvance(completed, counter, transitions, True)

        next_mask = self._masks[next_index]
        transitions = input_transitions(
            self._prepared_mask,
            next_mask,
            supported_mask=self._supported_mask,
        )
        self._prepared_index = next_index
        self._prepared_mask = next_mask
        return PlaybackAdvance(completed, counter, transitions, False)
