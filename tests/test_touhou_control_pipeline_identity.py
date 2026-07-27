from __future__ import annotations

import unittest

from touhou_control.pipeline_identity import (
    CanonicalPipelineRoot,
    PipelineObservationIdentity,
    PipelineQueryIdentity,
    VersionIdentity,
    float32_bits,
)


def _version(namespace: str, **components: object) -> VersionIdentity:
    return VersionIdentity.from_mapping(namespace, components)


def _identity(
    *,
    root: CanonicalPipelineRoot | None = None,
    hazard_revision: int = 4,
) -> PipelineQueryIdentity:
    return PipelineQueryIdentity(
        observation=PipelineObservationIdentity.from_coordinates(
            gameplay_epoch=3,
            stage_route_index=1,
            spell_id=42,
            manager_frame=100,
            query_frame=102,
            target_frame=105,
            player_x=192.0,
            player_y=384.0,
        ),
        root=root
        or CanonicalPipelineRoot(
            supported_mask=0xF7,
            active_mask=0x81,
            held_desired_mask=0x55,
            pending_mask=0x55,
            remaining_delay_support=(1, 2, 3),
        ),
        observation_version=_version("th08-native-snapshot", schema=1),
        hazard_version=_version(
            "th08-hazard-volume",
            revision=hazard_revision,
        ),
        policy_version=_version("corridor-policy", revision=9),
        model_version=_version("belief-pipeline", revision=2),
        clock_version=_version(
            "manager-frame-proxy",
            ce0120_open=True,
            revision=1,
        ),
    )


class PipelineIdentityTests(unittest.TestCase):
    def test_multikey_root_is_content_addressed_and_stable(self) -> None:
        first = _identity()
        second = _identity()

        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first.record()["sha256"], first.digest)
        self.assertEqual(
            first.record()["root"]["held_desired_mask"],
            0x55,
        )
        self.assertEqual(
            first.record()["root"]["remaining_delay_support"],
            [1, 2, 3],
        )

    def test_complete_masks_distinguish_no_write_identity(self) -> None:
        changed_shot = _identity(
            root=CanonicalPipelineRoot(
                supported_mask=0xF7,
                active_mask=0x80,
                held_desired_mask=0x54,
                pending_mask=0x54,
                remaining_delay_support=(1, 2, 3),
            )
        )

        self.assertNotEqual(_identity().digest, changed_shot.digest)

    def test_every_immutable_version_participates_in_digest(self) -> None:
        self.assertNotEqual(
            _identity(hazard_revision=4).digest,
            _identity(hazard_revision=5).digest,
        )

    def test_no_pending_requires_active_equals_held(self) -> None:
        with self.assertRaisesRegex(ValueError, "held desired"):
            CanonicalPipelineRoot(
                supported_mask=0xF7,
                active_mask=0x81,
                held_desired_mask=0x41,
            )

    def test_pending_requires_held_match_and_positive_support(self) -> None:
        with self.assertRaisesRegex(ValueError, "pending to equal"):
            CanonicalPipelineRoot(
                supported_mask=0xF7,
                active_mask=0x81,
                held_desired_mask=0x41,
                pending_mask=0x51,
                remaining_delay_support=(1,),
            )
        with self.assertRaisesRegex(ValueError, "requires remaining"):
            CanonicalPipelineRoot(
                supported_mask=0xF7,
                active_mask=0x81,
                held_desired_mask=0x51,
                pending_mask=0x51,
            )

    def test_float32_coordinate_identity_is_exact(self) -> None:
        self.assertEqual(float32_bits(1.0), "0x3f800000")
        with self.assertRaisesRegex(ValueError, "finite"):
            float32_bits(float("nan"))


if __name__ == "__main__":
    unittest.main()
