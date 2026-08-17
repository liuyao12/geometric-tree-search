#!/usr/bin/env python3

import math

from materials_gcts_frontier_state_grammar import (
    FrontierWaveSnapshot, compile_frontier_state_grammar)
from materials_gcts_frontier_state_transitions import (
    compile_frontier_substitution_system, compile_frontier_transition_grammar)
from materials_gcts_frontier_substitution_benchmark import (
    evaluate, source_snapshots)


def test_two_state_substitution_is_learned_executed_and_expanding():
    result = evaluate()
    assert result.input_positions_species_only
    assert not result.compiler_uses_material_family_cell_target_or_expected_matrix
    assert result.source_wave_sites == (12, 18, 30)
    assert result.heldout_wave_sites == 48
    assert not result.learner_received_heldout
    assert result.learned_state_types == 2
    assert result.recurrent_rules == 2
    assert result.substitution_matrix == ((1, 1), (1, 0))
    assert math.isclose(result.learned_scale, 2.)
    assert math.isclose(result.asymptotic_growth,
                        (1 + math.sqrt(5)) / 2, rel_tol=1e-10)
    assert result.total_description_saving == 3
    assert result.globally_unique_child_ownership
    assert result.exact_explicit_replay_levels == 2
    assert result.exact_heldout_levels == 1
    assert result.million_site_action == 24
    assert result.million_site_count == 1_178_508
    assert result.exponential_gate_passed
    assert not result.target_used
    assert len(result.system_digest) == 64


def test_substitution_is_permutation_and_proper_rigid_motion_invariant():
    source = source_snapshots()[:3]
    moved = []
    for wave in source:
        rows = tuple(reversed(tuple(zip(wave.species, wave.positions))))
        moved.append(FrontierWaveSnapshot(
            wave.wave,
            tuple((point[1] + 31., -point[0] + 11., point[2] - 7.)
                  for _species, point in rows),
            tuple(species for species, _point in rows)))
    states = compile_frontier_state_grammar(tuple(moved), maximum_nodes=3)
    transitions = compile_frontier_transition_grammar(states, tuple(moved))
    system = compile_frontier_substitution_system(transitions)
    assert system is not None
    assert system.system_digest == evaluate().system_digest


if __name__ == "__main__":
    test_two_state_substitution_is_learned_executed_and_expanding()
    test_substitution_is_permutation_and_proper_rigid_motion_invariant()
    print("frontier substitution benchmark: all assertions passed")
