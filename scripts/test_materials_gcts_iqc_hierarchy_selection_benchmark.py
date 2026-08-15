#!/usr/bin/env python3
"""Slow train-only regression for the future-RL hierarchy comparator."""

from materials_gcts_iqc_hierarchy_selection_benchmark import evaluate


def test_beam_selection_improves_but_does_not_hide_evidence_exhaustion():
    result = evaluate()
    assert result.selection_target_blind
    assert result.strict_stationarity_external_and_unchanged
    assert result.beam_improves_fixed_horizon_train_objective
    assert result.beam_retains_more_exact_derivations
    assert all(action.derivation_policy == "representative"
               for action in result.greedy.actions)
    assert all(action.derivation_policy == "alternative-consistent"
               for action in result.beam.actions)
    assert all(score.exact_cover_fraction == 1.
               for score in result.beam.step_scores)

    # Selection improves retained evidence/connectivity, but does not turn
    # evidence exhaustion into a stationary-recursion claim.
    assert not result.beam_avoids_greedy_collapse
    assert result.beam.positive_levels == result.greedy.positive_levels
    assert not result.greedy.stationary and not result.beam.stationary

    # A promoted-prototype heldout matcher is not yet implemented.  Keeping
    # this red is safer than accidentally applying the primitive matcher.
    assert not result.heldout_fixture_available
    assert not result.greedy_heldout.available
    assert not result.beam_heldout.available
    assert "not promoted macro vocabularies" in (
        result.beam_heldout.unavailable_reason)


if __name__ == "__main__":
    test_beam_selection_improves_but_does_not_hide_evidence_exhaustion()
    print("IQC hierarchy beam selection: all assertions passed")
