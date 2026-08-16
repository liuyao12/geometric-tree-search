#!/usr/bin/env python3
"""Target-blind recognition and execution of an exact frozen macro hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_frozen_hierarchy_transfer import (
    FrozenTransferStep, transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import (
    _frozen_heldout_program)
from materials_gcts_irregular_port_atlas import (
    enumerate_frozen_port_occurrences)
from materials_gcts_recurrent_macro_executor import (
    ExecutionBoundary, RecurrentMacroExecution,
    execute_recurrent_macro_program)


Site = tuple[Hashable, tuple[float, float, float]]


@dataclass(frozen=True)
class FrozenHierarchyLevel:
    quotient: object
    promoted_program: object


@dataclass(frozen=True)
class RecognizedHierarchyLevel:
    level: int
    transfer: FrozenTransferStep
    recognized_occurrences: int
    recognized_types: int
    seed_atoms_covered: int


@dataclass(frozen=True)
class HierarchicalSeedExecution:
    seed_sites: tuple[Site, ...]
    primitive_occurrences: int
    primitive_admitted_relations: int
    levels: tuple[RecognizedHierarchyLevel, ...]
    executions: tuple[tuple[int, RecurrentMacroExecution], ...]
    target_api_present: bool
    target_used_for_recognition_or_execution: bool


def recognize_and_execute_frozen_hierarchy(
    primitive_program, frozen_levels: Sequence[FrozenHierarchyLevel],
    seed_species: Sequence[Hashable],
    seed_positions: Sequence[Sequence[float]], *,
    boundary: ExecutionBoundary, maximum_waves: int = 3,
    maximum_accepted_per_wave: int = 40, pose_tolerance: float = .03,
) -> HierarchicalSeedExecution:
    """Recognize contained exact macros, then execute their frozen ports.

    There is intentionally no target argument.  Every recognized support is a
    subset of the supplied colored seed, while every exterior pose is composed
    from a train-frozen proper-SE(3) port.
    """
    if len(seed_species) != len(seed_positions) or not seed_species:
        raise ValueError("seed species and positions must be nonempty/aligned")
    sites = tuple((species, tuple(map(float, point)))
                  for species, point in zip(seed_species, seed_positions))
    namespaces = ("seed",) * len(sites)
    enumeration = enumerate_frozen_port_occurrences(
        primitive_program, seed_species, seed_positions)
    artifact = _frozen_heldout_program(primitive_program, enumeration)
    primitive_relations = len(artifact.atlas.relation_classes)
    recognized = []
    executions = []
    for index, level in enumerate(frozen_levels, 1):
        step = transfer_frozen_hierarchy_level(
            artifact, level.quotient, level.promoted_program, namespaces,
            pose_tolerance=pose_tolerance, raw_atom_sites=sites)
        occurrences = step.program.occurrences
        covered = {atom for _occurrence, support in
                   step.program.occurrence_supports for atom in support}
        recognized.append(RecognizedHierarchyLevel(
            index, step, len(occurrences),
            len({item.type_id for item in occurrences}), len(covered)))
        artifact = step.program
        if not occurrences:
            break
        execution = execute_recurrent_macro_program(
            level.promoted_program, occurrences,
            explicit_seed_sites=sites, boundary=boundary,
            maximum_waves=maximum_waves,
            maximum_accepted_per_wave=maximum_accepted_per_wave,
            pose_tolerance=pose_tolerance)
        executions.append((index, execution))
    return HierarchicalSeedExecution(
        sites, len(enumeration.occurrences),
        primitive_relations, tuple(recognized),
        tuple(executions), False, False)
