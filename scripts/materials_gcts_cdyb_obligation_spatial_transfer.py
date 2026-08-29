#!/usr/bin/env python3
"""Consumed spatial transfer of the Cd--Yb whole-child obligation policy.

The two reserved R14 windows have already been used by frozen-vocabulary
re-encoding audits, so this is not a fresh confirmation.  It is nevertheless a
strict spatial transfer diagnostic: the primitive/macro vocabulary, local site
model, whole-child aggregation, and action threshold are frozen from the five
training windows.  Execution receives only each R7 nucleus and a public R14
boundary; the remaining atoms are consulted afterward for scoring only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import RADIUS, TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    HELDOUT_CENTERS, PACK_SEPARATION, _pack, _window_ids)
from materials_gcts_cdyb_group_sealed_site_mask_execution import (
    _parent_map, _training_rows)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_cdyb_site_resolved_completion_section import (
    FEATURE_NAMES, FrozenSiteSection, _action_rows, _fit, _grouped_lambda,
    _predict, _select_aggregation)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_derivation import _site_key
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_completion_executor import PartialCompletionLevel
from materials_gcts_partial_completion_sections import (
    execute_partial_completion_sections)
from materials_gcts_partial_completion_site_policy import (
    adapt_frozen_site_section)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


@dataclass(frozen=True)
class SpatialWindowTransfer:
    window: int
    seed_atoms: int
    recognized_seed_occurrences: int
    waves: int
    whole_candidates_by_wave: tuple[int, ...]
    accepted_sections_by_wave: tuple[int, ...]
    appended_children_by_wave: tuple[int, ...]
    promoted_parents_by_wave: tuple[int, ...]
    emitted_sites: int
    correct_sites: int
    wrong_sites: int
    precision: float
    outer_recall: float
    self_fed: bool
    exact_certificates: bool
    first_wave_candidate_digest: str


@dataclass(frozen=True)
class CdYbObligationSpatialTransfer:
    training_windows: int
    reserved_windows: int
    training_atoms: int
    reserved_atoms: int
    training_reserve_raw_id_intersection: int
    spatial_domains_disjoint: bool
    final_site_model_rows: int
    final_negative_actions: int
    final_aggregation: str
    final_obligation_threshold: float
    frozen_support_types: int
    frozen_macro_alternatives: int
    windows: tuple[SpatialWindowTransfer, ...]
    total_emitted_sites: int
    total_correct_sites: int
    total_wrong_sites: int
    aggregate_precision: float
    aggregate_outer_recall: float
    completed_children: int
    promoted_parents: int
    self_fed_windows: int
    target_used_during_fit_enumeration_ranking_or_execution: bool
    reserved_windows_previously_consumed_by_reencoding: bool
    no_refit_on_reserved_windows: bool
    exact_execution_certificates: bool
    spatial_transfer_gate_passed: bool
    scientific_status: str
    audit_digest: str


def _digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        default=repr).encode()).hexdigest()


def _final_policy(rows):
    ridge = _grouped_lambda(rows)
    means, scales, weights, intercept = _fit(rows, ridge)
    model = (means, scales, weights, intercept)
    aggregation = _select_aggregation(rows, None)
    site_scores = tuple(_predict(model, row) for row in rows)
    actions = _action_rows(rows, site_scores, aggregation)
    negatives = tuple(score for successful, score in actions
                      if not successful)
    obligation_threshold = (math.nextafter(max(negatives), 1.)
                            if negatives else 1.)
    site_negatives = tuple(score for row, score in zip(rows, site_scores)
                           if not row.successful)
    site_threshold = (math.nextafter(max(site_negatives), 1.)
                      if site_negatives else 1.)
    frozen = FrozenSiteSection(
        FEATURE_NAMES, means, scales, weights, intercept, ridge, aggregation,
        site_threshold, False, False)
    return adapt_frozen_site_section(frozen), obligation_threshold, len(negatives)


def evaluate() -> CdYbObligationSpatialTransfer:
    atoms = generate_cdyb(5, (80.,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    reserved_windows = _window_ids(atoms, HELDOUT_CENTERS)
    train_ids = set().union(*map(set, train_windows))
    reserved_ids = set().union(*map(set, reserved_windows))
    train_species, train_positions, train_namespaces = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    held_species, held_positions, held_namespaces = _pack(
        atoms, HELDOUT_CENTERS, reserved_windows)

    primitive = compile_irregular_port_program(train_species, train_positions)
    quotient = quotient_macro_supports(mine_port_graph_macros(
        primitive, maximum_nodes=3,
        include_boundary_relations=True).macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    parent_map = _parent_map(quotient, promoted)
    level = PartialCompletionLevel(
        primitive, quotient.alternative_macros, parent_map, promoted)
    rows, _frontiers = _training_rows(
        primitive, quotient, parent_map, train_species, train_positions,
        train_namespaces)
    policy, obligation_threshold, negative_actions = _final_policy(rows)

    results = []
    total_outer = 0
    for held in range(len(HELDOUT_CENTERS)):
        center = (held * PACK_SEPARATION, 0., 0.)
        seed_indices = tuple(
            index for index, point in enumerate(held_positions)
            if held_namespaces[index] == held and
            math.dist(point, center) <= 7. + 1e-10)
        seed_species = tuple(held_species[index] for index in seed_indices)
        seed_positions = tuple(held_positions[index] for index in seed_indices)
        seed_sites = tuple(zip(seed_species, seed_positions))
        seed_keys = {_site_key(site, .03) for site in seed_sites}
        enumeration = enumerate_frozen_port_occurrences(
            primitive, seed_species, seed_positions)
        execution = execute_partial_completion_sections(
            level, enumeration.occurrences, marking=policy,
            minimum_marking_score=obligation_threshold,
            explicit_seed_sites=seed_sites,
            public_boundary=ExecutionBoundary(center, RADIUS),
            maximum_waves=3, minimum_child_coverage=.5)
        # The full reserved window first enters here, after immutable execution.
        target = {
            _site_key((held_species[index], held_positions[index]), .03)
            for index, namespace in enumerate(held_namespaces)
            if namespace == held}
        emitted = {_site_key(site, .03) for site in execution.sites} - seed_keys
        correct = emitted.intersection(target)
        wrong = emitted - target
        outer = target - seed_keys
        total_outer += len(outer)
        waves = execution.waves
        results.append(SpatialWindowTransfer(
            held, len(seed_indices), len(enumeration.occurrences), len(waves),
            tuple(item.whole_candidates for item in waves),
            tuple(item.accepted_sections for item in waves),
            tuple(item.appended_children for item in waves),
            tuple(item.completed_whole_macros for item in waves),
            len(emitted), len(correct), len(wrong),
            len(correct) / len(emitted) if emitted else 1.,
            len(correct) / max(1, len(outer)), execution.self_fed,
            execution.exact_certificates,
            waves[0].whole_candidate_digest if waves else _digest(())))

    emitted = sum(item.emitted_sites for item in results)
    correct = sum(item.correct_sites for item in results)
    wrong = sum(item.wrong_sites for item in results)
    children = sum(sum(item.appended_children_by_wave) for item in results)
    parents = sum(sum(item.promoted_parents_by_wave) for item in results)
    self_fed = sum(item.self_fed for item in results)
    exact = all(item.exact_certificates for item in results)
    spatial_disjoint = all(
        math.dist(left, right) > 2 * RADIUS
        for left in TRAIN_CENTERS for right in HELDOUT_CENTERS)
    payload = {
        "threshold": obligation_threshold,
        "aggregation": policy.aggregation,
        "windows": tuple(asdict(item) for item in results),
    }
    return CdYbObligationSpatialTransfer(
        len(TRAIN_CENTERS), len(HELDOUT_CENTERS), len(train_positions),
        len(held_positions), len(train_ids.intersection(reserved_ids)),
        spatial_disjoint, len(rows), negative_actions, policy.aggregation,
        obligation_threshold, len(primitive.prototypes),
        len(quotient.alternative_macros), tuple(results), emitted, correct,
        wrong, correct / emitted if emitted else 1.,
        correct / max(1, total_outer), children, parents, self_fed, False,
        True, True, exact,
        (emitted > 0 and not wrong and parents > 0 and self_fed > 0 and exact),
        ("consumed spatial transfer diagnostic; no reserved-window refit, but "
         "the structural windows were previously observed by re-encoding "
         "audits, so this is not fresh confirmation"), _digest(payload))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
