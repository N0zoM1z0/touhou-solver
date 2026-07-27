from __future__ import annotations

import io
import json
import unittest

from th08_live import TraceSink


class _Output(io.StringIO):
    def __init__(self) -> None:
        super().__init__()
        self.flush_count = 0

    def flush(self) -> None:
        self.flush_count += 1
        super().flush()


class TraceSinkTests(unittest.TestCase):
    def test_emit_many_preserves_jsonl_order_and_flush_boundary(
        self,
    ) -> None:
        output = _Output()
        ticks = iter((1.0, 1.004))
        sink = TraceSink(output, clock=lambda: next(ticks))

        elapsed = sink.emit_many(
            (
                {"kind": "first", "value": [1, 2]},
                {"kind": "second", "value": None},
            ),
            flush=True,
            measure=True,
        )

        self.assertAlmostEqual(elapsed, 4.0)
        self.assertEqual(output.flush_count, 1)
        self.assertEqual(
            [json.loads(line) for line in output.getvalue().splitlines()],
            [
                {"kind": "first", "value": [1, 2]},
                {"kind": "second", "value": None},
            ],
        )

    def test_summary_and_runtime_error_keep_exact_schema(self) -> None:
        output = _Output()
        sink = TraceSink(
            output,
            clock=lambda: self.fail(
                "unmeasured trace writes must not sample the clock"
            ),
        )

        sink.runtime_error(ValueError("bad"), last_frame=10)
        sink.summary(
            last_frame=10,
            counter_gaps=2,
            hit_count=1,
            termination_reason="agent_error",
        )

        self.assertEqual(
            [json.loads(line) for line in output.getvalue().splitlines()],
            [
                {
                    "kind": "runtime_error",
                    "error_type": "ValueError",
                    "error": "bad",
                    "last_frame": 10,
                },
                {
                    "kind": "summary",
                    "last_frame": 10,
                    "counter_gaps": 2,
                    "hit_count": 1,
                    "termination_reason": "agent_error",
                },
            ],
        )
        self.assertEqual(output.flush_count, 1)


if __name__ == "__main__":
    unittest.main()
