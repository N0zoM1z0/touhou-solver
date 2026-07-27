"""Synchronous JSONL publication boundary for live trace records."""

from __future__ import annotations

import json
import time
from typing import Callable, Iterable, TextIO


class TraceSink:
    """Serialize and synchronously publish exact live JSONL records."""

    def __init__(
        self,
        output: TextIO,
        *,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._output = output
        self._clock = clock

    def emit(
        self,
        record: dict[str, object],
        *,
        flush: bool = False,
        measure: bool = False,
    ) -> float:
        started = self._clock() if measure else 0.0
        self._output.write(json.dumps(record) + "\n")
        if flush:
            self._output.flush()
        return (
            (self._clock() - started) * 1000.0
            if measure
            else 0.0
        )

    def emit_many(
        self,
        records: Iterable[dict[str, object]],
        *,
        flush: bool = False,
        measure: bool = False,
    ) -> float:
        started = self._clock() if measure else 0.0
        for record in records:
            self._output.write(json.dumps(record) + "\n")
        if flush:
            self._output.flush()
        return (
            (self._clock() - started) * 1000.0
            if measure
            else 0.0
        )

    def summary(
        self,
        *,
        last_frame: int | None,
        counter_gaps: int,
        hit_count: int,
        termination_reason: str,
    ) -> float:
        return self.emit(
            {
                "kind": "summary",
                "last_frame": last_frame,
                "counter_gaps": counter_gaps,
                "hit_count": hit_count,
                "termination_reason": termination_reason,
            },
            flush=True,
        )

    def runtime_error(
        self,
        error: BaseException,
        *,
        last_frame: int | None,
    ) -> float:
        return self.emit(
            {
                "kind": "runtime_error",
                "error_type": type(error).__name__,
                "error": str(error),
                "last_frame": last_frame,
            }
        )


__all__ = ["TraceSink"]
