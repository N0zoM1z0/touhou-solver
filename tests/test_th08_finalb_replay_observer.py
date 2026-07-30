from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from th08_automation import finalb_replay_observer as replay_observer
from th08_replay import ReplayMetadata, ReplayStage


EXPECTED_SHA256 = "12" * 32


def _stage(
    *,
    stage_index: int = 7,
    bomb_press_frames: tuple[int, ...] = (),
) -> ReplayStage:
    return ReplayStage(
        stage_index=stage_index,
        data_offset=0x100,
        auxiliary_offset=0,
        rng_seed=0xF1B0,
        lives=8,
        bombs=3,
        byte_1c=0,
        byte_1f=0,
        input_record_stride=2,
        frame_count=51_711,
        input_sha256="34" * 32,
        bomb_press_frames=bomb_press_frames,
    )


def _metadata(
    name: str,
    *,
    route_id: int = 2,
    difficulty_index: int = 3,
    stages: tuple[ReplayStage, ...] | None = None,
) -> ReplayMetadata:
    return ReplayMetadata(
        name=name,
        sha256=EXPECTED_SHA256,
        file_size=1,
        encoded_main_size=1,
        compressed_size=1,
        uncompressed_size=1,
        trailing_size=0,
        checksum=0,
        rolling_key=0,
        route_id=route_id,
        difficulty_index=difficulty_index,
        extended_input_records=False,
        stages=stages if stages is not None else (_stage(),),
    )


class FinalBReplayValidationTests(unittest.TestCase):
    def _fixed_slots(self, root: Path, count: int) -> None:
        replay_dir = root / "replay"
        replay_dir.mkdir()
        for slot in range(1, count + 1):
            (replay_dir / f"th8_{slot:02d}.rpy").write_bytes(b"x")

    def test_exact_zero_bomb_finalb_slot_is_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixed_slots(root, 13)

            def decode(path: Path) -> tuple[ReplayMetadata, bytes]:
                return _metadata(path.name), b"decoded"

            with (
                patch.object(replay_observer, "decode_replay", side_effect=decode),
                patch.object(
                    replay_observer,
                    "_sha256",
                    return_value=EXPECTED_SHA256,
                ),
            ):
                contract = replay_observer.validate_finalb_replay(
                    root,
                    slot=13,
                    expected_sha256=EXPECTED_SHA256,
                )
        self.assertEqual(contract.slot, 13)
        self.assertEqual(contract.compact_index, 12)
        self.assertEqual(contract.stage_route_index, 7)
        self.assertEqual(contract.stage_frame_count, 51_711)
        self.assertEqual(contract.stage_bomb_press_frames, ())

    def test_missing_preceding_fixed_slot_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixed_slots(root, 12)
            with (
                patch.object(
                    replay_observer,
                    "decode_replay",
                    side_effect=lambda path: (_metadata(path.name), b"decoded"),
                ),
                self.assertRaises(FileNotFoundError),
            ):
                replay_observer.validate_finalb_replay(
                    root,
                    slot=13,
                    expected_sha256=EXPECTED_SHA256,
                )

    def test_bomb_press_in_target_stage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixed_slots(root, 1)
            metadata = _metadata(
                "th8_01.rpy",
                stages=(_stage(bomb_press_frames=(123,)),),
            )
            with (
                patch.object(
                    replay_observer,
                    "decode_replay",
                    return_value=(metadata, b"decoded"),
                ),
                patch.object(
                    replay_observer,
                    "_sha256",
                    return_value=EXPECTED_SHA256,
                ),
                self.assertRaisesRegex(RuntimeError, "Bomb presses"),
            ):
                replay_observer.validate_finalb_replay(
                    root,
                    slot=1,
                    expected_sha256=EXPECTED_SHA256,
                )

    def test_nonfinal_or_multistage_replay_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixed_slots(root, 1)
            metadata = _metadata(
                "th8_01.rpy",
                stages=(_stage(stage_index=5), _stage()),
            )
            with (
                patch.object(
                    replay_observer,
                    "decode_replay",
                    return_value=(metadata, b"decoded"),
                ),
                patch.object(
                    replay_observer,
                    "_sha256",
                    return_value=EXPECTED_SHA256,
                ),
                self.assertRaisesRegex(RuntimeError, "only Final-B"),
            ):
                replay_observer.validate_finalb_replay(
                    root,
                    slot=1,
                    expected_sha256=EXPECTED_SHA256,
                )

    def test_generic_stage5_contract_binds_exact_single_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixed_slots(root, 1)
            metadata = _metadata(
                "th8_01.rpy",
                stages=(_stage(stage_index=5),),
            )
            with (
                patch.object(
                    replay_observer,
                    "decode_replay",
                    return_value=(metadata, b"decoded"),
                ),
                patch.object(
                    replay_observer,
                    "_sha256",
                    return_value=EXPECTED_SHA256,
                ),
            ):
                contract = replay_observer.validate_native_stage_replay(
                    root,
                    slot=1,
                    expected_sha256=EXPECTED_SHA256,
                    expected_route_id=2,
                    expected_difficulty_index=3,
                    expected_stage_route_index=5,
                )
        self.assertEqual(contract.stage_route_index, 5)


class ReplayMenuStateTests(unittest.TestCase):
    def test_native_replay_offsets_are_read_from_title_manager(self) -> None:
        manager = 0x100000
        values = {
            manager + replay_observer.REPLAY_ENTRY_COUNT_OFFSET: 15,
            manager + replay_observer.REPLAY_SELECTED_ENTRY_OFFSET: 12,
            manager + replay_observer.REPLAY_SELECTED_STAGE_OFFSET: 7,
        }

        class Reader:
            def __init__(self, _api: object, _pid: int) -> None:
                pass

            def u32(self, address: int) -> int:
                return values[address]

            def close(self) -> None:
                pass

        with (
            patch.object(
                replay_observer,
                "read_title_menu_state",
                return_value={
                    "manager": manager,
                    "mode": replay_observer.TITLE_MODE_REPLAY,
                    "substate": replay_observer.REPLAY_SUBSTATE_CONFIRM,
                    "cursor": 0,
                },
            ),
            patch.object(replay_observer, "ProcessReader", Reader),
        ):
            state = replay_observer.read_replay_menu_state(object(), 123)
        self.assertEqual(state["replay_entry_count"], 15)
        self.assertEqual(state["replay_selected_entry"], 12)
        self.assertEqual(state["replay_selected_stage"], 7)

    def test_replay_substate_wait_does_not_accept_other_substate(self) -> None:
        states = iter(
            (
                {
                    "mode": replay_observer.TITLE_MODE_REPLAY,
                    "substate": replay_observer.REPLAY_SUBSTATE_LIST,
                },
                {
                    "mode": replay_observer.TITLE_MODE_REPLAY,
                    "substate": replay_observer.REPLAY_SUBSTATE_STAGE,
                },
            )
        )
        ticks = iter((0.0, 0.0, 0.01, 0.02))
        with patch.object(
            replay_observer,
            "read_replay_menu_state",
            side_effect=lambda _api, _pid: next(states),
        ):
            state = replay_observer.wait_for_replay_substate(
                object(),
                123,
                substate=replay_observer.REPLAY_SUBSTATE_STAGE,
                timeout_seconds=1.0,
                clock=lambda: next(ticks),
                sleeper=lambda _seconds: None,
            )
        self.assertEqual(
            state["substate"],
            replay_observer.REPLAY_SUBSTATE_STAGE,
        )


if __name__ == "__main__":
    unittest.main()
