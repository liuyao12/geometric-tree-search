#!/usr/bin/env python3
"""Regression checks for relational IQC obligation discharge."""

from collections import Counter

from materials_gcts_iqc_relational_port_discharge_dataset import (
    load_default_dataset, relational_transition)
from materials_gcts_iqc_relational_port_rule import load_default_result
from materials_gcts_iqc_wide_typed_port_discharge_dataset import (
    load_default_dataset as load_wide_dataset)
from materials_gcts_recursive_connections import (
    LocalClusterType, MarkedProposalResult, RecursiveConnectionState)


def _frontier(rows):
    point = (1., 0., 0.)
    states = Counter(dict(rows))
    total = sum(states.values())
    return MarkedProposalResult(
        Counter({point: total}), 1, None,
        {point: Counter({"A": total})},
        {point: Counter({"A": total})}, {point: states},
        {point: Counter({0: total})})


def test_reciprocal_gain_is_measured_from_full_frontier():
    a = LocalClusterType("A", (2,))
    b = LocalClusterType("B", (3,))
    forward = RecursiveConnectionState(a, b, 2)
    reverse = RecursiveConnectionState(b, a, 2)
    point = (1., 0., 0.)
    row = relational_transition(
        _frontier(((forward, 2), (reverse, 1))), point,
        _frontier(((forward, 1), (reverse, 3))))
    item = row["selected_role_transitions"][0]
    assert item["relation_counts"]["reverse"] == {
        "before": 1, "after": 3, "lost": 0,
        "retained": 1, "gained": 2}
    assert item["contradiction_flags"]["no_reverse_after"] is False


def test_relational_replay_preserves_every_wide_trajectory():
    relational = load_default_dataset()
    wide = load_wide_dataset()
    wide_rows = {(group["group"], row["stable_index"]): row
                 for group in wide["groups"] for row in group["rows"]}
    compared = 0
    for group in relational["groups"]:
        for row in group["rows"]:
            source = wide_rows[group["group"], row["stable_index"]]
            assert row["trace"] == source["trace"]
            stripped = []
            for transition in row["typed_transitions"]:
                base = {key: value for key, value in transition.items()
                        if key != "selected_pair_relations"}
                base["selected_role_transitions"] = [
                    {key: value for key, value in item.items()
                     if key not in ("relation_counts", "contradiction_flags")}
                    for item in base["selected_role_transitions"]]
                stripped.append(base)
            assert stripped == source["typed_transitions"]
            compared += 1
    assert compared == 120
    assert relational["full_background_role_multiset_scanned"] is True
    assert relational["background_role_identities_serialized"] is False
    assert relational["target_used_for_rollouts"] is False


def test_relational_rule_improves_sites_but_remains_red():
    row = load_default_result()
    assert row["nested_selected_exact_supplied_groups"] == 7
    assert row["nested_selected_correct_sites"] == 26
    assert row["development_selected_metric"] == "forward_after"
    assert row["development_selected_horizon"] == 2
    assert row["development_selected_direction"] == "minimize"
    assert row["shuffle_upper_tail_p"] == .1875
    assert row["development_gate_passed"] is False
    assert row["causal_superiority_gate_passed"] is False
    assert row["failure_detector_validated_target_free"] is False


if __name__ == "__main__":
    test_reciprocal_gain_is_measured_from_full_frontier()
    test_relational_replay_preserves_every_wide_trajectory()
    test_relational_rule_improves_sites_but_remains_red()
    print("relational port-discharge tests passed")
