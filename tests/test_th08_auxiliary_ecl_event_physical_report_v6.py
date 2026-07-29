from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.auxiliary_ecl_event.physical_report_v2 import (
    AuxiliaryEclEventPhysicalAuditError,
)
from analysis.auxiliary_ecl_event.physical_report_v6 import (
    build_physical_report_v6,
)
from analysis.th08_runtime_ecl_identity_audit import (
    STAGE5_STATIC_LABEL,
    STAGE5_STATIC_SHA256,
)
from th08_live.auxiliary_vm.coalesced_envelope import (
    COALESCED_ENVELOPE_FIELD,
    pack_auxiliary_vm_batch,
)

from test_th08_auxiliary_ecl_event_physical_report_v2 import (
    _decision,
    _identity,
    _write_rows,
)
from test_th08_auxiliary_ecl_event_physical_report_v5 import (
    AuxiliaryEclEventPhysicalReportV5Tests,
)


_ROOT = Path(__file__).resolve().parents[1]
_ECL = _ROOT / STAGE5_STATIC_LABEL


def _clock() -> object:
    values = iter((1.0, 1.0002))
    return values.__next__


def _decision_v6(
    frame: int,
    epoch: int,
    *,
    previous_trace: float | None,
) -> dict[str, object]:
    row = _decision(frame)
    row["gameplay_epoch"] = epoch
    row["snapshot_frame"] = frame
    row["timing_ms"]["previous_trace"] = previous_trace
    return row


class AuxiliaryEclEventPhysicalReportV6Tests(unittest.TestCase):
    def _rows(
        self,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        return AuxiliaryEclEventPhysicalReportV5Tests()._rows()

    def _fixture(
        self,
        root: Path,
        *,
        tamper: object | None = None,
        hit_count: int = 8,
        emit_ms: float = 0.2,
        include_final_measurement: bool = True,
        add_standalone: bool = False,
    ) -> tuple[Path, Path, Path]:
        preparation, batches = self._rows()
        trace = root / "trace.jsonl"
        baseline = root / "baseline.jsonl"
        session = root / "session.json"
        rows: list[dict[str, object]] = [
            _decision_v6(100, 0, previous_trace=None),
            _identity(),
            _decision_v6(102, 0, previous_trace=emit_ms),
            preparation,
        ]
        for sequence, batch in enumerate(batches):
            frame = batch["frame"]
            epoch = batch["gameplay_epoch"]
            snapshot = batch["snapshot_frame"]
            assert isinstance(frame, int)
            assert isinstance(epoch, int)
            assert isinstance(snapshot, int)
            parent = _decision_v6(
                frame,
                epoch,
                previous_trace=emit_ms,
            )
            parent[COALESCED_ENVELOPE_FIELD] = pack_auxiliary_vm_batch(
                batch,
                sequence=sequence,
                decision_frame=frame,
                gameplay_epoch=epoch,
                snapshot_frame=snapshot,
                stage_route_index=5,
                clock=_clock(),
            )
            rows.append(parent)
        if tamper is not None:
            assert callable(tamper)
            tamper(rows)
        if add_standalone:
            rows.append(copy.deepcopy(batches[0]))
        if include_final_measurement:
            rows.append(_decision_v6(170, 3, previous_trace=emit_ms))
        rows.append(
            {
                "kind": "summary",
                "last_frame": 170,
                "counter_gaps": 0,
                "hit_count": hit_count,
                "termination_reason": "route_complete",
            }
        )
        _write_rows(trace, rows)
        _write_rows(
            baseline,
            [
                _decision_v6(
                    frame,
                    0,
                    previous_trace=None if index == 0 else 0.2,
                )
                for index, frame in enumerate(
                    (100, 102, 120, 136, 152, 168, 170)
                )
            ]
            + [{"kind": "summary", "termination_reason": "route_complete"}],
        )
        session.write_text(
            json.dumps(
                {
                    "run_id": "synthetic-v6",
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

    def _report(self, root: Path, **kwargs: object) -> dict[str, object]:
        return build_physical_report_v6(
            *self._fixture(root, **kwargs),
            _ECL,
        )

    def test_exact_coalesced_replay_and_timing_gate_passes(self) -> None:
        with TemporaryDirectory() as temporary:
            report = self._report(Path(temporary))
        self.assertTrue(report["passed"])
        self.assertTrue(all(report["gates"].values()))
        self.assertEqual(report["transport"]["batch_count"], 4)
        coalesced = report["transport"]["coalesced"]
        self.assertEqual(coalesced["sequences"], [0, 1, 2, 3])
        self.assertEqual(coalesced["standalone_batch_count"], 0)
        self.assertEqual(
            report["replay"]["request_count"],
            report["replay"]["complete_count"],
        )

    def test_sequence_parent_and_payload_tamper_fail_closed(self) -> None:
        def sequence(rows: list[dict[str, object]]) -> None:
            rows[4][COALESCED_ENVELOPE_FIELD]["sequence"] = 3

        def parent(rows: list[dict[str, object]]) -> None:
            rows[4]["snapshot_frame"] += 1

        def payload(rows: list[dict[str, object]]) -> None:
            envelope = rows[4][COALESCED_ENVELOPE_FIELD]
            envelope["payload_base64"] = (
                envelope["payload_base64"][:-4] + "AAAA"
            )

        for tamper, pattern in (
            (sequence, "sequence"),
            (parent, "snapshot_frame"),
            (payload, "length|hash|zlib"),
        ):
            with self.subTest(pattern=pattern):
                with TemporaryDirectory() as temporary:
                    with self.assertRaisesRegex(
                        AuxiliaryEclEventPhysicalAuditError,
                        pattern,
                    ):
                        self._report(
                            Path(temporary),
                            tamper=tamper,
                        )

    def test_standalone_and_missing_next_timing_fail_closed(self) -> None:
        for options, pattern in (
            ({"add_standalone": True}, "standalone"),
            (
                {"include_final_measurement": False},
                "no causal publication timing",
            ),
        ):
            with self.subTest(pattern=pattern):
                with TemporaryDirectory() as temporary:
                    with self.assertRaisesRegex(
                        AuxiliaryEclEventPhysicalAuditError,
                        pattern,
                    ):
                        self._report(Path(temporary), **options)

    def test_emit_regression_and_eleven_hits_are_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            report = self._report(
                Path(temporary),
                emit_ms=2.0,
                hit_count=11,
            )
        self.assertFalse(report["passed"])
        self.assertFalse(
            report["gates"]["bearing_decision_emit_regression"]
        )
        self.assertFalse(
            report["gates"]["all_decision_emit_p95_regression"]
        )
        self.assertFalse(
            report["gates"]["stage5_survival_regression_boundary"]
        )


if __name__ == "__main__":
    unittest.main()
