#!/usr/bin/env python3

from materials_gcts_iqc_prefix_marking_portfolio_receipt import load_receipt


def test_prefix_portfolio_boundary_is_preserved_honestly_red():
    row = load_receipt()
    assert row["raw_prefix_reach"][
        "target_guided_exact_three_block_path_supplied"]
    assert row["channel_diverse_prefix_portfolio"][
        "block1_exact_candidates"] == 2
    assert row["channel_diverse_prefix_portfolio"][
        "block2_exact_candidates"] == 0
    assert not row["autonomous_growth_claimed"]


if __name__ == "__main__":
    test_prefix_portfolio_boundary_is_preserved_honestly_red()
    print("red IQC prefix marking portfolio boundary preserved")
