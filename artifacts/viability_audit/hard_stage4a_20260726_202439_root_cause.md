# Robust-Viability Differential Audit

- Hits: 15; audited pre-hit queries: 120; empty: 61.
- Exact spatial comparisons preserve the 8-frame action layer: `16px`, `8px`, and `4px`.
- The `8px/4f` result clips delays above four frames and is diagnostic only.
- Birth evidence is observed slot delta, not an injected ECL birth oracle.

## Empty-query labels

| Label | Count |
| --- | ---: |
| `finite_horizon_collapse` | 8 |
| `modeled_losing_unresolved` | 47 |
| `spatial_coarse_false_empty` | 6 |

## Independent empty-set rescue factors

| Counterfactual factor | Count |
| --- | ---: |
| `base_or_forecast_uncertainty` | 3 |
| `finite_horizon_requirement` | 12 |
| `forecast_uncertainty_growth` | 3 |
| `full_async_delay_envelope` | 1 |
| `spatial_quantization` | 6 |

## Losing-state survival shadow

- Labeled losing queries: 61.
- Label reaches the later native hit: 6.
- Issued action outside survival-best mask: 27.
- Reaches hit but issued outside best mask: 6.

## Orthogonal evidence

These flags do not by themselves explain why the queried kernel was empty.

| Evidence | Count |
| --- | ---: |
| `hazard_model_future_birth_gap` | 7 |

## Terminal overlap

- Comparable instant-winning queries: 59.
- Rejected by next-policy overlap: 9.
- Exact intra-layer overlap still needs residual-frame propagation; reported rejection remains diagnostic.

## Witnesses

| Hit | Decision | Spell | Base survival | 8px | 4px | Fresh | Birth collision | Labels |
| ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 3419 | 3383 | 0 | 1 | False | False | False | False | modeled_losing_unresolved |
| 3419 | 3417 | 0 | 1 | False | False | False | False | modeled_losing_unresolved |
| 4404 | 4166 | 0 | 0 | False | False | False | False | modeled_losing_unresolved |
| 4404 | 4198 | 0 | 58 | False | False | False | False | finite_horizon_collapse, forecast_uncertainty_growth, finite_horizon_requirement |
| 4404 | 4233 | 0 | 8 | False | False | False | False | modeled_losing_unresolved |
| 4404 | 4262 | 0 | 0 | False | False | False | False | modeled_losing_unresolved |
| 4404 | 4296 | 0 | 18 | False | False | False | False | modeled_losing_unresolved |
| 4404 | 4332 | 0 | 47 | False | False | False | False | finite_horizon_collapse, forecast_uncertainty_growth, finite_horizon_requirement |
| 4404 | 4370 | 0 | 2 | False | False | False | False | modeled_losing_unresolved |
| 4404 | 4401 | 0 | 2 | False | False | False | False | modeled_losing_unresolved |
| 8983 | 8883 | 0 | 0 | False | False | False | False | modeled_losing_unresolved |
| 8983 | 8918 | 0 | 0 | False | False | False | False | modeled_losing_unresolved |
| 8983 | 8950 | 0 | 1 | False | False | False | False | modeled_losing_unresolved |
| 8983 | 8981 | 0 | 2 | False | False | False | False | modeled_losing_unresolved |
| 10727 | 10688 | 56 | 39 | True | True | False | False | spatial_coarse_false_empty, spatial_quantization, finite_horizon_requirement |
| 10727 | 10723 | 56 | 3 | False | False | False | False | modeled_losing_unresolved |
| 11625 | 11385 | 56 | 11 | False | False | False | True | modeled_losing_unresolved, hazard_model_future_birth_gap |
| 11625 | 11421 | 56 | 0 | False | False | False | True | modeled_losing_unresolved, hazard_model_future_birth_gap |
| 11625 | 11455 | 56 | 1 | False | False | False | True | modeled_losing_unresolved, hazard_model_future_birth_gap |
| 11625 | 11492 | 56 | 0 | False | False | False | True | modeled_losing_unresolved, hazard_model_future_birth_gap |
| 11625 | 11527 | 56 | 0 | False | False | False | True | modeled_losing_unresolved, hazard_model_future_birth_gap |
| 11625 | 11589 | 56 | 2 | True | True | False | False | spatial_coarse_false_empty, spatial_quantization |
| 12184 | 12047 | 56 | 20 | True | True | False | False | spatial_coarse_false_empty, spatial_quantization |
| 12184 | 12149 | 56 | 39 | False | True | False | False | spatial_coarse_false_empty, spatial_quantization, finite_horizon_requirement |
| 12184 | 12181 | 56 | 2 | False | False | False | False | modeled_losing_unresolved |
| 12723 | 12689 | 56 | 35 | False | True | False | False | spatial_coarse_false_empty, spatial_quantization, finite_horizon_requirement |
| 12723 | 12720 | 56 | 9 | False | False | False | False | modeled_losing_unresolved |
| 13107 | 13105 | 56 | 1 | False | False | False | False | modeled_losing_unresolved |
| 17618 | 17580 | 56 | 42 | False | False | False | False | finite_horizon_collapse, finite_horizon_requirement |
| 17618 | 17616 | 56 | 4 | False | False | False | False | modeled_losing_unresolved |
| 19976 | 19736 | 60 | 20 | False | True | False | False | spatial_coarse_false_empty, full_async_delay_envelope, spatial_quantization, forecast_uncertainty_growth, finite_horizon_requirement |
| 19976 | 19938 | 60 | 32 | False | False | False | False | finite_horizon_collapse, finite_horizon_requirement |
| 19976 | 19973 | 60 | 0 | False | False | False | False | modeled_losing_unresolved |
| 21797 | 21557 | 60 | 5 | False | False | False | True | modeled_losing_unresolved, hazard_model_future_birth_gap |
| 21797 | 21595 | 60 | 44 | False | False | False | True | finite_horizon_collapse, hazard_model_future_birth_gap, base_or_forecast_uncertainty, finite_horizon_requirement |
| 21797 | 21631 | 60 | 18 | False | False | False | False | modeled_losing_unresolved |
| 21797 | 21663 | 60 | 0 | False | False | False | False | modeled_losing_unresolved |
| 21797 | 21695 | 60 | 0 | False | False | False | False | modeled_losing_unresolved |
| 21797 | 21728 | 60 | 46 | False | False | False | False | finite_horizon_collapse, base_or_forecast_uncertainty, finite_horizon_requirement |
| 21797 | 21762 | 60 | 12 | False | False | False | False | modeled_losing_unresolved |
| 21797 | 21794 | 60 | 0 | False | False | False | False | modeled_losing_unresolved |
| 28431 | 28428 | 60 | 9 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30420 | 64 | 7 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30453 | 64 | 3 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30484 | 64 | 5 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30516 | 64 | 12 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30552 | 64 | 0 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30591 | 64 | 3 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30624 | 64 | 0 | False | False | False | False | modeled_losing_unresolved |
| 30660 | 30657 | 64 | 2 | False | False | False | False | modeled_losing_unresolved |
| 31701 | 31462 | 64 | 20 | False | False | False | False | modeled_losing_unresolved |
| 31701 | 31499 | 64 | 0 | False | False | False | False | modeled_losing_unresolved |
| 31701 | 31533 | 64 | 4 | False | False | False | False | modeled_losing_unresolved |
| 31701 | 31565 | 64 | 19 | False | False | False | False | modeled_losing_unresolved |
| 31701 | 31596 | 64 | 25 | False | False | False | False | modeled_losing_unresolved |
| 31701 | 31629 | 64 | 37 | False | False | False | False | finite_horizon_collapse, finite_horizon_requirement |
| 31701 | 31665 | 64 | 1 | False | False | False | False | modeled_losing_unresolved |
| 31701 | 31699 | 64 | 0 | False | False | False | False | modeled_losing_unresolved |
| 38863 | 38786 | 68 | 28 | False | False | False | False | finite_horizon_collapse, base_or_forecast_uncertainty, finite_horizon_requirement |
| 38863 | 38825 | 68 | 2 | False | False | False | False | modeled_losing_unresolved |
| 38863 | 38860 | 68 | 0 | False | False | False | False | modeled_losing_unresolved |
