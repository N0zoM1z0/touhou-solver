"""Independent decoder for same-decision schema-v8 evidence envelopes."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any
import zlib

from .physical_replay import AuxiliaryEclEventReplayError


ENVELOPE_FIELD = "auxiliary_vm_batch_envelope"
ENVELOPE_SCHEMA = "th08-auxiliary-vm-batch-coalesced-envelope-v1"
ENVELOPE_ENCODING = "canonical-json-zlib-base64"
COMPRESSION_LEVEL = 6
INNER_SCHEMA_VERSION = 8
BASE64_MAXIMUM_BYTES = 12_288
COMPRESSED_MAXIMUM_BYTES = 9_216
UNCOMPRESSED_MAXIMUM_BYTES = 24_576
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ENVELOPE_KEYS = {
    "schema",
    "encoding",
    "compression_level",
    "sequence",
    "decision_frame",
    "gameplay_epoch",
    "snapshot_frame",
    "stage_route_index",
    "inner_schema_version",
    "uncompressed_bytes",
    "compressed_bytes",
    "uncompressed_sha256",
    "compressed_sha256",
    "payload_base64",
    "timing_ms",
}


@dataclass(frozen=True)
class DecodedCoalescedBatch:
    row: dict[str, Any]
    sequence: int
    pack_ms: float
    payload_base64_bytes: int
    compressed_bytes: int
    uncompressed_bytes: int


def _integer(value: object, *, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AuxiliaryEclEventReplayError(
            f"{context} is not a nonnegative integer"
        )
    return value


def _number(value: object, *, context: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} is not finite nonnegative"
        )
    return float(value)


def _sha256(value: object, *, context: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise AuxiliaryEclEventReplayError(
            f"{context} is not canonical SHA-256"
        )
    return value


def _bounded_decompress(compressed: bytes, *, context: str) -> bytes:
    decompressor = zlib.decompressobj()
    try:
        result = decompressor.decompress(
            compressed,
            UNCOMPRESSED_MAXIMUM_BYTES + 1,
        )
    except zlib.error as error:
        raise AuxiliaryEclEventReplayError(
            f"{context} zlib payload is invalid"
        ) from error
    if (
        len(result) > UNCOMPRESSED_MAXIMUM_BYTES
        or decompressor.unconsumed_tail
        or decompressor.unused_data
        or not decompressor.eof
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} zlib payload is incomplete, trailing, or oversized"
        )
    try:
        tail = decompressor.flush()
    except zlib.error as error:
        raise AuxiliaryEclEventReplayError(
            f"{context} zlib finalization failed"
        ) from error
    if tail:
        result += tail
    if len(result) > UNCOMPRESSED_MAXIMUM_BYTES:
        raise AuxiliaryEclEventReplayError(
            f"{context} decompressed payload is oversized"
        )
    return result


def decode_coalesced_batch(
    parent: dict[str, Any],
    *,
    expected_sequence: int,
    context: str,
) -> DecodedCoalescedBatch:
    """Decode, bind, and canonicalize one envelope without producer reuse."""

    envelope = parent.get(ENVELOPE_FIELD)
    if not isinstance(envelope, dict):
        raise AuxiliaryEclEventReplayError(
            f"{context} envelope is absent or invalid"
        )
    if set(envelope) != _ENVELOPE_KEYS:
        raise AuxiliaryEclEventReplayError(
            f"{context} envelope fields are invalid"
        )
    if (
        envelope.get("schema") != ENVELOPE_SCHEMA
        or envelope.get("encoding") != ENVELOPE_ENCODING
        or envelope.get("compression_level") != COMPRESSION_LEVEL
        or envelope.get("inner_schema_version") != INNER_SCHEMA_VERSION
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} envelope version is invalid"
        )
    sequence = _integer(
        envelope.get("sequence"),
        context=f"{context}.sequence",
    )
    if sequence != expected_sequence:
        raise AuxiliaryEclEventReplayError(
            f"{context} envelope sequence is duplicated or gapped"
        )
    uncompressed_bytes = _integer(
        envelope.get("uncompressed_bytes"),
        context=f"{context}.uncompressed_bytes",
    )
    compressed_bytes = _integer(
        envelope.get("compressed_bytes"),
        context=f"{context}.compressed_bytes",
    )
    if (
        uncompressed_bytes > UNCOMPRESSED_MAXIMUM_BYTES
        or compressed_bytes > COMPRESSED_MAXIMUM_BYTES
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} envelope size bound is exceeded"
        )
    payload = envelope.get("payload_base64")
    if (
        not isinstance(payload, str)
        or len(payload.encode("ascii", errors="ignore"))
        != len(payload)
        or len(payload) > BASE64_MAXIMUM_BYTES
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} base64 payload is invalid or oversized"
        )
    try:
        compressed = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error) as error:
        raise AuxiliaryEclEventReplayError(
            f"{context} base64 payload is invalid"
        ) from error
    if base64.b64encode(compressed).decode("ascii") != payload:
        raise AuxiliaryEclEventReplayError(
            f"{context} base64 payload is noncanonical"
        )
    if len(compressed) != compressed_bytes:
        raise AuxiliaryEclEventReplayError(
            f"{context} compressed length differs"
        )
    if hashlib.sha256(compressed).hexdigest() != _sha256(
        envelope.get("compressed_sha256"),
        context=f"{context}.compressed_sha256",
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} compressed hash differs"
        )
    uncompressed = _bounded_decompress(compressed, context=context)
    if len(uncompressed) != uncompressed_bytes:
        raise AuxiliaryEclEventReplayError(
            f"{context} uncompressed length differs"
        )
    if hashlib.sha256(uncompressed).hexdigest() != _sha256(
        envelope.get("uncompressed_sha256"),
        context=f"{context}.uncompressed_sha256",
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} uncompressed hash differs"
        )
    try:
        row = json.loads(uncompressed)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuxiliaryEclEventReplayError(
            f"{context} inner JSON is invalid"
        ) from error
    if not isinstance(row, dict):
        raise AuxiliaryEclEventReplayError(
            f"{context} inner JSON is not an object"
        )
    canonical = json.dumps(
        row,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if canonical != uncompressed:
        raise AuxiliaryEclEventReplayError(
            f"{context} inner JSON is noncanonical"
        )
    if (
        row.get("kind") != "auxiliary_vm_batch"
        or row.get("schema_version") != INNER_SCHEMA_VERSION
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} inner V5 schema is invalid"
        )
    timing = row.get("timing_ms")
    if (
        not isinstance(timing, dict)
        or "previous_emit" not in timing
        or timing["previous_emit"] is not None
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} inner standalone emit evidence is invalid"
        )
    for envelope_name, parent_name, inner_name in (
        ("decision_frame", "frame", "frame"),
        ("gameplay_epoch", "gameplay_epoch", "gameplay_epoch"),
        ("snapshot_frame", "snapshot_frame", "snapshot_frame"),
        ("stage_route_index", "stage_route_index", "stage_route_index"),
    ):
        bound = _integer(
            envelope.get(envelope_name),
            context=f"{context}.{envelope_name}",
        )
        if parent.get(parent_name) != bound or row.get(inner_name) != bound:
            raise AuxiliaryEclEventReplayError(
                f"{context} {envelope_name} binding differs"
            )
    outer_timing = envelope.get("timing_ms")
    if not isinstance(outer_timing, dict) or set(outer_timing) != {"pack"}:
        raise AuxiliaryEclEventReplayError(
            f"{context} envelope timing fields are invalid"
        )
    pack_ms = _number(
        outer_timing.get("pack"),
        context=f"{context}.timing_ms.pack",
    )
    return DecodedCoalescedBatch(
        row=row,
        sequence=sequence,
        pack_ms=pack_ms,
        payload_base64_bytes=len(payload),
        compressed_bytes=compressed_bytes,
        uncompressed_bytes=uncompressed_bytes,
    )


__all__ = [
    "BASE64_MAXIMUM_BYTES",
    "COMPRESSED_MAXIMUM_BYTES",
    "DecodedCoalescedBatch",
    "ENVELOPE_FIELD",
    "ENVELOPE_SCHEMA",
    "UNCOMPRESSED_MAXIMUM_BYTES",
    "decode_coalesced_batch",
]
