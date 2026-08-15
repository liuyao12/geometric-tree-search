#!/usr/bin/env python3
"""Slow sealed gate for disjoint-patch primitive IQC continuation."""

from materials_gcts_disjoint_iqc_frontier_benchmark import evaluate


def test_disjoint_iqc_frontier_replay_is_sealed_and_reproducible():
    result = evaluate()
    assert (result.training_atoms, result.seed_atoms,
            result.target_atoms) == (887, 223, 877)
    assert result.training_target_raw_id_intersection == 0
    assert result.spatial_domains_disjoint
    assert not result.centers_related_by_origin_fixing_proper_rotation
    assert result.recognized_seed_occurrences == 20
    assert result.target_materialized_after_all_replays
    assert not result.target_used_before_scoring
    one, ten, hundred = result.waves
    assert (one.proposed_atoms, one.correct_atoms) == (2, 2)
    assert (ten.proposed_atoms, ten.correct_atoms) == (23, 21)
    assert ten.precision > .91 and ten.heldout_recall > .032
    assert hundred.accepted_actions == 100
    assert hundred.elapsed_seconds < 120.0
    assert all(not wave.target_used_for_proposals for wave in result.waves)


if __name__ == "__main__":
    test_disjoint_iqc_frontier_replay_is_sealed_and_reproducible()
    print("slow disjoint IQC frontier benchmark: passed")
