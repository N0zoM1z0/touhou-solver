"""Narrow physical input dispatch boundary for the TH08 live controller."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from runtime_agent import InputTransition, input_transitions
from th08_runtime_agent import _require_foreground, send_transitions


@dataclass(frozen=True)
class InputDispatch:
    previous_mask: int
    target_mask: int
    transitions: tuple[InputTransition, ...]
    input_ms: float


class IssueController:
    """Validate masks and send one ordered input transition transaction."""

    def __init__(
        self,
        *,
        api: Any,
        pid: int,
        supported_mask: int,
        forbidden_mask: int = 0,
        transition_builder: Callable[..., tuple[InputTransition, ...]] = (
            input_transitions
        ),
        transition_sender: Callable[
            [Any, tuple[InputTransition, ...]], None
        ] = send_transitions,
        foreground_guard: Callable[[Any, int], None] = (
            _require_foreground
        ),
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._api = api
        self._pid = pid
        self._supported_mask = supported_mask
        self._forbidden_mask = forbidden_mask
        self._transition_builder = transition_builder
        self._transition_sender = transition_sender
        self._foreground_guard = foreground_guard
        self._clock = clock

    def dispatch(
        self,
        previous_mask: int,
        target_mask: int,
        *,
        require_foreground: bool = False,
    ) -> InputDispatch:
        forbidden = target_mask & self._forbidden_mask
        if forbidden:
            raise RuntimeError("no-bomb policy produced a Bomb input")
        if require_foreground:
            self._foreground_guard(self._api, self._pid)
        transitions = self._transition_builder(
            previous_mask,
            target_mask,
            supported_mask=self._supported_mask,
        )
        started = self._clock()
        self._transition_sender(self._api, transitions)
        input_ms = (self._clock() - started) * 1000.0
        return InputDispatch(
            previous_mask=previous_mask,
            target_mask=target_mask,
            transitions=transitions,
            input_ms=input_ms,
        )


__all__ = ["InputDispatch", "IssueController"]
