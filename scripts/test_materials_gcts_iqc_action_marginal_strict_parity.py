#!/usr/bin/env python3
"""Pinned no-saturation receipt parity for compute-bounded V4."""

from materials_gcts_iqc_action_marginal_strict_parity import \
    load_default_result


def test_compute_bounded_v4_is_exactly_v3_without_saturation():
    row = load_default_result()
    assert row["selected_prefixes"] == 8
    assert row["diverse_fallback_prefixes"] == 0
    assert row["raw_nine_action_lineages"] == 1102
    assert row["exact_receipt_parity"]
    assert row["raw_lineage_digest"] == row["expected_v3_digest"]


if __name__ == "__main__":
    test_compute_bounded_v4_is_exactly_v3_without_saturation()
    print("IQC strict action-marginal parity tests passed")
