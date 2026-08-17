#!/usr/bin/env python3
"""Regression for the sealed IQC symmetry-orbit channel preflight."""

from materials_gcts_iqc_symmetry_orbit_channel_preflight import evaluate


def test_symmetry_orbit_channel_rule_passes_every_development_nucleus():
    report = evaluate()
    assert report.reserved_confirmation_center_imported_or_accessed is False
    assert report.candidate_geometry_changed_between_views is False
    assert report.candidate_graph_digest == \
        "145884f7c057063e44c55d71e57f94d0bb5e6dea2b96317174dad5ae6e1daef8"
    assert report.descriptor_digest == \
        "4da17ec209403e5ce43b13d3a6f6d7e96fb94603e17ceeb31af615d8e48d8743"
    assert report.fold_model_digest == \
        "eefce584a71baa0077824827cf8cecd733fb6a7a834e49616d8b33d86db6e96a"
    assert report.candidates_by_group == (
        4164, 5156, 5008, 4842, 5034, 5034, 5034, 5034, 5296)
    assert report.detailed_top_band_by_group == (8, 4, 1, 6, 1, 1, 1, 1, 1)
    assert report.channel_top_band_by_group == (24, 2, 1, 6, 1, 1, 1, 1, 1)
    assert report.selected_view_by_group == (
        "channel", "detailed", "detailed", "detailed", "detailed",
        "detailed", "detailed", "detailed", "detailed")
    assert report.detailed_correct_by_group == (0, 2, 2, 2, 2, 2, 2, 2, 2)
    assert report.channel_correct_by_group == (2, 2, 1, 2, 2, 2, 2, 2, 0)
    assert report.orbit_selected_correct_by_group == (2,) * 9
    assert report.detailed_correct_actions == 16
    assert report.channel_correct_actions == 15
    assert report.orbit_selected_actions == 18
    assert report.orbit_selected_correct_actions == 18
    assert report.orbit_selected_false_actions == 0
    assert report.orbit_selected_precision == 1.
    assert report.exact_groups == 9
    assert report.selection_rule_target_free is True
    assert report.development_gate_passed is True


def main():
    test_symmetry_orbit_channel_rule_passes_every_development_nucleus()
    print("IQC symmetry-orbit channel preflight test passed")


if __name__ == "__main__":
    main()
