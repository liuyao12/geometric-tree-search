#!/usr/bin/env python3
"""Group-sealed Cd--Yb execution of the learned local site section.

This is a development/transport audit, not an untouched-material test.  The
support and macro vocabulary is learned from all five published training
windows.  For each execution fold, however, the site marking and its
zero-fitted-negative threshold are learned from the other four windows only.
The held window is used only after target-free execution to score emitted
colored sites.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import RADIUS, TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    PACK_SEPARATION, _pack, _window_ids)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_cdyb_site_resolved_completion_section import (
    FEATURE_NAMES, SEED_RADII, FrozenSiteSection, _action_rows, _dedupe, _fit,
    _frontier_rows, _grouped_lambda, _parent_map, _predict,
    _select_aggregation)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_derivation import _site_key
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_completion_executor import PartialCompletionLevel
from materials_gcts_partial_completion_site_mask_executor import (
    execute_partial_completion_site_masks)
from materials_gcts_partial_completion_sections import (
    execute_partial_completion_sections)
from materials_gcts_partial_completion_site_policy import (
    adapt_frozen_site_section)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


@dataclass(frozen=True)
class HeldWindowExecution:
    window: int
    seed_atoms: int
    fitted_marking_rows: int
    fitted_negative_rows: int
    frozen_threshold: float
    frozen_obligation_threshold: float
    waves: int
    candidates_by_wave: tuple[int, ...]
    proposed_sites_by_wave: tuple[int, ...]
    accepted_sites_by_wave: tuple[int, ...]
    completed_children_by_wave: tuple[int, ...]
    completed_parents_by_wave: tuple[int, ...]
    emitted_sites: int
    correct_sites: int
    wrong_sites: int
    precision: float
    outer_recall: float
    self_fed: bool
    exact_certificates: bool
    first_wave_candidate_digest: str
    closure_emitted_sites: int
    closure_correct_sites: int
    closure_wrong_sites: int
    closure_precision: float
    closure_completed_children: int
    closure_promoted_parents: int
    closure_self_fed: bool
    closure_exact_certificates: bool
    closure_first_wave_candidate_digest: str


@dataclass(frozen=True)
class CdYbGroupSealedSiteMaskAudit:
    train_windows: int
    vocabulary_atoms: int
    support_types: int
    macro_alternatives: int
    shifted_training_frontiers: int
    marking_fit_excludes_execution_window: bool
    geometry_vocabulary_fit_on_all_training_windows: bool
    future_confirmatory_target_opened: bool
    target_api_present_during_execution: bool
    held_windows: tuple[HeldWindowExecution, ...]
    total_emitted_sites: int
    total_correct_sites: int
    total_wrong_sites: int
    aggregate_precision: float
    aggregate_outer_recall: float
    nonempty_windows: int
    self_fed_windows: int
    completed_children: int
    completed_parents: int
    exact_execution_certificates: bool
    closure_total_emitted_sites: int
    closure_total_correct_sites: int
    closure_total_wrong_sites: int
    closure_aggregate_precision: float
    closure_completed_children: int
    closure_promoted_parents: int
    closure_self_fed_windows: int
    closure_candidate_batches_match_site_masks: bool
    obligation_closure_gate_passed: bool
    scientific_status: str
    audit_digest: str


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        default=repr).encode()).hexdigest()


def _training_rows(primitive, quotient, parent_map, species, positions,
                   namespaces):
    scale = primitive.cover.minimum_distance
    offsets = ((0., 0., 0.), (scale, 0., 0.), (-scale, 0., 0.),
               (0., scale, 0.), (0., -scale, 0.),
               (0., 0., scale), (0., 0., -scale))
    rows = []
    for seed_radius in SEED_RADII:
        for patch in range(len(TRAIN_CENTERS)):
            origin = (patch * PACK_SEPARATION, 0., 0.)
            for offset in offsets:
                center = tuple(origin[axis] + offset[axis]
                               for axis in range(3))
                rows.extend(_frontier_rows(
                    primitive, quotient, parent_map, species, positions,
                    namespaces, patch, center, seed_radius))
    return _dedupe(rows), len(offsets) * len(SEED_RADII) * len(TRAIN_CENTERS)


def _fold_policy(rows, held):
    discovery = tuple(row for row in rows if row.window != held)
    ridge = _grouped_lambda(rows, held)
    means, scales, weights, intercept = _fit(discovery, ridge)
    negative_scores = tuple(
        _predict((means, scales, weights, intercept), row)
        for row in discovery if not row.successful)
    threshold = (math.nextafter(max(negative_scores), 1.)
                 if negative_scores else 1.)
    aggregation = _select_aggregation(rows, held)
    discovery_scores = tuple(
        _predict((means, scales, weights, intercept), row)
        for row in discovery)
    discovery_actions = _action_rows(
        discovery, discovery_scores, aggregation)
    negative_action_scores = tuple(
        score for successful, score in discovery_actions if not successful)
    obligation_threshold = (
        math.nextafter(max(negative_action_scores), 1.)
        if negative_action_scores else 1.)
    model = FrozenSiteSection(
        FEATURE_NAMES, means, scales, weights, intercept, ridge,
        aggregation, threshold, False, False)
    return (adapt_frozen_site_section(model), obligation_threshold,
            len(discovery), len(negative_scores))


def evaluate() -> CdYbGroupSealedSiteMaskAudit:
    atoms = generate_cdyb(6, (120.,) * 3)
    windows = _window_ids(atoms, TRAIN_CENTERS)
    species, positions, namespaces = _pack(atoms, TRAIN_CENTERS, windows)
    primitive = compile_irregular_port_program(species, positions)
    quotient = quotient_macro_supports(mine_port_graph_macros(
        primitive, maximum_nodes=3,
        include_boundary_relations=True).macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    parent_map = _parent_map(quotient, promoted)
    level = PartialCompletionLevel(
        primitive, quotient.alternative_macros, parent_map, promoted)
    rows, frontier_count = _training_rows(
        primitive, quotient, parent_map, species, positions, namespaces)

    results = []
    total_outer = 0
    for held in range(len(TRAIN_CENTERS)):
        policy, obligation_threshold, fit_rows, negative_rows = \
            _fold_policy(rows, held)
        center = (held * PACK_SEPARATION, 0., 0.)
        seed_indices = tuple(
            index for index, point in enumerate(positions)
            if namespaces[index] == held and
            math.dist(point, center) <= 7. + 1e-10)
        seed_species = tuple(species[index] for index in seed_indices)
        seed_positions = tuple(positions[index] for index in seed_indices)
        seed_sites = tuple(zip(seed_species, seed_positions))
        seed_keys = {_site_key(site, .03) for site in seed_sites}
        target_keys = {
            _site_key((species[index], positions[index]), .03)
            for index, patch in enumerate(namespaces) if patch == held}
        total_outer += len(target_keys - seed_keys)
        enumeration = enumerate_frozen_port_occurrences(
            primitive, seed_species, seed_positions)
        execution = execute_partial_completion_site_masks(
            level, enumeration.occurrences, site_policy=policy,
            explicit_seed_sites=seed_sites,
            public_boundary=ExecutionBoundary(center, RADIUS),
            maximum_waves=3, minimum_child_coverage=.5)
        closure = execute_partial_completion_sections(
            level, enumeration.occurrences, marking=policy,
            minimum_marking_score=obligation_threshold,
            explicit_seed_sites=seed_sites,
            public_boundary=ExecutionBoundary(center, RADIUS),
            maximum_waves=3, minimum_child_coverage=.5)
        emitted = {_site_key(site, .03) for site in execution.sites} - seed_keys
        correct = emitted.intersection(target_keys)
        wrong = emitted - target_keys
        closure_emitted = ({_site_key(site, .03) for site in closure.sites} -
                           seed_keys)
        closure_correct = closure_emitted.intersection(target_keys)
        closure_wrong = closure_emitted - target_keys
        waves = execution.waves
        results.append(HeldWindowExecution(
            held, len(seed_indices), fit_rows, negative_rows,
            execution.frozen_site_threshold, obligation_threshold, len(waves),
            tuple(len(item.whole_candidate_ids) for item in waves),
            tuple(len(item.proposed_novel_site_keys) for item in waves),
            tuple(len(item.accepted_site_keys) for item in waves),
            tuple(item.completed_children for item in waves),
            tuple(item.completed_parents for item in waves),
            len(emitted), len(correct), len(wrong),
            len(correct) / len(emitted) if emitted else 1.,
            len(correct) / max(1, len(target_keys - seed_keys)),
            execution.self_fed, execution.exact_certificates,
            waves[0].whole_candidate_digest if waves else _digest(()),
            len(closure_emitted), len(closure_correct), len(closure_wrong),
            (len(closure_correct) / len(closure_emitted)
             if closure_emitted else 1.),
            sum(item.appended_children for item in closure.waves),
            len(closure.promoted_occurrences), closure.self_fed,
            closure.exact_certificates,
            (closure.waves[0].whole_candidate_digest
             if closure.waves else _digest(()))))

    emitted = sum(item.emitted_sites for item in results)
    correct = sum(item.correct_sites for item in results)
    wrong = sum(item.wrong_sites for item in results)
    closure_emitted = sum(item.closure_emitted_sites for item in results)
    closure_correct = sum(item.closure_correct_sites for item in results)
    closure_wrong = sum(item.closure_wrong_sites for item in results)
    payload = {
        "held_windows": [asdict(item) for item in results],
        "support_types": len(primitive.prototypes),
        "macro_alternatives": len(quotient.alternative_macros),
        "frontiers": frontier_count,
    }
    exact = all(item.exact_certificates for item in results)
    return CdYbGroupSealedSiteMaskAudit(
        len(TRAIN_CENTERS), len(species), len(primitive.prototypes),
        len(quotient.alternative_macros), frontier_count, True, True, False,
        False, tuple(results), emitted, correct, wrong,
        correct / emitted if emitted else 1.,
        correct / max(1, total_outer),
        sum(item.emitted_sites > 0 for item in results),
        sum(item.self_fed for item in results),
        sum(sum(item.completed_children_by_wave) for item in results),
        sum(sum(item.completed_parents_by_wave) for item in results), exact,
        closure_emitted, closure_correct, closure_wrong,
        closure_correct / closure_emitted if closure_emitted else 1.,
        sum(item.closure_completed_children for item in results),
        sum(item.closure_promoted_parents for item in results),
        sum(item.closure_self_fed for item in results),
        all(item.first_wave_candidate_digest ==
            item.closure_first_wave_candidate_digest for item in results),
        (closure_emitted > 0 and not closure_wrong and exact and
         all(item.closure_exact_certificates for item in results) and
         all(item.first_wave_candidate_digest ==
             item.closure_first_wave_candidate_digest for item in results) and
         any(item.closure_promoted_parents for item in results) and
         any(item.closure_self_fed for item in results)),
        ("group-sealed development child-obligation execution; geometry "
         "vocabulary is shared across the five training windows; exact finite "
         "self-feeding is established on development windows, with no "
         "untouched confirmation, stationary, or exponential-growth claim"),
        _digest(payload))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(result)


if __name__ == "__main__":
    main()
