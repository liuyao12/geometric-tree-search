#!/usr/bin/env python3
"""Deep generic clusters-of-clusters hierarchy on published Cd--Yb crops.

Five mutually disjoint radius-14 observations supply positions and species
only.  The generic irregular-cover, finite proper-port, exact macro quotient,
and promotion loop runs to evidence exhaustion.  No heldout cloud, model
family, cut-and-project coordinate, cell, potential, or expected scale enters
mining.  Stationarity is assessed separately by the strict semantic contract.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurring_action_submacro_audit import (
    PromotedSubmacroLevel, audit_promoted_submacro_levels)
from materials_gcts_stationary_progressive_diagnostic import (
    diagnose_progressive_stationarity)


RADIUS = 14.0
TRAIN_CENTERS = (
    (-16.0, -8.0, 8.0),
    (14.0, -12.0, -8.0),
    (15.0, -15.0, 20.0),
    (-15.0, 20.0, -15.0),
    (-15.0, -15.0, -20.0),
)


@dataclass(frozen=True)
class CdYbDeepHierarchyAudit:
    train_windows: int
    train_atoms: int
    atoms_by_window: tuple[int, ...]
    minimum_center_separation: float
    raw_domains_pairwise_disjoint: bool
    complete_cover_with_gap_clusters: bool
    repeated_covered_atoms: int
    gap_atoms: int
    primitive_support_types: int
    primitive_occurrences: int
    primitive_oriented_ports: int
    every_support_occurrence_window_local: bool
    every_promoted_occurrence_window_local: bool
    distinct_window_configuration_classes: int
    admitted_types_by_level: tuple[int, ...]
    quotient_types_by_level: tuple[int, ...]
    independently_witnessed_quotient_types_by_level: tuple[int, ...]
    single_window_quotient_types_by_level: tuple[int, ...]
    artifact_occurrences_by_level: tuple[int, ...]
    child_count_histograms: tuple[tuple[tuple[int, int], ...], ...]
    proof_multiplicity_histograms: tuple[tuple[tuple[int, int], ...], ...]
    maximum_atom_support_by_level: tuple[int, ...]
    positive_hierarchy_levels: int
    converged_at_evidence_exhaustion: bool
    strict_stationary_audit_invoked: bool
    stationary_adapted_records: int
    stationary_eligible_records: int
    stationary_adaptation_rejections: int
    stationary_common_three_level_keys: int
    stationary_evaluated_triples: int
    stationary_witnesses: int
    progressive_topology_intersections: tuple[int, ...]
    progressive_chemistry_chirality_intersections: tuple[int, ...]
    progressive_directed_port_intersections: tuple[int, ...]
    progressive_normalized_pose_intersections: tuple[int, ...]
    progressive_first_zero_field: str | None
    stationary_or_exponential_claimed: bool
    target_family_cell_potential_source_sites_or_expected_scale_used: bool
    hierarchy_gate_passed: bool
    limitation: str


def _histogram(values):
    return tuple(sorted(Counter(values).items()))


def evaluate():
    atoms = generate_cdyb(5, (80.0,) * 3)
    window_ids = tuple(tuple(
        index for index, point in enumerate(atoms.positions)
        if math.dist(center, point) <= RADIUS + 1e-10)
        for center in TRAIN_CENTERS)
    raw_disjoint = all(
        set(left).isdisjoint(right)
        for index, left in enumerate(window_ids)
        for right in window_ids[index + 1:])
    packed_species = []
    packed_positions = []
    patch_by_train_index = []
    separation = 80.0
    for patch, (center, ids) in enumerate(zip(TRAIN_CENTERS, window_ids)):
        for raw_id in ids:
            point = atoms.positions[raw_id]
            packed_species.append(atoms.symbols[raw_id])
            packed_positions.append((
                point[0] - center[0] + patch * separation,
                point[1] - center[1], point[2] - center[2]))
            patch_by_train_index.append(patch)
    program = compile_irregular_port_program(
        tuple(packed_species), tuple(packed_positions))
    support_local = all(
        len({patch_by_train_index[index]
             for index in occurrence.member_indices}) == 1
        for support_type in program.cover.support_types
        for occurrence in support_type.occurrences)
    gap_atoms = len(set(range(len(packed_positions))).difference(
        program.cover.repeated_covered_indices))

    admitted = []
    quotients = []
    occurrences = []
    child_histograms = []
    proof_histograms = []
    maximum_supports = []
    independently_witnessed = []
    single_window_witnessed = []
    promoted_local = True
    levels = []
    artifact = program
    for level in range(16):
        occurrence_supports = dict(artifact.occurrence_supports)
        promoted_local = promoted_local and all(
            len({patch_by_train_index[index] for index in support}) == 1
            for support in occurrence_supports.values())
        mined = mine_port_graph_macros(
            artifact, maximum_nodes=3, include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        admitted.append(len(mined.macro_types))
        quotients.append(quotient.quotient_types)
        occurrences.append(len(artifact.occurrences))
        child_histograms.append(_histogram(
            len(item.node_types) for item in mined.macro_types))
        proof_histograms.append(_histogram(
            len(item.occurrences) for item in mined.macro_types))
        maximum_supports.append(max(
            (len(item.atom_union) for item in quotient.quotient_macros),
            default=0))
        quotient_proof_windows = tuple(len({
            patch_by_train_index[index]
            for occurrence in item.occurrences
            for node in occurrence.node_occurrences
            for index in occurrence_supports[node]
        }) for item in quotient.quotient_macros)
        independently_witnessed.append(sum(
            count >= 2 for count in quotient_proof_windows))
        single_window_witnessed.append(sum(
            count < 2 for count in quotient_proof_windows))
        if not quotient.quotient_macros:
            break
        levels.append(PromotedSubmacroLevel(
            level, artifact, tuple(quotient.quotient_macros)))
        artifact = promote_macro_types(
            artifact, quotient.quotient_macros,
            level=getattr(artifact, "level", 0) + 1)
    else:
        raise RuntimeError("CdYb hierarchy did not converge")
    strict = audit_promoted_submacro_levels(tuple(levels))
    progressive = diagnose_progressive_stationarity(tuple(levels))
    positive_levels = sum(value > 0 for value in quotients)
    minimum_separation = min(
        math.dist(left, right)
        for index, left in enumerate(TRAIN_CENTERS)
        for right in TRAIN_CENTERS[index + 1:])
    hierarchy_gate = (
        program.cover.complete and support_local and raw_disjoint and
        promoted_local and
        positive_levels >= 8 and quotients[-1] == 0 and
        not strict.stationary)
    window_signatures = {
        tuple(sorted((atoms.symbols[index], tuple(round(
            atoms.positions[index][axis] - center[axis], 6)
            for axis in range(3))) for index in ids))
        for center, ids in zip(TRAIN_CENTERS, window_ids)
    }
    return CdYbDeepHierarchyAudit(
        len(TRAIN_CENTERS), len(packed_positions), tuple(map(len, window_ids)),
        minimum_separation, raw_disjoint, program.cover.complete,
        len(program.cover.repeated_covered_indices), gap_atoms,
        len(program.prototypes), len(program.occurrences),
        len(program.atlas.ports), support_local, promoted_local,
        len(window_signatures), tuple(admitted),
        tuple(quotients), tuple(independently_witnessed),
        tuple(single_window_witnessed), tuple(occurrences), tuple(child_histograms),
        tuple(proof_histograms), tuple(maximum_supports), positive_levels,
        quotients[-1] == 0, len(levels) >= 3, strict.adapted_records,
        strict.eligible_records, len(strict.rejected),
        strict.common_normalized_keys,
        strict.evaluated_consecutive_triples, len(strict.witnesses),
        progressive.child_count_topology_intersections,
        progressive.chemistry_chirality_intersections,
        progressive.directed_port_semantics_intersections,
        progressive.normalized_pose_intersections,
        progressive.first_zero_field, False, False, hierarchy_gate,
        "This is deep exact train-corpus compression. One of 80 first-level "
        "quotient types is witnessed in only one window; all quotient types "
        "at later positive levels have evidence in two disjoint raw windows. "
        "The five windows are distinct exact local configurations, although "
        "disjoint atom domains alone are not statistical independence. "
        "The nine-level depth is deterministic for this packed corpus but is "
        "not yet a resampling- or perturbation-robust depth estimate. It does "
        "not yet transfer or "
        "execute a stationary production on an unopened quasicrystal window, "
        "so exponential growth remains red.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
