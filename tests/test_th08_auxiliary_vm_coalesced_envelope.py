from __future__ import annotations

import base64
import copy
import hashlib
import json
import unittest
import zlib

from analysis.auxiliary_ecl_event.coalesced_replay_v6 import (
    AuxiliaryEclEventReplayError,
    decode_coalesced_batch,
)
from th08_live.auxiliary_vm.coalesced_envelope import (
    COALESCED_ENVELOPE_FIELD,
    pack_auxiliary_vm_batch,
)


def _inner() -> dict[str, object]:
    return {
        "kind": "auxiliary_vm_batch",
        "schema_version": 8,
        "frame": 120,
        "gameplay_epoch": 3,
        "snapshot_frame": 118,
        "stage_route_index": 5,
        "status": "success",
        "timing_ms": {
            "event_derive": 0.2,
            "compact": 0.1,
            "previous_emit": 9.9,
            "total": 0.8,
        },
        "evidence": {"value": [1, 2, 3]},
    }


def _clock() -> object:
    values = iter((1.0, 1.0002))
    return values.__next__


def _parent(envelope: dict[str, object]) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": 120,
        "gameplay_epoch": 3,
        "snapshot_frame": 118,
        "stage_route_index": 5,
        COALESCED_ENVELOPE_FIELD: envelope,
    }


def _replace_compressed(
    envelope: dict[str, object],
    compressed: bytes,
) -> None:
    payload = base64.b64encode(compressed).decode("ascii")
    envelope["payload_base64"] = payload
    envelope["compressed_bytes"] = len(compressed)
    envelope["compressed_sha256"] = hashlib.sha256(compressed).hexdigest()


class AuxiliaryVmCoalescedEnvelopeTests(unittest.TestCase):
    def test_exact_canonical_round_trip_and_no_previous_emit(self) -> None:
        inner = _inner()
        envelope = pack_auxiliary_vm_batch(
            inner,
            sequence=0,
            decision_frame=120,
            gameplay_epoch=3,
            snapshot_frame=118,
            stage_route_index=5,
            clock=_clock(),
        )

        decoded = decode_coalesced_batch(
            _parent(envelope),
            expected_sequence=0,
            context="test",
        )

        expected = copy.deepcopy(inner)
        expected["timing_ms"]["previous_emit"] = None
        self.assertEqual(decoded.row, expected)
        self.assertAlmostEqual(decoded.pack_ms, 0.2)
        self.assertEqual(inner["timing_ms"]["previous_emit"], 9.9)

    def test_producer_rejects_binding_and_size_divergence(self) -> None:
        with self.assertRaisesRegex(ValueError, "differs"):
            pack_auxiliary_vm_batch(
                _inner(),
                sequence=0,
                decision_frame=121,
                gameplay_epoch=3,
                snapshot_frame=118,
                stage_route_index=5,
            )

        oversized = _inner()
        oversized["evidence"] = {"value": "x" * 30_000}
        with self.assertRaisesRegex(ValueError, "size bound"):
            pack_auxiliary_vm_batch(
                oversized,
                sequence=0,
                decision_frame=120,
                gameplay_epoch=3,
                snapshot_frame=118,
                stage_route_index=5,
            )

    def test_decoder_rejects_corruption_sequence_and_parent_mismatch(
        self,
    ) -> None:
        envelope = pack_auxiliary_vm_batch(
            _inner(),
            sequence=0,
            decision_frame=120,
            gameplay_epoch=3,
            snapshot_frame=118,
            stage_route_index=5,
        )
        corrupt = copy.deepcopy(envelope)
        corrupt["payload_base64"] = corrupt["payload_base64"][:-4] + "AAAA"
        with self.assertRaisesRegex(
            AuxiliaryEclEventReplayError,
            "length|hash|zlib",
        ):
            decode_coalesced_batch(
                _parent(corrupt),
                expected_sequence=0,
                context="corrupt",
            )
        with self.assertRaisesRegex(
            AuxiliaryEclEventReplayError,
            "sequence",
        ):
            decode_coalesced_batch(
                _parent(envelope),
                expected_sequence=1,
                context="sequence",
            )
        parent = _parent(envelope)
        parent["snapshot_frame"] = 119
        with self.assertRaisesRegex(
            AuxiliaryEclEventReplayError,
            "snapshot_frame",
        ):
            decode_coalesced_batch(
                parent,
                expected_sequence=0,
                context="binding",
            )

    def test_decoder_rejects_trailing_zlib_and_noncanonical_inner(self) -> None:
        envelope = pack_auxiliary_vm_batch(
            _inner(),
            sequence=0,
            decision_frame=120,
            gameplay_epoch=3,
            snapshot_frame=118,
            stage_route_index=5,
        )
        trailing = copy.deepcopy(envelope)
        compressed = base64.b64decode(trailing["payload_base64"])
        _replace_compressed(trailing, compressed + zlib.compress(b"extra"))
        with self.assertRaisesRegex(
            AuxiliaryEclEventReplayError,
            "trailing",
        ):
            decode_coalesced_batch(
                _parent(trailing),
                expected_sequence=0,
                context="trailing",
            )

        noncanonical = copy.deepcopy(envelope)
        raw = zlib.decompress(
            base64.b64decode(noncanonical["payload_base64"])
        )
        parsed = json.loads(raw)
        spaced = json.dumps(parsed, sort_keys=True).encode()
        compressed = zlib.compress(spaced, level=6)
        _replace_compressed(noncanonical, compressed)
        noncanonical["uncompressed_bytes"] = len(spaced)
        noncanonical["uncompressed_sha256"] = hashlib.sha256(spaced).hexdigest()
        with self.assertRaisesRegex(
            AuxiliaryEclEventReplayError,
            "noncanonical",
        ):
            decode_coalesced_batch(
                _parent(noncanonical),
                expected_sequence=0,
                context="noncanonical",
            )


if __name__ == "__main__":
    unittest.main()
