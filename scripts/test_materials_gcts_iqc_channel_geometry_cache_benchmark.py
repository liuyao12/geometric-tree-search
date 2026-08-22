#!/usr/bin/env python3
"""Frozen regression for exact IQC geometry memoization."""

from materials_gcts_iqc_channel_geometry_cache_benchmark import (
    load_default_result)


def test_cache_parity():
    row = load_default_result()
    assert row["exact_state_parity"]
    assert row["uncached"]["terminal_states"] == 132
    assert row["cached"]["terminal_states"] == 132
    assert row["uncached"]["telemetry"]["unique_geometry_expansions"] == 368
    assert row["cached"]["telemetry"]["unique_geometry_expansions"] == 177
    assert row["cached"]["telemetry"]["geometry_cache_hits"] == 191
    assert row["geometry_expansion_reduction"] == 191
    assert row["measured_speedup"] > 1.
    assert not row["target_used"]


if __name__ == "__main__":
    test_cache_parity()
    print("IQC channel geometry cache benchmark: passed")
