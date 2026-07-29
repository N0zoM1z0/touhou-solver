from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from th08_ecl_auxiliary import (
    AuxiliaryEclVmState,
    AuxiliaryLiteralFireBatchLowerer,
    AuxiliaryLiteralFireRequest,
    build_exact_runtime_instruction_index,
    lower_auxiliary_literal_fire_batch,
)
from th08_ecl_tool.core import parse_ecl
from th08_live.auxiliary_vm.model import (
    ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
    ACTIVE_VM_BYTES,
)


_ROOT = Path(__file__).resolve().parents[1]
_ECL_PATH = _ROOT / "artifacts" / "decoded" / "ecldata5.ecl"
_BASE = 0x02100000


class AuxiliaryEclCachedBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.image = _ECL_PATH.read_bytes()
        cls.ecl = parse_ecl(_ECL_PATH)
        cls.image_sha256 = hashlib.sha256(cls.image).hexdigest()
        cls.index = build_exact_runtime_instruction_index(
            cls.ecl,
            cls.image,
            runtime_base=_BASE,
            expected_sha256=cls.image_sha256,
        )
        cls.pc = _BASE + cls.ecl.subroutines[69].instructions[0].offset

    def _request(self, elapsed: int) -> AuxiliaryLiteralFireRequest:
        active_vm = bytearray(ACTIVE_VM_BYTES)
        struct.pack_into(
            "<IiIi",
            active_vm,
            0,
            self.pc,
            -1,
            0,
            elapsed,
        )
        struct.pack_into(
            "<I",
            active_vm,
            ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
            1,
        )
        return AuxiliaryLiteralFireRequest(
            state=AuxiliaryEclVmState.from_active_vm(bytes(active_vm)),
            timer_tick_horizon=16,
        )

    def _reference(
        self,
        requests: tuple[AuxiliaryLiteralFireRequest, ...],
    ):
        return lower_auxiliary_literal_fire_batch(
            requests,
            instruction_at=self.index.__getitem__,
            active_difficulty_mask=0x08,
            time_scale=None,
            max_instructions=64,
            max_physical_steps=65536,
        )

    def test_bounded_lru_preserves_results_and_request_mapping(self) -> None:
        request_0 = self._request(0)
        request_1 = self._request(1)
        lowerer = AuxiliaryLiteralFireBatchLowerer(
            instruction_at=self.index.__getitem__,
            active_difficulty_mask=0x08,
            cache_capacity=1,
        )

        first_requests = (request_0, request_0, request_1)
        first = lowerer.lower(first_requests)
        self.assertEqual(first.batch, self._reference(first_requests))
        self.assertEqual(
            first.cache.record(),
            {
                "request_count": 3,
                "request_local_hits": 1,
                "persistent_hits": 0,
                "misses": 2,
                "evictions": 1,
                "entries_after": 1,
                "capacity": 1,
            },
        )

        second_requests = (request_1, request_0)
        second = lowerer.lower(second_requests)
        self.assertEqual(second.batch, self._reference(second_requests))
        self.assertEqual(second.cache.persistent_hits, 1)
        self.assertEqual(second.cache.misses, 1)
        self.assertEqual(second.cache.evictions, 1)
        self.assertEqual(second.cache.entries_after, 1)

        lowerer.clear()
        self.assertEqual(lowerer.cache_entries, 0)
        after_clear = lowerer.lower((request_0,))
        self.assertEqual(after_clear.cache.misses, 1)
        self.assertEqual(after_clear.cache.persistent_hits, 0)

    def test_invalid_resource_bounds_fail_closed(self) -> None:
        common = {
            "instruction_at": self.index.__getitem__,
            "active_difficulty_mask": 0x08,
        }
        for override in (
            {"cache_capacity": 0},
            {"max_instructions": 0},
            {"max_physical_steps": 0},
            {"active_difficulty_mask": 0},
        ):
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    AuxiliaryLiteralFireBatchLowerer(
                        **{**common, **override},
                    )


if __name__ == "__main__":
    unittest.main()
