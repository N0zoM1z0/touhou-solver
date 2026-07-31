"""Native local sensing and baseline beam-reduction bindings."""

from __future__ import annotations

from .local_abi import DecodedBulletPool as DecodedBulletPool
from .local_reducers import (
    _load_local_beam_reduce_function as _load_local_beam_reduce_function,
    reduce_local_beam as reduce_local_beam,
)
from .local_sensing import (
    _load_bullet_pool_decode_function as _load_bullet_pool_decode_function,
    _load_local_hazards_function as _load_local_hazards_function,
    decode_bullet_pool as decode_bullet_pool,
    query_local_hazards as query_local_hazards,
)
