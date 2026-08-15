#!/usr/bin/env python3
"""Re-cluster exact target-free grown patches, discarding move history.

Each patch contributes only its final colored point cloud.  Clouds are
translated into disjoint corpus namespaces by a separation derived from their
observed diameter; no action/node/production IDs survive.  The generic
irregular-support, oriented-port, sparse-macro, quotient, and promotion stack
is then rerun until positive-MDL recurrence terminates.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_action_submacro_mining import (
    ActionMacroCorpusEntry, mine_action_submacros)
from materials_gcts_action_submacro_promotion import promote_action_submacros
from materials_gcts_frozen_frontier_replay import fit_frozen_frontier_program
from materials_gcts_iqc_action_graph_corpus import (
    PATCH_CENTERS, TRAINING_CENTER, _build_with_executions)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurring_action_submacro_audit import (
    PromotedSubmacroLevel, audit_promoted_submacro_levels)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop
from materials_gcts_stationary_progressive_diagnostic import (
    diagnose_progressive_stationarity)


@dataclass(frozen=True)
class ReclusteredGrowthCorpusAudit:
    corpus_digest: str
    maximum_nodes: int
    patches: int
    initial_atoms_by_patch: tuple[int, ...]
    final_atoms_by_patch: tuple[int, ...]
    novel_atoms_by_patch: tuple[int, ...]
    pooled_atoms: int
    corpus_separation: float
    complete_cover: bool
    repeated_support_types: int
    repeated_support_occurrences: int
    repeated_covered_atoms: int
    gap_types: int
    gap_atoms: int
    every_support_occurrence_patch_local: bool
    every_macro_occurrence_patch_local: bool
    primitive_prototypes: int
    primitive_occurrences: int
    primitive_ports: int
    overlap_admitted_types_by_level: tuple[int, ...]
    overlap_quotient_types_by_level: tuple[int, ...]
    overlap_artifact_occurrences_by_level: tuple[int, ...]
    overlap_proof_multiplicity_histograms: tuple[tuple[tuple[int, int], ...], ...]
    overlap_child_count_histograms: tuple[tuple[tuple[int, int], ...], ...]
    overlap_mining_seconds_by_level: tuple[float, ...]
    boundary_admitted_types_by_level: tuple[int, ...]
    boundary_quotient_types_by_level: tuple[int, ...]
    boundary_artifact_occurrences_by_level: tuple[int, ...]
    boundary_proof_multiplicity_histograms: tuple[tuple[tuple[int, int], ...], ...]
    boundary_child_count_histograms: tuple[tuple[tuple[int, int], ...], ...]
    boundary_mining_seconds_by_level: tuple[float, ...]
    initial_overlap_boundary_mining_reused: bool
    action_history_base_types: int
    action_history_maximum_dense_occurrence_multiplicity: int
    action_history_positive_quotient_levels: int
    reclustered_maximum_proof_multiplicity: int
    reclustered_positive_quotient_levels: int
    reclustering_improves_maximum_proof_multiplicity: bool
    reclustering_improves_positive_hierarchy_depth: bool
    strict_stationary_audit_invoked: bool
    stationary_adapted_records: int
    stationary_eligible_records: int
    stationary_adaptation_rejections: int
    stationary_common_three_level_keys: int
    stationary_evaluated_triples: int
    stationary_witnesses: int
    stationary: bool
    stationary_first_two_levels_materialized: bool
    progressive_stationary_windows: tuple[tuple[int, int, int], ...]
    progressive_topology_intersections: tuple[int, ...]
    progressive_chemistry_chirality_intersections: tuple[int, ...]
    progressive_directed_port_intersections: tuple[int, ...]
    progressive_normalized_pose_intersections: tuple[int, ...]
    progressive_population_substitution_intersections: tuple[int, ...]
    progressive_first_zero_field: str | None
    target_used: bool
    family_or_cell_used: bool
    action_history_ids_used: bool
    total_evaluation_seconds: float


def _histogram(values):
    return tuple(sorted(Counter(values).items()))


def _pack(executions):
    local_clouds = []
    radii = []
    # These are the public radial-domain origins supplied to execution, not a
    # material frame, unit cell, family label, or fitted geometric parameter.
    for center, execution in zip(PATCH_CENTERS, executions):
        local = tuple((species, tuple(point[axis] - center[axis]
                                     for axis in range(3)))
                      for species, point in execution.sites)
        local_clouds.append(local)
        radii.append(max((math.dist((0., 0., 0.), point)
                          for _, point in local), default=0.))
    separation = max(1., 4 * max(radii, default=0.) + 1.)
    species = []
    positions = []
    patch_by_index = []
    for patch_id, cloud in enumerate(local_clouds):
        offset = (patch_id * separation, 0., 0.)
        for label, point in cloud:
            species.append(label)
            positions.append(tuple(point[axis] + offset[axis]
                                   for axis in range(3)))
            patch_by_index.append(patch_id)
    return (tuple(species), tuple(positions), tuple(patch_by_index),
            separation)


def _recursive(program, include_boundary_relations, patch_by_index,
               maximum_nodes, initial_mining_cache=None):
    admitted = []
    quotients = []
    occurrences = []
    multiplicities = []
    child_counts = []
    mining_seconds = []
    every_patch_local = True
    levels = []
    artifact = program
    for level_index in range(12):
        started = time.perf_counter()
        cacheable = (level_index == 0 and
                     not getattr(artifact, "boundary_ports", ()))
        if (cacheable and initial_mining_cache is not None and
                "overlap-equivalent" in initial_mining_cache):
            mined = initial_mining_cache["overlap-equivalent"]
        else:
            mined = mine_port_graph_macros(
                artifact, maximum_nodes=maximum_nodes,
                include_boundary_relations=include_boundary_relations)
            if cacheable and initial_mining_cache is not None:
                initial_mining_cache["overlap-equivalent"] = mined
        mining_seconds.append(time.perf_counter() - started)
        quotient = quotient_macro_supports(mined.macro_types)
        admitted.append(len(mined.macro_types))
        quotients.append(quotient.quotient_types)
        occurrences.append(len(artifact.occurrences))
        multiplicities.append(_histogram(
            len(item.occurrences) for item in mined.macro_types))
        child_counts.append(_histogram(
            len(item.node_types) for item in mined.macro_types))
        every_patch_local = every_patch_local and all(
            len({patch_by_index[index] for index in occurrence.atom_indices}) == 1
            for macro in mined.macro_types
            for occurrence in macro.occurrences)
        if not quotient.quotient_macros:
            break
        levels.append(PromotedSubmacroLevel(
            len(levels), artifact, tuple(quotient.quotient_macros)))
        artifact = promote_macro_types(
            artifact, quotient.quotient_macros,
            level=getattr(artifact, "level", 0) + 1)
    else:
        raise RuntimeError("re-clustered hierarchy did not terminate")
    strict = audit_promoted_submacro_levels(levels)
    return (tuple(admitted), tuple(quotients), tuple(occurrences),
            tuple(multiplicities), tuple(child_counts),
            tuple(mining_seconds), every_patch_local, strict, tuple(levels))


def _positive_depth(program, include_boundary_relations=True,
                    maximum_nodes=3):
    artifact = program
    depth = 0
    for _ in range(12):
        mined = mine_port_graph_macros(
            artifact, maximum_nodes=maximum_nodes,
            include_boundary_relations=include_boundary_relations)
        quotient = quotient_macro_supports(mined.macro_types)
        if not quotient.quotient_macros:
            return depth
        depth += 1
        artifact = promote_macro_types(
            artifact, quotient.quotient_macros,
            level=getattr(artifact, "level", 0) + 1)
    raise RuntimeError("action-history comparison did not terminate")


def evaluate(maximum_nodes: int = 3) -> ReclusteredGrowthCorpusAudit:
    if not 3 <= maximum_nodes <= 5:
        raise ValueError("maximum_nodes must be between three and five")
    evaluation_started = time.perf_counter()
    corpus, executions, oracle = _build_with_executions()
    species, positions, patch_by_index, separation = _pack(executions)
    program = compile_irregular_port_program(species, positions)
    every_local = all(len({patch_by_index[index]
                           for index in occurrence.member_indices}) == 1
                      for support_type in program.cover.support_types
                      for occurrence in support_type.occurrences)
    initial_mining_cache = {}
    overlap = _recursive(
        program, False, patch_by_index, maximum_nodes, initial_mining_cache)
    boundary = _recursive(
        program, True, patch_by_index, maximum_nodes, initial_mining_cache)
    gap_atoms = len(set(range(len(positions))).difference(
        program.cover.repeated_covered_indices))
    maximum_proof = max((multiplicity
                         for levels in (overlap[3], boundary[3])
                         for histogram in levels
                         for multiplicity, _ in histogram), default=0)
    overlap_depth = sum(value > 0 for value in overlap[1])
    boundary_depth = sum(value > 0 for value in boundary[1])
    training, _ = _crop(oracle, TRAINING_CENTER, 11., "IQC-corpus-train")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    action_entries = []
    for patch, execution in zip(corpus.patches, executions):
        promoted_actions = promote_batch_action_macros(frozen, execution)
        action_entries.extend(ActionMacroCorpusEntry(
            str(patch.patch_id), macro) for macro in promoted_actions.macros)
    action_mined = mine_action_submacros(frozen, tuple(action_entries))
    action_promoted, _ = promote_action_submacros(
        frozen, action_mined.submacro_types, tuple(action_entries))
    action_maximum = max((len(item.dense_occurrences)
                          for item in action_mined.submacro_types), default=0)
    action_depth = _positive_depth(
        action_promoted, maximum_nodes=maximum_nodes)
    strict = boundary[7]
    progressive = diagnose_progressive_stationarity(boundary[8])
    materialized = bool(
        strict.witnesses and len(boundary[8]) >= 3 and
        all(level.artifact.occurrences for level in boundary[8][1:3]))
    return ReclusteredGrowthCorpusAudit(
        corpus.corpus_digest, maximum_nodes, len(executions),
        tuple(len(item.initial_sites) for item in executions),
        tuple(len(item.sites) for item in executions),
        tuple(len(item.sites) - len(item.initial_sites)
              for item in executions), len(positions), separation,
        program.cover.complete, program.cover.repeated_type_count,
        program.cover.repeated_occurrence_count,
        len(program.cover.repeated_covered_indices),
        program.cover.gap_type_count, gap_atoms, every_local,
        overlap[6] and boundary[6],
        len(program.prototypes), len(program.occurrences),
        len(program.atlas.ports), *overlap[:6], *boundary[:6], True,
        len(action_mined.submacro_types), action_maximum, action_depth,
        maximum_proof,
        max(overlap_depth, boundary_depth), maximum_proof > 2,
        max(overlap_depth, boundary_depth) > action_depth,
        len(boundary[8]) >= 3, strict.adapted_records,
        strict.eligible_records, len(strict.rejected),
        strict.common_normalized_keys,
        strict.evaluated_consecutive_triples, len(strict.witnesses),
        strict.stationary, materialized,
        progressive.consecutive_windows,
        progressive.child_count_topology_intersections,
        progressive.chemistry_chirality_intersections,
        progressive.directed_port_semantics_intersections,
        progressive.normalized_pose_intersections,
        progressive.population_substitution_intersections,
        progressive.first_zero_field,
        corpus.target_used_during_execution,
        program.family_label_used or program.lattice_used, False,
        time.perf_counter() - evaluation_started)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--maximum-nodes", type=int, default=3,
                        choices=(3, 4, 5))
    arguments = parser.parse_args()
    result = evaluate(arguments.maximum_nodes)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
