#!/usr/bin/env python3

from materials_gcts_amplifying_pair_benchmark import evaluate


def test_higher_order_batches_amplify_exactly_across_unseen_scales() -> None:
    result = evaluate()
    assert result.training_atoms == 507
    assert result.seed_minimum_pair_votes == 11
    assert tuple(scale.consensus_threshold for scale in result.scales) == (7, 5)
    assert tuple(scale.target_atoms for scale in result.scales) == (8603, 37073)
    assert tuple(scale.accepted_sites for scale in result.scales) == (80, 480)
    assert all(scale.precision == 1.0 for scale in result.scales)
    assert result.accepted_batch_growth_factor == 6.0
    assert result.exact_at_both_unseen_scales
    assert not result.heldout_geometry_used_for_fitting
    assert not result.oracle_colors_used_for_proposals
    assert result.exponential_style_amplification
    assert not result.million_site_growth_claimed
    assert result.benchmark_passed


if __name__ == "__main__":
    test_higher_order_batches_amplify_exactly_across_unseen_scales()
    print("amplifying higher-order GCTS batches: benchmark passed")
