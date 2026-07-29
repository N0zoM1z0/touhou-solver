"""Replay retained raw-state batches through epoch-safe delivery transports."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from analysis.auxiliary_ecl_event.physical_gate_support import (
    distribution,
    trace_event_rows,
    within,
)
from analysis.auxiliary_ecl_event.cache_oracle import IndependentIntentLru
from analysis.auxiliary_ecl_event.physical_replay import (
    ReplayProgram,
    audit_event_batch_v4,
)
from analysis.auxiliary_ecl_event.physical_replay_v5 import (
    audit_event_batch_v5,
)
from th08_ecl_tool.core import parse_ecl
from th08_live.auxiliary_vm.event_service import (
    AuxiliaryEclEventConfiguration,
    AuxiliaryEclEventTraceService,
)
from th08_live.auxiliary_vm.columnar_projection import (
    REQUEST_COLUMNS,
    REQUEST_PROJECTION_SCHEMA,
    compact_usable_observation,
)
from th08_live.auxiliary_vm.model import (
    AUXILIARY_VM_BATCH_LAYOUT_V2,
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    BatchStatus,
    RecordStatus,
)
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion


EVENT_DERIVE_LIMIT_MS = (0.50, 1.00, 3.00)
REPLAY_COMPACT_LIMIT_MS = (0.50, 1.00, 3.00)
SERIALIZE_LIMIT_MS = (0.25, 0.50, 1.50)
PREPARATION_MAXIMUM_MS = 1.0
PROJECTED_LINE_MAXIMUM = 24576


def _integer(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} is not an integer")
    return value


def _optional_integer(value: object, context: str) -> int | None:
    return None if value is None else _integer(value, context)


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} is not an object")
    return value


def _array(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{context} is not an array")
    return value


def _raw_hex(
    value: object,
    *,
    expected_sha256: object,
    context: str,
) -> bytes:
    if not isinstance(value, str):
        raise ValueError(f"{context} raw state is absent")
    try:
        raw = bytes.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{context} raw state is invalid hex") from error
    if (
        len(raw) != 0x228
        or not isinstance(expected_sha256, str)
        or hashlib.sha256(raw).hexdigest() != expected_sha256
    ):
        raise ValueError(f"{context} raw state differs from its hash")
    return raw


def _version(row: dict[str, Any]) -> RuntimeEclAcceptedVersion:
    event = _mapping(row.get("event_derivation"), "event")
    version = _mapping(event.get("runtime_version"), "runtime_version")
    return RuntimeEclAcceptedVersion(
        runtime_base=_integer(version.get("runtime_base"), "runtime_base"),
        image_length=_integer(version.get("image_length"), "image_length"),
        relocated_sha256=str(version.get("relocated_sha256")),
        normalized_sha256=str(version.get("normalized_sha256")),
        static_sha256=str(version.get("static_sha256")),
        route_id=_integer(version.get("route_id"), "route_id"),
        difficulty_index=_integer(
            version.get("difficulty_index"),
            "difficulty_index",
        ),
        stage_route_index=_integer(
            version.get("stage_route_index"),
            "stage_route_index",
        ),
        gameplay_epoch=_integer(
            version.get("gameplay_epoch"),
            "gameplay_epoch",
        ),
        decision_frame=_integer(
            version.get("decision_frame"),
            "decision_frame",
        ),
        snapshot_frame=_integer(
            version.get("snapshot_frame"),
            "snapshot_frame",
        ),
    )


def _observation(
    row: dict[str, Any],
    *,
    context: str,
) -> AuxiliaryVmBatchObservation:
    compact = _mapping(row.get("observation"), f"{context}.observation")
    records: list[AuxiliaryVmBatchRecord] = []
    for index, raw_record in enumerate(
        _array(compact.get("records"), f"{context}.records")
    ):
        record = _mapping(raw_record, f"{context}.records[{index}]")
        active_vm = (
            b""
            if record.get("active_vm_hex") is None
            else _raw_hex(
                record.get("active_vm_hex"),
                expected_sha256=record.get("active_vm_sha256"),
                context=f"{context}.records[{index}].active_vm",
            )
        )
        saved_hex = _array(
            record.get("saved_frame_hex"),
            f"{context}.records[{index}].saved_frame_hex",
        )
        saved_hashes = _array(
            record.get("saved_frame_sha256"),
            f"{context}.records[{index}].saved_frame_sha256",
        )
        if len(saved_hex) != len(saved_hashes):
            raise ValueError(f"{context} saved-frame mapping differs")
        saved_frames = tuple(
            _raw_hex(
                value,
                expected_sha256=saved_hashes[saved_index],
                context=(
                    f"{context}.records[{index}]"
                    f".saved_frames[{saved_index}]"
                ),
            )
            for saved_index, value in enumerate(saved_hex)
        )
        records.append(
            AuxiliaryVmBatchRecord(
                slot=_integer(record.get("slot"), f"{context}.slot"),
                auxiliary_index=_integer(
                    record.get("auxiliary_index"),
                    f"{context}.auxiliary_index",
                ),
                enemy_pointer=_integer(
                    record.get("enemy_pointer"),
                    f"{context}.enemy_pointer",
                ),
                context_pointer=_integer(
                    record.get("context_pointer"),
                    f"{context}.context_pointer",
                ),
                context_pointer_after=_integer(
                    record.get("context_pointer_after"),
                    f"{context}.context_pointer_after",
                ),
                enemy_flags_before=_integer(
                    record.get("enemy_flags_before"),
                    f"{context}.enemy_flags_before",
                ),
                enemy_flags_after=_integer(
                    record.get("enemy_flags_after"),
                    f"{context}.enemy_flags_after",
                ),
                status=RecordStatus(
                    _integer(
                        record.get("status_bits"),
                        f"{context}.status_bits",
                    )
                ),
                target_subroutine=_optional_integer(
                    record.get("target_subroutine"),
                    f"{context}.target_subroutine",
                ),
                call_depth=_optional_integer(
                    record.get("call_depth"),
                    f"{context}.call_depth",
                ),
                auxiliary_marker=_optional_integer(
                    record.get("auxiliary_marker"),
                    f"{context}.auxiliary_marker",
                ),
                active_vm=active_vm,
                saved_frames=saved_frames,
            )
        )
    return AuxiliaryVmBatchObservation(
        expected_manager_frame=_integer(
            compact.get("selected_manager_frame"),
            f"{context}.selected_manager_frame",
        ),
        manager_frame_before=_integer(
            compact.get("context_manager_frame_before"),
            f"{context}.context_manager_frame_before",
        ),
        manager_frame_after=_integer(
            compact.get("manager_frame_after"),
            f"{context}.manager_frame_after",
        ),
        batch_status=BatchStatus(
            _integer(
                compact.get("batch_status_bits"),
                f"{context}.batch_status_bits",
            )
        ),
        records=tuple(records),
        process_read_count=_integer(
            compact.get("process_read_count"),
            f"{context}.process_read_count",
        ),
        state_payload_bytes=_integer(
            compact.get("state_payload_bytes"),
            f"{context}.state_payload_bytes",
        ),
        layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
        owner_manager_frame_after=_integer(
            compact.get("owner_manager_frame_after"),
            f"{context}.owner_manager_frame_after",
        ),
        owner_blob_bytes=_integer(
            compact.get("owner_blob_bytes"),
            f"{context}.owner_blob_bytes",
        ),
    )


def _legacy_event_v4(event: dict[str, object]) -> dict[str, object]:
    projection = _mapping(
        event.get("request_projection"),
        "event.request_projection",
    )
    if (
        projection.get("schema") != REQUEST_PROJECTION_SCHEMA
        or projection.get("columns") != list(REQUEST_COLUMNS)
    ):
        raise ValueError("V5 request projection is invalid")
    rows = _array(projection.get("rows"), "event.request_projection.rows")
    legacy = dict(event)
    legacy["schema"] = "th08-auxiliary-ecl-event-derivation-v4"
    legacy["request_projection"] = [
        dict(zip(REQUEST_COLUMNS, _array(row, "request_projection.row")))
        for row in rows
    ]
    return legacy


def _benchmark_runtime_delivery(
    trace_path: Path,
    static_path: Path,
    *,
    expected_static_sha256: str,
    repeats: int,
    transport_version: int,
) -> dict[str, object]:
    if transport_version not in (4, 5):
        raise ValueError("runtime delivery transport version is invalid")
    if repeats <= 0:
        raise ValueError("runtime delivery repeats must be positive")
    rows, trace_sha256, trace_bytes = trace_event_rows(trace_path)
    if not rows:
        raise ValueError("source trace has no auxiliary event rows")
    version = _version(rows[0])
    if any(_version(row) != version for row in rows):
        raise ValueError("source rows do not share one immutable version")
    observations = tuple(
        _observation(row, context=f"batch[{index}]")
        for index, row in enumerate(rows)
    )
    image = static_path.read_bytes()
    program = ReplayProgram.from_ecl(
        parse_ecl(static_path),
        image,
        runtime_base=version.runtime_base,
    )
    shells = tuple(
        {
            key: value
            for key, value in row.items()
            if key not in {"observation", "event_derivation", "timing_ms"}
        }
        for row in rows
    )
    derive_ms: list[float] = []
    compact_ms: list[float] = []
    serialize_ms: list[float] = []
    static_prevalidation_ms: list[float] = []
    preparation_ms: list[float] = []
    status_counts: Counter[str] = Counter()
    observation_epochs: Counter[int] = Counter()
    first_cache_totals: Counter[str] = Counter()
    serialized_bytes: list[int] = []
    epoch_provenance_valid = True
    preparation_shape_valid = True
    independent_cache_parity = True
    replay_counts: Counter[str] = Counter()
    first_target_counts: Counter[int] = Counter()
    for repeat in range(repeats):
        independent_cache = IndependentIntentLru(512)
        started = time.perf_counter()
        service = AuxiliaryEclEventTraceService(
            AuxiliaryEclEventConfiguration(
                static_path=static_path,
                expected_static_sha256=expected_static_sha256,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
        )
        static_prevalidation_ms.append(
            (time.perf_counter() - started) * 1000.0
        )
        preparation = service.prepare_if_needed(
            version,
            gameplay_epoch=version.gameplay_epoch,
            stage_route_index=version.stage_route_index,
            decision_frame=version.decision_frame,
            snapshot_frame=version.snapshot_frame,
        )
        if preparation is None or preparation["status"] != "success":
            raise ValueError(
                f"V{transport_version} runtime preparation failed"
            )
        preparation_timing = _mapping(
            preparation.get("timing_ms"),
            "preparation.timing_ms",
        )
        preparation_ms.append(float(preparation_timing["total"]))
        preparation_shape_valid = bool(
            preparation_shape_valid
            and preparation.get("prevalidated_instruction_count") == 1664
            and preparation.get("bound_instruction_count") == 9
            and preparation.get("accepted_gameplay_epoch")
            == version.gameplay_epoch
            and preparation.get("observation_gameplay_epoch")
            == version.gameplay_epoch
        )
        for index, (observation, shell) in enumerate(
            zip(observations, shells)
        ):
            observation_epoch = (
                version.gameplay_epoch
                + 1
                + min(2, (index * 3) // len(observations))
            )
            if repeat == 0:
                observation_epochs[observation_epoch] += 1
            started = time.perf_counter()
            event = service.derive(
                observation,
                runtime_version=version,
                gameplay_epoch=observation_epoch,
                stage_route_index=version.stage_route_index,
            )
            derive_ms.append((time.perf_counter() - started) * 1000.0)
            status_counts[str(event["status"])] += 1
            epoch_provenance_valid = bool(
                epoch_provenance_valid
                and event.get("accepted_gameplay_epoch")
                == version.gameplay_epoch
                and event.get("observation_gameplay_epoch")
                == observation_epoch
                and event.get("observation_epoch_semantics")
                == "provenance_not_program_mutation"
            )
            cache = _mapping(event.get("cache"), f"batch[{index}].cache")
            if repeat == 0:
                first_cache_totals.update(
                    {
                        "request_local_hits": int(
                            cache["request_local_hits"]
                        ),
                        "persistent_hits": int(cache["persistent_hits"]),
                        "misses": int(cache["misses"]),
                        "evictions": int(cache["evictions"]),
                    }
                )
            started = time.perf_counter()
            compact = (
                compact_usable_observation(observation)
                if transport_version == 5
                else observation.compact_record(
                    include_replay_bundle=True,
                    usable_projection=True,
                )
            )
            compact_ms.append((time.perf_counter() - started) * 1000.0)
            output_row = {
                **shell,
                "schema_version": 8 if transport_version == 5 else 7,
                "gameplay_epoch": observation_epoch,
                "observation": compact,
                "event_derivation": (
                    event
                    if transport_version == 5
                    else _legacy_event_v4(event)
                ),
            }
            replay = (
                audit_event_batch_v5
                if transport_version == 5
                else audit_event_batch_v4
            )(
                output_row,
                expected_runtime_version=version.record(),
                program=program,
                context=f"repeat[{repeat}].batch[{index}]",
            )
            expected_cache = independent_cache.observe(
                replay.intent_keys
            ).record()
            independent_cache_parity = bool(
                independent_cache_parity
                and event.get("cache") == expected_cache
            )
            replay_counts.update(
                {
                    "request_count": replay.request_count,
                    "lowerable_count": replay.lowerable_count,
                    "complete_count": replay.complete_count,
                    "unknown_count": replay.unknown_count,
                    "replayable_record_count": (
                        replay.replayable_record_count
                    ),
                }
            )
            if repeat == 0:
                first_target_counts.update(dict(replay.target_counts))
            started = time.perf_counter()
            encoded = json.dumps(
                output_row,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            serialize_ms.append((time.perf_counter() - started) * 1000.0)
            if repeat == 0:
                serialized_bytes.append(
                    len(encoded.encode("utf-8")) + 1
                )
    derive_distribution = distribution(derive_ms)
    compact_distribution = distribution(compact_ms)
    serialize_distribution = distribution(serialize_ms)
    preparation_distribution = distribution(preparation_ms)
    report: dict[str, object] = {
        "schema": (
            "th08-auxiliary-ecl-event-"
            f"v{transport_version}-replay-benchmark-v1"
        ),
        "authority": "isolated_replay_not_physical_delivery_authority",
        "source": {
            "trace": str(trace_path),
            "trace_bytes": trace_bytes,
            "trace_sha256": trace_sha256,
            "static_image": str(static_path),
            "static_sha256": expected_static_sha256,
        },
        "workload": {
            "batch_count": len(rows),
            "repeats": repeats,
            "sample_count": len(rows) * repeats,
            "status_counts": dict(sorted(status_counts.items())),
            "accepted_gameplay_epoch": version.gameplay_epoch,
            "observation_gameplay_epochs_first_repeat": {
                str(key): value
                for key, value in sorted(observation_epochs.items())
            },
            "serialized_bytes_first_repeat": {
                "total": sum(serialized_bytes),
                "minimum": min(serialized_bytes),
                "maximum": max(serialized_bytes),
            },
        },
        "static_prevalidation_ms": distribution(static_prevalidation_ms),
        "preparation_ms": preparation_distribution,
        "cache_first_repeat": dict(sorted(first_cache_totals.items())),
        "independent_replay": {
            **dict(sorted(replay_counts.items())),
            "target_counts_first_repeat": {
                str(key): value
                for key, value in sorted(first_target_counts.items())
            },
        },
        "timing_ms": {
            "event_derive": derive_distribution,
            "replay_compact": compact_distribution,
            "json_serialize_without_write": serialize_distribution,
        },
        "limits_ms": {
            "preparation_maximum": PREPARATION_MAXIMUM_MS,
            "event_derive_p95_p99_max": list(EVENT_DERIVE_LIMIT_MS),
            "replay_compact_p95_p99_max": list(
                REPLAY_COMPACT_LIMIT_MS
            ),
            "json_serialize_p95_p99_max": list(SERIALIZE_LIMIT_MS),
        },
        "limits_bytes": {
            "projected_json_line_maximum": PROJECTED_LINE_MAXIMUM,
        },
        "gates": {
            "all_rows_classified": bool(
                sum(status_counts.values()) == len(rows) * repeats
                and set(status_counts).issubset(
                    {"success", "empty_complete"}
                )
            ),
            "target_closure_prevalidated_and_bound": (
                preparation_shape_valid
            ),
            "cross_epoch_program_reuse": bool(
                epoch_provenance_valid
                and len(observation_epochs) == 3
                and all(
                    epoch != version.gameplay_epoch
                    for epoch in observation_epochs
                )
            ),
            "preparation_timing": bool(
                preparation_distribution is not None
                and preparation_distribution["max"]
                <= PREPARATION_MAXIMUM_MS
            ),
            "exact_cache_workload": bool(
                first_cache_totals["misses"] == 46
                and first_cache_totals["persistent_hits"] > 0
                and first_cache_totals["evictions"] == 0
            ),
            "independent_oracle_parity": bool(
                replay_counts["request_count"]
                == 3830 * repeats
                and replay_counts["request_count"]
                == replay_counts["lowerable_count"]
                == replay_counts["complete_count"]
                == replay_counts["replayable_record_count"]
                and replay_counts["unknown_count"] == 0
            ),
            "independent_cache_parity": independent_cache_parity,
            "event_derive_timing": within(
                derive_distribution,
                EVENT_DERIVE_LIMIT_MS,
            ),
            "replay_compact_timing": within(
                compact_distribution,
                REPLAY_COMPACT_LIMIT_MS,
            ),
            "json_serialize_timing": within(
                serialize_distribution,
                SERIALIZE_LIMIT_MS,
            ),
            "projected_json_line_size": bool(
                serialized_bytes
                and max(serialized_bytes) <= PROJECTED_LINE_MAXIMUM
            ),
        },
    }
    gates = report["gates"]
    assert isinstance(gates, dict)
    report["passed"] = all(gates.values())
    return report


def benchmark_runtime_delivery_v4(
    trace_path: Path,
    static_path: Path,
    *,
    expected_static_sha256: str,
    repeats: int,
) -> dict[str, object]:
    return _benchmark_runtime_delivery(
        trace_path,
        static_path,
        expected_static_sha256=expected_static_sha256,
        repeats=repeats,
        transport_version=4,
    )


def benchmark_runtime_delivery_v5(
    trace_path: Path,
    static_path: Path,
    *,
    expected_static_sha256: str,
    repeats: int,
) -> dict[str, object]:
    return _benchmark_runtime_delivery(
        trace_path,
        static_path,
        expected_static_sha256=expected_static_sha256,
        repeats=repeats,
        transport_version=5,
    )


def benchmark_runtime_delivery(
    trace_path: Path,
    static_path: Path,
    *,
    expected_static_sha256: str,
    repeats: int,
) -> dict[str, object]:
    """Compatibility alias for the current retained-trace benchmark."""

    return benchmark_runtime_delivery_v5(
        trace_path,
        static_path,
        expected_static_sha256=expected_static_sha256,
        repeats=repeats,
    )


def benchmark_runtime_delivery_v3(
    trace_path: Path,
    static_path: Path,
    *,
    expected_static_sha256: str,
    repeats: int,
) -> dict[str, object]:
    """Deprecated command alias; emits the current V4 benchmark schema."""

    return benchmark_runtime_delivery_v4(
        trace_path,
        static_path,
        expected_static_sha256=expected_static_sha256,
        repeats=repeats,
    )


__all__ = [
    "benchmark_runtime_delivery",
    "benchmark_runtime_delivery_v3",
    "benchmark_runtime_delivery_v4",
    "benchmark_runtime_delivery_v5",
]
