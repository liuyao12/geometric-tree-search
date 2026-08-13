#!/usr/bin/env python3

import math

from materials_gcts_cross_family_transfer_audit import _learn_anchor
from materials_gcts_fibonacci_3d import PHI, make_input
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_geometry_vm import (
    compile_anchor, execute, transform_instruction)
from materials_gcts_geometry_vm_benchmark import evaluate
from materials_gcts_recursive_connections import point_key


def test_one_geometry_vm_executes_three_selected_markings() -> None:
    result = evaluate()
    assert result.interpreter_opcodes == (
        "translation_cover", "overlap_section", "anchor_similarity")
    assert result.one_interpreter
    assert not result.family_labels_used
    assert not result.heldout_geometry_used_for_fitting
    assert all(case.exact_species_and_positions for case in result.cases)
    assert result.benchmark_passed


def test_vm_instruction_moves_with_rotated_translated_cloud() -> None:
    seed = make_input(9)
    edges = (1.1, 1.7, 2.4, 3.0)
    _, anchor = _learn_anchor(seed, PHI, edges)
    instruction = compile_anchor(seed, PHI, edges, anchor)
    angle = .37
    rotation = ((math.cos(angle), -math.sin(angle), 0.0),
                (math.sin(angle), math.cos(angle), 0.0),
                (0.0, 0.0, 1.0))
    translation = (7.25, -3.5, 11.0)
    move = lambda point: tuple(sum(rotation[row][column] * point[column]
                                   for column in range(3)) + translation[row]
                               for row in range(3))
    state = make_input(15)
    moved = AtomicConfiguration(
        state.name, tuple(move(point) for point in state.positions),
        state.species, None, False, state.provenance)
    # The VM's public site key is 1e-6 in its current coordinate frame; after
    # composing two floating transforms compare at the declared 1e-4 rigid
    # congruence tolerance instead of requiring identical decimal histories.
    expected = frozenset((point_key(move(point), 4), chemical)
                         for point, chemical in
                         execute(instruction, state).emitted_sites)
    actual = frozenset((point_key(point, 4), chemical) for point, chemical in
                       execute(transform_instruction(
                           instruction, rotation, translation),
                               moved).emitted_sites)
    assert actual == expected


if __name__ == "__main__":
    test_one_geometry_vm_executes_three_selected_markings()
    test_vm_instruction_moves_with_rotated_translated_cloud()
    print("generic GCTS geometry VM: benchmark passed")
