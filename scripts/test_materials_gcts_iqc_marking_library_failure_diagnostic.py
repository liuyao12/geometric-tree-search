#!/usr/bin/env python3
"""Regression for the consumed five-channel failure localization."""

from materials_gcts_iqc_marking_library_failure_diagnostic import (
    load_default_diagnostic)


def test_exact_geometry_was_present_but_both_children_were_truncated() -> None:
    row = load_default_diagnostic()
    assert row["exact_complete_second_child_count"] == 2
    assert row["omitted_exact_second_child_count"] == 2
    assert row["exact_nine_action_lineages_after_posthoc_expansion"] > 0
    assert row["failure_localized_to_child_ranking_truncation"]
    children = row["exact_complete_second_children"]
    assert [(child["parent"], child["child"],
             child["local_section_rank"])
            for child in children] == [(1, 51, 7), (7, 39, 5)]
    assert all(not child["union_selected"] for child in children)
    assert all(child["exact_nine_action_lineages"] > 0
               for child in children)
    assert not row["candidate_selection_target_used"]
    assert row["consumed_target_diagnostic_only"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["winner_or_autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_exact_geometry_was_present_but_both_children_were_truncated()
    print("fresh five-channel IQC failure localization: passed")
