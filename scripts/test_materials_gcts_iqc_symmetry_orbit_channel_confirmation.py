#!/usr/bin/env python3
"""Durable regression for the consumed IQC channel confirmation."""

from materials_gcts_iqc_symmetry_orbit_channel_confirmation import evaluate


def test_reserved_symmetry_orbit_confirmation_is_honestly_red():
    report = evaluate()
    assert report.protocol_digest == \
        "3675cd8b4883c611bea899ad6d9c2629882e62b00881f84501898abc99f4030a"
    assert report.model_digest == \
        "38ee6bf62d4f58450a5f5ba666f350a5a04e6ea5dee797d420dad385ae314742"
    assert report.candidate_graph_digest == \
        "e596a0cfb0412aefd05205b400083f2ea759497eb443103e001cc1003cb40253"
    assert report.descriptor_digest == \
        "fd10be3ad1d2e27ba45f286ee99810e613b15c401addd0fd170f882ed21119e5"
    assert report.selected_action_digest == \
        "05c2566979d86c135c247a9bbe6420839768a64a54a6eb08da161beff0503bad"
    assert report.detailed_top_band == 4
    assert report.channel_top_band == 2
    assert report.selected_view == "detailed"
    assert report.selected_actions == 2
    assert report.selected_correct_actions == 0
    assert report.selected_false_actions == 2
    assert report.precision == 0.
    assert report.spatial_domains_disjoint is True
    assert report.event_order == (
        "fit-frozen", "candidate-graph-frozen", "selection-frozen",
        "target-opened", "scored")
    assert report.target_open_count == 1
    assert report.target_materialized_after_selection_freeze is True
    assert report.target_used_for_fit_or_selection is False
    assert report.confirmation_gate_passed is False
    assert report.stationary_or_exponential_certificate is False


def main():
    test_reserved_symmetry_orbit_confirmation_is_honestly_red()
    print("IQC symmetry-orbit channel confirmation regression passed")


if __name__ == "__main__":
    main()
