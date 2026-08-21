#!/usr/bin/env python3

from materials_gcts_iqc_simultaneous_port_cover_audit import evaluate
from materials_gcts_iqc_simultaneous_port_cover_dataset import (
    EXPECTED_DATASET_DIGEST, load_default_dataset)


def test_iqc_simultaneous_port_cover():
    dataset = load_default_dataset()
    assert dataset["dataset_digest"] == EXPECTED_DATASET_DIGEST
    row = evaluate()
    assert row["development_groups"] == 10
    assert row["retained_branches"] == 120
    assert row["exact_branches"] == 59
    assert row["false_branches"] == 61
    assert row["satisfied_branches"] == 120
    assert row["unsatisfied_branches"] == 0
    assert row["unknown_branches"] == 0
    assert row["branches_with_no_persisting_role"] == 41
    assert row["branches_with_persisting_role"] == 79
    assert row["maximum_distinct_persisting_roles"] == 1
    assert row["role_relevant_successor_actions"] == 137
    assert row["maximum_role_relevant_actions_per_branch"] == 3
    assert row["pair_conflicts"] == 0
    assert row["search_nodes"] == 257
    assert row["all_successor_enumerations_complete"]
    assert row["all_searches_complete"]
    assert row["all_candidate_geometry_target_blind"]
    assert not row["semantic_role_cover_rejects_any_false_branch"]
    assert not row["simultaneous_semantic_role_gate_passed"]
    assert row["exact_port_instance_certificate_required"]
    assert not row["physical_valence_or_mandatory_occupancy_claimed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_iqc_simultaneous_port_cover()
    print("IQC simultaneous port-cover audit passed")
