"""Native local sensing, beam reduction, and rollout bindings."""

from __future__ import annotations

from .local_abi import (
    DecodedBulletPool as DecodedBulletPool,
    LocalSupplementalNativeCancelledError as LocalSupplementalNativeCancelledError,
    LocalSupplementalNativeDeadlineError as LocalSupplementalNativeDeadlineError,
    LocalSupplementalNativeResult as LocalSupplementalNativeResult,
    _LocalSupplementalOutputV1 as _LocalSupplementalOutputV1,
    _LocalSupplementalQueryV1 as _LocalSupplementalQueryV1,
)
from .local_reducers import (
    _load_local_beam_reduce_function as _load_local_beam_reduce_function,
    _load_local_supplemental_beam_reduce_function as _load_local_supplemental_beam_reduce_function,
    reduce_local_beam as reduce_local_beam,
    reduce_local_supplemental_beam as reduce_local_supplemental_beam,
)
from .local_sensing import (
    _load_bullet_pool_decode_function as _load_bullet_pool_decode_function,
    _load_local_hazards_function as _load_local_hazards_function,
    decode_bullet_pool as decode_bullet_pool,
    query_local_hazards as query_local_hazards,
)
from .local_supplemental import (
    LocalSupplementalNativeWorkspace as LocalSupplementalNativeWorkspace,
    _frame_major_fields as _frame_major_fields,
    _load_local_supplemental_workspace_functions as _load_local_supplemental_workspace_functions_impl,
)
from .library import load_library as _load_library


















def _load_local_supplemental_workspace_functions():
    """Load through the facade hook retained for fault-injection tests."""

    return _load_local_supplemental_workspace_functions_impl(
        library_loader=_load_library,
    )
