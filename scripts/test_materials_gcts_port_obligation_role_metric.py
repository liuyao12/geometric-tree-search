#!/usr/bin/env python3
"""Focused contracts for the role-conditioned obligation metric."""

from copy import deepcopy

from materials_gcts_port_obligation_role_metric import (
    PortObligationRoleMetricSpec, fit_port_obligation_role_metric,
    role_conditioned_features, score_port_obligation_role_metric)


RELATIONS = ("backward", "forward", "reverse", "same_parent",
             "same_source", "touch_parent", "touch_source")
FLAGS = ("forward_depleted", "no_forward_after", "no_reverse_after",
         "no_touch_source_after", "source_touch_depleted")


def transition(parent="X", source="Y", separation=10, discharged=1):
    return {
        "selected_role_transitions": ({
            "role": (parent, (999,), source, (888,), separation),
            "before": 2, "after": 2 - discharged,
            "discharged": discharged, "produced": 0,
            "contradiction_flags": {name: name == "forward_depleted"
                                    for name in FLAGS},
            "relation_counts": {name: {
                "lost": discharged if name == "forward" else 0,
                "gained": 0, "after": 1,
            } for name in RELATIONS},
        },),
        "selected_pair_relations": (),
    }


def test_features_preserve_role_owner_but_ignore_raw_neighbor_identity():
    spec = PortObligationRoleMetricSpec(4, True, False, 1, True)
    first = transition()
    second = deepcopy(first)
    second["selected_role_transitions"][0]["role"] = (
        "X", (1, 2, 3), "Y", (4, 5), 10)
    assert role_conditioned_features((first,), spec, 10.) == \
        role_conditioned_features((second,), spec, 10.)
    changed = transition(parent="Y", source="X")
    assert role_conditioned_features((first,), spec, 10.) != \
        role_conditioned_features((changed,), spec, 10.)


def test_metric_is_group_balanced_and_target_free():
    spec = PortObligationRoleMetricSpec(4, False, False, 2, True)
    rows = (
        {"group": 0, "candidate_id": "a", "fit_label": True,
         "transitions": (transition(),)},
        {"group": 0, "candidate_id": "duplicate", "fit_label": True,
         "transitions": (transition(),)},
        {"group": 1, "candidate_id": "b", "fit_label": False,
         "transitions": (transition(parent="Z"),)},
    )
    model = fit_port_obligation_role_metric(rows, spec)
    value = score_port_obligation_role_metric(model, (transition(),))
    assert 0. < value < 1.
    assert not model.target_used
    assert not model.candidate_geometry_changed
    assert not model.raw_role_ids_or_coordinates_serialized


if __name__ == "__main__":
    test_features_preserve_role_owner_but_ignore_raw_neighbor_identity()
    test_metric_is_group_balanced_and_target_free()
    print("port-obligation role metric contracts: passed")
