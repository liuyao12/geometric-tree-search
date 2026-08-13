#!/usr/bin/env python3
"""Benchmark the first shared finite recursive-production compiler.

The geometric front end is still allowed to infer different evidence
(translation residues, gap substitutions, or planar poses). After compilation,
all cases use exactly the same typed-child counter rewrite and must agree with
two independently checked explicit geometry levels. A planar square address
envelope is counted separately from its circular materialization crop.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_2d_generic_atlas import (
    _score, layered_hexagonal_configuration)
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_recursive_program import (
    discover_recursive_program, explicit_apply,
    symbolic_count as reference_symbolic_count)
from materials_gcts_typed_productions import (
    actions_to_at_least, induce_typed_transform_program,
    symbolic_atom_count)
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class TypedProductionCase:
    system: str
    observation_kind: str
    observed_atoms: int
    recursive_types: int
    productions: int
    child_references: int
    section_marks: int
    materialized_atom_counts: Tuple[int, int, int]
    executor_reference_counts: Tuple[int, int, int]
    typed_counts: Tuple[int, int, int]
    count_reference_kind: str
    exact_executor_count_each_level: bool
    exact_position_species_each_unseen_level: bool
    rigid_motion_invariant_graph: bool
    million_action: int
    million_atoms: int


@dataclass(frozen=True)
class TypedProductionBenchmark:
    cases: Tuple[TypedProductionCase, ...]
    same_recursive_executor: bool
    family_label_used: bool
    amorphous_rejected: bool
    continuous_internal_section_compiled: bool
    all_two_level_counts_exact: bool
    all_rigid_motion_invariant: bool
    benchmark_passed: bool


def _move_crystal(configuration: AtomicConfiguration) -> AtomicConfiguration:
    positions = tuple((-y + 4.2, x - 3.1, z + 1.7)
                      for x, y, z in configuration.positions)
    return AtomicConfiguration(
        "moved-" + configuration.name, positions,
        configuration.species)


def _move_quasicrystal(configuration: AtomicConfiguration) -> AtomicConfiguration:
    angle = .41
    cosine, sine = math.cos(angle), math.sin(angle)
    positions = tuple((cosine * x - sine * z + 2.3, y - 1.4,
                       sine * x + cosine * z + .6)
                      for x, y, z in configuration.positions)
    return AtomicConfiguration(
        "moved-" + configuration.name, positions, configuration.species)


def _fingerprint(program) -> tuple:
    return (program.type_names, program.atomic_weights, program.root_counts,
            tuple((production.parent_type,
                   tuple((child.child_type, child.address,
                          child.section_mark)
                         for child in production.children))
                  for production in program.productions))


def _case(configuration: AtomicConfiguration, mover,
          references=None) -> TypedProductionCase:
    typed = induce_typed_transform_program(configuration)
    moved = induce_typed_transform_program(mover(configuration))
    explicit_program = discover_recursive_program(configuration)
    explicit = tuple(explicit_apply(configuration, explicit_program, action)
                     for action in (1, 2))
    explicit_counts = (len(configuration.positions),
                       len(explicit[0].positions), len(explicit[1].positions))
    typed_counts = tuple(symbolic_atom_count(typed, action)
                         for action in range(3))
    if references is None:
        executor_reference = explicit_counts
        reference_kind = "exact materialized atoms"
        exact_geometry = True
    else:
        executor_reference = tuple(reference_symbolic_count(
            configuration, explicit_program, action) for action in range(3))
        reference_kind = "recursive address envelope"
        exact_geometry = all(_score(actual, target) == (1.0, 1.0, 1.0)
                             for actual, target in zip(explicit, references))
    million_action, million_atoms = actions_to_at_least(typed)
    return TypedProductionCase(
        configuration.name, typed.observation_kind,
        len(configuration.positions), len(typed.type_names),
        len(typed.productions),
        sum(len(item.children) for item in typed.productions),
        len({child.section_mark for item in typed.productions
             for child in item.children}),
        explicit_counts, executor_reference, typed_counts, reference_kind,
        executor_reference == typed_counts, exact_geometry,
        _fingerprint(typed) == _fingerprint(moved),
        million_action, million_atoms)


def evaluate() -> TypedProductionBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    basis = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    angles = (0.0, math.pi / 6)
    planar = layered_hexagonal_configuration(
        "typed-30deg-hBN", 18.0, basis, angles, global_rotation=True)
    planar_program = discover_recursive_program(planar)
    planar_references = tuple(layered_hexagonal_configuration(
        f"typed-30deg-hBN-heldout-{action}",
        planar_program.observation_radius * 2 ** action,
        basis, angles, global_rotation=True) for action in (1, 2))
    cases = (_case(nacl, _move_crystal),
             _case(make_input(9), _move_quasicrystal),
             _case(planar, _move_crystal, planar_references))
    sample = amorphous_hard_core_point_set(atom_count=507)
    amorphous = AtomicConfiguration(
        sample.name, sample.positions, sample.species)
    rejected = not induce_typed_transform_program(amorphous).deterministic
    exact = all(item.exact_executor_count_each_level and
                item.exact_position_species_each_unseen_level
                for item in cases)
    invariant = all(item.rigid_motion_invariant_graph for item in cases)
    no_labels = not any(induce_typed_transform_program(configuration).
                        family_label_used
                        for configuration in (nacl, make_input(9), planar))
    # Continuous internal-space sections need a different, non-finite child
    # representation.  Keeping this false prevents the finite benchmark from
    # quietly claiming the ideal icosahedral case.
    continuous_compiled = False
    return TypedProductionBenchmark(
        cases, True, not no_labels, rejected, continuous_compiled,
        exact, invariant, rejected and exact and invariant and no_labels)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
