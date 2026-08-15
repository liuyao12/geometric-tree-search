#!/usr/bin/env python3
"""Sealed train/heldout transfer audit for history-free grown-patch grammar."""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from types import SimpleNamespace

from materials_gcts_batch_frontier_search import run_batch_frontier_search
from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, fit_frozen_frontier_program)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_frozen_target_atlas, compile_irregular_port_program,
    enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_oriented_overlap_ports import PortAtlas
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_promoted_type_quotient import (
    fit_derivation_alternative_marking)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


BASE_TRAINING_CENTER = (-16., 0., 0.)
PATCH_CENTERS = tuple((x, y, z) for x in (-12., 12.)
                      for y in (-12., 12.) for z in (-12., 12.))
TRAIN_PATCH_IDS = (0, 1, 2, 3, 4)
HELDOUT_PATCH_IDS = (5, 6, 7)


@dataclass(frozen=True)
class ReclusteredTransferAudit:
    predeclared_patches: int
    train_patch_ids: tuple[int, ...]
    heldout_patch_ids: tuple[int, ...]
    raw_patch_domains_mutually_disjoint: bool
    train_heldout_raw_ids_disjoint: bool
    train_atoms: int
    heldout_atoms: int
    train_complete_cover: bool
    train_gap_atoms: int
    heldout_frozen_covered_atoms: int
    heldout_explicit_gap_atoms: int
    heldout_frozen_support_coverage: float
    frozen_support_types: int
    heldout_recognized_support_types: int
    heldout_support_type_coverage: float
    heldout_support_occurrences_patch_local: bool
    frozen_primitive_types: int
    heldout_primitive_occurrences: int
    frozen_port_types: int
    heldout_witnessed_frozen_port_types: int
    heldout_port_type_coverage: float
    train_positive_hierarchy_levels: int
    train_quotient_types_by_level: tuple[int, ...]
    train_derivation_alternatives_by_level: tuple[int, ...]
    train_alternative_marking_samples_by_level: tuple[int, ...]
    heldout_macro_types_replayed_by_level: tuple[int, ...]
    heldout_macro_type_coverage_by_level: tuple[float, ...]
    heldout_macro_occurrences_by_level: tuple[int, ...]
    heldout_derivation_alternatives_replayed_by_level: tuple[int, ...]
    heldout_derivation_alternative_occurrences_by_level: tuple[int, ...]
    heldout_macro_atom_coverage_by_level: tuple[float, ...]
    exact_replay_geometry_verified_by_level: tuple[bool, ...]
    frozen_type_map_preserved_by_level: tuple[bool, ...]
    transferred_positive_levels: int
    six_level_hierarchy_transfers: bool
    transfer_stopped_reason: str
    heldout_used_for_fit_or_admission: bool
    family_phi_cell_used: bool
    target_labels_used: bool
    elapsed_seconds: float


def _grow_patches():
    oracle, _ = oracle_patch_fast(9, 36.)
    base, _ = _crop(oracle, BASE_TRAINING_CENTER, 11., "transfer-base-train")
    learned = compile_irregular_port_program(base.species, base.positions)
    frozen = fit_frozen_frontier_program(learned)
    executions = []
    raw_domains = []
    for patch_id, center in enumerate(PATCH_CENTERS):
        seed_cloud, _ = _crop(
            oracle, center, 7., f"transfer-seed-{patch_id}")
        _, raw_domain = _crop(
            oracle, center, 11., f"transfer-domain-{patch_id}")
        enumeration = enumerate_frozen_port_occurrences(
            learned, seed_cloud.species, seed_cloud.positions,
            select_greedy_cover=True)
        covered = {index for _, support in enumeration.occurrence_supports
                   for index in support}
        gaps = tuple((seed_cloud.species[index], seed_cloud.positions[index])
                     for index in range(len(seed_cloud.positions))
                     if index not in covered)
        executions.append(run_batch_frontier_search(
            frozen, FrontierSeed(enumeration.occurrences, gaps),
            threshold_ratio=15 / 21, maximum_waves=5,
            maximum_accepted_per_wave=40,
            boundary=RadialBoundary(center, 11.)))
        raw_domains.append(frozenset(raw_domain))
    return tuple(executions), tuple(raw_domains)


def _pack(executions, patch_ids):
    clouds = []
    radii = []
    for patch_id in patch_ids:
        center = PATCH_CENTERS[patch_id]
        cloud = tuple((species, tuple(point[axis] - center[axis]
                                      for axis in range(3)))
                      for species, point in executions[patch_id].sites)
        clouds.append(cloud)
        radii.append(max(math.dist((0., 0., 0.), point)
                         for _, point in cloud))
    separation = 4 * max(radii) + 1.
    species = []
    positions = []
    patch_by_index = []
    for corpus_patch, (patch_id, cloud) in enumerate(zip(patch_ids, clouds)):
        offset = (corpus_patch * separation, 0., 0.)
        for label, point in cloud:
            species.append(label)
            positions.append(tuple(point[axis] + offset[axis]
                                   for axis in range(3)))
            patch_by_index.append(patch_id)
    return tuple(species), tuple(positions), tuple(patch_by_index)


def _frozen_heldout_program(training, enumeration):
    observed = compile_frozen_target_atlas(training, enumeration)
    admitted = {(port.parent_type, port.child_type,
                 port.symmetry_orbit_key) for port in training.atlas.ports}
    relations = tuple(item for item in observed.relation_classes
                      if (item[2], item[3], item[4]) in admitted)
    atlas = PortAtlas(
        training.atlas.ports, len(relations), 0, 0, 0, 0, relations)
    return SimpleNamespace(
        prototypes=training.prototypes,
        occurrences=enumeration.occurrences,
        occurrence_supports=enumeration.occurrence_supports,
        atlas=atlas, boundary_ports=(), boundary_relation_classes=(),
        minimum_shared_atoms=training.minimum_shared_atoms,
        minimum_distance=training.cover.minimum_distance,
        family_label_used=False, lattice_used=False,
        physical_potential_used=False, target_used=False)


def evaluate(maximum_nodes: int = 3) -> ReclusteredTransferAudit:
    if not 3 <= maximum_nodes <= 5:
        raise ValueError("maximum_nodes must be between three and five")
    started = time.perf_counter()
    executions, raw_domains = _grow_patches()
    mutually_disjoint = all(not left.intersection(right)
                            for index, left in enumerate(raw_domains)
                            for right in raw_domains[index + 1:])
    train_raw = set().union(*(raw_domains[index]
                             for index in TRAIN_PATCH_IDS))
    heldout_raw = set().union(*(raw_domains[index]
                               for index in HELDOUT_PATCH_IDS))
    train_species, train_positions, _ = _pack(executions, TRAIN_PATCH_IDS)
    held_species, held_positions, held_patch = _pack(
        executions, HELDOUT_PATCH_IDS)
    training = compile_irregular_port_program(train_species, train_positions)
    held_enumeration = enumerate_frozen_port_occurrences(
        training, held_species, held_positions)
    held_program = _frozen_heldout_program(training, held_enumeration)
    frozen_enumeration = training.vocabulary
    frozen_support_types = len(frozen_enumeration.prototypes)
    # Re-enumeration groups retain the train-frozen type ordering.
    from materials_gcts_irregular_supports import enumerate_frozen_vocabulary
    held_supports = enumerate_frozen_vocabulary(
        training.vocabulary, held_species, held_positions)
    recognized_types = sum(bool(group)
                           for group in held_supports.occurrences_by_type)
    covered = set(held_supports.covered_indices)
    support_patch_local = all(
        len({held_patch[index] for index in occurrence.member_indices}) == 1
        for group in held_supports.occurrences_by_type
        for occurrence in group)
    train_gap = len(train_positions) - len(training.cover.repeated_covered_indices)
    train_levels = []
    artifact = training
    for level in range(8):
        mined = mine_port_graph_macros(
            artifact, maximum_nodes=maximum_nodes,
            include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        if not quotient.quotient_macros:
            break
        marking = fit_derivation_alternative_marking(quotient)
        train_levels.append((artifact, quotient, marking))
        artifact = promote_macro_types(
            artifact, quotient.quotient_macros, level=level + 1)

    replayed_types = []
    replayed_type_coverage = []
    replayed_occurrences = []
    replayed_alternatives = []
    replayed_alternative_occurrences = []
    macro_coverages = []
    exact = []
    preserved = []
    target_artifact = held_program
    stop_reason = "training hierarchy exhausted"
    for level, (train_artifact, quotient, marking) in enumerate(train_levels):
        train_macros = tuple(quotient.quotient_macros)
        dense = match_dense_macro_types(target_artifact, train_macros)
        matches = tuple(macro for macro in dense.dense_macro_types
                        if macro.promotion_occurrences)
        replayed_types.append(len(matches))
        replayed_type_coverage.append(len(matches) / max(1, len(train_macros)))
        replayed_occurrences.append(sum(
            len(item.promotion_occurrences) for item in matches))
        atoms = {atom for item in matches
                 for occurrence in item.promotion_occurrences
                 for atom in occurrence.atom_indices}
        macro_coverages.append(len(atoms) / max(1, len(held_positions)))
        exact.append(dense.every_dense_match_proper)
        alternative_dense = match_dense_macro_types(
            target_artifact, quotient.alternative_macros)
        alternative_matches = tuple(
            macro for macro in alternative_dense.dense_macro_types
            if macro.promotion_occurrences)
        replayed_alternatives.append(len(alternative_matches))
        replayed_alternative_occurrences.append(sum(
            len(item.promotion_occurrences) for item in alternative_matches))
        full_map = (len(matches) == len(train_macros) and
                    all(len(item.promotion_occurrences) >= 2
                        for item in matches))
        preserved.append(full_map)
        if not full_map:
            stop_reason = (
                "frozen promotion stopped: not every train quotient type has "
                "two heldout exact occurrences; type IDs were not renumbered")
            break
        target_artifact = promote_macro_types(
            target_artifact, matches, level=level + 1)
        if level + 1 < len(train_levels):
            next_train_artifact = train_levels[level + 1][0]
            if (target_artifact.prototype_macro_types !=
                    next_train_artifact.prototype_macro_types):
                preserved[-1] = False
                stop_reason = "frozen promotion type map differs from training"
                break

    observed_port_keys = {(item[2], item[3], item[4])
                          for item in held_program.atlas.relation_classes}
    train_port_keys = {(port.parent_type, port.child_type,
                        port.symmetry_orbit_key)
                       for port in training.atlas.ports}
    transferred = sum(preserved)
    return ReclusteredTransferAudit(
        len(PATCH_CENTERS), TRAIN_PATCH_IDS, HELDOUT_PATCH_IDS,
        mutually_disjoint, not train_raw.intersection(heldout_raw),
        len(train_positions), len(held_positions), training.cover.complete,
        train_gap, len(covered), len(held_positions) - len(covered),
        len(covered) / len(held_positions), frozen_support_types,
        recognized_types, recognized_types / max(1, frozen_support_types),
        support_patch_local,
        len(training.prototypes), len(held_enumeration.occurrences),
        len(train_port_keys), len(observed_port_keys),
        len(observed_port_keys) / max(1, len(train_port_keys)),
        len(train_levels),
        tuple(len(item[1].quotient_macros) for item in train_levels),
        tuple(sum(len(group.alternatives) for group in item[1].derivation_classes)
              for item in train_levels),
        tuple(item[2].training_samples for item in train_levels),
        tuple(replayed_types), tuple(replayed_type_coverage),
        tuple(replayed_occurrences), tuple(replayed_alternatives),
        tuple(replayed_alternative_occurrences),
        tuple(macro_coverages), tuple(exact), tuple(preserved), transferred,
        transferred >= 6, stop_reason, False, False, False,
        time.perf_counter() - started)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maximum-nodes", type=int, default=3,
                        choices=(3, 4, 5))
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.maximum_nodes)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
