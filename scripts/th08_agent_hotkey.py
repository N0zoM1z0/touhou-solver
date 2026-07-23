#!/usr/bin/env python3
"""Prewarmed F8/F9 handoff for manually selected TH08 route-2 trials."""

from __future__ import annotations

import ctypes
import json
import os
import sys
import threading
import time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

from runtime_agent import InputTransition
from th08_corridor_adapter import prewarm_th08_corridor
from th08_live_dodge_agent import build_parser as build_agent_parser
from th08_live_dodge_agent import run as run_agent
from th08_runtime_agent import (
    ADDR_NO_LIFE_DECREMENT_PATCH,
    TARGET_EXE,
    ProcessReader,
    Win32,
    _require_foreground,
    observe_state,
    release_injected_keys,
    send_transitions,
    verify_target,
)
from th08_trial_report import summarize_rows


HOTKEY_ARM = 1
HOTKEY_STOP = 2
HOTKEY_QUIT = 3
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
LONG_RUN_DURATION_SECONDS = 3600
ERROR_ALREADY_EXISTS = 183
INSTANCE_MUTEX_NAME = r"Local\Codex_TH08_Agent_Hotkey"


def one_shot_trial_finished(*, agent_started: bool, agent_alive: bool) -> bool:
    """Return whether a one-shot daemon must exit before accepting another arm."""
    return agent_started and not agent_alive


def build_long_run_arguments(
    *,
    output: Path,
    stop_file: Path,
    pid: int,
    difficulty: int,
    expected_stage: int | None = None,
    terminal_stage: int | None = None,
) -> list[str]:
    arguments = [
        str(output),
        "--pid",
        str(pid),
        "--duration",
        str(LONG_RUN_DURATION_SECONDS),
        "--difficulty",
        str(difficulty),
        "--stop-after-hits",
        "0",
        "--post-hit-frames",
        "0",
        "--log-every",
        "1",
        "--trace-radius",
        "160",
        "--auto-confirm-every",
        "15",
        "--auto-confirm-idle-frames",
        "20",
        "--no-bomb",
        "--stop-file",
        str(stop_file),
        "--armed",
    ]
    if expected_stage is not None:
        arguments.extend(("--expected-stage", str(expected_stage)))
    if terminal_stage is not None:
        arguments.extend(("--terminal-stage", str(terminal_stage)))
    return arguments


class AgentHotkey:
    def __init__(
        self,
        *,
        expected_stage: int | None = None,
        terminal_stage: int | None = None,
    ) -> None:
        if os.name != "nt":
            raise RuntimeError("th08_agent_hotkey.py must run under Windows Python")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.CreateMutexW.argtypes = [
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        self.kernel32.CreateMutexW.restype = wintypes.HANDLE
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        ctypes.set_last_error(0)
        self.instance_mutex = self.kernel32.CreateMutexW(
            None,
            False,
            INSTANCE_MUTEX_NAME,
        )
        if not self.instance_mutex:
            raise ctypes.WinError(ctypes.get_last_error(), "CreateMutexW")
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            self.kernel32.CloseHandle(self.instance_mutex)
            self.instance_mutex = None
            raise RuntimeError("another TH08 hotkey daemon is already running")
        self.api = Win32()
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = ctypes.c_short
        self.agent_thread: threading.Thread | None = None
        self.agent_error: Exception | None = None
        self.last_summary: dict[str, object] | None = None
        self.stop_file: Path | None = None
        self.output: Path | None = None
        self.expected_stage = expected_stage
        self.terminal_stage = terminal_stage
        self.artifact_dir = (
            Path(__file__).resolve().parent.parent
            / "artifacts"
            / "runtime_reports"
        )
        prewarm_th08_corridor()

    def _open_target(self) -> tuple[int, ProcessReader, dict[str, object]]:
        pid = self.api.find_pid(TARGET_EXE)
        reader = ProcessReader(self.api, pid)
        try:
            identity = verify_target(reader)
            if reader.u8(ADDR_NO_LIFE_DECREMENT_PATCH) != 0:
                raise RuntimeError("the no-life-decrement runtime patch is absent")
            return pid, reader, identity
        except Exception:
            reader.close()
            raise

    def _wait_ready(self, timeout: float = 10.0) -> None:
        assert self.output is not None
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            if self.agent_thread is None or not self.agent_thread.is_alive():
                raise RuntimeError("agent exited before wait_ready")
            if self.output.is_file():
                text = self.output.read_text(encoding="utf-8")
                if '"kind": "wait_ready"' in text:
                    return
            time.sleep(0.01)
        raise RuntimeError("timed out waiting for prewarmed agent")

    def _agent_worker(self, arguments: list[str]) -> None:
        assert self.output is not None
        try:
            result = run_agent(build_agent_parser().parse_args(arguments))
            if result:
                raise RuntimeError(f"agent returned {result}")
            rows = [
                json.loads(line)
                for line in self.output.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            report = summarize_rows(rows)
            self.last_summary = report
            summary = self.output.with_suffix(".summary.json")
            summary.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(
                "trial complete:",
                f"reason={report['termination_reason']}",
                f"hits={report['hit_frames']}",
                f"frames={report['first_frame']}..{report['last_frame']}",
                f"summary={summary}",
                flush=True,
            )
        except Exception as exc:
            self.agent_error = exc
            print(f"agent error: {exc}", file=sys.stderr, flush=True)

    def arm(self, *, output_path: Path | None = None) -> None:
        if self.agent_thread is not None and self.agent_thread.is_alive():
            print("agent is already active", flush=True)
            return
        self.agent_error = None
        self.last_summary = None
        pid, reader, _identity = self._open_target()
        try:
            _require_foreground(self.api, pid)
            state = observe_state(reader)
            gameplay_active = bool(state["gameplay_active"])
            if gameplay_active:
                difficulty = int(state["difficulty_index"])
                if difficulty not in (3, 4):
                    raise RuntimeError(
                        f"active gameplay difficulty is unsupported: {difficulty}"
                    )
                if int(state["route_id"]) != 2:
                    raise RuntimeError(
                        f"active gameplay route is not Sakuya/Remilia: "
                        f"{state['route_id']}"
                    )
            else:
                difficulty = 3

            self.artifact_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode = "lunatic" if difficulty == 3 else "extra"
            self.output = output_path or self.artifact_dir / (
                f"{mode}_route2_hotkey_longrun_{stamp}.jsonl"
            )
            self.output.parent.mkdir(parents=True, exist_ok=True)
            self.stop_file = self.output.with_suffix(".stop")
            self.output.unlink(missing_ok=True)
            self.stop_file.unlink(missing_ok=True)
            arguments = build_long_run_arguments(
                output=self.output,
                stop_file=self.stop_file,
                pid=pid,
                difficulty=difficulty,
                expected_stage=self.expected_stage,
                terminal_stage=self.terminal_stage,
            )
            if not gameplay_active:
                arguments.extend(("--wait-gameplay", "--wait-timeout", "30"))
            self.agent_thread = threading.Thread(
                target=self._agent_worker,
                args=(arguments,),
                name="th08-live-agent",
                daemon=False,
            )
            self.agent_thread.start()
            if not gameplay_active:
                self._wait_ready()
                _require_foreground(self.api, pid)
                send_transitions(
                    self.api,
                    (InputTransition(0x01, True),),
                )
                try:
                    time.sleep(0.06)
                finally:
                    send_transitions(
                        self.api,
                        (InputTransition(0x01, False),),
                    )
            print(
                f"agent armed: pid={pid} difficulty={difficulty} "
                f"gameplay={gameplay_active} output={self.output}",
                flush=True,
            )
        finally:
            reader.close()

    def wait_for_trial(self, timeout: float | None = None) -> Path:
        if self.agent_thread is None:
            raise RuntimeError("agent has not been armed")
        self.agent_thread.join(timeout=timeout)
        if self.agent_thread.is_alive():
            raise TimeoutError("agent trial did not finish before timeout")
        if self.agent_error is not None:
            raise RuntimeError(f"agent trial failed: {self.agent_error}")
        if self.output is None:
            raise RuntimeError("agent trial completed without an output path")
        return self.output

    def stop(self) -> None:
        if self.agent_thread is None or not self.agent_thread.is_alive():
            print("agent is not active", flush=True)
            return
        assert self.stop_file is not None
        self.stop_file.write_text("stop\n", encoding="ascii")
        print("safe stop requested", flush=True)

    def close(self) -> None:
        try:
            release_injected_keys(self.api)
        except OSError:
            pass
        if self.instance_mutex is not None:
            self.kernel32.CloseHandle(self.instance_mutex)
            self.instance_mutex = None

    def run(self) -> int:
        print(
            "TH08 agent prewarmed (async-key polling). "
            "F8 arm/enter long run, F9 stop+pause, F10 quit.",
            flush=True,
        )
        try:
            keys = {
                VK_F8: self.arm,
                VK_F9: self.stop,
            }
            previous = {virtual_key: False for virtual_key in keys}
            previous[VK_F10] = False
            while True:
                if one_shot_trial_finished(
                    agent_started=self.agent_thread is not None,
                    agent_alive=(
                        self.agent_thread is not None
                        and self.agent_thread.is_alive()
                    ),
                ):
                    print(
                        "trial worker finished; one-shot daemon exiting",
                        flush=True,
                    )
                    break
                quit_pressed = bool(
                    self.user32.GetAsyncKeyState(VK_F10) & 0x8000
                )
                if quit_pressed and not previous[VK_F10]:
                    self.stop()
                    break
                previous[VK_F10] = quit_pressed
                for virtual_key, callback in keys.items():
                    pressed = bool(
                        self.user32.GetAsyncKeyState(virtual_key) & 0x8000
                    )
                    if pressed and not previous[virtual_key]:
                        try:
                            callback()
                        except Exception as exc:
                            print(
                                f"hotkey error: {exc}",
                                file=sys.stderr,
                                flush=True,
                            )
                    previous[virtual_key] = pressed
                time.sleep(0.01)
            if self.agent_thread is not None and self.agent_thread.is_alive():
                self.agent_thread.join(timeout=10.0)
            return 0
        finally:
            self.close()


if __name__ == "__main__":
    try:
        agent = AgentHotkey()
    except Exception as exc:
        with open(
            r"\\wsl.localhost\ubuntu\tmp\th08_agent_hotkey.err",
            "a",
            encoding="utf-8",
        ) as error_output:
            print(f"startup error: {exc}", file=error_output)
        raise SystemExit(1)
    sys.stdout = open(
        r"\\wsl.localhost\ubuntu\tmp\th08_agent_hotkey.out",
        "w",
        encoding="utf-8",
        buffering=1,
    )
    sys.stderr = open(
        r"\\wsl.localhost\ubuntu\tmp\th08_agent_hotkey.err",
        "w",
        encoding="utf-8",
        buffering=1,
    )
    try:
        raise SystemExit(agent.run())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
