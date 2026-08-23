"""Fast structural contract for the fresh parent-balanced executor."""

import inspect

from materials_gcts_iqc_fresh_parent_balanced_execution import (
    FrozenFreshParentBalancedExecution,
    freeze_fresh_parent_balanced_execution)


def test_fresh_executor_has_no_target_or_scorer_api():
    parameters = inspect.signature(
        freeze_fresh_parent_balanced_execution).parameters
    assert "target" not in parameters
    assert "scorer" not in parameters
    assert "correctness" not in parameters
    assert FrozenFreshParentBalancedExecution.__dataclass_fields__[\
        "target_used"].default is False
if __name__ == "__main__":
    test_fresh_executor_has_no_target_or_scorer_api()
    print("fresh parent-balanced executor API: passed")
