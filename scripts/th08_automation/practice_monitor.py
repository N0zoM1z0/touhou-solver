"""Bounded trace-tail monitoring for supervised TH08 practice trials."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from th08_agent_hotkey import AgentHotkey


def read_last_json_record(path: Path) -> dict[str, object] | None:
    if not path.is_file() or path.stat().st_size == 0:
        return None
    with path.open("rb") as source:
        source.seek(0, os.SEEK_END)
        position = source.tell()
        suffix = b""
        while position > 0:
            size = min(64 * 1024, position)
            position -= size
            source.seek(position)
            suffix = source.read(size) + suffix
            lines = [line for line in suffix.splitlines() if line.strip()]
            if len(lines) >= 2 or position == 0:
                for line in reversed(lines):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
                return None
    return None


def progress_text(record: dict[str, object] | None) -> str:
    if not record:
        return "waiting for trace output"
    spell_id = record.get("spell_id")
    spell = record.get("spell")
    if (
        spell_id is None
        and isinstance(spell, dict)
        and spell.get("active")
    ):
        spell_id = spell.get("spell_id")
    return (
        f"kind={record.get('kind')} frame={record.get('frame')} "
        f"stage={record.get('stage_route_index')} "
        f"spell={spell_id} hits={record.get('hit_count')} "
        f"bullets={record.get('active_bullets')} "
        f"lasers={record.get('active_lasers')}"
    )


def monitor_trial(
    agent: AgentHotkey,
    *,
    trace: Path,
    timeout_seconds: float,
    status_seconds: float,
    stall_timeout_seconds: float,
) -> Path:
    if agent.agent_thread is None:
        raise RuntimeError("agent was not started")
    deadline = time.perf_counter() + timeout_seconds
    last_trace_mtime = 0
    last_progress_at = time.perf_counter()
    while agent.agent_thread.is_alive():
        if trace.is_file():
            trace_mtime = trace.stat().st_mtime_ns
            if trace_mtime != last_trace_mtime:
                last_trace_mtime = trace_mtime
                last_progress_at = time.perf_counter()
        if time.perf_counter() - last_progress_at >= stall_timeout_seconds:
            agent.stop()
            agent.agent_thread.join(timeout=15.0)
            raise TimeoutError(
                "unattended practice trace made no progress for "
                f"{stall_timeout_seconds:.1f} seconds"
            )
        remaining = deadline - time.perf_counter()
        if remaining <= 0.0:
            agent.stop()
            agent.agent_thread.join(timeout=15.0)
            raise TimeoutError("unattended practice trial exceeded its timeout")
        agent.agent_thread.join(timeout=min(status_seconds, remaining))
        print(
            "trial status:",
            progress_text(read_last_json_record(trace)),
            flush=True,
        )
    return agent.wait_for_trial()


def accepted_practice_termination(
    summary: dict[str, object] | None,
) -> bool:
    return (
        isinstance(summary, dict)
        and summary.get("termination_reason") == "route_complete"
    )
