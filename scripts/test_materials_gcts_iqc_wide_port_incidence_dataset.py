#!/usr/bin/env python3
"""Regression contract for the shared-schema wide IQC fixture."""

from materials_gcts_iqc_wide_port_incidence_dataset import (
    load_default_dataset)
from materials_gcts_port_incidence_graph import (
    development_geometry_to_incidence_graph)
from materials_gcts_iqc_recurrent_macro_geometry_dataset import load_fixture


def test_wide_fixture_and_common_schema():
    wide = load_default_dataset()
    development = load_fixture()
    development_graphs = tuple(development_geometry_to_incidence_graph(
        row["geometry"]) for group in development["groups"]
        for row in group["rows"])
    wide_graphs = tuple(row["port_incidence_graph"]
                       for group in wide["groups"] for row in group["rows"])
    assert len(development_graphs) == 168
    assert len(wide_graphs) == 120
    fields = set(development_graphs[0])
    assert all(set(graph) == fields for graph in development_graphs)
    assert all(set(graph) == fields for graph in wide_graphs)
    assert all(len(graph["nodes"]) == 3 and len(graph["edges"]) == 3
               for graph in development_graphs + wide_graphs)
    assert not wide["second_block_targets_or_labels_used_for_graph_generation"]
    assert wide["labels_joined_after_all_graphs_freeze"]
    assert not wide["raw_occurrence_ids_serialized"]
    assert not wide["global_frame_semantic"]


if __name__ == "__main__":
    test_wide_fixture_and_common_schema()
    print("wide port incidence dataset tests passed")
