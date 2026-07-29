"""Compact hash-addressed replay-state transport encoding."""

from __future__ import annotations

import base64
import hashlib
import re
import zlib
from collections.abc import Iterable


REPLAY_BUNDLE_SCHEMA = "th08-auxiliary-vm-replay-bundle-v1"
REPLAY_BUNDLE_ENCODING = "zlib-base64"
REPLAY_BUNDLE_COMPRESSION_LEVEL = 1
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def encode_replay_bundle(
    blobs: Iterable[tuple[str, bytes]],
    *,
    blob_bytes: int,
) -> dict[str, object]:
    """Encode unique fixed-size blobs in stable first-reference order."""

    if blob_bytes <= 0:
        raise ValueError("replay blob size must be positive")
    hashes: list[str] = []
    payload_parts: list[bytes] = []
    seen: set[str] = set()
    for expected_sha256, blob in blobs:
        if (
            _SHA256.fullmatch(expected_sha256) is None
            or expected_sha256 in seen
        ):
            raise ValueError("replay blob SHA-256 is invalid or repeated")
        if len(blob) != blob_bytes:
            raise ValueError("replay blob has an invalid size")
        if hashlib.sha256(blob).hexdigest() != expected_sha256:
            raise ValueError("replay blob differs from its SHA-256")
        seen.add(expected_sha256)
        hashes.append(expected_sha256)
        payload_parts.append(blob)

    uncompressed = b"".join(payload_parts)
    compressed = zlib.compress(
        uncompressed,
        level=REPLAY_BUNDLE_COMPRESSION_LEVEL,
    )
    return {
        "schema": REPLAY_BUNDLE_SCHEMA,
        "encoding": REPLAY_BUNDLE_ENCODING,
        "compression_level": REPLAY_BUNDLE_COMPRESSION_LEVEL,
        "blob_bytes": blob_bytes,
        "blob_count": len(hashes),
        "uncompressed_bytes": len(uncompressed),
        "uncompressed_sha256": hashlib.sha256(uncompressed).hexdigest(),
        "blob_sha256": hashes,
        "payload_base64": base64.b64encode(compressed).decode("ascii"),
    }


__all__ = [
    "REPLAY_BUNDLE_COMPRESSION_LEVEL",
    "REPLAY_BUNDLE_ENCODING",
    "REPLAY_BUNDLE_SCHEMA",
    "encode_replay_bundle",
]
