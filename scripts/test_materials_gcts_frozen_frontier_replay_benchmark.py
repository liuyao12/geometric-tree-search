#!/usr/bin/env python3

from materials_gcts_frozen_frontier_replay_benchmark import evaluate


def test_frozen_frontier_replay_has_honest_cross_family_gate():
    result = evaluate()
    assert result.all_targets_sealed_from_proposals
    # These statuses are evidence, not desired labels.  The NaCl scorer uses a
    # symmetric oracle crop so either side of the observed frontier is valid.
    # Greedy replay then makes one correct atom, while an oracle ranking of the
    # already-enumerated candidate set could make six.  IQC has no exterior
    # action at all.  CdYb makes three correct atoms, but recall is below 0.6%.
    assert result.crystal_gate_passed
    assert not result.ideal_quasicrystal_gate_passed
    assert result.real_quasicrystal_gate_passed
    assert result.cases[0].precision == 1.0
    assert result.cases[0].oracle_correct_action_exists
    assert result.cases[0].oracle_best_correct_atoms >= 6
    assert result.cases[1].proposed_novel_atoms == 0
    assert not result.cases[1].oracle_correct_action_exists
    assert result.cases[2].correct_novel_atoms == 3
    assert result.cases[2].oracle_best_correct_atoms >= 19
    assert result.cases[2].heldout_recall < .006
    assert all(case.explicit_unoriented_seed_atoms > 0
               for case in result.cases)


if __name__ == "__main__":
    test_frozen_frontier_replay_has_honest_cross_family_gate()
    print("frozen cross-family frontier replay gate: honest partial pass")
