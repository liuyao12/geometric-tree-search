#!/usr/bin/env python3
"""Regression for the frozen IQC parent→child incidence corpus."""

from materials_gcts_iqc_parent_child_port_incidence_dataset import (
    load_default_result)


def test_parent_child_port_incidence_dataset():
    row = load_default_result()
    assert row["development_groups"] == 10
    assert row["examples"] == 1278
    assert row["exact_examples"] == 142
    assert row["nodes_per_graph"] == 6
    assert row["incidence_edges_per_graph"] == 15
    assert row["raw_type_ids_in_graph"] is False
    assert row["proper_se3_invariant"] is True
    assert row["target_used_for_geometry"] is False


if __name__ == "__main__":
    test_parent_child_port_incidence_dataset()
    print("IQC parent-child port-incidence dataset tests passed")
