#!/usr/bin/env python3
"""Executable two-state frontier substitution benchmark.

This is a generic algebra/control, not a claim about the real IQC trace.  The
learner receives only three colored point-cloud waves.  It must recover global
one-owner parent/child assignments, the mixed rules ``A -> AB`` and ``B -> A``,
their common proper similarity scale, and the expanding substitution matrix.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_state_grammar import (
    FrontierWaveSnapshot, compile_frontier_state_grammar)
from materials_gcts_frontier_state_transitions import (
    GeneratedFrontierState, as_generated_state,
    compile_frontier_substitution_system, compile_frontier_transition_grammar,
    execute_frontier_substitution,
    symbolic_frontier_substitution_expansion)
from materials_gcts_oriented_overlap_ports import (
    IDENTITY, matmul, matvec)

Point = tuple[float, float, float]
R180 = ((-1., 0., 0.), (0., -1., 0.), (0., 0., 1.))
LOCAL = ((-0.5, -math.sqrt(3) / 6, 0.),
         (0.5, -math.sqrt(3) / 6, 0.),
         (0., math.sqrt(3) / 3, 0.))
SPECIES = {0: ("A", "B", "C"), 1: ("D", "E", "F")}


@dataclass(frozen=True)
class FrontierSubstitutionBenchmark:
    input_positions_species_only: bool
    compiler_uses_material_family_cell_target_or_expected_matrix: bool
    source_wave_sites: tuple[int, ...]
    heldout_wave_sites: int
    learner_received_heldout: bool
    learned_state_types: int
    recurrent_rules: int
    substitution_matrix: tuple[tuple[int, ...], ...]
    learned_scale: float
    asymptotic_growth: float
    total_description_saving: int
    globally_unique_child_ownership: bool
    exact_explicit_replay_levels: int
    exact_heldout_levels: int
    million_site_action: int | None
    million_site_count: int
    exponential_gate_passed: bool
    target_used: bool
    system_digest: str


def _add(left: Point, right: Point) -> Point:
    return tuple(left[axis] + right[axis]
                 for axis in range(3))  # type: ignore[return-value]


def _scale(factor: float, point: Point) -> Point:
    return tuple(factor * value for value in point)  # type: ignore[return-value]


def _children(parent: GeneratedFrontierState):
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


def _render(wave: int, instances):
    rows = []
    for instance in instances:
        for species, local in zip(SPECIES[instance.type_id], LOCAL):
            rows.append((species, _add(
                instance.translation,
                matvec(instance.rotation, _scale(instance.scale, local)))))
    rows.sort(key=repr)
    return FrontierWaveSnapshot(
        wave, tuple(point for _species, point in rows),
        tuple(species for species, _point in rows))


def source_snapshots(level_count=4):
    levels = [(
        GeneratedFrontierState(0, 1., IDENTITY, (-10000., 0., 0.)),
        GeneratedFrontierState(0, 1., IDENTITY, (-8000., 0., 0.)),
        GeneratedFrontierState(1, 1., IDENTITY, (8000., 0., 0.)),
        GeneratedFrontierState(1, 1., IDENTITY, (10000., 0., 0.)),
    )]
    for _ in range(level_count - 1):
        levels.append(tuple(child for parent in levels[-1]
                            for child in _children(parent)))
    return tuple(_render(wave, instances)
                 for wave, instances in enumerate(levels, 1))


def _site_keys(rows, tolerance=5e-6):
    return {(repr(species), tuple(round(value / tolerance)
                                  for value in point))
            for species, point in rows}


def evaluate():
    snapshots = source_snapshots()
    training = snapshots[:3]
    states = compile_frontier_state_grammar(training, maximum_nodes=3)
    transitions = compile_frontier_transition_grammar(states, training)
    system = compile_frontier_substitution_system(transitions)
    if system is None:
        raise AssertionError("the closed substitution control was not learned")
    parents = tuple(as_generated_state(state.type_id, occurrence)
                    for state in states.recurring_state_types
                    if state.type_id in system.state_types
                    for occurrence in state.occurrences
                    if occurrence.wave == 1)
    first = execute_frontier_substitution(
        transitions, system, states.recurring_state_types, parents)
    second = execute_frontier_substitution(
        transitions, system, states.recurring_state_types, first.children)
    third = execute_frontier_substitution(
        transitions, system, states.recurring_state_types, second.children)
    expected_first = tuple(zip(training[1].species, training[1].positions))
    expected_second = tuple(zip(training[2].species, training[2].positions))
    expected_third = tuple(zip(snapshots[3].species, snapshots[3].positions))
    exact_levels = int(first.exact_colored_union and first.collision_free and
                       _site_keys(first.sites) == _site_keys(expected_first))
    exact_levels += int(second.exact_colored_union and second.collision_free and
                        _site_keys(second.sites) == _site_keys(expected_second))
    exact_heldout = int(third.exact_colored_union and third.collision_free and
                        _site_keys(third.sites) == _site_keys(expected_third))
    symbolic = symbolic_frontier_substitution_expansion(
        system, states.recurring_state_types, (2, 2), 30)
    million_count = (symbolic.represented_site_counts[
        symbolic.million_site_action]
        if symbolic.million_site_action is not None else 0)
    return FrontierSubstitutionBenchmark(
        True, False, tuple(len(wave.positions) for wave in training),
        len(snapshots[3].positions), False,
        len(system.state_types), sum(rule.recurrent
                                     for rule in transitions.rules),
        system.substitution_matrix, system.learned_scale,
        system.asymptotic_growth, system.total_description_saving,
        len(first.children) == 6 and len(second.children) == 10 and
        len(third.children) == 16,
        exact_levels, exact_heldout, symbolic.million_site_action, million_count,
        system.exponential_gate_passed, system.target_used,
        system.system_digest)


def main():
    print(json.dumps(asdict(evaluate()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
