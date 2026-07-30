"""Native differential binding for asynchronous ordered input publication."""

from __future__ import annotations

import ctypes

from touhou_control.native.library import load_function
from touhou_control.ordered_input_transaction_oracle import (
    AsynchronousOrderedInputIssueBranch,
    OrderedInputExactState,
)


class _AsyncOrderedInputIssueQueryV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("active_mask", ctypes.c_uint32),
        ("held_desired_mask", ctypes.c_uint32),
        ("queued_masks", ctypes.POINTER(ctypes.c_uint32)),
        ("queued_mask_count", ctypes.c_int32),
        ("completion_remaining", ctypes.c_int32),
        ("selected_mask", ctypes.c_uint32),
        (
            "post_dispatch_delay_support",
            ctypes.POINTER(ctypes.c_int32),
        ),
        ("post_dispatch_delay_count", ctypes.c_int32),
        (
            "dispatch_callback_count_support",
            ctypes.POINTER(ctypes.c_int32),
        ),
        ("dispatch_callback_count", ctypes.c_int32),
        ("supported_mask", ctypes.c_uint32),
        ("forbidden_mask", ctypes.c_uint32),
    ]


class _AsyncOrderedInputIssueBranchV1(ctypes.Structure):
    _fields_ = [
        ("selected_mask", ctypes.c_uint32),
        ("write_required", ctypes.c_uint8),
        ("reserved_u8", ctypes.c_uint8 * 3),
        ("older_remaining", ctypes.c_int32),
        ("new_delay", ctypes.c_int32),
        ("dispatch_history_offset", ctypes.c_int32),
        ("dispatch_history_count", ctypes.c_int32),
        ("successor_active_mask", ctypes.c_uint32),
        ("successor_held_desired_mask", ctypes.c_uint32),
        ("successor_queue_offset", ctypes.c_int32),
        ("successor_queue_count", ctypes.c_int32),
        ("successor_completion_remaining", ctypes.c_int32),
    ]


class _AsyncOrderedInputIssueOutputV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        (
            "branches",
            ctypes.POINTER(_AsyncOrderedInputIssueBranchV1),
        ),
        ("branch_capacity", ctypes.c_int32),
        (
            "active_masks_consumed_during_dispatch",
            ctypes.POINTER(ctypes.c_uint32),
        ),
        (
            "publications_during_dispatch",
            ctypes.POINTER(ctypes.c_uint32),
        ),
        ("dispatch_history_capacity", ctypes.c_int32),
        ("successor_queued_masks", ctypes.POINTER(ctypes.c_uint32)),
        ("successor_queue_capacity", ctypes.c_int32),
        ("branch_count", ctypes.POINTER(ctypes.c_int32)),
        (
            "dispatch_history_count",
            ctypes.POINTER(ctypes.c_int32),
        ),
        ("successor_queue_count", ctypes.POINTER(ctypes.c_int32)),
    ]


def _load_async_ordered_input_issue():
    return load_function(
        "touhou_async_ordered_input_issue_v1",
        argtypes=[
            ctypes.POINTER(_AsyncOrderedInputIssueQueryV1),
            ctypes.POINTER(_AsyncOrderedInputIssueOutputV1),
        ],
        restype=ctypes.c_int,
        optional=True,
    )


def async_ordered_input_native_available() -> bool:
    """Return whether the exact-state native differential is available."""

    return _load_async_ordered_input_issue() is not None


def _uint32_array(values: tuple[int, ...]):
    if not values:
        return None
    return (ctypes.c_uint32 * len(values))(*values)


def _int32_array(values: tuple[int, ...]):
    if not values:
        return None
    return (ctypes.c_int32 * len(values))(*values)


def _output(
    *,
    branches=None,
    active_consumed=None,
    published=None,
    successor_queued=None,
    branch_count: ctypes.c_int32,
    dispatch_count: ctypes.c_int32,
    queue_count: ctypes.c_int32,
) -> _AsyncOrderedInputIssueOutputV1:
    return _AsyncOrderedInputIssueOutputV1(
        struct_size=ctypes.sizeof(_AsyncOrderedInputIssueOutputV1),
        branches=branches,
        branch_capacity=0 if branches is None else len(branches),
        active_masks_consumed_during_dispatch=active_consumed,
        publications_during_dispatch=published,
        dispatch_history_capacity=(
            0 if active_consumed is None else len(active_consumed)
        ),
        successor_queued_masks=successor_queued,
        successor_queue_capacity=(
            0 if successor_queued is None else len(successor_queued)
        ),
        branch_count=ctypes.pointer(branch_count),
        dispatch_history_count=ctypes.pointer(dispatch_count),
        successor_queue_count=ctypes.pointer(queue_count),
    )


def issue_ordered_input_state_asynchronously_native(
    state: OrderedInputExactState,
    *,
    selected_mask: int,
    post_dispatch_delay_support: tuple[int, ...],
    dispatch_callback_count_support: tuple[int, ...],
    supported_mask: int,
    forbidden_mask: int = 0,
) -> tuple[AsynchronousOrderedInputIssueBranch, ...]:
    """Enumerate one exact state's branches with the independent C++ model."""

    function = _load_async_ordered_input_issue()
    if function is None:
        raise RuntimeError(
            "native asynchronous ordered-input differential is unavailable"
        )

    queued_masks = _uint32_array(state.queued_masks)
    delays = _int32_array(post_dispatch_delay_support)
    callback_counts = _int32_array(dispatch_callback_count_support)
    query = _AsyncOrderedInputIssueQueryV1(
        struct_size=ctypes.sizeof(_AsyncOrderedInputIssueQueryV1),
        active_mask=state.active_mask,
        held_desired_mask=state.held_desired_mask,
        queued_masks=queued_masks,
        queued_mask_count=len(state.queued_masks),
        completion_remaining=state.completion_remaining or 0,
        selected_mask=selected_mask,
        post_dispatch_delay_support=delays,
        post_dispatch_delay_count=len(post_dispatch_delay_support),
        dispatch_callback_count_support=callback_counts,
        dispatch_callback_count=len(dispatch_callback_count_support),
        supported_mask=supported_mask,
        forbidden_mask=forbidden_mask,
    )

    branch_count = ctypes.c_int32()
    dispatch_count = ctypes.c_int32()
    queue_count = ctypes.c_int32()
    measured = _output(
        branch_count=branch_count,
        dispatch_count=dispatch_count,
        queue_count=queue_count,
    )
    result = function(ctypes.byref(query), ctypes.byref(measured))
    if result != 0:
        raise ValueError(
            f"native asynchronous ordered-input measure returned {result}"
        )

    branches = (
        _AsyncOrderedInputIssueBranchV1 * branch_count.value
    )()
    active_consumed = (ctypes.c_uint32 * dispatch_count.value)()
    published = (ctypes.c_uint32 * dispatch_count.value)()
    successor_queued = (ctypes.c_uint32 * queue_count.value)()
    filled = _output(
        branches=branches,
        active_consumed=active_consumed,
        published=published,
        successor_queued=successor_queued,
        branch_count=branch_count,
        dispatch_count=dispatch_count,
        queue_count=queue_count,
    )
    result = function(ctypes.byref(query), ctypes.byref(filled))
    if result != 0:
        raise RuntimeError(
            f"native asynchronous ordered-input fill returned {result}"
        )

    decoded: list[AsynchronousOrderedInputIssueBranch] = []
    for branch in branches:
        dispatch_start = branch.dispatch_history_offset
        dispatch_end = dispatch_start + branch.dispatch_history_count
        queue_start = branch.successor_queue_offset
        queue_end = queue_start + branch.successor_queue_count
        successor = OrderedInputExactState(
            active_mask=branch.successor_active_mask,
            held_desired_mask=branch.successor_held_desired_mask,
            queued_masks=tuple(successor_queued[queue_start:queue_end]),
            completion_remaining=(
                branch.successor_completion_remaining or None
            ),
        )
        decoded.append(
            AsynchronousOrderedInputIssueBranch(
                source_state=state,
                selected_mask=branch.selected_mask,
                write_required=bool(branch.write_required),
                older_remaining=branch.older_remaining or None,
                new_delay=branch.new_delay or None,
                active_masks_consumed_during_dispatch=tuple(
                    active_consumed[dispatch_start:dispatch_end]
                ),
                publications_during_dispatch=tuple(
                    published[dispatch_start:dispatch_end]
                ),
                successor_state=successor,
            )
        )
    return tuple(decoded)


__all__ = [
    "async_ordered_input_native_available",
    "issue_ordered_input_state_asynchronously_native",
]
