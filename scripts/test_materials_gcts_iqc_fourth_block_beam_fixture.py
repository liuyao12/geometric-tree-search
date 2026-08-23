"""Regression for the target-sealed fourth-block beam receipt."""

from materials_gcts_iqc_fourth_block_beam_fixture import load_default_result


def test_fourth_block_beams_are_complete_and_target_sealed():
    row = load_default_result()
    assert row["groups"] == 5
    assert row["retained_candidates"] == 320
    assert row["parents_per_group"] == 8
    assert row["retained_per_parent"] == 8
    assert len(row["beams"]) == 5
    assert all(beam["retained_candidates"] == 64 for beam in row["beams"])
    assert not row["heldout_targets_opened"]
    assert not row["target_used_for_ranking"]
    assert not row["extension_executed"]
    assert not row["correctness_labels_present"]
    assert not row["candidate_geometry_changed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_fourth_block_beams_are_complete_and_target_sealed()
    print("target-sealed fourth-block beam fixture: passed")
