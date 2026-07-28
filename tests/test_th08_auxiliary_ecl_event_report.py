from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from analysis.auxiliary_ecl_event.report import (
    build_auxiliary_ecl_event_inventory_report,
)
from analysis.auxiliary_ecl_event.trace_inventory import (
    scan_compact_auxiliary_trace,
)


_ECL_SHA256 = (
    "3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19"
)


def _batch(frame: int, target: int, active_hash: str) -> dict[str, object]:
    return {
        "kind": "auxiliary_vm_batch",
        "schema_version": 3,
        "frame": frame,
        "status": "success",
        "observation": {
            "records": [
                {
                    "status_bits": 0,
                    "target_subroutine": target,
                    "call_depth": 0,
                    "auxiliary_marker": 1,
                    "active_vm_sha256": active_hash,
                },
                {
                    "status_bits": 1,
                    "target_subroutine": None,
                    "call_depth": None,
                    "auxiliary_marker": None,
                    "active_vm_sha256": None,
                },
            ]
        },
    }


class AuxiliaryEclEventReportTests(unittest.TestCase):
    def test_hash_only_trace_retains_limitation_and_exact_target_programs(
        self,
    ) -> None:
        ecl = (
            Path(__file__).resolve().parents[1]
            / "artifacts"
            / "decoded"
            / "ecldata5.ecl"
        )
        rows = [
            {"kind": "decision", "frame": 1},
            _batch(100, 69, "1" * 64),
            _batch(116, 73, "2" * 64),
            {"kind": "summary"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            trace.write_text(
                "".join(
                    json.dumps(row, sort_keys=True) + "\n" for row in rows
                ),
                encoding="utf-8",
            )
            first = build_auxiliary_ecl_event_inventory_report(
                trace,
                ecl,
                expected_ecl_sha256=_ECL_SHA256,
            )
            second = build_auxiliary_ecl_event_inventory_report(
                trace,
                ecl,
                expected_ecl_sha256=_ECL_SHA256,
            )

        self.assertEqual(first, second)
        self.assertEqual(first["schema"], "th08-g5-auxiliary-ecl-event-inventory-v1")
        self.assertEqual(first["trace"]["batch_count"], 2)
        self.assertEqual(first["trace"]["usable_record_count"], 2)
        self.assertEqual(
            first["trace"]["target_subroutines"],
            {"69": 1, "73": 1},
        )
        self.assertEqual(
            first["trace"]["event_replay_status"],
            "unavailable_hash_only",
        )
        self.assertFalse(first["conclusion"]["hash_is_reversible_state"])
        self.assertFalse(first["conclusion"]["timer_or_geometry_authority"])
        self.assertTrue(
            first["static_ecl"][
                "all_observed_targets_are_literal_fire_cycles"
            ]
        )
        programs = first["static_ecl"]["target_programs"]
        self.assertEqual(
            [program["timer_threshold"] for program in programs],
            [8, 30],
        )
        self.assertEqual(
            [program["literal_requested_count_fields"] for program in programs],
            [2, 2],
        )

    def test_static_identity_mismatch_fails_closed(self) -> None:
        ecl = (
            Path(__file__).resolve().parents[1]
            / "artifacts"
            / "decoded"
            / "ecldata5.ecl"
        )
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            trace.write_text(
                json.dumps(_batch(1, 69, "1" * 64)) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "digest"):
                build_auxiliary_ecl_event_inventory_report(
                    trace,
                    ecl,
                    expected_ecl_sha256="0" * 64,
                )

    def test_replay_state_requires_valid_complete_evidence(self) -> None:
        active_vm = b"\0" * 0x228
        active_hash = hashlib.sha256(active_vm).hexdigest()
        row = _batch(1, 69, active_hash)
        record = row["observation"]["records"][0]
        record["active_vm_hex"] = active_vm.hex()
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
            inventory = scan_compact_auxiliary_trace(trace)
            self.assertEqual(inventory.event_replay_status, "raw_state_available")

            record["active_vm_sha256"] = "0" * 64
            trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                scan_compact_auxiliary_trace(trace)

            record.pop("active_vm_hex")
            record["active_pc"] = 0x500000
            trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "partial structural"):
                scan_compact_auxiliary_trace(trace)


if __name__ == "__main__":
    unittest.main()
