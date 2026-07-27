from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from th08_live import LiveSession


class _FakeApi:
    def __init__(self, events: list[object]) -> None:
        self.events = events

    def find_pid(self, target_exe: str) -> int:
        self.events.append(("find_pid", target_exe))
        return 73


class _FakeReader:
    def __init__(
        self,
        api: _FakeApi,
        pid: int,
        events: list[object],
    ) -> None:
        self.api = api
        self.pid = pid
        self.events = events
        self.closed = False
        events.append(("reader_open", pid))

    def close(self) -> None:
        if not self.closed:
            self.events.append("reader_close")
            self.closed = True


class LiveSessionTests(unittest.TestCase):
    def test_context_discovers_pid_and_releases_in_order(self) -> None:
        events: list[object] = []
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "nested" / "trace.jsonl"
            api = _FakeApi(events)

            with LiveSession(
                output_path=output_path,
                requested_pid=None,
                target_exe="th08.exe",
                api_factory=lambda: api,
                reader_factory=lambda current_api, pid: _FakeReader(
                    current_api,
                    pid,
                    events,
                ),
                key_releaser=lambda current_api: events.append(
                    ("release_keys", current_api is api)
                ),
            ) as session:
                self.assertIs(session.api, api)
                self.assertEqual(session.pid, 73)
                session.output.write('{"kind":"test"}\n')

            self.assertEqual(
                events,
                [
                    ("find_pid", "th08.exe"),
                    ("reader_open", 73),
                    ("release_keys", True),
                    "reader_close",
                ],
            )
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                '{"kind":"test"}\n',
            )

    def test_release_and_close_are_idempotent_with_explicit_pid(self) -> None:
        events: list[object] = []
        with tempfile.TemporaryDirectory() as directory:
            api = _FakeApi(events)
            session = LiveSession(
                output_path=Path(directory) / "trace.jsonl",
                requested_pid=91,
                target_exe="unused.exe",
                api_factory=lambda: api,
                reader_factory=lambda current_api, pid: _FakeReader(
                    current_api,
                    pid,
                    events,
                ),
                key_releaser=lambda _api: events.append("release_keys"),
            )

            session.__enter__()
            session.release_keys()
            session.release_keys()
            session.close()
            session.close()

            self.assertEqual(
                events,
                [
                    ("reader_open", 91),
                    "release_keys",
                    "reader_close",
                ],
            )

    def test_exception_still_releases_keys_and_closes_reader(self) -> None:
        events: list[object] = []
        with tempfile.TemporaryDirectory() as directory:
            api = _FakeApi(events)
            with self.assertRaisesRegex(RuntimeError, "boom"):
                with LiveSession(
                    output_path=Path(directory) / "trace.jsonl",
                    requested_pid=19,
                    target_exe="unused.exe",
                    api_factory=lambda: api,
                    reader_factory=lambda current_api, pid: _FakeReader(
                        current_api,
                        pid,
                        events,
                    ),
                    key_releaser=lambda _api: events.append(
                        "release_keys"
                    ),
                ):
                    raise RuntimeError("boom")

            self.assertEqual(
                events,
                [
                    ("reader_open", 19),
                    "release_keys",
                    "reader_close",
                ],
            )


if __name__ == "__main__":
    unittest.main()
