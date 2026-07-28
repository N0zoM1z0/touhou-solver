#!/usr/bin/env python3
"""Tests for one-shot shipped runtime-ECL identity observation."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace
import unittest

from th08_live.runtime_ecl_identity import (
    RuntimeEclIdentityDependencies,
    RuntimeEclIdentityService,
    RuntimeEclPhysicalProvenance,
)
from th08_live.runtime_ecl_image import (
    RuntimeEclImageCapture,
    RuntimeEclImageIdentity,
)
from th08_runtime.game_state import EXPECTED_EXE_SHA256


class _TraceSink:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, object], bool, bool]] = []

    def emit(
        self,
        record: dict[str, object],
        *,
        flush: bool,
        measure: bool,
    ) -> float:
        self.calls.append((record, flush, measure))
        return 0.25


class RuntimeEclIdentityServiceTests(unittest.TestCase):
    @staticmethod
    def _provenance(
        *,
        stage_route_index: int = 5,
        executable_sha256: str = EXPECTED_EXE_SHA256,
    ) -> RuntimeEclPhysicalProvenance:
        return RuntimeEclPhysicalProvenance(
            pid=1234,
            executable_sha256=executable_sha256,
            route_id=2,
            difficulty_index=3,
            stage_route_index=stage_route_index,
            gameplay_epoch=7,
            decision_frame=120,
            snapshot_frame=118,
            gameplay_active=True,
        )

    def test_first_matching_stage_attempt_is_exact_and_never_repeats(
        self,
    ) -> None:
        static_image = b"static ECL"
        digest = hashlib.sha256(static_image).hexdigest()
        calls: list[object] = []
        capture = RuntimeEclImageCapture(
            runtime_base=0x02100000,
            image_length=len(static_image),
            subroutine_count=3,
            timeline_count=1,
            relocated_sha256="1" * 64,
            normalized_sha256=digest,
            capture_ms=0.5,
            read_count=4,
            relocated_image=b"relocated",
            normalized_image=static_image,
        )
        identity = RuntimeEclImageIdentity(
            exact_match=True,
            static_sha256=digest,
            normalized_runtime_sha256=digest,
            image_length=len(static_image),
            first_difference_offset=None,
        )

        def capture_image(
            reader: object,
            *,
            clock: object,
        ) -> RuntimeEclImageCapture:
            calls.append(("capture", reader, clock))
            return capture

        def compare_image(
            observed: RuntimeEclImageCapture,
            static: bytes,
        ) -> RuntimeEclImageIdentity:
            calls.append(("compare", observed, static))
            return identity

        ticks = iter((1.0, 1.002))
        service = RuntimeEclIdentityService(
            static_image=static_image,
            static_label="artifacts/decoded/ecldata5.ecl",
            expected_static_sha256=digest,
            expected_route_id=2,
            expected_difficulty_index=3,
            expected_stage_route_index=5,
            dependencies=RuntimeEclIdentityDependencies(
                capture=capture_image,  # type: ignore[arg-type]
                compare=compare_image,
                clock=lambda: next(ticks),
            ),
        )
        sink = _TraceSink()
        reader = SimpleNamespace()

        self.assertIsNone(
            service.observe_if_due(
                reader,  # type: ignore[arg-type]
                sink,  # type: ignore[arg-type]
                provenance=self._provenance(stage_route_index=4),
            )
        )
        self.assertFalse(service.attempted)

        result = service.observe_if_due(
            reader,  # type: ignore[arg-type]
            sink,  # type: ignore[arg-type]
            provenance=self._provenance(),
        )
        assert result is not None
        self.assertTrue(service.attempted)
        self.assertEqual([call[0] for call in calls], ["capture", "compare"])
        self.assertEqual(result.record["status"], "exact_match")
        self.assertAlmostEqual(result.record["transaction_ms"], 2.0)
        self.assertEqual(result.emit_ms, 0.25)
        self.assertEqual(len(sink.calls), 1)
        self.assertEqual(sink.calls[0][1:], (True, True))
        accepted = service.accepted_version
        self.assertIsNotNone(accepted)
        assert accepted is not None
        self.assertEqual(
            accepted.record(),
            {
                "schema": "th08-runtime-ecl-accepted-version-v1",
                "runtime_base": capture.runtime_base,
                "image_length": capture.image_length,
                "relocated_sha256": capture.relocated_sha256,
                "normalized_sha256": digest,
                "static_sha256": digest,
                "route_id": 2,
                "difficulty_index": 3,
                "stage_route_index": 5,
                "gameplay_epoch": 7,
                "decision_frame": 120,
                "snapshot_frame": 118,
            },
        )

        self.assertIsNone(
            service.observe_if_due(
                reader,  # type: ignore[arg-type]
                sink,  # type: ignore[arg-type]
                provenance=self._provenance(),
            )
        )
        self.assertEqual(len(sink.calls), 1)

    def test_capture_failure_is_visible_and_not_retried(self) -> None:
        static_image = b"static ECL"
        digest = hashlib.sha256(static_image).hexdigest()
        attempts = 0

        def fail_capture(
            _reader: object,
            *,
            clock: object,
        ) -> RuntimeEclImageCapture:
            del clock
            nonlocal attempts
            attempts += 1
            raise OSError("unreadable")

        ticks = iter((2.0, 2.003))
        service = RuntimeEclIdentityService(
            static_image=static_image,
            static_label="stage5",
            expected_static_sha256=digest,
            expected_route_id=2,
            expected_difficulty_index=3,
            expected_stage_route_index=5,
            dependencies=RuntimeEclIdentityDependencies(
                capture=fail_capture,  # type: ignore[arg-type]
                clock=lambda: next(ticks),
            ),
        )
        sink = _TraceSink()
        result = service.observe_if_due(
            SimpleNamespace(),  # type: ignore[arg-type]
            sink,  # type: ignore[arg-type]
            provenance=self._provenance(),
        )
        assert result is not None
        self.assertEqual(result.record["status"], "capture_error")
        self.assertEqual(result.record["error"], "OSError: unreadable")
        self.assertIsNone(result.record["capture"])
        self.assertIsNone(result.record["identity"])
        self.assertEqual(attempts, 1)
        self.assertIsNone(service.accepted_version)
        self.assertIsNone(
            service.observe_if_due(
                SimpleNamespace(),  # type: ignore[arg-type]
                sink,  # type: ignore[arg-type]
                provenance=self._provenance(),
            )
        )
        self.assertEqual(attempts, 1)
        self.assertTrue(sink.calls[0][1])

    def test_executable_mismatch_uses_no_process_read(self) -> None:
        static_image = b"static ECL"
        digest = hashlib.sha256(static_image).hexdigest()
        ticks = iter((3.0, 3.001))
        service = RuntimeEclIdentityService(
            static_image=static_image,
            static_label="stage5",
            expected_static_sha256=digest,
            expected_route_id=2,
            expected_difficulty_index=3,
            expected_stage_route_index=5,
            dependencies=RuntimeEclIdentityDependencies(
                capture=lambda *_args, **_kwargs: self.fail(
                    "capture must not run"
                ),
                clock=lambda: next(ticks),
            ),
        )
        sink = _TraceSink()
        result = service.observe_if_due(
            SimpleNamespace(),  # type: ignore[arg-type]
            sink,  # type: ignore[arg-type]
            provenance=self._provenance(executable_sha256="0" * 64),
        )
        assert result is not None
        self.assertEqual(
            result.record["status"],
            "physical_identity_mismatch",
        )
        self.assertTrue(service.attempted)
        self.assertIsNone(service.accepted_version)


if __name__ == "__main__":
    unittest.main()
