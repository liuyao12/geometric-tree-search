#!/usr/bin/env python3
"""Regression and ID-erasure controls for port-transition macros."""

from copy import deepcopy

from materials_gcts_iqc_parent_child_port_transition_dataset import (
    graph_features, load_default_result)


def test_port_transition_dataset():
    row = load_default_result()
    assert row["development_groups"] == 10
    assert row["examples"] == 1278
    assert row["exact_examples"] == 142
    assert row["raw_type_ids_in_features"] is False
    assert row["target_used_for_geometry"] is False


def test_graph_features_erase_raw_ids():
    graph = {
        "nodes": [{"support_type_id": 4, "action_species": ["str", "'X'"],
                   "matched_atoms": 3, "prototype_atoms": 5,
                   "training_group_support": 4}],
        "edges": [], "incidence_edges": [], "isolated_nodes": 1,
        "canonical_digest": "a", "target_used": False,
        "lattice_coordinates_used": False,
    }
    changed = deepcopy(graph)
    changed["nodes"][0]["support_type_id"] = 999
    changed["canonical_digest"] = "different"
    assert graph_features(graph) == graph_features(changed)


if __name__ == "__main__":
    test_port_transition_dataset()
    test_graph_features_erase_raw_ids()
    print("parent-child port-transition dataset tests passed")
