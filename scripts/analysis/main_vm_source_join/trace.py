"""Strict streaming reader for schema-11 main-VM inventory traces."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from th08_live.enemy_ecl_inventory import (
    ENEMY_MAIN_ECL_VM_INVENTORY_LAYOUT,
)

from .model import (
    ActivationBatch,
    DecisionScope,
    InventoryCapture,
    TraceScan,
    VmRow,
)


TRACE_KIND = "bullet_birth_audit"
TRACE_SCHEMA_VERSION = 11
ACTIVATION_EDGE_CODE = 3


class MainVmTraceError(ValueError):
    """Raised when trace evidence cannot support a strict offline join."""


def _integer(value: object, *, label: str) -> int:
    if type(value) is not int:
        raise MainVmTraceError(f"{label} must be an integer")
    return value


def _optional_integer(value: object, *, label: str) -> int | None:
    if value is None:
        return None
    return _integer(value, label=label)


def _decision_scope(record: dict[str, Any]) -> DecisionScope:
    spell = record.get("spell")
    if not isinstance(spell, dict):
        raise MainVmTraceError("decision spell must be an object")
    spell_id = None
    if spell.get("active") is True:
        spell_id = _integer(
            spell.get("spell_id"),
            label="active decision spell_id",
        )
    return DecisionScope(
        gameplay_epoch=_integer(
            record.get("gameplay_epoch"),
            label="decision gameplay_epoch",
        ),
        frame=_integer(record.get("frame"), label="decision frame"),
        stage_route_index=_integer(
            record.get("stage_route_index"),
            label="decision stage_route_index",
        ),
        spell_id=spell_id,
    )


def _vm_rows(inventory: dict[str, Any]) -> tuple[VmRow, ...]:
    if inventory.get("layout") != ENEMY_MAIN_ECL_VM_INVENTORY_LAYOUT:
        raise MainVmTraceError("unknown main-VM inventory layout")
    scanned_slots = _integer(
        inventory.get("scanned_slots"),
        label="inventory scanned_slots",
    )
    if scanned_slots != 64:
        raise MainVmTraceError("main-VM inventory must scan exactly 64 slots")
    active_slots = _integer(
        inventory.get("active_slots"),
        label="inventory active_slots",
    )
    valid_vms = _integer(
        inventory.get("valid_vms"),
        label="inventory valid_vms",
    )
    invalid_vms = _integer(
        inventory.get("invalid_active_vms"),
        label="inventory invalid_active_vms",
    )
    rows = inventory.get("rows")
    invalid_rows = inventory.get("invalid_rows")
    if not isinstance(rows, list) or not isinstance(invalid_rows, list):
        raise MainVmTraceError("inventory rows must be arrays")
    if (
        len(rows) != valid_vms
        or len(invalid_rows) != invalid_vms
        or valid_vms + invalid_vms != active_slots
    ):
        raise MainVmTraceError("inventory counts do not reconcile")

    decoded: list[VmRow] = []
    seen_slots: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != 9:
            raise MainVmTraceError(f"VM row {index} has invalid shape")
        values = [
            _integer(row[column], label=f"VM row {index} column {column}")
            for column in range(6)
        ]
        slot = values[0]
        if not 0 <= slot < scanned_slots or slot in seen_slots:
            raise MainVmTraceError(f"VM row {index} has invalid slot")
        seen_slots.add(slot)
        if not all(
            isinstance(row[column], list)
            for column in (6, 7, 8)
        ):
            raise MainVmTraceError(f"VM row {index} local projections are invalid")
        if (
            len(row[6]) != 8
            or len(row[7]) != 8
            or len(row[8]) != 4
            or not all(
                type(value) is int
                for column in (6, 7, 8)
                for value in row[column]
            )
        ):
            raise MainVmTraceError(f"VM row {index} local widths are invalid")
        decoded.append(VmRow(*values))
    return tuple(decoded)


def _activation_batch(
    record: dict[str, Any],
    *,
    scope: DecisionScope,
) -> ActivationBatch | None:
    observation = record.get("observation")
    if not isinstance(observation, dict):
        raise MainVmTraceError("birth observation must be an object")
    evidence_count = _integer(
        observation.get("evidence_count"),
        label="birth evidence_count",
    )
    evidence = observation.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("format") != "columnar_v1":
        raise MainVmTraceError("schema-11 evidence must use columnar_v1")
    codes = evidence.get("code")
    ages = evidence.get("age")
    if (
        not isinstance(codes, list)
        or not isinstance(ages, list)
        or len(codes) != evidence_count
        or len(ages) != evidence_count
        or not all(type(value) is int for value in (*codes, *ages))
    ):
        raise MainVmTraceError("birth code/age columns are invalid")
    activation_ages = tuple(
        age
        for code, age in zip(codes, ages, strict=True)
        if code == ACTIVATION_EDGE_CODE
    )
    if not activation_ages:
        return None
    support_start = _optional_integer(
        observation.get("previous_frame_before"),
        label="birth support start",
    )
    support_end = _integer(
        observation.get("frame_after"),
        label="birth support end",
    )
    if support_start is not None and support_start > support_end:
        raise MainVmTraceError("birth support is reversed")
    return ActivationBatch(
        scope=scope,
        support_start=support_start,
        support_end=support_end,
        bullet_count=len(activation_ages),
        ages=activation_ages,
    )


def scan_schema11_trace(trace_path: Path) -> TraceScan:
    """Read only decisions and schema-11 birth audits with strict joins."""

    digest = hashlib.sha256()
    trace_bytes = 0
    trace_lines = 0
    schema11_rows = 0
    decisions: dict[tuple[int, int], DecisionScope] = {}
    pending_captures: list[
        tuple[tuple[int, int], int, int, int, tuple[VmRow, ...]]
    ] = []
    pending_batches: list[
        tuple[tuple[int, int], int, int | None, int, int, tuple[int, ...]]
    ] = []
    invalid_active_vm_rows = 0

    with trace_path.open("rb") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            digest.update(raw_line)
            trace_bytes += len(raw_line)
            trace_lines = line_number
            try:
                record = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise MainVmTraceError(
                    f"line {line_number} is not valid UTF-8 JSON"
                ) from error
            if not isinstance(record, dict):
                raise MainVmTraceError(f"line {line_number} is not an object")
            kind = record.get("kind")
            if kind == "decision":
                scope = _decision_scope(record)
                key = (scope.gameplay_epoch, scope.frame)
                if key in decisions:
                    raise MainVmTraceError(f"duplicate decision scope {key}")
                decisions[key] = scope
                continue
            if (
                kind != TRACE_KIND
                or record.get("schema_version") != TRACE_SCHEMA_VERSION
            ):
                continue

            schema11_rows += 1
            key = (
                _integer(
                    record.get("gameplay_epoch"),
                    label="audit gameplay_epoch",
                ),
                _integer(record.get("frame"), label="audit frame"),
            )
            stage_route_index = _integer(
                record.get("stage_route_index"),
                label="audit stage_route_index",
            )

            alignment = record.get("alignment")
            inventory = record.get("nonspell_main_vm_inventory")
            if not isinstance(alignment, dict) or not isinstance(inventory, dict):
                raise MainVmTraceError("schema-11 row omits alignment/inventory")
            before = _integer(
                alignment.get("enemy_prefix_frame_before"),
                label="enemy prefix frame before",
            )
            after = _integer(
                alignment.get("enemy_prefix_frame_after"),
                label="enemy prefix frame after",
            )
            if before > after:
                raise MainVmTraceError("enemy prefix frame bracket is reversed")
            rows = _vm_rows(inventory)
            invalid_active_vm_rows += _integer(
                inventory.get("invalid_active_vms"),
                label="inventory invalid_active_vms",
            )
            decode_ms = inventory.get("decode_ms")
            if (
                not isinstance(decode_ms, (int, float))
                or not math.isfinite(decode_ms)
                or decode_ms < 0.0
            ):
                raise MainVmTraceError("inventory decode_ms is invalid")
            pending_captures.append(
                (key, stage_route_index, before, after, rows)
            )
            provisional_scope = DecisionScope(
                gameplay_epoch=key[0],
                frame=key[1],
                stage_route_index=stage_route_index,
                spell_id=None,
            )
            batch = _activation_batch(record, scope=provisional_scope)
            if batch is not None:
                pending_batches.append(
                    (
                        key,
                        stage_route_index,
                        batch.support_start,
                        batch.support_end,
                        batch.bullet_count,
                        batch.ages,
                    )
                )

    if schema11_rows == 0:
        raise MainVmTraceError("trace contains no schema-11 audit rows")
    captures: list[InventoryCapture] = []
    for key, stage, before, after, rows in pending_captures:
        scope = decisions.get(key)
        if scope is None:
            raise MainVmTraceError(f"audit has no matching decision {key}")
        if scope.stage_route_index != stage:
            raise MainVmTraceError("audit/decision stage scope differs")
        captures.append(
            InventoryCapture(
                scope=scope,
                prefix_frame_before=before,
                prefix_frame_after=after,
                rows=rows,
            )
        )
    activation_batches: list[ActivationBatch] = []
    for key, stage, support_start, support_end, count, ages in pending_batches:
        scope = decisions.get(key)
        if scope is None:
            raise MainVmTraceError(f"audit has no matching decision {key}")
        if scope.stage_route_index != stage:
            raise MainVmTraceError("audit/decision stage scope differs")
        activation_batches.append(
            ActivationBatch(
                scope=scope,
                support_start=support_start,
                support_end=support_end,
                bullet_count=count,
                ages=ages,
            )
        )
    return TraceScan(
        trace_sha256=digest.hexdigest(),
        trace_bytes=trace_bytes,
        trace_lines=trace_lines,
        schema11_rows=schema11_rows,
        captures=tuple(captures),
        activation_batches=tuple(activation_batches),
        invalid_active_vm_rows=invalid_active_vm_rows,
    )


__all__ = [
    "MainVmTraceError",
    "scan_schema11_trace",
]
