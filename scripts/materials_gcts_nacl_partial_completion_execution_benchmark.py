#!/usr/bin/env python3
"""NaCl control for target-blind multiwave whole-macro completion."""

from __future__ import annotations

import math
from dataclasses import dataclass

from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_completion_executor import (
    PartialCompletionLevel, execute_partial_completion_level)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


@dataclass(frozen=True)
class NaClPartialCompletionExecutionAudit:
    atoms: int
    seed_atoms: int
    seed_occurrences: int
    candidate_counts: tuple[int, ...]
    accepted_whole_macros: tuple[int, ...]
    emitted_atoms: int
    correct_atoms: int
    wrong_atoms: int
    primitive_child_actions: int
    whole_macro_actions: int
    symbolic_action_compression: float
    exact_certificates: bool
    candidate_digests_frozen_before_scorer: bool
    target_used_for_execution: bool
    gate_passed: bool


def _parent_map(quotient, promoted):
    parent = {macro_id: prototype_id for prototype_id, macro_id
              in promoted.prototype_macro_types}
    result = []
    cursor = 0
    for geometry in quotient.derivation_classes:
        for _alternative in geometry.alternatives:
            macro = quotient.alternative_macros[cursor]
            result.append((macro.macro_id, parent[geometry.geometry_class_id]))
            cursor += 1
    return tuple(result)


def _key(site, tolerance=.03):
    return (repr(site[0]),) + tuple(round(value / tolerance)
                                    for value in site[1])


def evaluate():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    primitive = compile_irregular_port_program(nacl.species, nacl.positions)
    mined = mine_port_graph_macros(
        primitive, maximum_nodes=2, include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    center = (7.05, 7.05, 7.05)
    seed_indices = tuple(index for index, point in enumerate(nacl.positions)
                         if math.dist(center, point) <= 5. + 1e-10)
    seed_species = tuple(nacl.species[index] for index in seed_indices)
    seed_positions = tuple(nacl.positions[index] for index in seed_indices)
    enumeration = enumerate_frozen_port_occurrences(
        primitive, seed_species, seed_positions)
    execution = execute_partial_completion_level(
        PartialCompletionLevel(
            primitive, quotient.alternative_macros,
            _parent_map(quotient, promoted), promoted),
        enumeration.occurrences,
        explicit_seed_sites=tuple(zip(seed_species, seed_positions)),
        public_boundary=ExecutionBoundary(center, 8.),
        maximum_waves=2, maximum_accepted_per_wave=16,
        minimum_child_coverage=.5)

    # Full finite crystal is consulted only after immutable wave digests exist.
    initial = {_key(site) for site in zip(seed_species, seed_positions)}
    final = {_key(site) for site in execution.sites}
    emitted = final - initial
    target = {_key(site) for site in zip(nacl.species, nacl.positions)}
    correct = emitted.intersection(target)
    exact = all(all((item.exact_frozen_rhs_geometry, item.proper_se3,
                     item.frozen_port_witnessed,
                     item.emitted_is_exact_difference,
                     item.collision_free, item.promoted_pose_exact))
                for item in execution.certificates)
    gate = bool(execution.certificates) and exact and not (emitted - target)
    return NaClPartialCompletionExecutionAudit(
        len(nacl.positions), len(seed_indices), len(enumeration.occurrences),
        tuple(item.candidate_count for item in execution.waves),
        tuple(item.accepted_whole_macros for item in execution.waves),
        len(emitted), len(correct), len(emitted - target),
        execution.primitive_child_actions, execution.whole_macro_actions,
        execution.symbolic_action_compression, exact,
        execution.candidate_digests_frozen_before_scorer,
        execution.target_used, gate)


if __name__ == "__main__":
    print(evaluate())
