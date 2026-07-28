"""Raw replay evidence validation independent of the live event service."""

from __future__ import annotations

import hashlib
import math
import re
import struct
from typing import Any


EVENT_SCHEMA = "th08-auxiliary-ecl-event-derivation-v1"
EVENT_AUTHORITY = "trace_only_no_action_authority"
ACCEPTED_VERSION_SCHEMA = "th08-runtime-ecl-accepted-version-v1"
TARGET_HORIZONS = {69: 16, 72: 16, 73: 60}
ACTIVE_VM_BYTES = 0x228
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class AuxiliaryEclEventReplayError(ValueError):
    """Raised when a schema-v4 batch cannot reproduce its live result."""


def mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AuxiliaryEclEventReplayError(f"{context} must be an object")
    return value


def array(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise AuxiliaryEclEventReplayError(f"{context} must be an array")
    return value


def integer(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AuxiliaryEclEventReplayError(f"{context} must be an integer")
    return value


def _sha256(value: object, context: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise AuxiliaryEclEventReplayError(
            f"{context} must be a lowercase SHA-256"
        )
    return value


def _raw_hex(
    value: object,
    *,
    expected_bytes: int,
    context: str,
) -> bytes:
    if (
        not isinstance(value, str)
        or len(value) != expected_bytes * 2
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} is not exact lowercase replay bytes"
        )
    return bytes.fromhex(value)


def validate_replay_record(
    record: dict[str, Any],
    *,
    context: str,
) -> bytes | None:
    active_hash = record.get("active_vm_sha256")
    active_hex = record.get("active_vm_hex")
    if active_hash is None:
        if active_hex is not None:
            raise AuxiliaryEclEventReplayError(
                f"{context} has raw active state without a hash"
            )
        active_vm = None
    else:
        expected_hash = _sha256(active_hash, f"{context}.active_vm_sha256")
        active_vm = _raw_hex(
            active_hex,
            expected_bytes=ACTIVE_VM_BYTES,
            context=f"{context}.active_vm_hex",
        )
        if hashlib.sha256(active_vm).hexdigest() != expected_hash:
            raise AuxiliaryEclEventReplayError(
                f"{context} active VM hash mismatch"
            )

    saved_hashes = array(
        record.get("saved_frame_sha256"),
        f"{context}.saved_frame_sha256",
    )
    saved_hex = array(
        record.get("saved_frame_hex"),
        f"{context}.saved_frame_hex",
    )
    if len(saved_hashes) != len(saved_hex):
        raise AuxiliaryEclEventReplayError(
            f"{context} saved-frame replay length mismatch"
        )
    for index, (raw_hash, raw_hex) in enumerate(
        zip(saved_hashes, saved_hex)
    ):
        expected_hash = _sha256(
            raw_hash,
            f"{context}.saved_frame_sha256[{index}]",
        )
        frame = _raw_hex(
            raw_hex,
            expected_bytes=ACTIVE_VM_BYTES,
            context=f"{context}.saved_frame_hex[{index}]",
        )
        if hashlib.sha256(frame).hexdigest() != expected_hash:
            raise AuxiliaryEclEventReplayError(
                f"{context} saved frame {index} hash mismatch"
            )
    return active_vm


def decoded_state(active_vm: bytes) -> dict[str, int] | None:
    if len(active_vm) != ACTIVE_VM_BYTES:
        return None
    pc, previous, fraction_bits, elapsed = struct.unpack_from(
        "<IiIi",
        active_vm,
        0,
    )
    fraction = struct.unpack("<f", struct.pack("<I", fraction_bits))[0]
    marker = struct.unpack_from("<I", active_vm, 0x220)[0]
    if not (
        0x00010000 <= pc <= 0x7FFFFFFF
        and math.isfinite(fraction)
        and 0.0 <= fraction < 1.0
        and elapsed >= 0
        and 1 <= marker <= 4
    ):
        return None
    return {
        "instruction_pointer": pc,
        "timer_previous": previous,
        "timer_fraction_bits": fraction_bits,
        "timer_elapsed": elapsed,
        "auxiliary_marker": marker,
    }


__all__ = [
    "ACCEPTED_VERSION_SCHEMA",
    "ACTIVE_VM_BYTES",
    "AuxiliaryEclEventReplayError",
    "EVENT_AUTHORITY",
    "EVENT_SCHEMA",
    "TARGET_HORIZONS",
    "array",
    "decoded_state",
    "integer",
    "mapping",
    "validate_replay_record",
]
