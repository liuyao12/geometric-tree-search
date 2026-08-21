#!/usr/bin/env python3

from materials_gcts_iqc_marking_portfolio_multiblock_receipt import load_receipt


def test_multiblock_portfolio_is_preserved_as_supply_only():
    row = load_receipt()
    assert row.center == (120., -40., -220.)
    assert row.seed_atoms == 476 and row.target_atoms == 2069
    assert row.level_candidate_counts == (8, 16, 16)
    assert row.level_unique_state_counts == (8, 15, 16)
    assert row.first_block_exact_connection_head_preserved
    assert row.terminal_correct_sites == (6, 6)
    assert row.terminal_wrong_sites == (3, 3)
    assert row.terminal_exact == (False, False)
    assert row.exact_terminal_supply == 0
    assert not row.target_used_during_tree_construction
    assert row.target_opened_after_complete_tree_froze
    assert row.consumed_target_diagnostic_only
    assert not row.winner_selected
    assert not row.autonomous_growth_claimed
    assert not row.stationary_or_exponential_claimed


if __name__ == "__main__":
    test_multiblock_portfolio_is_preserved_as_supply_only()
    print("red three-block IQC marking portfolio receipt preserved")
