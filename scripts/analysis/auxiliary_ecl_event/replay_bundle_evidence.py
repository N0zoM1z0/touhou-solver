"""Independent bounded decoder for schema-v5 replay-state bundles."""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
import zlib
from typing import Any

from .replay_evidence import (
    ACTIVE_VM_BYTES,
    AuxiliaryEclEventReplayError,
    array,
    mapping,
)


REPLAY_BUNDLE_SCHEMA = "th08-auxiliary-vm-replay-bundle-v1"
REPLAY_BUNDLE_ENCODING = "zlib-base64"
REPLAY_BUNDLE_COMPRESSION_LEVEL = 1
MAXIMUM_REPLAY_BLOBS = 4096
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _integer(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AuxiliaryEclEventReplayError(f"{context} is not an integer")
    return value


def _hash(value: object, context: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise AuxiliaryEclEventReplayError(f"{context} is not SHA-256")
    return value


def _referenced_hashes(
    records: list[Any],
    *,
    context: str,
) -> list[str]:
    referenced: list[str] = []
    seen: set[str] = set()
    for index, raw_record in enumerate(records):
        record_context = f"{context}.records[{index}]"
        record = mapping(raw_record, record_context)
        if "active_vm_hex" in record or "saved_frame_hex" in record:
            raise AuxiliaryEclEventReplayError(
                f"{record_context} contains legacy raw replay fields"
            )
        active_hash = record.get("active_vm_sha256")
        if active_hash is not None:
            parsed = _hash(active_hash, f"{record_context}.active_vm_sha256")
            if parsed not in seen:
                seen.add(parsed)
                referenced.append(parsed)
        saved_hashes = array(
            record.get("saved_frame_sha256"),
            f"{record_context}.saved_frame_sha256",
        )
        for saved_index, saved_hash in enumerate(saved_hashes):
            parsed = _hash(
                saved_hash,
                f"{record_context}.saved_frame_sha256[{saved_index}]",
            )
            if parsed not in seen:
                seen.add(parsed)
                referenced.append(parsed)
    return referenced


def decode_replay_bundle(
    observation: dict[str, Any],
    *,
    context: str,
) -> dict[str, bytes]:
    records = array(observation.get("records"), f"{context}.records")
    expected_hashes = _referenced_hashes(records, context=context)
    bundle = mapping(
        observation.get("replay_state_bundle"),
        f"{context}.replay_state_bundle",
    )
    if bundle.get("schema") != REPLAY_BUNDLE_SCHEMA:
        raise AuxiliaryEclEventReplayError(
            f"{context} replay bundle schema is invalid"
        )
    if bundle.get("encoding") != REPLAY_BUNDLE_ENCODING:
        raise AuxiliaryEclEventReplayError(
            f"{context} replay bundle encoding is invalid"
        )
    if (
        bundle.get("compression_level")
        != REPLAY_BUNDLE_COMPRESSION_LEVEL
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} replay compression level changed"
        )
    blob_bytes = _integer(bundle.get("blob_bytes"), f"{context}.blob_bytes")
    blob_count = _integer(bundle.get("blob_count"), f"{context}.blob_count")
    uncompressed_bytes = _integer(
        bundle.get("uncompressed_bytes"),
        f"{context}.uncompressed_bytes",
    )
    if blob_bytes != ACTIVE_VM_BYTES:
        raise AuxiliaryEclEventReplayError(
            f"{context} replay blob size changed"
        )
    if not 0 <= blob_count <= MAXIMUM_REPLAY_BLOBS:
        raise AuxiliaryEclEventReplayError(
            f"{context} replay blob count is unbounded"
        )
    expected_bytes = blob_count * blob_bytes
    if uncompressed_bytes != expected_bytes:
        raise AuxiliaryEclEventReplayError(
            f"{context} replay byte count is inconsistent"
        )
    raw_hashes = array(bundle.get("blob_sha256"), f"{context}.blob_sha256")
    hashes = [
        _hash(value, f"{context}.blob_sha256[{index}]")
        for index, value in enumerate(raw_hashes)
    ]
    if (
        len(hashes) != blob_count
        or len(set(hashes)) != len(hashes)
        or hashes != expected_hashes
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} replay hashes do not exactly cover references"
        )
    payload_base64 = bundle.get("payload_base64")
    if not isinstance(payload_base64, str):
        raise AuxiliaryEclEventReplayError(
            f"{context} replay payload is not text"
        )
    try:
        compressed = base64.b64decode(
            payload_base64.encode("ascii"),
            validate=True,
        )
    except (UnicodeEncodeError, binascii.Error) as error:
        raise AuxiliaryEclEventReplayError(
            f"{context} replay payload is not canonical base64"
        ) from error
    if len(compressed) > expected_bytes + 65536:
        raise AuxiliaryEclEventReplayError(
            f"{context} compressed replay payload is unbounded"
        )
    decompressor = zlib.decompressobj()
    try:
        uncompressed = decompressor.decompress(
            compressed,
            expected_bytes + 1,
        )
    except zlib.error as error:
        raise AuxiliaryEclEventReplayError(
            f"{context} replay payload does not decompress"
        ) from error
    if (
        len(uncompressed) != expected_bytes
        or not decompressor.eof
        or decompressor.unused_data
        or decompressor.unconsumed_tail
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} replay decompression boundary is invalid"
        )
    expected_uncompressed_hash = _hash(
        bundle.get("uncompressed_sha256"),
        f"{context}.uncompressed_sha256",
    )
    if hashlib.sha256(uncompressed).hexdigest() != expected_uncompressed_hash:
        raise AuxiliaryEclEventReplayError(
            f"{context} uncompressed replay digest differs"
        )
    decoded: dict[str, bytes] = {}
    for index, expected_hash in enumerate(hashes):
        start = index * blob_bytes
        blob = uncompressed[start : start + blob_bytes]
        if hashlib.sha256(blob).hexdigest() != expected_hash:
            raise AuxiliaryEclEventReplayError(
                f"{context} replay blob digest differs"
            )
        decoded[expected_hash] = blob
    return decoded


def validate_bundled_replay_record(
    record: dict[str, Any],
    replay_blobs: dict[str, bytes],
    *,
    context: str,
) -> bytes | None:
    active_hash = record.get("active_vm_sha256")
    active_vm = None
    if active_hash is not None:
        parsed = _hash(active_hash, f"{context}.active_vm_sha256")
        active_vm = replay_blobs.get(parsed)
        if active_vm is None:
            raise AuxiliaryEclEventReplayError(
                f"{context} active VM replay blob is missing"
            )
    saved_hashes = array(
        record.get("saved_frame_sha256"),
        f"{context}.saved_frame_sha256",
    )
    for index, saved_hash in enumerate(saved_hashes):
        parsed = _hash(
            saved_hash,
            f"{context}.saved_frame_sha256[{index}]",
        )
        if parsed not in replay_blobs:
            raise AuxiliaryEclEventReplayError(
                f"{context} saved-frame replay blob is missing"
            )
    return active_vm


__all__ = [
    "MAXIMUM_REPLAY_BLOBS",
    "REPLAY_BUNDLE_COMPRESSION_LEVEL",
    "REPLAY_BUNDLE_ENCODING",
    "REPLAY_BUNDLE_SCHEMA",
    "decode_replay_bundle",
    "validate_bundled_replay_record",
]
