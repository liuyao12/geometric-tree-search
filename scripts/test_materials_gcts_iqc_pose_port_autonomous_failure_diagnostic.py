#!/usr/bin/env python3

import json
from pathlib import Path


def test_failure_is_value_and_train_supply_not_missing_confirmation_geometry():
    path = Path(__file__).resolve().parent / "fixtures" / \
        "iqc_pose_port_autonomous_failure_diagnostic.json"
    report = json.loads(path.read_text())
    assert report["confirmation_exact_candidates_by_depth"] == [1, 7, 7]
    assert report["confirmation_exact_prefixes_by_depth"] == [1, 1, 1]
    assert report["confirmation_exact_path_within_parent_ranks"] == [1, 4, 4]
    assert report["confirmation_selected_action_exact"] == [True, False, False]
    assert report["confirmation_exact_terminal_configurations"] == 1
    assert report["confirmation_exact_terminal_cumulative_rank"] == 10
    assert max(rank for rows in report["training_group_stage_first_exact_ranks"]
               for rank in rows if rank is not None) == 847
    assert all(row["groups_selected_exact"] == 4
               for row in report["capacity_audits"])
    assert report["target_status"].startswith("consumed confirmation")
    assert "branch value" in report["next_gate"]


if __name__ == "__main__":
    test_failure_is_value_and_train_supply_not_missing_confirmation_geometry()
    print("autonomous failure diagnostic fixture passed")
