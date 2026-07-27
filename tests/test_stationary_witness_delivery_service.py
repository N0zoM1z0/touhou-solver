#!/usr/bin/env python3
"""Publication, lookup, and cancellation tests for the offline service."""

from __future__ import annotations

import os
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest

import numpy as np

from benchmarks.stationary_witness_delivery.native import (
    NativeStationaryWitnessLibrary,
    NativeWitnessAction,
)
from benchmarks.stationary_witness_delivery.service import (
    NewestWitnessService,
)
from th08_pipeline_actions import TH08_COMPLETE_MASK_ACTION_SPACE
from touhou_control.partial_survival_witness import (
    build_stationary_witness_portfolio,
)
from touhou_control.query_survival import SurvivalQueryProblem
from touhou_control.viability import ViabilityConfig


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = (
    ROOT
    / "native"
    / "build"
    / ("windows-x86_64" if os.name == "nt" else "linux-x86_64")
    / (
        "belief_stationary_witness_benchmark.dll"
        if os.name == "nt"
        else "libbelief_stationary_witness_benchmark.so"
    )
)


def _complete_workload(identity: str) -> SimpleNamespace:
    actions = TH08_COMPLETE_MASK_ACTION_SPACE.control_actions
    held = actions[0].name
    problem = SurvivalQueryProblem(
        x_axis=np.arange(3, dtype=np.float32),
        y_axis=np.arange(3, dtype=np.float32),
        clearance_volume=np.ones((5, 3, 3), dtype=np.float32),
        actions=actions,
        delay_frames=(1,),
        nominal_delay=1,
        config=ViabilityConfig(
            frames_per_layer=1,
            required_clearance=0.0,
            clamp_to_bounds=True,
        ),
    )
    query = {
        "frame": 0,
        "row": 1,
        "column": 1,
        "observed_action": held,
        "pending_command": None,
    }
    expected = build_stationary_witness_portfolio(
        problem=problem,
        decision_frame_support=(1,),
        continuation_candidates=(held,),
        unrestricted_status="unresolved",
        **query,
    )
    return SimpleNamespace(
        identity=identity,
        problem=problem,
        query=query,
        expected=expected,
        root=SimpleNamespace(held_token=held),
    )


@unittest.skipUnless(LIBRARY.exists(), "witness benchmark library is not built")
class StationaryWitnessDeliveryServiceTests(unittest.TestCase):
    def test_complete_newest_publication_uses_exact_lookup(self) -> None:
        service = NewestWitnessService(
            library=NativeStationaryWitnessLibrary(LIBRARY),
            decision_frame_support=(1,),
            deadline_ms=1000.0,
            lower_priority=False,
            affinity_cpu=max(0, (os.cpu_count() or 1) - 1),
        )
        try:
            workload = _complete_workload("identity-newest")
            revision = service.submit(workload)
            attempt = service.wait_for_attempt(revision, timeout=5.0)
            self.assertEqual(attempt.status, "complete")
            self.assertEqual(attempt.completed_action_count, 36)
            self.assertTrue(service.affinity_applied)
            publication = service.lookup("identity-newest")
            self.assertIsNotNone(publication)
            assert publication is not None
            self.assertEqual(len(publication.actions), 36)
            self.assertIsNone(service.lookup("identity-older"))
            self.assertIsNone(service.lookup("identity-newest-altered"))
        finally:
            service.close()


class _BlockingWorkspace:
    def __init__(self) -> None:
        self.cancelled = threading.Event()

    def query(self, **_kwargs: object) -> NativeWitnessAction:
        if not self.cancelled.wait(timeout=5.0):
            raise TimeoutError("fake native query was not cancelled")
        return NativeWitnessAction(5, "root", 0, 0.0, (), 0)

    def cancel(self) -> int:
        self.cancelled.set()
        return 0

    def close(self) -> None:
        return None


class _BlockingLibrary:
    def create_workspace(self, **_kwargs: object) -> _BlockingWorkspace:
        return _BlockingWorkspace()


class StationaryWitnessDeliveryCancellationTests(unittest.TestCase):
    def test_replacement_acknowledges_active_native_cancellation(self) -> None:
        expected = SimpleNamespace(
            complete_root_actions=("root",),
            action_witnesses=(),
        )
        workload = SimpleNamespace(
            identity="old",
            problem=object(),
            query={
                "frame": 0,
                "row": 0,
                "column": 0,
                "observed_action": "root",
                "pending_command": None,
            },
            expected=expected,
            root=SimpleNamespace(held_token="root"),
        )
        newer = SimpleNamespace(**{**workload.__dict__, "identity": "new"})
        service = NewestWitnessService(
            library=_BlockingLibrary(),
            deadline_ms=1000.0,
            lower_priority=False,
        )
        try:
            old_revision = service.submit(workload)
            self.assertTrue(
                service.wait_until_workspace_active(
                    old_revision,
                    timeout=2.0,
                )
            )
            service.submit(newer)
            attempt = service.wait_for_attempt(old_revision, timeout=2.0)
            self.assertEqual(attempt.status, "cancelled")
            self.assertIsNotNone(attempt.cancel_ack_ms)
            self.assertIsNone(service.lookup("old"))
        finally:
            service.close()


if __name__ == "__main__":
    unittest.main()
