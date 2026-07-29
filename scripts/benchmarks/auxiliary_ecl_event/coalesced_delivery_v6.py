"""Retained-trace packing and independent replay gate for V6 delivery."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from analysis.auxiliary_ecl_event.cache_oracle import IndependentIntentLru
from analysis.auxiliary_ecl_event.coalesced_replay_v6 import (
    decode_coalesced_batch,
)
from analysis.auxiliary_ecl_event.physical_gate_support import (
    distribution,
    expected_runtime_version,
    trace_event_rows,
    within,
)
from analysis.auxiliary_ecl_event.physical_replay import ReplayProgram
from analysis.auxiliary_ecl_event.physical_replay_v5 import (
    audit_event_batch_v5,
)
from analysis.auxiliary_ecl_event.physical_report_v2 import CACHE_CAPACITY
from analysis.auxiliary_ecl_event.physical_report_v6 import PACK_LIMIT_MS
from analysis.th08_runtime_ecl_identity_audit import (
    STAGE5_STATIC_LABEL,
    STAGE5_STATIC_LENGTH,
    audit as audit_runtime_ecl_identity,
)
from th08_ecl_tool.core import parse_ecl
from th08_live.auxiliary_vm.coalesced_envelope import (
    COALESCED_ENVELOPE_FIELD,
    pack_auxiliary_vm_batch,
)


DECODE_LIMIT_MS = (1.000, 2.000, 6.000)


def benchmark_coalesced_delivery_v6(
    trace_path: Path,
    static_path: Path,
    *,
    expected_static_sha256: str,
    repeats: int,
) -> dict[str, object]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    image = static_path.read_bytes()
    if hashlib.sha256(image).hexdigest() != expected_static_sha256:
        raise ValueError("static ECL identity differs")
    if len(image) != STAGE5_STATIC_LENGTH:
        raise ValueError("static ECL length differs")
    ecl = parse_ecl(static_path)
    identity = audit_runtime_ecl_identity(
        trace_path,
        expected_static_label=STAGE5_STATIC_LABEL,
        expected_static_length=STAGE5_STATIC_LENGTH,
        expected_static_sha256=expected_static_sha256,
    )
    version = expected_runtime_version(identity)
    runtime_base = version["runtime_base"]
    assert isinstance(runtime_base, int)
    program = ReplayProgram.from_ecl(
        ecl,
        image,
        runtime_base=runtime_base,
    )
    source_rows, source_sha256, source_bytes = trace_event_rows(trace_path)
    selected = [
        row for row in source_rows if row.get("schema_version") == 8
    ]
    if not selected or len(selected) != len(source_rows):
        raise ValueError("retained trace is not an exact schema-v8 workload")

    pack_ms: list[float] = []
    decode_ms: list[float] = []
    base64_bytes: list[float] = []
    compressed_bytes: list[float] = []
    uncompressed_bytes: list[float] = []
    replay_counts: Counter[str] = Counter()
    first_cache_totals: Counter[str] = Counter()
    exact_round_trip = True
    independent_cache_parity = True
    for repeat in range(repeats):
        cache = IndependentIntentLru(CACHE_CAPACITY)
        for sequence, source in enumerate(selected):
            frame = source.get("frame")
            epoch = source.get("gameplay_epoch")
            snapshot = source.get("snapshot_frame")
            stage = source.get("stage_route_index")
            if not all(
                isinstance(value, int) and not isinstance(value, bool)
                for value in (frame, epoch, snapshot, stage)
            ):
                raise ValueError("retained row binding is invalid")
            envelope = pack_auxiliary_vm_batch(
                source,
                sequence=sequence,
                decision_frame=frame,
                gameplay_epoch=epoch,
                snapshot_frame=snapshot,
                stage_route_index=stage,
            )
            pack_value = envelope["timing_ms"]["pack"]
            assert isinstance(pack_value, float)
            pack_ms.append(pack_value)
            parent: dict[str, Any] = {
                "kind": "decision",
                "frame": frame,
                "gameplay_epoch": epoch,
                "snapshot_frame": snapshot,
                "stage_route_index": stage,
                COALESCED_ENVELOPE_FIELD: envelope,
            }
            started = time.perf_counter()
            decoded = decode_coalesced_batch(
                parent,
                expected_sequence=sequence,
                context=f"repeat[{repeat}].batch[{sequence}]",
            )
            decode_ms.append((time.perf_counter() - started) * 1000.0)
            expected = json.loads(
                json.dumps(
                    source,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
            expected["timing_ms"]["previous_emit"] = None
            exact_round_trip = exact_round_trip and decoded.row == expected
            replay = audit_event_batch_v5(
                decoded.row,
                expected_runtime_version=version,
                program=program,
                context=f"repeat[{repeat}].batch[{sequence}]",
            )
            replay_counts.update(
                {
                    "request_count": replay.request_count,
                    "complete_count": replay.complete_count,
                    "unknown_count": replay.unknown_count,
                    "replayable_record_count": (
                        replay.replayable_record_count
                    ),
                }
            )
            event = decoded.row["event_derivation"]
            assert isinstance(event, dict)
            observed_cache = event.get("cache")
            expected_cache = cache.observe(replay.intent_keys).record()
            independent_cache_parity = (
                independent_cache_parity
                and observed_cache == expected_cache
            )
            if repeat == 0:
                first_cache_totals.update(
                    {
                        "request_local_hits": expected_cache[
                            "request_local_hits"
                        ],
                        "persistent_hits": expected_cache[
                            "persistent_hits"
                        ],
                        "misses": expected_cache["misses"],
                        "evictions": expected_cache["evictions"],
                    }
                )
            base64_bytes.append(float(decoded.payload_base64_bytes))
            compressed_bytes.append(float(decoded.compressed_bytes))
            uncompressed_bytes.append(float(decoded.uncompressed_bytes))

    pack = distribution(pack_ms)
    decode = distribution(decode_ms)
    payload = distribution(base64_bytes)
    compressed = distribution(compressed_bytes)
    uncompressed = distribution(uncompressed_bytes)
    report: dict[str, object] = {
        "schema": "th08-g5-auxiliary-ecl-event-coalesced-v6-preflight-v1",
        "authority": "isolated_replay_no_physical_action_authority",
        "source": {
            "trace": str(trace_path),
            "trace_sha256": source_sha256,
            "trace_bytes": source_bytes,
            "static_ecl": str(static_path),
            "static_sha256": expected_static_sha256,
            "batch_count": len(selected),
            "repeats": repeats,
        },
        "timing_ms": {
            "pack": pack,
            "independent_decode": decode,
        },
        "transport": {
            "payload_base64_bytes": payload,
            "compressed_bytes": compressed,
            "uncompressed_bytes": uncompressed,
        },
        "replay": dict(sorted(replay_counts.items())),
        "cache_first_repeat": dict(sorted(first_cache_totals.items())),
        "gates": {
            "exact_schema_v8_round_trip": exact_round_trip,
            "independent_v5_oracle_parity": bool(
                replay_counts["request_count"] > 0
                and replay_counts["request_count"]
                == replay_counts["complete_count"]
                == replay_counts["replayable_record_count"]
                and replay_counts["unknown_count"] == 0
            ),
            "independent_cache_parity": independent_cache_parity,
            "pack_timing": within(pack, PACK_LIMIT_MS),
            "decode_timing": within(decode, DECODE_LIMIT_MS),
            "payload_size": bool(
                payload is not None and payload["max"] <= 12_288
            ),
            "compressed_size": bool(
                compressed is not None and compressed["max"] <= 9_216
            ),
            "uncompressed_size": bool(
                uncompressed is not None and uncompressed["max"] <= 24_576
            ),
        },
    }
    gates = report["gates"]
    assert isinstance(gates, dict)
    report["passed"] = all(bool(value) for value in gates.values())
    return report


__all__ = [
    "DECODE_LIMIT_MS",
    "benchmark_coalesced_delivery_v6",
]
