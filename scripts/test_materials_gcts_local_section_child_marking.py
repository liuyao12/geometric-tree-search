#!/usr/bin/env python3
"""Fast invariants for the frozen local-section child marking."""

from materials_gcts_local_section_child_marking import (
    EXPECTED_ARTIFACT_DIGEST, EXPECTED_FIXTURE_SHA256,
    EXPECTED_MODEL_DIGEST, load_default_marking, rank_child_states,
    select_child_ids)


def test_frozen_model_is_id_free_and_ranks_immutable_children() -> None:
    model, artifact = load_default_marking()
    assert len(EXPECTED_FIXTURE_SHA256) == 64
    assert artifact["artifact_digest"] == EXPECTED_ARTIFACT_DIGEST
    assert model.model_digest == EXPECTED_MODEL_DIGEST
    assert artifact["training_rows"] == 324
    assert artifact["positive_rows"] == 145
    assert artifact["selected"]["supplied_exact_child_groups"] == 4
    assert artifact["selected"]["total_exact_child_groups"] == 4
    assert model.ridge_lambda == 1000.
    assert model.child_top_k == 2
    assert model.aggregation == "minimum"
    assert len(model.feature_names) == 136
    assert model.target_used_for_fitting
    assert not model.target_used_for_scoring
    assert not artifact["family_or_global_origin_feature"]

    branch = {
        "first_actions": (((0., 0., 0.), "X"),
                          ((2., 0., 0.), "Y"),
                          ((0., 2., 0.), "Z")),
        "second_actions": ((((3., 0., 0.), "X"),
                            ((0., 3., 0.), "Y"),
                            ((0., 0., 3.), "Z")),
                           (((4., 0., 0.), "X"),
                            ((0., 4., 0.), "Y"),
                            ((0., 0., 4.), "Z"))),
        "second_channel_scores": ((.1, .2, .3, .4),
                                  (.4, .3, .2, .1)),
    }
    seed_positions = ((-1., 0., 0.), (0., -1., 0.), (0., 0., -1.))
    seed_species = ("X", "Y", "Z")
    ranked = rank_child_states(
        model=model, seed_positions=seed_positions,
        seed_species=seed_species, branch=branch)
    assert {row[0] for row in ranked} == {0, 1}
    assert all(0. <= row[1] <= 1. for row in ranked)
    assert select_child_ids(
        model=model, seed_positions=seed_positions,
        seed_species=seed_species, branch=branch) == tuple(
            row[0] for row in ranked)


if __name__ == "__main__":
    test_frozen_model_is_id_free_and_ranks_immutable_children()
    print("frozen local-section child marking: passed")
