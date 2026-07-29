from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.auxiliary_ecl_event.physical_report_v4 import (
    AuxiliaryEclEventPhysicalAuditError,
    build_physical_report_v4,
)
from analysis.th08_runtime_ecl_identity_audit import (
    STAGE5_STATIC_LABEL,
    STAGE5_STATIC_SHA256,
)
from th08_live.auxiliary_vm.event_service import (
    AuxiliaryEclEventConfiguration,
    AuxiliaryEclEventTraceService,
)

from test_th08_auxiliary_ecl_event_physical_report_v2 import (
    _batch_row,
    _decision,
    _identity,
    _observation,
    _version,
    _write_rows,
)


_ROOT = Path(__file__).resolve().parents[1]
_ECL = _ROOT / STAGE5_STATIC_LABEL


def _epoch_decision(frame: int, epoch: int) -> dict[str, object]:
    row = _decision(frame)
    row["gameplay_epoch"] = epoch
    return row


class AuxiliaryEclEventPhysicalReportV4Tests(unittest.TestCase):
    def _rows(
        self,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        service = AuxiliaryEclEventTraceService(
            AuxiliaryEclEventConfiguration(
                static_path=_ECL,
                expected_static_sha256=STAGE5_STATIC_SHA256,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
        )
        preparation = service.prepare_if_needed(
            _version(),
            gameplay_epoch=0,
            stage_route_index=5,
            decision_frame=102,
            snapshot_frame=102,
        )
        assert preparation is not None
        batches: list[dict[str, object]] = []
        for index, (frame, epoch, populated) in enumerate(
            (
                (120, 1, False),
                (136, 1, True),
                (152, 2, True),
                (168, 3, True),
            )
        ):
            observation = _observation(frame, populated=populated)
            event = service.derive(
                observation,
                runtime_version=_version(),
                gameplay_epoch=epoch,
                stage_route_index=5,
            )
            batch = _batch_row(
                observation,
                event,
                frame=frame,
                previous_emit_ms=None if index == 0 else 0.2,
                usable_projection=True,
            )
            batch["schema_version"] = 7
            batch["gameplay_epoch"] = epoch
            batches.append(batch)
        return preparation, batches

    def _fixture(
        self,
        root: Path,
        *,
        preparation: dict[str, object] | None = None,
        batches: list[dict[str, object]] | None = None,
        hit_count: int = 8,
    ) -> tuple[Path, Path, Path]:
        default_preparation, default_batches = self._rows()
        selected_preparation = (
            default_preparation if preparation is None else preparation
        )
        selected_batches = default_batches if batches is None else batches
        trace = root / "trace.jsonl"
        baseline = root / "baseline.jsonl"
        session = root / "session.json"
        rows: list[dict[str, object]] = [
            _epoch_decision(100, 0),
            _identity(),
            _epoch_decision(102, 0),
        ]
        if selected_preparation:
            rows.append(selected_preparation)
        for batch in selected_batches:
            frame = batch["frame"]
            epoch = batch["gameplay_epoch"]
            assert isinstance(frame, int)
            assert isinstance(epoch, int)
            rows.extend((_epoch_decision(frame, epoch), batch))
        rows.extend(
            (
                _epoch_decision(170, 3),
                {
                    "kind": "summary",
                    "last_frame": 170,
                    "counter_gaps": 0,
                    "hit_count": hit_count,
                    "termination_reason": "route_complete",
                },
            )
        )
        _write_rows(trace, rows)
        _write_rows(
            baseline,
            [
                _epoch_decision(frame, 0)
                for frame in (100, 102, 120, 136, 152, 168, 170)
            ]
            + [{"kind": "summary", "termination_reason": "route_complete"}],
        )
        session.write_text(
            json.dumps(
                {
                    "run_id": "synthetic-v4",
                    "status": "completed",
                    "trial_accepted": True,
                    "hard_no_bomb": True,
                    "trace_auxiliary_vm_batches": True,
                    "trace_auxiliary_ecl_events": True,
                    "auxiliary_vm_batch_spell_id": 107,
                    "runtime_ecl_static_sha256": STAGE5_STATIC_SHA256,
                    "agent_summary": {
                        "termination_reason": "route_complete",
                        "hit_count": hit_count,
                        "hit_frames": list(range(hit_count)),
                    },
                }
            ),
            encoding="utf-8",
        )
        return trace, baseline, session

    def test_cross_epoch_compact_delivery_passes(self) -> None:
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(Path(temporary))
            report = build_physical_report_v4(
                trace,
                baseline,
                session,
                _ECL,
            )
        self.assertTrue(report["passed"])
        self.assertTrue(all(report["gates"].values()))
        self.assertEqual(
            report["observation_epochs"]["batch_gameplay_epochs"],
            {"1": 2, "2": 1, "3": 1},
        )
        line_bytes = report["transport"]["batch_line_bytes"]
        self.assertLessEqual(line_bytes["max"], 24576)

    def _assert_tamper_rejected(
        self,
        batches: list[dict[str, object]],
        pattern: str,
    ) -> None:
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                batches=batches,
            )
            with self.assertRaisesRegex(
                AuxiliaryEclEventPhysicalAuditError,
                pattern,
            ):
                build_physical_report_v4(
                    trace,
                    baseline,
                    session,
                    _ECL,
                )

    def test_source_index_and_histogram_tamper_fail_closed(self) -> None:
        _preparation, batches = self._rows()
        source_tamper = copy.deepcopy(batches)
        observation = source_tamper[1]["observation"]
        assert isinstance(observation, dict)
        records = observation["records"]
        assert isinstance(records, list)
        records[0]["source_record_index"] = 999
        self._assert_tamper_rejected(source_tamper, "source indices")

        histogram_tamper = copy.deepcopy(batches)
        observation = histogram_tamper[1]["observation"]
        assert isinstance(observation, dict)
        projection = observation["record_projection"]
        assert isinstance(projection, dict)
        projection["record_status_bits"] = {"0": 2}
        self._assert_tamper_rejected(
            histogram_tamper,
            "record-status histogram mismatch|status proof",
        )

    def test_bundle_and_commitment_tamper_fail_closed(self) -> None:
        _preparation, batches = self._rows()
        bundle_tamper = copy.deepcopy(batches)
        observation = bundle_tamper[1]["observation"]
        assert isinstance(observation, dict)
        bundle = observation["replay_state_bundle"]
        assert isinstance(bundle, dict)
        bundle["payload_base64"] = "AAAA"
        self._assert_tamper_rejected(bundle_tamper, "bundle|payload")

        commitment_tamper = copy.deepcopy(batches)
        event = commitment_tamper[1]["event_derivation"]
        assert isinstance(event, dict)
        commitment = event["lowering_commitment"]
        assert isinstance(commitment, dict)
        hashes = commitment["unique_result_sha256"]
        assert isinstance(hashes, list)
        hashes[0] = "0" * 64
        self._assert_tamper_rejected(
            commitment_tamper,
            "commitment differs",
        )

    def test_slow_preparation_and_eleven_hits_are_rejected(self) -> None:
        preparation, batches = self._rows()
        slow = copy.deepcopy(preparation)
        timing = slow["timing_ms"]
        assert isinstance(timing, dict)
        timing["total"] = 1.01
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                preparation=slow,
                batches=batches,
                hit_count=11,
            )
            report = build_physical_report_v4(
                trace,
                baseline,
                session,
                _ECL,
            )
        self.assertFalse(report["passed"])
        self.assertFalse(report["gates"]["preparation_exact_and_bounded"])
        self.assertFalse(
            report["gates"]["stage5_survival_regression_boundary"]
        )


if __name__ == "__main__":
    unittest.main()
