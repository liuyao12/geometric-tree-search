#!/usr/bin/env python3

import math

from materials_gcts_iqc_exact_port_instance_audit import evaluate
from materials_gcts_iqc_exact_port_instance_dataset import (
    EXPECTED_DATASET_DIGEST, _boundary_context,
    _canonical_branch_action_graph, _distance_signature, _relation_flags,
    _selected_endpoint_geometry,
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
    assert row["selected_endpoint_metric_graph_serialized"]
    assert row["complete_branch_metric_graph_serialized"]
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

    center = (0., 0., 0.)
    context = _boundary_context(
        center, selected_target, positions[0], positions[1], 9., 1., 512)
    moved_context = _boundary_context(
        transform(center), transform(selected_target), transform(positions[0]),
        transform(positions[1]), 9., 1., 512)
    assert context == moved_context
    assert context["current_frontier_fraction"] == .5

    endpoint_target = (1., 2., 3.)
    endpoint_parent = (2., 0., 0.)
    endpoint_source = (0., 3., 0.)
    geometry = _selected_endpoint_geometry(
        center, endpoint_target, endpoint_parent, endpoint_source, 1., "blue")
    moved_geometry = _selected_endpoint_geometry(
        transform(center), transform(endpoint_target), transform(endpoint_parent),
        transform(endpoint_source), 1., "blue")
    assert geometry == moved_geometry
    assert geometry["target_color"] == "blue"

    reflected = lambda point: (-point[0], point[1], point[2])
    mirrored = _selected_endpoint_geometry(
        reflected(center), reflected(endpoint_target),
        reflected(endpoint_parent), reflected(endpoint_source), 1., "blue")
    assert geometry["normalized_pair_distances"] == \
        mirrored["normalized_pair_distances"]
    assert geometry["proper_signed_volume"] == \
        -mirrored["proper_signed_volume"]

    actions = ((endpoint_target, "Y"), (endpoint_parent, "X"),
               (endpoint_source, "Y"))
    branch = _canonical_branch_action_graph(center, actions, 1.)
    assert branch == _canonical_branch_action_graph(
        transform(center), tuple((transform(point), color)
                                 for point, color in reversed(actions)), 1.)
    reflected_branch = _canonical_branch_action_graph(
        reflected(center), tuple((reflected(point), color)
                                 for point, color in actions), 1.)
    assert branch["node_colors"] == reflected_branch["node_colors"]
    assert branch["center_distances_nn"] == \
        reflected_branch["center_distances_nn"]
    assert branch["pair_distances_nn"] == \
        reflected_branch["pair_distances_nn"]
    # Equal colors alone do not create a metric automorphism: the two Y sites
    # have distinct distance profiles, so this scalene colored set is chiral.
    assert branch["proper_signed_volumes"] == tuple(
        -value for value in reflected_branch["proper_signed_volumes"])

    chiral_actions = ((endpoint_target, "Z"), (endpoint_parent, "X"),
                      (endpoint_source, "Y"))
    chiral = _canonical_branch_action_graph(center, chiral_actions, 1.)
    chiral_mirror = _canonical_branch_action_graph(
        reflected(center), tuple((reflected(point), color)
                                 for point, color in chiral_actions), 1.)
    assert chiral["proper_signed_volumes"] == tuple(
        -value for value in chiral_mirror["proper_signed_volumes"])


if __name__ == "__main__":
    test_exact_port_instance_audit()
    test_instance_relations_and_metric_signature_are_invariant()
    print("IQC exact port-instance audit passed")
