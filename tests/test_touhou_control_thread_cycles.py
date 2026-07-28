from __future__ import annotations

import unittest
from unittest import mock

from touhou_control import thread_cycles


class _Call:
    def __init__(self, function):
        self.function = function
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.function(*args)


class _Kernel32:
    def __init__(self, values: list[int | None]) -> None:
        self.values = iter(values)
        self.GetCurrentThread = _Call(lambda: 123)
        self.QueryThreadCycleTime = _Call(self._query)

    def _query(self, thread, destination) -> int:
        if thread != 123:
            raise AssertionError("unexpected thread handle")
        value = next(self.values)
        if value is None:
            return 0
        destination.contents.value = value
        return 1


class CurrentThreadCycleSamplerTests(unittest.TestCase):
    def test_non_windows_is_explicitly_unavailable(self) -> None:
        with mock.patch.object(thread_cycles.os, "name", "posix"):
            sampler = thread_cycles.CurrentThreadCycleSampler()
        self.assertEqual(
            sampler.source,
            thread_cycles.THREAD_CYCLE_SOURCE_UNAVAILABLE,
        )
        self.assertIsNone(sampler.read())

    def test_windows_reuses_one_destination_and_keeps_gil_boundary(self) -> None:
        kernel32 = _Kernel32([100, 175])
        with (
            mock.patch.object(thread_cycles.os, "name", "nt"),
            mock.patch.object(
                thread_cycles.ctypes,
                "PyDLL",
                return_value=kernel32,
            ) as loader,
        ):
            sampler = thread_cycles.CurrentThreadCycleSampler()
        self.assertEqual(
            sampler.source,
            thread_cycles.THREAD_CYCLE_SOURCE_WINDOWS,
        )
        pointer = sampler._value_pointer
        self.assertEqual(sampler.read(), 100)
        self.assertIs(sampler._value_pointer, pointer)
        self.assertEqual(sampler.read(), 175)
        loader.assert_called_once_with("kernel32", use_last_error=True)

    def test_query_failure_is_sticky_and_never_fabricates_zero(self) -> None:
        kernel32 = _Kernel32([None, 400])
        with (
            mock.patch.object(thread_cycles.os, "name", "nt"),
            mock.patch.object(
                thread_cycles.ctypes,
                "PyDLL",
                return_value=kernel32,
            ),
        ):
            sampler = thread_cycles.CurrentThreadCycleSampler()
        self.assertIsNone(sampler.read())
        self.assertEqual(
            sampler.source,
            thread_cycles.THREAD_CYCLE_SOURCE_QUERY_FAILED,
        )
        self.assertIsNone(sampler.read())


if __name__ == "__main__":
    unittest.main()
