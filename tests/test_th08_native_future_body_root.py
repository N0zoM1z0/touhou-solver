from __future__ import annotations

import struct
import unittest

from th08_live.enemy_sensor import (
    ENEMY_FLAGS_OFFSET,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
)
from th08_native_future_body_root import (
    MINIMUM_ROOT_REQUIREMENTS,
    TH08_ENEMY_MANAGER_TEMPLATE_BASE,
    TH08_TIMELINE_RUNTIME_BASE,
    Route2NativeRootComponentCapture,
    Route2NativeRootComponentSpec,
    capture_route2_native_future_body_root_slice,
    decode_route2_ordinary_pool_active_slots,
    route2_revalidated_native_root_component_specs,
)
from touhou_control.pipeline_identity import VersionIdentity


def _version(namespace: str) -> VersionIdentity:
    return VersionIdentity.from_mapping(namespace, {"fixture": "root-v1"})


def _spec(
    name: str,
    address: int,
    data_size: int,
    requirements: tuple[str, ...],
    *,
    evidence_state: str = "revalidated",
    complete_requirement_coverage: bool = True,
) -> Route2NativeRootComponentSpec:
    return Route2NativeRootComponentSpec(
        name=name,
        address=address,
        size=data_size,
        requirements=requirements,
        layout_version=f"{name}-layout-v1",
        evidence_state=evidence_state,
        complete_requirement_coverage=complete_requirement_coverage,
    )


class _Reader:
    def __init__(
        self,
        *,
        frames: tuple[int, ...],
        regions: dict[tuple[int, int], bytes],
    ) -> None:
        self.frames = list(frames)
        self.regions = regions

    def u32(self, _address: int) -> int:
        if not self.frames:
            raise AssertionError("unexpected frame read")
        return self.frames.pop(0)

    def read(self, address: int, size: int) -> bytes:
        return self.regions[(address, size)]


class Route2NativeFutureBodyRootTests(unittest.TestCase):
    def test_revalidated_inventory_is_capture_canonical(self) -> None:
        specs = route2_revalidated_native_root_component_specs()
        names = tuple(spec.name for spec in specs)
        self.assertEqual(names, tuple(sorted(names)))
        self.assertEqual(len(names), len(set(names)))

    def test_stable_capture_is_content_addressed_but_not_predictive(
        self,
    ) -> None:
        specs = (
            _spec(
                "control",
                0x1000,
                4,
                ("gameplay_and_route_identity",),
            ),
            _spec(
                "rng",
                0x2000,
                6,
                ("shared_gameplay_rng",),
            ),
        )
        capture = capture_route2_native_future_body_root_slice(
            _Reader(
                frames=(77, 77),
                regions={
                    (0x1000, 4): b"ctrl",
                    (0x2000, 6): b"rng123",
                },
            ),
            root_identity=_version("native-root"),
            clock_version=_version("native-clock"),
            component_specs=specs,
            active_slots_from_components=lambda _components: (3, 7),
        )

        self.assertTrue(capture.coherent)
        self.assertFalse(capture.inventory_complete)
        self.assertFalse(capture.record()["physical_predictive_authority"])
        self.assertEqual(
            capture.authority_status,
            "partial_native_root_inventory",
        )
        self.assertEqual(
            tuple(
                identity.slot
                for identity in capture.lifetime_ledger.active_identities
            ),
            (3, 7),
        )
        self.assertEqual(capture.record()["sha256"], capture.digest)

    def test_inherited_layout_does_not_satisfy_a_requirement(self) -> None:
        spec = _spec(
            "rng",
            0x2000,
            2,
            ("shared_gameplay_rng",),
            evidence_state="inherited",
        )
        capture = capture_route2_native_future_body_root_slice(
            _Reader(frames=(8, 8), regions={(0x2000, 2): b"xx"}),
            root_identity=_version("native-root"),
            clock_version=_version("native-clock"),
            component_specs=(spec,),
            active_slots_from_components=lambda _components: (),
        )

        self.assertIn("shared_gameplay_rng", capture.missing_requirements)
        self.assertEqual(capture.revalidated_requirements, ())

    def test_revalidated_pointer_root_does_not_claim_complete_coverage(
        self,
    ) -> None:
        spec = _spec(
            "run_state_pointer",
            0x160F510,
            4,
            ("damage_power_and_resources",),
            complete_requirement_coverage=False,
        )
        capture = capture_route2_native_future_body_root_slice(
            _Reader(frames=(8, 8), regions={(0x160F510, 4): b"ptr!"}),
            root_identity=_version("native-root"),
            clock_version=_version("native-clock"),
            component_specs=(spec,),
            active_slots_from_components=lambda _components: (),
        )

        self.assertIn(
            "damage_power_and_resources",
            capture.missing_requirements,
        )
        self.assertFalse(
            spec.record()["complete_requirement_coverage"]
        )

    def test_capture_retries_one_crossed_manager_frame(self) -> None:
        spec = _spec(
            "rng",
            0x2000,
            2,
            ("shared_gameplay_rng",),
        )
        capture = capture_route2_native_future_body_root_slice(
            _Reader(
                frames=(10, 11, 12, 12),
                regions={(0x2000, 2): b"xx"},
            ),
            root_identity=_version("native-root"),
            clock_version=_version("native-clock"),
            component_specs=(spec,),
            active_slots_from_components=lambda _components: (),
            maximum_attempts=2,
        )

        self.assertTrue(capture.coherent)
        self.assertEqual(capture.attempts, 2)
        self.assertEqual((capture.frame_before, capture.frame_after), (12, 12))

    def test_exhausted_crossed_capture_remains_incoherent(self) -> None:
        spec = _spec(
            "rng",
            0x2000,
            2,
            ("shared_gameplay_rng",),
        )
        capture = capture_route2_native_future_body_root_slice(
            _Reader(
                frames=(10, 11, 12, 13),
                regions={(0x2000, 2): b"xx"},
            ),
            root_identity=_version("native-root"),
            clock_version=_version("native-clock"),
            component_specs=(spec,),
            active_slots_from_components=lambda _components: (),
            maximum_attempts=2,
        )

        self.assertFalse(capture.coherent)
        self.assertEqual(
            capture.authority_status,
            "incoherent_native_root_slice",
        )

    def test_complete_byte_inventory_still_has_no_executor_authority(
        self,
    ) -> None:
        spec = _spec(
            "all_revalidated_root_bytes",
            0x3000,
            1,
            MINIMUM_ROOT_REQUIREMENTS,
        )
        capture = capture_route2_native_future_body_root_slice(
            _Reader(frames=(9, 9), regions={(0x3000, 1): b"x"}),
            root_identity=_version("native-root"),
            clock_version=_version("native-clock"),
            component_specs=(spec,),
            active_slots_from_components=lambda _components: (),
        )

        self.assertTrue(capture.inventory_complete)
        self.assertEqual(
            capture.authority_status,
            "complete_root_bytes_without_executor_authority",
        )
        self.assertFalse(capture.record()["physical_predictive_authority"])

    def test_short_component_read_fails_closed(self) -> None:
        spec = _spec(
            "rng",
            0x2000,
            2,
            ("shared_gameplay_rng",),
        )

        with self.assertRaisesRegex(RuntimeError, "short native-root read"):
            capture_route2_native_future_body_root_slice(
                _Reader(frames=(1,), regions={(0x2000, 2): b"x"}),
                root_identity=_version("native-root"),
                clock_version=_version("native-clock"),
                component_specs=(spec,),
                active_slots_from_components=lambda _components: (),
            )

    def test_full_pool_decoder_uses_native_active_bit(self) -> None:
        pool = bytearray(ENEMY_POOL_SIZE * ENEMY_STRIDE)
        for slot, flags in ((0, 1), (17, 0x101), (479, 0x800)):
            struct.pack_into(
                "<I",
                pool,
                slot * ENEMY_STRIDE + ENEMY_FLAGS_OFFSET,
                flags,
            )
        spec = _spec(
            "ordinary_enemy_template_and_pool",
            0x005826C0,
            len(pool),
            (
                "main_and_auxiliary_ecl_contexts",
                "motion_flag_and_lifecycle_state",
                "ordinary_enemy_template_and_pool",
            ),
        )
        component = Route2NativeRootComponentCapture(
            spec=spec,
            data=bytes(pool),
        )

        self.assertEqual(
            decode_route2_ordinary_pool_active_slots((component,)),
            (0, 17),
        )

    def test_product_template_plus_pool_decoder_skips_template(self) -> None:
        region = bytearray((ENEMY_POOL_SIZE + 1) * ENEMY_STRIDE)
        for slot in (2, 479):
            struct.pack_into(
                "<I",
                region,
                ENEMY_STRIDE
                + slot * ENEMY_STRIDE
                + ENEMY_FLAGS_OFFSET,
                1,
            )
        spec = _spec(
            "ordinary_enemy_template_and_pool",
            TH08_ENEMY_MANAGER_TEMPLATE_BASE,
            len(region),
            (
                "motion_flag_and_lifecycle_state",
                "ordinary_enemy_template_and_pool",
            ),
        )
        component = Route2NativeRootComponentCapture(
            spec=spec,
            data=bytes(region),
        )

        self.assertEqual(
            decode_route2_ordinary_pool_active_slots((component,)),
            (2, 479),
        )

    def test_component_bytes_change_root_version(self) -> None:
        spec = _spec(
            "rng",
            0x2000,
            2,
            ("shared_gameplay_rng",),
        )

        def capture(data: bytes):
            return capture_route2_native_future_body_root_slice(
                _Reader(frames=(5, 5), regions={(0x2000, 2): data}),
                root_identity=_version("native-root"),
                clock_version=_version("native-clock"),
                component_specs=(spec,),
                active_slots_from_components=lambda _components: (),
            )

        self.assertNotEqual(capture(b"aa").digest, capture(b"ab").digest)

    def test_revalidated_layout_inventory_preserves_open_dynamic_roots(
        self,
    ) -> None:
        specs = route2_revalidated_native_root_component_specs()
        by_name = {spec.name: spec for spec in specs}

        self.assertEqual(
            by_name["ordinary_enemy_template_and_pool"].address,
            TH08_ENEMY_MANAGER_TEMPLATE_BASE,
        )
        self.assertEqual(
            by_name["timeline_runtime_clock_table"].address,
            TH08_TIMELINE_RUNTIME_BASE,
        )
        self.assertEqual(
            by_name["ordinary_enemy_template_and_pool"].size,
            (ENEMY_POOL_SIZE + 1) * ENEMY_STRIDE,
        )
        complete = {
            requirement
            for spec in specs
            if (
                spec.evidence_state == "revalidated"
                and spec.complete_requirement_coverage
            )
            for requirement in spec.requirements
        }
        self.assertEqual(
            complete,
            {
                "motion_flag_and_lifecycle_state",
                "ordinary_enemy_template_and_pool",
                "shared_gameplay_rng",
            },
        )


if __name__ == "__main__":
    unittest.main()
