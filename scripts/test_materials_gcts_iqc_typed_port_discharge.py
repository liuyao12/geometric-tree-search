#!/usr/bin/env python3
"""Regression checks for identity-preserving IQC obligation discharge."""

from collections import Counter

from materials_gcts_iqc_typed_port_discharge_dataset import (
    load_default_dataset, typed_transition)
from materials_gcts_iqc_typed_port_discharge_rollback import (
    load_default_result)
from materials_gcts_recursive_connections import (
    LocalClusterType, MarkedProposalResult, RecursiveConnectionState)


def _frontier(role_counts):
    point = (1., 0., 0.)
    states = Counter({role: count for role, count in role_counts})
    total = sum(states.values())
    return MarkedProposalResult(
        Counter({point: total}), 1, None,
        {point: Counter({"A": total})},
        {point: Counter({"A": total})}, {point: states},
        {point: Counter({0: total})})


def test_typed_transition_preserves_selected_role_identity():
    a = LocalClusterType("A", (2, 4))
    b = LocalClusterType("B", (3, 6))
    role = RecursiveConnectionState(a, b, 3)
    other = RecursiveConnectionState(b, a, 5)
    before = _frontier(((role, 4), (other, 2)))
    after = _frontier(((role, 1), (other, 5)))
    row = typed_transition(before, (1., 0., 0.), after)
    selected = {tuple(item["role"]): item
                for item in row["selected_role_transitions"]}
    key = ("A", (2, 4), "B", (3, 6), 3)
    assert selected[key]["before"] == 4
    assert selected[key]["after"] == 1
    assert selected[key]["discharged"] == 3
    assert selected[key]["persisted"] == 1


def test_frozen_typed_dataset_is_target_free_and_complete():
    row = load_default_dataset()
    assert row["retained_candidates"] == 19
    assert row["target_used_for_rollouts"] is False
    assert row["candidate_geometry_unchanged"] is True
    transitions = [transition for group in row["groups"]
                   for candidate in group["rows"]
                   for transition in candidate["typed_transitions"]]
    assert len(transitions) == 304
    assert max(len(transition["selected_role_transitions"])
               for transition in transitions) == 3


def test_typed_rollback_is_exact_but_randomization_limited():
    row = load_default_result()
    assert row["nested_supplied_groups"] == 9
    assert row["nested_selected_exact_groups"] == 9
    assert row["nested_selected_correct_sites"] == 27
    assert row["development_selected_metric"] == \
        "selected_persisted_mass"
    assert row["development_selected_horizon"] == 8
    assert row["development_selected_correct_sites"] == 28
    assert row["exhaustive_within_nucleus_assignments"] == 8
    assert row["exact_randomization_upper_tail_p"] == .25
    assert row["minimum_attainable_exact_randomization_p"] == .25
    assert row["causal_superiority_gate_passed"] is False
    assert row["failure_detector_validated_target_free"] is False


if __name__ == "__main__":
    test_typed_transition_preserves_selected_role_identity()
    test_frozen_typed_dataset_is_target_free_and_complete()
    test_typed_rollback_is_exact_but_randomization_limited()
    print("typed port-discharge tests passed")
