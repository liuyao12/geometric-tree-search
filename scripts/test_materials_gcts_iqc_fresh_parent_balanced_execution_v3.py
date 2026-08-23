"""Fast contracts for the auditable chunk-cached executor."""

import inspect
from types import SimpleNamespace

import materials_gcts_iqc_fresh_parent_balanced_execution_v3 as execution


def test_v3_has_no_target_api_and_exposes_raw_lineages_and_timings():
    parameters = inspect.signature(
        execution.freeze_fresh_parent_balanced_execution_v3).parameters
    assert "target" not in parameters and "scorer" not in parameters
    fields = execution.FrozenFreshParentBalancedExecutionV3.__dataclass_fields__
    assert "raw_nine_action_lineages" in fields
    assert "raw_nine_action_lineage_digest" in fields
    assert "selected_nine_action_lineage_indices" in fields
    assert "stage_seconds" in fields
    assert fields["target_used"].default is False


def test_chunk_worker_loads_runtime_once_for_multiple_parents():
    old_runtime = execution.load_fourth_block_runtime
    old_policy = execution.load_parent_policy
    old_tree = execution._channel_tree
    old_features = execution.branch_features
    old_score = execution._score
    old_beam = execution.parent_balanced_beam
    loads = []
    execution.load_fourth_block_runtime = lambda: loads.append("runtime") or {}
    execution.load_parent_policy = lambda: loads.append("policy") or {
        "model": {}}
    states = tuple(SimpleNamespace(
        proposals=SimpleNamespace(votes={(float(i), 0., 0.): i + 1}),
        actions=(((float(i), 0., 0.), "X"),)) for i in range(10))
    execution._channel_tree = lambda *args, **kwargs: (states, ())
    execution.branch_features = lambda state: (state.actions[0][0][0],)
    execution._score = lambda model, features: features[0]
    execution.parent_balanced_beam = lambda scores, parents, ties, width: \
        tuple(range(width))
    tasks = tuple(((0., 0., 0.), ((0., 0., 0.),), ("X",), 4., index,
                   SimpleNamespace(parent_id=index + 1,
                                   child_stable_index=2,
                                   third_stable_index=3,
                                   all_actions=(((1., 1., 1.), "X"),)))
                  for index in range(3))
    try:
        rows = execution._fourth_parent_chunk_worker(tasks)
    finally:
        execution.load_fourth_block_runtime = old_runtime
        execution.load_parent_policy = old_policy
        execution._channel_tree = old_tree
        execution.branch_features = old_features
        execution._score = old_score
        execution.parent_balanced_beam = old_beam
    assert loads == ["runtime", "policy"]
    assert len(rows) == 3
    assert all(count == 10 and len(candidates) == 8
               for _parent, count, candidates in rows)


if __name__ == "__main__":
    test_v3_has_no_target_api_and_exposes_raw_lineages_and_timings()
    test_chunk_worker_loads_runtime_once_for_multiple_parents()
    print("auditable chunk-cached fresh executor: passed")
