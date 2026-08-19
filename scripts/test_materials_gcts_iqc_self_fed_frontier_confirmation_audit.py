#!/usr/bin/env python3

from materials_gcts_iqc_self_fed_frontier_confirmation_audit import audit


def test_consumed_confirmation_is_supply_green_and_autonomy_red():
    row = audit()
    assert row["complete_tree_supplies_exact"]
    assert row["exact_terminal_count"] == 62
    assert not row["dual_portfolio_supplies_exact"]
    assert not row["six_action_autonomous_gate_passed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_consumed_confirmation_is_supply_green_and_autonomy_red()
    print("self-fed frontier confirmation-audit tests passed")
