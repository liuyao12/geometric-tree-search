#!/usr/bin/env python3

import math

from materials_gcts_iqc_exact_port_instance_audit import evaluate
from materials_gcts_iqc_exact_port_instance_dataset import (
    EXPECTED_DATASET_DIGEST, _distance_signature, _relation_flags,
    load_default_dataset)
from materials_gcts_recursive_connections import (
    LocalClusterType, ProposalPairAction, RecursiveConnectionState)


def test_exact_port_instance_audit():
    dataset = load_default_dataset()
    assert dataset["dataset_digest"] == EXPECTED_DATASET_DIGEST
    row = evaluate()
    assert row["retained_branches"] == 120
    assert row["exact_branches"] == 59
    assert row["false_branches"] == 61
    expected = {
        "reverse": (43, 22, 16, 39, 65),
        "forward": (57, 35, 2, 26, 786),
        "backward": (59, 60, 0, 1, 419),
        "same_parent": (59, 61, 0, 0, 1019),
        "same_source": (56, 41, 3, 20, 302),
        "touch_parent": (59, 61, 0, 0, 1438),
        "touch_source": (57, 43, 2, 18, 1088),
    }
    for relation in row["relations"]:
        values = expected[relation["relation"]]
        assert (relation["satisfied_exact"],
                relation["satisfied_false"],
                relation["unsatisfied_exact"],
                relation["unsatisfied_false"],
                relation["raw_matching_pair_actions"]) == values
        assert relation["invariant_candidate_classes"] == values[-1]
    forward = next(item for item in row["relations"]
                   if item["relation"] == "forward")
    assert forward["exact_supply_groups_after_filter"] == 8
    assert abs(row["fixed_forward_exact_retention"] - 57 / 59) < 1e-12
    assert abs(row["fixed_forward_false_rejection"] - 26 / 61) < 1e-12
    assert abs(row["fixed_forward_filtered_precision"] - 57 / 92) < 1e-12
    assert not row["fixed_forward_preserves_every_supplied_group"]
    assert row["exact_instance_improves_over_semantic_role_cover"]
    assert not row["exact_instance_gate_passed"]
    assert row["boundary_conditioned_backoff_required"]
    assert row["all_successor_enumerations_complete"]
    assert row["all_searches_complete"]
    assert not row["raw_occurrence_indices_serialized"]
    assert row["proper_motion_invariant_candidate_identity"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


def test_instance_relations_and_metric_signature_are_invariant():
    cluster = LocalClusterType("A", (1, 2, 3))
    state = RecursiveConnectionState(cluster, cluster, 4)
    selected = ProposalPairAction(0, 1, state)
    forward = ProposalPairAction(1, 2, state)
    reverse = ProposalPairAction(1, 0, state)
    assert _relation_flags(selected, forward)["forward"]
    assert _relation_flags(selected, reverse)["reverse"]
    permutation = {0: 4, 1: 3, 2: 5}
    moved_selected = ProposalPairAction(4, 3, state)
    moved_forward = ProposalPairAction(3, 5, state)
    assert _relation_flags(selected, forward) == _relation_flags(
        moved_selected, moved_forward)

    positions = ((0., 0., 0.), (1., 0., 0.), (1., 1., 0.))
    selected_target = (2., 0., 0.)
    candidate_target = (1., 2., 0.)
    angle = .73

    def transform(point):
        x, y, z = point
        return (math.cos(angle) * x - math.sin(angle) * y + 3.,
                math.sin(angle) * x + math.cos(angle) * y - 2., z + 4.)

    original = _distance_signature(
        selected, forward, selected_target, candidate_target, positions, 1.)
    moved = _distance_signature(
        selected, forward, transform(selected_target),
        transform(candidate_target), tuple(map(transform, positions)), 1.)
    assert original == moved


if __name__ == "__main__":
    test_exact_port_instance_audit()
    test_instance_relations_and_metric_signature_are_invariant()
    print("IQC exact port-instance audit passed")
