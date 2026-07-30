from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from th08_automation import practice_replay_save


class PracticeReplaySaveTests(unittest.TestCase):
    def test_result_menu_base_resolves_through_live_update_node(self) -> None:
        node1 = 0x09000000
        node2 = 0x09000100
        context = 0x0A000000

        class Reader:
            def __init__(self, _api, _pid) -> None:
                pass

            def close(self) -> None:
                pass

            def u32(self, address: int) -> int:
                values = {
                    (
                        practice_replay_save.UPDATE_CHAIN_HEAD
                        + practice_replay_save.UPDATE_CHAIN_NEXT_OFFSET
                    ): node1,
                    (
                        node1
                        + practice_replay_save
                        .UPDATE_NODE_CALLBACK_OFFSET
                    ): 0x00400000,
                    (
                        node1
                        + practice_replay_save.UPDATE_CHAIN_NEXT_OFFSET
                    ): node2,
                    (
                        node2
                        + practice_replay_save
                        .UPDATE_NODE_CALLBACK_OFFSET
                    ): practice_replay_save.RESULT_MENU_UPDATE_CALLBACK,
                    (
                        node2
                        + practice_replay_save
                        .UPDATE_NODE_CONTEXT_OFFSET
                    ): context,
                    (
                        context
                        + practice_replay_save
                        .RESULT_MENU_UPDATE_NODE_OFFSET
                    ): node2,
                    (
                        node2
                        + practice_replay_save.UPDATE_CHAIN_NEXT_OFFSET
                    ): 0,
                }
                return values[address]

            def i32(self, address: int) -> int:
                if address != (
                    context
                    + practice_replay_save.REPLAY_SAVE_STATE_OFFSET
                ):
                    raise AssertionError(
                        f"unexpected i32 address {address:#x}"
                    )
                return practice_replay_save.REPLAY_SAVE_STATE_PROMPT

        with patch.object(
            practice_replay_save,
            "ProcessReader",
            Reader,
        ):
            self.assertEqual(
                practice_replay_save.find_replay_save_menu_base(
                    object(),
                    123,
                ),
                context,
            )

    def test_wait_requires_exact_native_state_and_age(self) -> None:
        states = iter(
            (
                {"state": 10, "age": 19},
                {"state": 12, "age": 30},
                {"state": 10, "age": 20},
            )
        )
        ticks = iter((0.0, 0.0, 0.1, 0.2, 0.3, 0.4))
        with patch.object(
            practice_replay_save,
            "read_replay_save_menu_state",
            side_effect=lambda _api, _pid: next(states),
        ):
            state = practice_replay_save.wait_for_replay_save_state(
                object(),
                123,
                states=(10,),
                minimum_age=20,
                timeout_seconds=1.0,
                clock=lambda: next(ticks),
                sleeper=lambda _seconds: None,
            )
        self.assertEqual(state, {"state": 10, "age": 20})

    def test_saved_replay_validation_rejects_bomb(self) -> None:
        from th08_replay import ReplayMetadata, ReplayStage

        stage = ReplayStage(
            stage_index=5,
            data_offset=0,
            auxiliary_offset=0,
            rng_seed=1,
            lives=8,
            bombs=3,
            byte_1c=0,
            byte_1f=0,
            input_record_stride=2,
            frame_count=10,
            input_sha256="12" * 32,
            bomb_press_frames=(4,),
        )
        metadata = ReplayMetadata(
            name="th8_15.rpy",
            sha256="34" * 32,
            file_size=1,
            encoded_main_size=1,
            compressed_size=1,
            uncompressed_size=1,
            trailing_size=0,
            checksum=0,
            rolling_key=0,
            route_id=2,
            difficulty_index=3,
            extended_input_records=False,
            stages=(stage,),
        )
        with (
            patch.object(
                practice_replay_save,
                "decode_replay",
                return_value=(metadata, b"decoded"),
            ),
            self.assertRaisesRegex(RuntimeError, "Bomb"),
        ):
            practice_replay_save._validate_saved_replay(
                object(),
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )

    def test_failed_overwrite_restores_content_addressed_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay = root / "th8_15.rpy"
            archive = root / "archive.rpy"
            replay.write_bytes(b"invalid-new")
            archive.write_bytes(b"known-old")
            metadata = type("Metadata", (), {"sha256": "ab" * 32})()
            with patch.object(
                practice_replay_save,
                "decode_replay",
                return_value=(metadata, b"decoded"),
            ):
                status = (
                    practice_replay_save
                    ._restore_replay_after_failed_write(
                        replay,
                        {
                            "archive": archive.as_posix(),
                            "metadata": {"sha256": "ab" * 32},
                        },
                    )
                )

            self.assertEqual(replay.read_bytes(), b"known-old")
            self.assertIn("previous replay restored", status)


if __name__ == "__main__":
    unittest.main()
