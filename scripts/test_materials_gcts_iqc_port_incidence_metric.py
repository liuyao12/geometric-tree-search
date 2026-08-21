#!/usr/bin/env python3
"""Focused contracts for continuous shared port-graph features and metric."""

from materials_gcts_iqc_port_incidence_metric import (
    all_specs, graph_features, metric_rows, select_spec)


def test_metric_feature_and_selection_contract():
    rows = metric_rows()
    assert len(rows) == 168
    assert len(all_specs()) == 440
    names, features, ranges = graph_features(rows[0]["graph"])
    assert len(names) == len(features) == len(rows[0]["features"])
    assert set(ranges) == {
        "geometry", "roles", "pose", "environment", "incidence"}
    assert not any("candidate" in name or "group" in name for name in names)
    selected, audits = select_spec(rows)
    assert len(audits) == 440
    assert selected.supplied_groups == 9
    assert selected.selected_precision >= .95


if __name__ == "__main__":
    test_metric_feature_and_selection_contract()
    print("port incidence metric tests passed")
