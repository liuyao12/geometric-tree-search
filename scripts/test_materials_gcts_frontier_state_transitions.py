#!/usr/bin/env python3

import math
from dataclasses import replace

from materials_gcts_frontier_state_grammar import (
    FrontierWaveSnapshot, compile_frontier_state_grammar)
from materials_gcts_frontier_state_transitions import (
    GeneratedFrontierState, as_generated_state,
    compile_frontier_substitution_system, compile_frontier_transition_grammar,
    execute_frontier_substitution, execute_frontier_transition,
    symbolic_frontier_expansion,
    symbolic_frontier_substitution_expansion)
from materials_gcts_oriented_overlap_ports import IDENTITY, matmul, matvec


R90 = ((0., -1., 0.), (1., 0., 0.), (0., 0., 1.))
R180 = ((-1., 0., 0.), (0., -1., 0.), (0., 0., 1.))
LOCAL = ((-0.5, -math.sqrt(3) / 6, 0.),
         (0.5, -math.sqrt(3) / 6, 0.),
         (0., math.sqrt(3) / 3, 0.))
SPECIES = ("A", "B", "C")
OTHER_SPECIES = ("D", "E", "F")


def _add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def _scale(value, point):
    return tuple(value * coordinate for coordinate in point)


def _children(parent):
    first = GeneratedFrontierState(
        0, parent.scale * 2., matmul(parent.rotation, R90),
        parent.translation)
    second = GeneratedFrontierState(
        0, parent.scale * 2., parent.rotation,
        _add(parent.translation, matvec(
            parent.rotation, _scale(parent.scale, (20., 0., 0.)))))
    return first, second


def _render(instances):
    rows = []
    for instance in instances:
        for species, local in zip(SPECIES, LOCAL):
            rows.append((species, _add(
                instance.translation,
                matvec(instance.rotation, _scale(instance.scale, local)))))
    rows.sort(key=repr)
    return tuple(species for species, _point in rows), \
        tuple(point for _species, point in rows)


def _fixture():
    levels = [(
        GeneratedFrontierState(0, 1., IDENTITY, (-100., 0., 0.)),
        GeneratedFrontierState(0, 1., IDENTITY, (100., 0., 0.)),
    )]
    for _ in range(2):
        levels.append(tuple(child for parent in levels[-1]
                            for child in _children(parent)))
    waves = []
    for wave, instances in enumerate(levels, 1):
        species, positions = _render(instances)
        waves.append(FrontierWaveSnapshot(wave, positions, species))
    return tuple(waves)


def _substitution_children(parent):
    offset = matvec(parent.rotation, _scale(
        parent.scale, (20., 0., 0.)))
    if parent.type_id == 0:
        return (
            GeneratedFrontierState(
                0, parent.scale * 2.,
                matmul(parent.rotation, R180), parent.translation),
            GeneratedFrontierState(
                1, parent.scale * 2., parent.rotation,
                _add(parent.translation, offset)))
    return (GeneratedFrontierState(
        0, parent.scale * 2., parent.rotation,
        _add(parent.translation, offset)),)


def _render_typed(instances):
    rows = []
    species_by_type = {0: SPECIES, 1: OTHER_SPECIES}
    for instance in instances:
        for species, local in zip(species_by_type[instance.type_id], LOCAL):
            rows.append((species, _add(
                instance.translation,
                matvec(instance.rotation, _scale(instance.scale, local)))))
    rows.sort(key=repr)
    return tuple(species for species, _point in rows), \
        tuple(point for _species, point in rows)


def _substitution_fixture():
    levels = [(
        GeneratedFrontierState(0, 1., IDENTITY, (-10000., 0., 0.)),
        GeneratedFrontierState(0, 1., IDENTITY, (-8000., 0., 0.)),
        GeneratedFrontierState(1, 1., IDENTITY, (8000., 0., 0.)),
        GeneratedFrontierState(1, 1., IDENTITY, (10000., 0., 0.)),
    )]
    for _ in range(2):
        levels.append(tuple(child for parent in levels[-1]
                            for child in _substitution_children(parent)))
    waves = []
    for wave, instances in enumerate(levels, 1):
        species, positions = _render_typed(instances)
        waves.append(FrontierWaveSnapshot(wave, positions, species))
    return tuple(waves)


def _site_keys(sites, tolerance=5e-6):
    return {(repr(species), tuple(round(value / tolerance) for value in point))
            for species, point in sites}


def test_stationary_transition_executes_two_levels_and_crosses_million():
    waves = _fixture()
    states = compile_frontier_state_grammar(waves, maximum_nodes=3)
    transitions = compile_frontier_transition_grammar(states, waves)
    assert not transitions.target_used
    assert len(transitions.stationary_rule_ids) == 1
    rule = transitions.rules[transitions.stationary_rule_ids[0]]
    assert len(rule.child_placements) == 2
    state = states.recurring_state_types[rule.parent_type]
    parents = tuple(as_generated_state(state.type_id, occurrence)
                    for occurrence in state.occurrences
                    if occurrence.wave == 1)
    first = execute_frontier_transition(
        transitions, states.recurring_state_types, rule.rule_id, parents)
    assert first.exact_colored_union
    assert first.collision_free
    expected_first = tuple(zip(waves[1].species, waves[1].positions))
    assert _site_keys(first.sites) == _site_keys(expected_first)
    second = execute_frontier_transition(
        transitions, states.recurring_state_types, rule.rule_id,
        first.children)
    assert second.collision_free
    expected_second = tuple(zip(waves[2].species, waves[2].positions))
    assert _site_keys(second.sites) == _site_keys(expected_second)
    symbolic = symbolic_frontier_expansion(rule, state, 2, 18)
    assert symbolic.action_counts[:3] == (2, 4, 8)
    assert symbolic.represented_site_counts[:3] == (6, 12, 24)
    assert symbolic.million_site_action == 18
    assert symbolic.represented_site_counts[-1] == 1_572_864


def test_closed_heterogeneous_substitution_replays_and_crosses_million():
    waves = _substitution_fixture()
    states = compile_frontier_state_grammar(waves, maximum_nodes=3)
    transitions = compile_frontier_transition_grammar(states, waves)
    system = compile_frontier_substitution_system(transitions)
    assert system is not None and system.exponential_gate_passed
    assert system.substitution_matrix == ((1, 1), (1, 0))
    assert math.isclose(system.learned_scale, 2.)
    assert math.isclose(system.asymptotic_growth,
                        (1 + math.sqrt(5)) / 2, rel_tol=1e-10)
    assert system.total_description_saving == 3
    parents = tuple(as_generated_state(state.type_id, occurrence)
                    for state in states.recurring_state_types
                    if state.type_id in system.state_types
                    for occurrence in state.occurrences
                    if occurrence.wave == 1)
    first = execute_frontier_substitution(
        transitions, system, states.recurring_state_types, parents)
    assert first.exact_colored_union and first.collision_free
    assert _site_keys(first.sites) == _site_keys(tuple(zip(
        waves[1].species, waves[1].positions)))
    second = execute_frontier_substitution(
        transitions, system, states.recurring_state_types, first.children)
    assert second.exact_colored_union and second.collision_free
    assert _site_keys(second.sites) == _site_keys(tuple(zip(
        waves[2].species, waves[2].positions)))
    symbolic = symbolic_frontier_substitution_expansion(
        system, states.recurring_state_types, (2, 2), 28)
    assert symbolic.action_type_counts[:3] == ((2, 2), (4, 2), (6, 4))
    assert symbolic.represented_site_counts[:3] == (12, 18, 30)
    assert symbolic.million_site_action is not None
    assert symbolic.represented_site_counts[
        symbolic.million_site_action] >= 1_000_000


def test_target_taint_fails_closed_before_transition_learning():
    waves = _fixture()
    tainted = waves[:-1] + (FrontierWaveSnapshot(
        waves[-1].wave, waves[-1].positions, waves[-1].species, True),)
    states = compile_frontier_state_grammar(tainted, maximum_nodes=3)
    transitions = compile_frontier_transition_grammar(states, tainted)
    assert transitions.target_used
    assert not transitions.rules
    assert compile_frontier_substitution_system(transitions) is None


def test_altered_frozen_rule_geometry_is_rejected():
    waves = _fixture()
    states = compile_frontier_state_grammar(waves, maximum_nodes=3)
    transitions = compile_frontier_transition_grammar(states, waves)
    rule = transitions.rules[transitions.stationary_rule_ids[0]]
    altered_placement = replace(
        rule.child_placements[0], relative_translation=(.01, 0., 0.))
    altered_rule = replace(
        rule, child_placements=(altered_placement,) +
        rule.child_placements[1:])
    altered = replace(transitions, rules=(altered_rule,))
    state = states.recurring_state_types[rule.parent_type]
    parent = as_generated_state(state.type_id, state.occurrences[0])
    try:
        execute_frontier_transition(
            altered, states.recurring_state_types, rule.rule_id, (parent,))
    except ValueError as error:
        assert "frozen code" in str(error)
    else:
        raise AssertionError("altered transition geometry must fail closed")


def test_child_batches_reject_subminimum_inter_parent_collisions():
    waves = _fixture()
    states = compile_frontier_state_grammar(waves, maximum_nodes=3)
    transitions = compile_frontier_transition_grammar(states, waves)
    rule = transitions.rules[transitions.stationary_rule_ids[0]]
    state = states.recurring_state_types[rule.parent_type]
    parent = as_generated_state(state.type_id, state.occurrences[0])
    crowded = replace(parent, translation=(
        parent.translation[0] + .01,
        parent.translation[1], parent.translation[2]))
    execution = execute_frontier_transition(
        transitions, states.recurring_state_types, rule.rule_id,
        (parent, crowded))
    assert not execution.collision_free


def test_transition_grammar_is_rigid_motion_and_permutation_invariant():
    waves = _fixture()
    original_states = compile_frontier_state_grammar(waves, maximum_nodes=3)
    original = compile_frontier_transition_grammar(original_states, waves)
    moved = []
    for wave in waves:
        rows = tuple(reversed(tuple(zip(wave.species, wave.positions))))
        moved.append(FrontierWaveSnapshot(
            wave.wave,
            tuple((point[1] + 31., -point[0] + 11., point[2] - 7.)
                  for _species, point in rows),
            tuple(species for species, _point in rows)))
    moved = tuple(moved)
    moved_states = compile_frontier_state_grammar(moved, maximum_nodes=3)
    transformed = compile_frontier_transition_grammar(moved_states, moved)
    assert transformed.grammar_digest == original.grammar_digest
    assert transformed.stationary_rule_ids == original.stationary_rule_ids


if __name__ == "__main__":
    test_stationary_transition_executes_two_levels_and_crosses_million()
    test_closed_heterogeneous_substitution_replays_and_crosses_million()
    test_target_taint_fails_closed_before_transition_learning()
    test_altered_frozen_rule_geometry_is_rejected()
    test_child_batches_reject_subminimum_inter_parent_collisions()
    test_transition_grammar_is_rigid_motion_and_permutation_invariant()
    print("frontier-state transition tests: passed")
