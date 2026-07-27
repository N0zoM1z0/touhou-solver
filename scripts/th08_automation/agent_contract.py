"""Pure launch arguments and terminal-summary contracts for TH08 agents."""

from __future__ import annotations

import json
import os
from pathlib import Path


LONG_RUN_DURATION_SECONDS = 3600


def one_shot_trial_finished(*, agent_started: bool, agent_alive: bool) -> bool:
    """Return whether a one-shot daemon must exit before another arm."""

    return agent_started and not agent_alive


def read_runtime_summary(path: Path) -> dict[str, object]:
    """Read the terminal in-trace summary without decoding a long raw trace."""

    with path.open("rb") as source:
        source.seek(0, os.SEEK_END)
        end = source.tell()
        source.seek(max(0, end - 64 * 1024))
        tail = source.read()
    for binary_line in reversed(tail.splitlines()):
        try:
            row = json.loads(binary_line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if row.get("kind") == "summary":
            return {
                "decision_count": None,
                "first_frame": None,
                "last_frame": row.get("last_frame"),
                "termination_reason": row.get(
                    "termination_reason",
                    "missing_summary",
                ),
                "counter_gaps": row.get("counter_gaps"),
                "hit_count": row.get("hit_count"),
                "hit_frames": [],
            }
    raise ValueError("trial contains no terminal summary record")


def build_long_run_arguments(
    *,
    output: Path,
    stop_file: Path,
    pid: int,
    difficulty: int,
    expected_stage: int | None = None,
    terminal_stage: int | None = None,
    trace_transform_runtime: bool = False,
    trace_bullet_births: bool = False,
    safety_value_horizon: int = 0,
    viability_audit_dir: Path | None = None,
    postpublished_survival_shadow: bool = False,
    pipeline_prewarm_shadow: bool = False,
    candidate_verifier_shadow: bool = False,
    input_clock_boundary_shadow: bool = False,
    input_clock_shadow_sample_ms: float = 1.0,
    local_pipeline_root_shadow_every: int = 0,
    local_hazard_backend: str = "native",
    local_beam_reducer: str = "native",
    bullet_decode_backend: str = "native",
    duration_seconds: float = LONG_RUN_DURATION_SECONDS,
) -> list[str]:
    if safety_value_horizon < 0:
        raise ValueError("safety-value horizon cannot be negative")
    if duration_seconds <= 0.0:
        raise ValueError("long-run duration must be positive")
    if input_clock_shadow_sample_ms <= 0.0:
        raise ValueError("input-clock shadow sample cadence must be positive")
    if local_pipeline_root_shadow_every < 0:
        raise ValueError(
            "local pipeline root shadow cadence cannot be negative"
        )
    if local_hazard_backend not in {"numpy", "native"}:
        raise ValueError("unknown local hazard backend")
    if local_beam_reducer not in {"python", "native"}:
        raise ValueError("unknown local beam reducer")
    if bullet_decode_backend not in {"python", "native"}:
        raise ValueError("unknown bullet decode backend")
    arguments = [
        str(output),
        "--pid",
        str(pid),
        "--duration",
        str(duration_seconds),
        "--difficulty",
        str(difficulty),
        "--stop-after-hits",
        "0",
        "--post-hit-frames",
        "0",
        "--log-every",
        "1",
        "--trace-radius",
        "160",
        "--auto-confirm-every",
        "15",
        "--auto-confirm-idle-frames",
        "20",
        "--no-bomb",
        "--stop-file",
        str(stop_file),
        "--armed",
    ]
    if expected_stage is not None:
        arguments.extend(("--expected-stage", str(expected_stage)))
    if terminal_stage is not None:
        arguments.extend(("--terminal-stage", str(terminal_stage)))
    if trace_transform_runtime:
        arguments.append("--trace-transform-runtime")
    if trace_bullet_births:
        arguments.append("--trace-bullet-births")
    if safety_value_horizon:
        arguments.extend(
            ("--safety-value-horizon", str(safety_value_horizon))
        )
    if viability_audit_dir is not None:
        arguments.extend(
            ("--viability-audit-dir", str(viability_audit_dir))
        )
    if postpublished_survival_shadow:
        arguments.append("--postpublished-survival-shadow")
    if pipeline_prewarm_shadow:
        arguments.append("--pipeline-prewarm-shadow")
    if candidate_verifier_shadow:
        arguments.append("--candidate-verifier-shadow")
    if input_clock_boundary_shadow:
        arguments.extend(
            (
                "--input-clock-boundary-shadow",
                "--input-clock-shadow-sample-ms",
                str(input_clock_shadow_sample_ms),
            )
        )
    if local_pipeline_root_shadow_every:
        arguments.extend(
            (
                "--local-pipeline-root-shadow-every",
                str(local_pipeline_root_shadow_every),
            )
        )
    arguments.extend(("--local-hazard-backend", local_hazard_backend))
    arguments.extend(("--local-beam-reducer", local_beam_reducer))
    arguments.extend(("--bullet-decode-backend", bullet_decode_backend))
    return arguments
