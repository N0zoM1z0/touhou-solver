from __future__ import annotations

import base64
import copy
import hashlib
import unittest

from analysis.auxiliary_ecl_event.replay_bundle_evidence import (
    decode_replay_bundle,
)
from analysis.auxiliary_ecl_event.replay_evidence import (
    AuxiliaryEclEventReplayError,
)
from th08_live.auxiliary_vm.replay_bundle import encode_replay_bundle


class AuxiliaryVmReplayBundleTests(unittest.TestCase):
    def _observation(self) -> dict[str, object]:
        first = b"\x01" * 0x228
        second = b"\x02" * 0x228
        first_hash = hashlib.sha256(first).hexdigest()
        second_hash = hashlib.sha256(second).hexdigest()
        return {
            "records": [
                {
                    "active_vm_sha256": first_hash,
                    "saved_frame_sha256": [second_hash],
                },
                {
                    "active_vm_sha256": first_hash,
                    "saved_frame_sha256": [],
                },
            ],
            "replay_state_bundle": encode_replay_bundle(
                ((first_hash, first), (second_hash, second)),
                blob_bytes=0x228,
            ),
        }

    def test_independent_decoder_recovers_exact_first_reference_map(
        self,
    ) -> None:
        observation = self._observation()
        decoded = decode_replay_bundle(
            observation,
            context="observation",
        )
        records = observation["records"]
        assert isinstance(records, list)
        first_hash = records[0]["active_vm_sha256"]
        second_hash = records[0]["saved_frame_sha256"][0]
        self.assertEqual(decoded[first_hash], b"\x01" * 0x228)
        self.assertEqual(decoded[second_hash], b"\x02" * 0x228)
        self.assertEqual(len(decoded), 2)

    def test_bundle_boundary_and_reference_tampering_fail_closed(self) -> None:
        cases: list[tuple[str, dict[str, object]]] = []

        legacy = copy.deepcopy(self._observation())
        legacy["records"][0]["active_vm_hex"] = "00"
        cases.append(("legacy", legacy))

        duplicate = copy.deepcopy(self._observation())
        duplicate_bundle = duplicate["replay_state_bundle"]
        duplicate_hashes = duplicate_bundle["blob_sha256"]
        duplicate_hashes[1] = duplicate_hashes[0]
        cases.append(("hashes", duplicate))

        byte_count = copy.deepcopy(self._observation())
        byte_count["replay_state_bundle"]["uncompressed_bytes"] += 1
        cases.append(("byte count", byte_count))

        trailing = copy.deepcopy(self._observation())
        trailing_bundle = trailing["replay_state_bundle"]
        compressed = base64.b64decode(trailing_bundle["payload_base64"])
        trailing_bundle["payload_base64"] = base64.b64encode(
            compressed + b"trailing"
        ).decode("ascii")
        cases.append(("boundary", trailing))

        missing = copy.deepcopy(self._observation())
        missing["records"][0]["active_vm_sha256"] = "0" * 64
        cases.append(("cover references", missing))

        for label, observation in cases:
            with self.subTest(label=label):
                with self.assertRaises(AuxiliaryEclEventReplayError):
                    decode_replay_bundle(
                        observation,
                        context="observation",
                    )


if __name__ == "__main__":
    unittest.main()
