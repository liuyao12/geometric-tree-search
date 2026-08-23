#!/usr/bin/env python3
"""Pinned exact-parity/runtime regression for the optimized V3 replay."""

from materials_gcts_iqc_v3_optimized_consumed_replay import \
    load_default_result
from materials_gcts_port_incidence_search import PortRole, _port_role_repr


def test_pinned_replay_clears_runtime_gate_without_receipt_drift():
    row = load_default_result()
    assert row["runtime_gate_passed"]
    assert row["all_frozen_outputs_identical"]
    assert row["total_execution_seconds"] == 436.35797812500005
    assert row["stage_seconds"][-1] == [
        "chunked_fourth_frontiers", 214.5793755]


def test_port_role_repr_cache_preserves_historical_serialization():
    _port_role_repr.cache_clear()
    role = PortRole("X", (1, 2), "Y", (3,), 4)
    expected = ("PortRole(parent_color='X', parent_neighbors=(1, 2), "
                "source_color='Y', source_neighbors=(3,), "
                "separation_bin=4)")
    assert repr(role) == expected
    assert repr(role) == expected
    assert _port_role_repr.cache_info().hits == 1


if __name__ == "__main__":
    test_pinned_replay_clears_runtime_gate_without_receipt_drift()
    test_port_role_repr_cache_preserves_historical_serialization()
    print("optimized consumed V3 replay tests passed")
