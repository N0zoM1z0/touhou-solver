"""Pure launch arguments and terminal-summary contracts for TH08 agents."""

from __future__ import annotations

import json
import os
from pathlib import Path

from th08_live.bullet_birth_native import (
    NATIVE_CALL_MODES,
    NATIVE_CALL_MODE_GIL_HELD,
    NATIVE_CALL_MODE_GIL_RELEASED,
)


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
    trace_derived_pattern_sources: bool = False,
    trace_nonspell_main_vms: bool = False,
    trace_enemy_combat_progress: bool = False,
    trace_auxiliary_vm_batches: bool = False,
    trace_auxiliary_ecl_events: bool = False,
    auxiliary_vm_batch_every: int = 16,
    auxiliary_vm_batch_spell_id: int | None = None,
    auxiliary_vm_native_call_mode: str = NATIVE_CALL_MODE_GIL_HELD,
    runtime_ecl_static_image: Path | None = None,
    runtime_ecl_static_sha256: str | None = None,
    enable_finalb_scale_source_authority: bool = False,
    bullet_birth_backend: str = "python",
    bullet_birth_native_call_mode: str = NATIVE_CALL_MODE_GIL_RELEASED,
    safety_value_horizon: int = 0,
    viability_audit_dir: Path | None = None,
    postpublished_survival_shadow: bool = False,
    pipeline_prewarm_shadow: bool = False,
    candidate_verifier_shadow: bool = False,
    corridor_background_low_priority: bool = False,
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
    if bullet_birth_backend not in {"python", "native"}:
        raise ValueError("unknown bullet birth backend")
    if bullet_birth_native_call_mode not in NATIVE_CALL_MODES:
        raise ValueError("unknown native bullet birth call mode")
    if auxiliary_vm_native_call_mode not in NATIVE_CALL_MODES:
        raise ValueError("unknown native auxiliary-VM call mode")
    if auxiliary_vm_batch_every <= 0:
        raise ValueError("auxiliary-VM batch cadence must be positive")
    if (
        auxiliary_vm_batch_spell_id is not None
        and auxiliary_vm_batch_spell_id < 0
    ):
        raise ValueError("auxiliary-VM spell filter cannot be negative")
    if (runtime_ecl_static_image is None) != (
        runtime_ecl_static_sha256 is None
    ):
        raise ValueError(
            "runtime ECL identity requires both a static image and SHA-256"
        )
    if runtime_ecl_static_image is not None and expected_stage is None:
        raise ValueError(
            "runtime ECL identity requires an explicit expected stage"
        )
    if enable_finalb_scale_source_authority and (
        difficulty != 3 or expected_stage != 7
    ):
        raise ValueError(
            "Final-B scale-source authority requires Lunatic stage 7"
        )
    if enable_finalb_scale_source_authority and (
        runtime_ecl_static_image is None
        or runtime_ecl_static_sha256 is None
    ):
        raise ValueError(
            "Final-B scale-source authority requires exact runtime ECL identity"
        )
    if trace_auxiliary_ecl_events and not trace_auxiliary_vm_batches:
        raise ValueError(
            "auxiliary ECL event tracing requires auxiliary-VM batch tracing"
        )
    if trace_auxiliary_ecl_events and runtime_ecl_static_image is None:
        raise ValueError(
            "auxiliary ECL event tracing requires exact runtime ECL identity"
        )
    if trace_auxiliary_ecl_events and (
        difficulty != 3 or expected_stage != 5
    ):
        raise ValueError(
            "the contracted auxiliary ECL event service is limited to "
            "Lunatic Stage 5"
        )
    if trace_derived_pattern_sources and not trace_bullet_births:
        raise ValueError(
            "derived-pattern source tracing requires bullet-birth tracing"
        )
    if trace_nonspell_main_vms and not trace_bullet_births:
        raise ValueError(
            "nonspell main-VM tracing requires bullet-birth tracing"
        )
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
        arguments.extend(
            (
                "--trace-bullet-births",
                "--bullet-birth-backend",
                bullet_birth_backend,
                "--bullet-birth-native-call-mode",
                bullet_birth_native_call_mode,
            )
        )
    if trace_derived_pattern_sources:
        arguments.append("--trace-derived-pattern-sources")
    if trace_nonspell_main_vms:
        arguments.append("--trace-nonspell-main-vms")
    if trace_enemy_combat_progress:
        arguments.append("--trace-enemy-combat-progress")
    if trace_auxiliary_vm_batches:
        arguments.extend(
            (
                "--trace-auxiliary-vm-batches",
                "--auxiliary-vm-batch-every",
                str(auxiliary_vm_batch_every),
                "--auxiliary-vm-native-call-mode",
                auxiliary_vm_native_call_mode,
            )
        )
        if trace_auxiliary_ecl_events:
            arguments.append("--trace-auxiliary-ecl-events")
        if auxiliary_vm_batch_spell_id is not None:
            arguments.extend(
                (
                    "--auxiliary-vm-batch-spell-id",
                    str(auxiliary_vm_batch_spell_id),
                )
            )
    if runtime_ecl_static_image is not None:
        arguments.extend(
            (
                "--runtime-ecl-static-image",
                str(runtime_ecl_static_image),
                "--runtime-ecl-static-sha256",
                str(runtime_ecl_static_sha256),
            )
        )
    if enable_finalb_scale_source_authority:
        arguments.append("--enable-finalb-scale-source-authority")
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
    if corridor_background_low_priority:
        arguments.append("--corridor-background-low-priority")
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
