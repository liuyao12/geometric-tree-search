"""Fast structural tests for the parallel fresh executor."""

import inspect
from types import SimpleNamespace

import materials_gcts_iqc_fresh_parent_balanced_execution_v2 as execution


def test_parallel_executor_has_no_target_api():
    parameters = inspect.signature(
        execution.freeze_fresh_parent_balanced_execution_v2).parameters
    assert "target" not in parameters
    assert "scorer" not in parameters


def test_parallel_graphs_deduplicate_shared_prefixes():
    old_runtime = execution.load_fourth_block_runtime
    old_features = execution._transported_stage_features
    execution.load_fourth_block_runtime = lambda: object()
    calls = []

    def features(**kwargs):
        key = (kwargs["prior_actions"], kwargs["block_actions"])
        calls.append(key)
        return (), key, None

    execution._transported_stage_features = features
    common = tuple(((float(index), 0., 0.), "X") for index in range(6))
    lineages = (
        SimpleNamespace(all_actions=common + tuple(
            ((float(index), 1., 0.), "Y") for index in range(6, 9))),
        SimpleNamespace(all_actions=common + tuple(
            ((float(index), 2., 0.), "Y") for index in range(6, 9))),
    )
    try:
        rows = execution._parallel_lineage_graphs(
            lineages, ((0., 0., 0.),), ("X",), 1)
    finally:
        execution.load_fourth_block_runtime = old_runtime
        execution._transported_stage_features = old_features
    assert len(calls) == 4
    assert rows[0][1][:2] == rows[1][1][:2]
    assert rows[0][1][2] != rows[1][1][2]


if __name__ == "__main__":
    test_parallel_executor_has_no_target_api()
    test_parallel_graphs_deduplicate_shared_prefixes()
    print("parallel fresh parent-balanced executor: passed")
