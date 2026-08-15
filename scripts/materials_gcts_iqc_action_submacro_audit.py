#!/usr/bin/env python3
"""Exact five-wave IQC audit for recurring induced action submacros."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_action_submacro_mining import mine_action_submacros
from materials_gcts_batch_frontier_search import run_batch_frontier_search
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, fit_frozen_frontier_program)
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)


@dataclass(frozen=True)
class IQCActionSubmacroAudit:
    training_atoms: int
    seed_atoms: int
    accepted_action_nodes: int
    action_macro_child_counts: tuple[int, ...]
    connected_induced_candidates: int
    exact_canonical_classes: int
    rejected_insufficient_disjoint_evidence: int
    rejected_nonpositive_mdl: int
    admitted_submacro_types: int
    admitted_node_counts: tuple[int, ...]
    admitted_occurrence_counts: tuple[int, ...]
    all_admitted_positive_mdl: bool
    all_admitted_have_boundary_slots: bool
    exact_action_node_cover: bool
    target_used: bool


def _crop(configuration, center, radius, name):
    indices = tuple(index for index, point in enumerate(configuration.positions)
                    if math.dist(point, center) <= radius + 1e-10)
    return AtomicConfiguration(
        name, tuple(configuration.positions[index] for index in indices),
        tuple(configuration.species[index] for index in indices))


def evaluate() -> IQCActionSubmacroAudit:
    training_center = (-16.0, 0.0, 0.0)
    seed_center = (5.0, -17.0, 4.0)
    oracle, _ = oracle_patch_fast(8, 32.0)
    training = _crop(
        oracle, training_center, 11.0, "IQC-submacro-training")
    seed_cloud = _crop(
        oracle, seed_center, 7.0, "IQC-submacro-confirmation")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    enumeration = enumerate_frozen_port_occurrences(
        learned, seed_cloud.species, seed_cloud.positions,
        select_greedy_cover=True)
    covered = {index for _, support in enumeration.occurrence_supports
               for index in support}
    gaps = tuple((seed_cloud.species[index], seed_cloud.positions[index])
                 for index in range(len(seed_cloud.positions))
                 if index not in covered)
    batch = run_batch_frontier_search(
        frozen, FrontierSeed(enumeration.occurrences, gaps),
        threshold_ratio=15 / 21, maximum_waves=5,
        maximum_accepted_per_wave=40,
        boundary=RadialBoundary(seed_center, 11.0))
    actions = promote_batch_action_macros(frozen, batch)
    mined = mine_action_submacros(frozen, actions.macros)
    return IQCActionSubmacroAudit(
        len(training.positions), len(seed_cloud.positions),
        actions.accepted_nodes,
        tuple(len(item.children) for item in actions.macros),
        mined.connected_induced_candidates, mined.exact_canonical_classes,
        mined.rejected_insufficient_disjoint_evidence,
        mined.rejected_nonpositive_mdl, len(mined.submacro_types),
        tuple(len(item.node_types) for item in mined.submacro_types),
        tuple(len(item.occurrences) for item in mined.submacro_types),
        all(item.mdl_saving > 0 for item in mined.submacro_types),
        all(item.boundary_slots for item in mined.submacro_types),
        actions.exact_cover_of_accepted_nodes,
        batch.target_used or actions.target_used or mined.target_used)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
