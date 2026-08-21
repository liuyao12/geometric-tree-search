#!/usr/bin/env python3

from materials_gcts_iqc_port_obligation_confirmation import (
    load_default_result)


def test_one_shot_confirmation_is_honestly_red():
    row = load_default_result()
    assert row["confirmation_center"] == [-110., -70., -70.]
    assert row["seed_atoms"] == 480
    assert row["target_atoms"] == 2066
    assert row["candidate_counts_by_depth"] == [8, 40, 152]
    assert row["complete_terminal_count"] == 152
    assert row["retained_candidates"] == 13
    assert row["candidate_portfolio_contains_exact"] is True
    assert row["exact_candidates"] == 2
    assert row["first_exact_rank"] == 5
    assert row["selected_action_exact"] is False
    assert row["selected_action_correct_sites"] == 2
    assert row["selected_action_false_sites"] == 1
    assert row["selected_rollout_steps"] == 16
    assert min(row["ranked_recognized_state_fractions"]) == .0625
    assert max(row["ranked_recognized_state_fractions"]) == .1875
    assert row["oracle_bound_plus_one_stable"] is True
    assert row["target_open_count"] == 1
    assert row["event_order"] == [
        "protocol-verified", "model-frozen", "seed-frozen",
        "candidates-frozen", "execution-frozen", "target-opened", "scored"]
    assert row["target_used_for_fit_candidates_trajectory_or_rank"] is False
    assert row["confirmation_gate_passed"] is False
    assert row["autonomous_growth_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


def main():
    test_one_shot_confirmation_is_honestly_red()
    print("IQC port-obligation one-shot confirmation regression passed")


if __name__ == "__main__":
    main()
