#!/usr/bin/env python3
"""Sealed Cd--Yb audit of partial promoted-macro frontier recognition."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    _pack, _window_ids)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_cdyb_hierarchical_growth_design import (
    EVAL_CENTER, SEED_RADIUS, TARGET_RADIUS, _ids)
from materials_gcts_iqc_reclustered_transfer_audit import (
    _frozen_heldout_program)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_irregular_port_atlas import enumerate_frozen_port_occurrences
from materials_gcts_macro_derivation import _site_key
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


@dataclass(frozen=True)
class CdYbPartialPromotedFrontierAudit:
    train_atoms: int
    seed_atoms: int
    lower_seed_occurrences: int
    frozen_parent_types: int
    frozen_derivation_alternatives: int
    partial_completion_candidates: int
    candidate_digest: str
    candidates_with_two_or_more_admitted_port_connected_witnesses: int
    frame_hypotheses: int
    insufficient_geometric_witness_hypotheses: int
    internal_port_rejections: int
    child_coverage_rejections: int
    one_child_missing_port_rejections: int
    collision_rejections: int
    redundant_completion_rejections: int
    public_boundary_rejections: int
    ambiguous_completion_signatures: int
    emitted_atoms_union: int
    posthoc_exact_completion_candidates: int
    posthoc_wrong_completion_candidates: int
    train_target_raw_id_intersection: int
    minimum_train_eval_center_separation: float
    spatial_domains_disjoint: bool
    oracle_target_ball_unclipped: bool
    target_opened_after_candidate_trace_frozen: bool
    target_used_for_candidate_enumeration_or_ranking: bool
    family_cell_scale_or_origin_heuristic_used: bool


def evaluate():
    atoms = generate_cdyb(6, (120.,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    train_ids = set().union(*map(set, train_windows))
    train_species, train_positions, _ = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    primitive = compile_irregular_port_program(train_species, train_positions)
    mined = mine_port_graph_macros(
        primitive, maximum_nodes=3, include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    promoted = promote_macro_types(
        primitive, quotient.quotient_macros, level=1)

    seed_ids = _ids(atoms, EVAL_CENTER, SEED_RADIUS)
    seed_species = tuple(atoms.symbols[index] for index in seed_ids)
    seed_positions = tuple(atoms.positions[index] for index in seed_ids)
    seed_sites = tuple(zip(seed_species, seed_positions))
    # Partial RHS recognition needs the complete finite occurrence graph, not
    # the atom-cover subset used by the primitive renderer.  Greedy cover can
    # discard exactly the overlapping child witness that fixes a macro pose.
    enumeration = enumerate_frozen_port_occurrences(
        primitive, seed_species, seed_positions)
    seed_program = _frozen_heldout_program(primitive, enumeration)
    parent_by_geometry = {macro_id: prototype_id for prototype_id, macro_id
                          in promoted.prototype_macro_types}
    alternative_parent_types = []
    cursor = 0
    for geometry in quotient.derivation_classes:
        for _alternative in geometry.alternatives:
            macro = quotient.alternative_macros[cursor]
            alternative_parent_types.append((
                macro.macro_id,
                parent_by_geometry[geometry.geometry_class_id]))
            cursor += 1
    assert cursor == len(quotient.alternative_macros)
    frontier = enumerate_partial_promoted_completions(
        seed_program, quotient.alternative_macros,
        minimum_matched_children=1, minimum_child_coverage=.5,
        explicit_seed_sites=seed_sites,
        public_boundary=ExecutionBoundary(EVAL_CENTER, TARGET_RADIUS),
        frozen_parent_types=tuple(alternative_parent_types))
    completion_records = tuple(
        (item.frozen_parent_type, item.macro_id, item.matched_nodes,
         item.matched_occurrence_ids,
         tuple((child.node, child.type_id,
                tuple(_site_key(site, .03) for site in child.sites))
               for child in item.missing_children))
        for item in frontier.completions)
    candidate_digest = hashlib.sha256(
        repr(completion_records).encode()).hexdigest()

    # Scorer boundary: target does not exist until the immutable candidate
    # tuple and its digest above have been produced.
    target_ids = _ids(atoms, EVAL_CENTER, TARGET_RADIUS)
    target_keys = {_site_key(
        (atoms.symbols[index], atoms.positions[index]), .03)
                   for index in target_ids}
    seed_keys = {_site_key(site, .03) for site in seed_sites}
    emitted_by_candidate = tuple(
        {_site_key(site, .03) for child in candidate.missing_children
         for site in child.sites} - seed_keys
        for candidate in frontier.completions)
    exact = sum(bool(emitted) and emitted.issubset(target_keys)
                for emitted in emitted_by_candidate)
    emitted = set().union(*emitted_by_candidate) \
        if emitted_by_candidate else set()
    separation = min(math.dist(EVAL_CENTER, center)
                     for center in TRAIN_CENTERS)
    unclipped = all(abs(EVAL_CENTER[axis]) + TARGET_RADIUS <= 60.
                    for axis in range(3))
    return CdYbPartialPromotedFrontierAudit(
        len(train_positions), len(seed_ids), len(seed_program.occurrences),
        len(promoted.prototypes), len(quotient.alternative_macros),
        len(frontier.completions), candidate_digest,
        sum(len(item.matched_occurrence_ids) >= 2
            for item in frontier.completions), frontier.frame_hypotheses,
        frontier.insufficient_hypotheses,
        frontier.internal_port_rejections,
        frontier.child_coverage_rejections,
        frontier.one_child_missing_port_rejections,
        frontier.collision_rejections,
        frontier.redundant_completion_rejections,
        frontier.public_boundary_rejections,
        frontier.ambiguous_completion_signatures, len(emitted), exact,
        len(frontier.completions) - exact,
        len(train_ids.intersection(target_ids)), separation,
        separation > 14. + TARGET_RADIUS, unclipped, True,
        frontier.target_used, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
