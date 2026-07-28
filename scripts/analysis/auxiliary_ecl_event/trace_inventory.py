"""Streaming inventory for compact auxiliary-VM trace records."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


_ACTIVE_VM_BYTES = 0x228
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_ACTIVE_VM_HEX_PATTERN = re.compile(
    rf"[0-9a-fA-F]{{{_ACTIVE_VM_BYTES * 2}}}\Z"
)


@dataclass(frozen=True)
class AuxiliaryTraceInventory:
    path: Path
    sha256: str
    byte_count: int
    line_count: int
    batch_count: int
    first_batch_frame: int | None
    last_batch_frame: int | None
    schema_versions: tuple[tuple[int, int], ...]
    statuses: tuple[tuple[str, int], ...]
    usable_record_count: int
    target_subroutines: tuple[tuple[int, int], ...]
    call_depths: tuple[tuple[int, int], ...]
    auxiliary_markers: tuple[tuple[int, int], ...]
    unique_active_vm_hashes: int
    active_vm_hash_only_rows: int
    replayable_raw_state_rows: int

    @property
    def event_replay_status(self) -> str:
        if self.replayable_raw_state_rows == self.usable_record_count:
            return "raw_state_available"
        if self.replayable_raw_state_rows:
            return "partial_raw_state"
        if self.active_vm_hash_only_rows:
            return "unavailable_hash_only"
        return "unavailable_no_active_state"

    def record(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "bytes": self.byte_count,
            "line_count": self.line_count,
            "batch_count": self.batch_count,
            "first_batch_frame": self.first_batch_frame,
            "last_batch_frame": self.last_batch_frame,
            "schema_versions": {
                str(key): value for key, value in self.schema_versions
            },
            "statuses": dict(self.statuses),
            "usable_record_count": self.usable_record_count,
            "target_subroutines": {
                str(key): value for key, value in self.target_subroutines
            },
            "call_depths": {
                str(key): value for key, value in self.call_depths
            },
            "auxiliary_markers": {
                str(key): value for key, value in self.auxiliary_markers
            },
            "unique_active_vm_hashes": self.unique_active_vm_hashes,
            "active_vm_hash_only_rows": self.active_vm_hash_only_rows,
            "replayable_raw_state_rows": self.replayable_raw_state_rows,
            "event_replay_status": self.event_replay_status,
        }


def _integer(value: object, *, field: str, line_number: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"trace line {line_number} has invalid integer {field}"
        )
    return value


def _raw_active_vm(
    record: dict[str, object],
    *,
    active_hash: str | None,
    line_number: int,
) -> bytes | None:
    active_vm_hex = record.get("active_vm_hex")
    if active_vm_hex is None:
        return None
    if (
        not isinstance(active_vm_hex, str)
        or _ACTIVE_VM_HEX_PATTERN.fullmatch(active_vm_hex) is None
    ):
        raise ValueError(
            f"trace line {line_number} has invalid raw active VM"
        )
    active_vm = bytes.fromhex(active_vm_hex)
    if (
        active_hash is not None
        and hashlib.sha256(active_vm).hexdigest() != active_hash
    ):
        raise ValueError(
            f"trace line {line_number} active VM hash mismatch"
        )
    return active_vm


def _has_structural_active_state(
    record: dict[str, object],
    *,
    line_number: int,
) -> bool:
    fields = ("active_pc", "timer_elapsed", "timer_fraction_bits")
    present = tuple(field in record for field in fields)
    if any(present) and not all(present):
        raise ValueError(
            f"trace line {line_number} has partial structural active VM state"
        )
    if not all(present):
        return False
    active_pc = _integer(
        record["active_pc"],
        field="record.active_pc",
        line_number=line_number,
    )
    timer_elapsed = _integer(
        record["timer_elapsed"],
        field="record.timer_elapsed",
        line_number=line_number,
    )
    timer_fraction_bits = _integer(
        record["timer_fraction_bits"],
        field="record.timer_fraction_bits",
        line_number=line_number,
    )
    if not 0x00010000 <= active_pc <= 0x7FFFFFFF:
        raise ValueError(
            f"trace line {line_number} has invalid structural active PC"
        )
    if timer_elapsed < 0:
        raise ValueError(
            f"trace line {line_number} has negative structural timer"
        )
    if not 0 <= timer_fraction_bits <= 0xFFFFFFFF:
        raise ValueError(
            f"trace line {line_number} has invalid timer fraction bits"
        )
    return True


def scan_compact_auxiliary_trace(path: Path) -> AuxiliaryTraceInventory:
    """Scan one JSONL trace without retaining decision or batch payloads."""

    digest = hashlib.sha256()
    byte_count = 0
    line_count = 0
    batch_count = 0
    first_batch_frame: int | None = None
    last_batch_frame: int | None = None
    schema_versions: Counter[int] = Counter()
    statuses: Counter[str] = Counter()
    targets: Counter[int] = Counter()
    call_depths: Counter[int] = Counter()
    markers: Counter[int] = Counter()
    active_hashes: set[str] = set()
    active_vm_hash_only_rows = 0
    replayable_raw_state_rows = 0
    usable_records = 0

    with path.open("rb") as stream:
        for raw_line in stream:
            digest.update(raw_line)
            byte_count += len(raw_line)
            line_count += 1
            try:
                row = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError(
                    f"invalid JSONL at trace line {line_count}: {error}"
                ) from error
            if not isinstance(row, dict) or row.get("kind") != "auxiliary_vm_batch":
                continue
            batch_count += 1
            frame = _integer(
                row.get("frame"),
                field="frame",
                line_number=line_count,
            )
            first_batch_frame = (
                frame if first_batch_frame is None else min(first_batch_frame, frame)
            )
            last_batch_frame = (
                frame if last_batch_frame is None else max(last_batch_frame, frame)
            )
            schema_versions[
                _integer(
                    row.get("schema_version"),
                    field="schema_version",
                    line_number=line_count,
                )
            ] += 1
            status = row.get("status")
            if not isinstance(status, str):
                raise ValueError(
                    f"trace line {line_count} has invalid batch status"
                )
            statuses[status] += 1
            observation = row.get("observation")
            if observation is None:
                continue
            if not isinstance(observation, dict):
                raise ValueError(
                    f"trace line {line_count} has invalid observation"
                )
            records = observation.get("records")
            if not isinstance(records, list):
                raise ValueError(
                    f"trace line {line_count} has invalid record list"
                )
            for record in records:
                if not isinstance(record, dict):
                    raise ValueError(
                        f"trace line {line_count} has invalid record"
                    )
                status_bits = _integer(
                    record.get("status_bits"),
                    field="record.status_bits",
                    line_number=line_count,
                )
                if status_bits:
                    continue
                usable_records += 1
                targets[
                    _integer(
                        record.get("target_subroutine"),
                        field="record.target_subroutine",
                        line_number=line_count,
                    )
                ] += 1
                call_depths[
                    _integer(
                        record.get("call_depth"),
                        field="record.call_depth",
                        line_number=line_count,
                    )
                ] += 1
                markers[
                    _integer(
                        record.get("auxiliary_marker"),
                        field="record.auxiliary_marker",
                        line_number=line_count,
                    )
                ] += 1
                active_hash = record.get("active_vm_sha256")
                if active_hash is not None:
                    if (
                        not isinstance(active_hash, str)
                        or _SHA256_PATTERN.fullmatch(active_hash) is None
                    ):
                        raise ValueError(
                            f"trace line {line_count} has invalid active VM hash"
                        )
                    active_hashes.add(active_hash)
                raw_active_vm = _raw_active_vm(
                    record,
                    active_hash=active_hash,
                    line_number=line_count,
                )
                has_raw_state = (
                    raw_active_vm is not None
                    or _has_structural_active_state(
                        record,
                        line_number=line_count,
                    )
                )
                if has_raw_state:
                    replayable_raw_state_rows += 1
                elif active_hash is not None:
                    active_vm_hash_only_rows += 1

    return AuxiliaryTraceInventory(
        path=path,
        sha256=digest.hexdigest(),
        byte_count=byte_count,
        line_count=line_count,
        batch_count=batch_count,
        first_batch_frame=first_batch_frame,
        last_batch_frame=last_batch_frame,
        schema_versions=tuple(sorted(schema_versions.items())),
        statuses=tuple(sorted(statuses.items())),
        usable_record_count=usable_records,
        target_subroutines=tuple(sorted(targets.items())),
        call_depths=tuple(sorted(call_depths.items())),
        auxiliary_markers=tuple(sorted(markers.items())),
        unique_active_vm_hashes=len(active_hashes),
        active_vm_hash_only_rows=active_vm_hash_only_rows,
        replayable_raw_state_rows=replayable_raw_state_rows,
    )


__all__ = ["AuxiliaryTraceInventory", "scan_compact_auxiliary_trace"]
