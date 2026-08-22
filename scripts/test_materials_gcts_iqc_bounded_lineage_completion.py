"""Regression for the target-blind bounded lineage completion fixture."""

from materials_gcts_iqc_bounded_lineage_completion import load_default_result


def test_bounded_lineage_completion_is_complete_and_target_blind():
    row = load_default_result()
    assert row["missing_prefixes_completed"] == 70
    assert row["generated_lineages"] > 0
    assert row["unique_geometry_expansions"] < \
        row["naive_geometry_expansions"]
    assert row["saved_geometry_expansions"] > 0
    assert row["all_selected_prefixes_complete"]
    assert not row["target_used_for_completion"]
    assert not row["correctness_labels_present"]
    assert not row["winner_selected"]
    assert not row["stationary_or_exponential_claimed"]
    for case in row["cases"]:
        selected = {tuple(item) for item in case["selected_pairs"]}
        existing = {tuple(item) for item in case["existing_pairs"]}
        missing = {tuple(item) for item in case["missing_pairs"]}
        generated = {(item["parent_id"], item["child_stable_index"])
                     for item in case["generated"]}
        assert not existing & missing
        assert selected == existing | missing
        assert generated == missing
        assert not case["target_used"]


if __name__ == "__main__":
    test_bounded_lineage_completion_is_complete_and_target_blind()
    print("bounded target-blind lineage completion: passed")
