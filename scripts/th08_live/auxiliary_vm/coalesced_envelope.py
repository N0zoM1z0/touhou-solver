"""Same-iteration envelope for exact schema-v8 auxiliary evidence."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from typing import Callable
import zlib


COALESCED_ENVELOPE_FIELD = "auxiliary_vm_batch_envelope"
COALESCED_ENVELOPE_SCHEMA = (
    "th08-auxiliary-vm-batch-coalesced-envelope-v1"
)
COALESCED_ENVELOPE_ENCODING = "canonical-json-zlib-base64"
COALESCED_COMPRESSION_LEVEL = 6
COALESCED_INNER_SCHEMA_VERSION = 8
COALESCED_BASE64_MAXIMUM_BYTES = 12_288
COALESCED_COMPRESSED_MAXIMUM_BYTES = 9_216
COALESCED_UNCOMPRESSED_MAXIMUM_BYTES = 24_576


def _nonnegative_integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def pack_auxiliary_vm_batch(
    record: dict[str, object],
    *,
    sequence: int,
    decision_frame: int,
    gameplay_epoch: int,
    snapshot_frame: int,
    stage_route_index: int,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, object]:
    """Pack one exact V5 row for its same-iteration decision record."""

    binding = {
        "sequence": _nonnegative_integer(sequence, field="sequence"),
        "decision_frame": _nonnegative_integer(
            decision_frame,
            field="decision_frame",
        ),
        "gameplay_epoch": _nonnegative_integer(
            gameplay_epoch,
            field="gameplay_epoch",
        ),
        "snapshot_frame": _nonnegative_integer(
            snapshot_frame,
            field="snapshot_frame",
        ),
        "stage_route_index": _nonnegative_integer(
            stage_route_index,
            field="stage_route_index",
        ),
    }
    if record.get("kind") != "auxiliary_vm_batch":
        raise ValueError("coalesced inner record kind is invalid")
    if record.get("schema_version") != COALESCED_INNER_SCHEMA_VERSION:
        raise ValueError("coalesced inner schema version is invalid")
    for outer_name, inner_name in (
        ("decision_frame", "frame"),
        ("gameplay_epoch", "gameplay_epoch"),
        ("snapshot_frame", "snapshot_frame"),
        ("stage_route_index", "stage_route_index"),
    ):
        if record.get(inner_name) != binding[outer_name]:
            raise ValueError(
                f"coalesced inner {inner_name} differs from its decision"
            )
    timing = record.get("timing_ms")
    if not isinstance(timing, dict):
        raise ValueError("coalesced inner timing is absent")
    canonical_record = dict(record)
    canonical_timing = dict(timing)
    canonical_timing["previous_emit"] = None
    canonical_record["timing_ms"] = canonical_timing

    started = clock()
    uncompressed = json.dumps(
        canonical_record,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(uncompressed) > COALESCED_UNCOMPRESSED_MAXIMUM_BYTES:
        raise ValueError("coalesced inner evidence exceeds its size bound")
    compressed = zlib.compress(
        uncompressed,
        level=COALESCED_COMPRESSION_LEVEL,
    )
    if len(compressed) > COALESCED_COMPRESSED_MAXIMUM_BYTES:
        raise ValueError("coalesced compressed evidence exceeds its size bound")
    payload = base64.b64encode(compressed).decode("ascii")
    if len(payload) > COALESCED_BASE64_MAXIMUM_BYTES:
        raise ValueError("coalesced base64 evidence exceeds its size bound")
    uncompressed_sha256 = hashlib.sha256(uncompressed).hexdigest()
    compressed_sha256 = hashlib.sha256(compressed).hexdigest()
    pack_ms = (clock() - started) * 1000.0

    return {
        "schema": COALESCED_ENVELOPE_SCHEMA,
        "encoding": COALESCED_ENVELOPE_ENCODING,
        "compression_level": COALESCED_COMPRESSION_LEVEL,
        **binding,
        "inner_schema_version": COALESCED_INNER_SCHEMA_VERSION,
        "uncompressed_bytes": len(uncompressed),
        "compressed_bytes": len(compressed),
        "uncompressed_sha256": uncompressed_sha256,
        "compressed_sha256": compressed_sha256,
        "payload_base64": payload,
        "timing_ms": {"pack": pack_ms},
    }


__all__ = [
    "COALESCED_BASE64_MAXIMUM_BYTES",
    "COALESCED_COMPRESSED_MAXIMUM_BYTES",
    "COALESCED_COMPRESSION_LEVEL",
    "COALESCED_ENVELOPE_ENCODING",
    "COALESCED_ENVELOPE_FIELD",
    "COALESCED_ENVELOPE_SCHEMA",
    "COALESCED_INNER_SCHEMA_VERSION",
    "COALESCED_UNCOMPRESSED_MAXIMUM_BYTES",
    "pack_auxiliary_vm_batch",
]
