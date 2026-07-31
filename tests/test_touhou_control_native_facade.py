from __future__ import annotations

import dataclasses
from types import SimpleNamespace
import unittest
from unittest import mock

from touhou_control import native_backend
from touhou_control.native import belief, geometry, library, local, pipeline, viability


class NativeBackendFacadeTests(unittest.TestCase):
    def test_historical_names_are_exact_domain_reexports(self) -> None:
        expected = {
            "_library_path": library.library_path,
            "_load_library": library.load_library,
            "_raise_pipeline_result": library.raise_pipeline_result,
            "available": library.available,
            "PipelineNativeCancelledError": (
                library.PipelineNativeCancelledError
            ),
            "PipelineNativeDeadlineError": library.PipelineNativeDeadlineError,
            "_load_clearance_function": geometry._load_clearance_function,
            "_load_trajectory_clearance_function": (
                geometry._load_trajectory_clearance_function
            ),
            "_load_aabb_trajectory_clearance_function": (
                geometry._load_aabb_trajectory_clearance_function
            ),
            "_load_piecewise_aabb_clearance_function": (
                geometry._load_piecewise_aabb_clearance_function
            ),
            "build_clearance_volume": geometry.build_clearance_volume,
            "apply_segment_trajectory_clearance": (
                geometry.apply_segment_trajectory_clearance
            ),
            "apply_packed_segment_clearance": (
                geometry.apply_packed_segment_clearance
            ),
            "apply_aabb_trajectory_clearance": (
                geometry.apply_aabb_trajectory_clearance
            ),
            "apply_piecewise_aabb_clearance": (
                geometry.apply_piecewise_aabb_clearance
            ),
            "_load_local_hazards_function": (
                local._load_local_hazards_function
            ),
            "_load_bullet_pool_decode_function": (
                local._load_bullet_pool_decode_function
            ),
            "_load_local_beam_reduce_function": (
                local._load_local_beam_reduce_function
            ),
            "DecodedBulletPool": local.DecodedBulletPool,
            "query_local_hazards": local.query_local_hazards,
            "decode_bullet_pool": local.decode_bullet_pool,
            "reduce_local_beam": local.reduce_local_beam,
            "_load_viability_function": viability._load_viability_function,
            "_load_viability_worker_limit_function": (
                viability._load_viability_worker_limit_function
            ),
            "_load_terminal_viability_function": (
                viability._load_terminal_viability_function
            ),
            "_load_safety_value_function": (
                viability._load_safety_value_function
            ),
            "_load_safety_policy_function": (
                viability._load_safety_policy_function
            ),
            "_load_survival_viability_function": (
                viability._load_survival_viability_function
            ),
            "_load_query_local_survival_function": (
                viability._load_query_local_survival_function
            ),
            "_load_losing_survival_labels_function": (
                viability._load_losing_survival_labels_function
            ),
            "set_current_thread_viability_worker_limit": (
                viability.set_current_thread_viability_worker_limit
            ),
            "build_viability_arrays": viability.build_viability_arrays,
            "build_safety_value_arrays": viability.build_safety_value_arrays,
            "build_safety_policy_arrays": viability.build_safety_policy_arrays,
            "build_survival_viability_arrays": (
                viability.build_survival_viability_arrays
            ),
            "query_local_survival_arrays": (
                viability.query_local_survival_arrays
            ),
            "build_losing_survival_label_arrays": (
                viability.build_losing_survival_label_arrays
            ),
            "_load_pipeline_workspace_functions": (
                pipeline._load_pipeline_workspace_functions
            ),
            "PipelineSurvivalNativeWorkspace": (
                pipeline.PipelineSurvivalNativeWorkspace
            ),
            "create_pipeline_survival_workspace": (
                pipeline.create_pipeline_survival_workspace
            ),
            "_load_belief_pipeline_workspace_functions": (
                belief._load_belief_pipeline_workspace_functions
            ),
            "BeliefPipelineNativeWorkspace": (
                belief.BeliefPipelineNativeWorkspace
            ),
            "create_belief_pipeline_survival_workspace": (
                belief.create_belief_pipeline_survival_workspace
            ),
        }
        for name, domain_value in expected.items():
            with self.subTest(name=name):
                self.assertIs(getattr(native_backend, name), domain_value)

    def test_result_records_remain_frozen_dataclasses(self) -> None:
        self.assertTrue(dataclasses.is_dataclass(local.DecodedBulletPool))
        self.assertTrue(
            local.DecodedBulletPool.__dataclass_params__.frozen
        )
    def test_domain_loader_uses_shared_cache_without_caching_miss(self) -> None:
        fake_library = SimpleNamespace()

        def function() -> None:
            pass

        with (
            mock.patch.object(geometry, "_load_library", return_value=fake_library),
            mock.patch.object(library, "_FUNCTION_CACHE", {}),
        ):
            self.assertIsNone(
                geometry._load_trajectory_clearance_function()
            )
            fake_library.touhou_segment_trajectory_clearance_v1 = function
            self.assertIs(
                geometry._load_trajectory_clearance_function(),
                function,
            )
            del fake_library.touhou_segment_trajectory_clearance_v1
            self.assertIs(
                geometry._load_trajectory_clearance_function(),
                function,
            )

if __name__ == "__main__":
    unittest.main()
