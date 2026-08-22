#!/usr/bin/env python3
"""Fast contract for target-free committed three-block execution."""

from pathlib import Path


def test_three_block_execution_has_no_target_surface() -> None:
    source = Path(__file__).with_name(
        "materials_gcts_iqc_three_block_channel_execution.py").read_text()
    assert "def freeze_three_block_channel_execution(" in source
    signature = source.split(
        "def freeze_three_block_channel_execution(", 1)[1].split(
            ") -> FrozenThreeBlockChannelExecution", 1)[0]
    assert "target" not in signature
    assert "scorer" not in signature
    assert "oracle_patch" not in source
    assert "_crop(" not in source
    assert "THIRD_ACTION_BUDGET = 8" in source
    assert "THIRD_BASELINE_SLOTS = 3" in source
    assert "THIRD_DEPTH = 3" in source
    assert "select_pose_port_channel_diverse(" in source
    assert "_second_block_candidates(" in source
    assert "_rollout(" in source


if __name__ == "__main__":
    test_three_block_execution_has_no_target_surface()
    print("target-free committed three-block IQC execution: passed")
