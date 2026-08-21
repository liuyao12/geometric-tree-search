#!/usr/bin/env python3

from materials_gcts_iqc_port_obligation_automaton_audit import evaluate


def test_iqc_obligation_automaton_is_improved_but_red():
    report = evaluate()
    assert report["candidate_count"] == 120
    assert report["group_count"] == 10
    assert report["supplied_groups"] == 9
    assert report["heldout_selected_exact_supplied_groups"] == 8
    assert report["heldout_selected_correct_sites"] == 27
    assert report["maximum_available_correct_sites"] == 28
    assert report["prior_relational_selected_exact_supplied_groups"] == 7
    assert report["weakest_link_sequence_improves_prior"] is True
    assert report["shuffle_exact_median"] == 5
    assert report["finite_state_count"] == 102
    assert report["finite_state_group_support_histogram"] == (
        (1, 47), (2, 38), (3, 9), (4, 3), (5, 1), (7, 4))
    assert report["shuffle_exact_maximum"] == 7
    assert report["shuffle_upper_tail_p"] == .03125
    assert report["model_digest"] == \
        "ad001ae110fdb54c43950a9a37c25512cbca87605254b3a0caf6e5991465804f"
    assert report["audit_digest"] == \
        "ebb0abf7492d478bbd4921890a5fc95d1618b53620bebae9b08b5756be8a92ef"
    assert report["exploratory_spec_not_preregistered"] is True
    assert report["integrated_as_default_marking"] is False
    assert report["obligation_automaton_gate_passed"] is False


def main():
    test_iqc_obligation_automaton_is_improved_but_red()
    print("IQC obligation automaton audit passed")


if __name__ == "__main__":
    main()
