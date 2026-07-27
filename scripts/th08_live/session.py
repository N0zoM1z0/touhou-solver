"""Process, trace-file, and injected-key ownership for one live run."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, TextIO

from th08_runtime_agent import (
    ProcessReader,
    Win32,
    release_injected_keys,
)


class LiveSession:
    """Acquire and release the base resources shared by one live run."""

    def __init__(
        self,
        *,
        output_path: Path,
        requested_pid: int | None,
        target_exe: str,
        api_factory: Callable[[], Any] = Win32,
        reader_factory: Callable[[Any, int], Any] = ProcessReader,
        key_releaser: Callable[[Any], None] = release_injected_keys,
    ) -> None:
        self._output_path = output_path
        self._requested_pid = requested_pid
        self._target_exe = target_exe
        self._api_factory = api_factory
        self._reader_factory = reader_factory
        self._key_releaser = key_releaser
        self._api: Any | None = None
        self._pid: int | None = None
        self._reader: Any | None = None
        self._output: TextIO | None = None
        self._entered = False
        self._keys_released = False
        self._closed = False

    @property
    def api(self) -> Any:
        if self._api is None:
            raise RuntimeError("live session has not been entered")
        return self._api

    @property
    def pid(self) -> int:
        if self._pid is None:
            raise RuntimeError("live session has not been entered")
        return self._pid

    @property
    def reader(self) -> Any:
        if self._reader is None:
            raise RuntimeError("live session has not been entered")
        return self._reader

    @property
    def output(self) -> TextIO:
        if self._output is None:
            raise RuntimeError("live session has not been entered")
        return self._output

    def __enter__(self) -> LiveSession:
        if self._entered:
            raise RuntimeError("live session cannot be entered twice")
        if self._closed:
            raise RuntimeError("closed live session cannot be entered")
        self._entered = True
        try:
            self._api = self._api_factory()
            self._pid = (
                self._requested_pid
                if self._requested_pid is not None
                else int(self._api.find_pid(self._target_exe))
            )
            self._reader = self._reader_factory(self._api, self._pid)
            self._output_path.parent.mkdir(parents=True, exist_ok=True)
            self._output = self._output_path.open(
                "w",
                encoding="utf-8",
                newline="\n",
            )
        except BaseException:
            self._close_acquired_resources()
            self._closed = True
            raise
        return self

    def release_keys(self) -> None:
        """Release injected input at most once after a successful release."""

        if self._keys_released or self._api is None:
            return
        self._key_releaser(self._api)
        self._keys_released = True

    def close(self) -> None:
        """Idempotently release input, trace output, and process access."""

        if self._closed:
            return
        try:
            self.release_keys()
        finally:
            self._close_acquired_resources()
            self._closed = True

    def _close_acquired_resources(self) -> None:
        try:
            if self._output is not None:
                self._output.close()
        finally:
            if self._reader is not None:
                self._reader.close()

    def __exit__(
        self,
        _exc_type: object,
        _exc: object,
        _traceback: object,
    ) -> None:
        self.close()
