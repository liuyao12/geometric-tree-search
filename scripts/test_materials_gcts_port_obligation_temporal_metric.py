#!/usr/bin/env python3
"""Contracts for the temporal port-obligation metric."""

from materials_gcts_port_obligation_temporal_metric import (
    PortObligationTemporalMetricSpec, fit_port_obligation_temporal_metric,
    score_port_obligation_temporal_metric, temporal_role_features)
from materials_gcts_port_obligation_automaton import (
    CONTRADICTION_FLAGS, ROLE_RELATIONS)


def _transition(*, discharged=0, contradiction=False):
    return {
        "selected_role_transitions": ({
            "role": ("X", 99, "Y", 101, 1.25),
            "before": 1, "after": 1 - discharged,
            "discharged": discharged, "produced": 0,
            "contradiction_flags": {
                name: contradiction and name == "forward_depleted"
                for name in CONTRADICTION_FLAGS
            },
            "relation_counts": {
                name: {"lost": 0, "gained": 0, "after": 0}
                for name in ROLE_RELATIONS
            },
        },),
        "selected_pair_relations": (),
    }


def test_temporal_bins_retain_order_without_raw_role_identity() -> None:
    spec = PortObligationTemporalMetricSpec(4, 2, False, 1, False)
    early = (_transition(discharged=1), _transition(),
             _transition(), _transition())
    late = (_transition(), _transition(),
            _transition(), _transition(discharged=1))
    early_features = temporal_role_features(early, spec, 0.)
    late_features = temporal_role_features(late, spec, 0.)
    assert early_features != late_features
    assert early_features[:270] == late_features[:270]

    rows = (
        {"group": 0, "candidate_id": "a", "fit_label": True,
         "transitions": early},
        {"group": 1, "candidate_id": "b", "fit_label": False,
         "transitions": late},
    )
    model = fit_port_obligation_temporal_metric(rows, spec)
    assert score_port_obligation_temporal_metric(model, early) > \
        score_port_obligation_temporal_metric(model, late)
    assert not model.target_used
    assert not model.candidate_geometry_changed
    assert not model.raw_role_ids_or_coordinates_serialized


def test_invalid_temporal_partition_fails_closed() -> None:
    try:
        temporal_role_features(
            (), PortObligationTemporalMetricSpec(2, 3, False, 1, False), 0.)
    except ValueError:
        pass
    else:
        raise AssertionError("more time bins than horizon must fail")


if __name__ == "__main__":
    test_temporal_bins_retain_order_without_raw_role_identity()
    test_invalid_temporal_partition_fails_closed()
    print("temporal port-obligation metric contracts: passed")
