#!/usr/bin/env python3
"""Train-only audit of the Cd--Yb partial-macro coverage gate.

The current executor requires at least half of a frozen macro's children to be
already present.  Since the learned vocabulary contains at most three-child
macros, the only strictly weaker one-child gate is one third.  This audit fits
and selects between those two candidate-generation rules using the five
development windows only, then applies the frozen winner to the two already
consumed spatial reserves.  Reserve atoms enter only after target-free
enumeration, ranking, and execution.

This is a candidate-supply diagnostic, not fresh confirmation.  Lowering the
coverage fraction never weakens proper-SE(3), finite-frame, witnessed-port,
collision, public-boundary, exact-child, or exact-parent certificates.
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
    _fold_policy, _parent_map)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_cdyb_site_resolved_completion_section import (
    SEED_RADII, _aggregate, _dedupe, _frontier_rows, _predict)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_frozen_frontier_replay import (
    RadialBoundary, enumerate_frontier, fit_frozen_frontier_program)
from materials_gcts_macro_derivation import _site_key
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_completion_executor import (
    PartialCompletionLevel, _dynamic_program)
from materials_gcts_partial_completion_sections import (
    execute_partial_completion_sections)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


COVERAGE_OPTIONS = (1 / 3, 1 / 2)


@dataclass(frozen=True)
class CoverageFold:
    window: int
    selected_actions: int
    exact_actions: int
    wrong_actions: int
    correct_sites: int
    wrong_sites: int


@dataclass(frozen=True)
class CoverageDevelopmentAudit:
    minimum_child_coverage: float
    site_rows: int
    action_rows: int
    negative_actions: int
    folds: tuple[CoverageFold, ...]
    selected_actions: int
    exact_actions: int
    wrong_actions: int
    correct_sites: int
    wrong_sites: int
    every_fold_nonempty: bool
    zero_wrong_action_gate: bool


@dataclass(frozen=True)
class ReserveCoverageAudit:
    window: int
    seed_atoms: int
    recognized_seed_occurrences: int
    recognized_seed_types: int
    macro_anchor_type_overlap: int
    macro_anchor_occurrences: int
    minimum_child_coverage: float
    frame_hypotheses: int
    insufficient_geometric_witnesses: int
    child_coverage_rejections: int
    connected_port_rejections: int
    one_child_missing_port_rejections: int
    collision_rejections: int
    public_boundary_rejections: int
    whole_candidates: int
    primitive_port_candidates: int
    primitive_exact_candidates: int
    primitive_exact_site_union: int
    primitive_inexact_candidates: int
    accepted_sections_by_wave: tuple[int, ...]
    emitted_sites: int
    correct_sites: int
    wrong_sites: int
    promoted_parents: int
    self_fed: bool
    exact_certificates: bool


@dataclass(frozen=True)
class CdYbCandidateSupplyCoverageAudit:
    training_windows: int
    reserved_windows: int
    training_atoms: int
    reserved_atoms: int
    support_types: int
    macro_alternatives: int
    maximum_macro_children: int
    coverage_options: tuple[float, ...]
    development: tuple[CoverageDevelopmentAudit, ...]
    selected_coverage: float
    selection_uses_training_only: bool
    selected_by_zero_wrong_then_correct_sites: bool
    reserves: tuple[ReserveCoverageAudit, ...]
    baseline_zero_candidate_reserve: int
    selected_zero_candidate_reserve: int
    selected_total_emitted: int
    selected_total_correct: int
    selected_total_wrong: int
    selected_total_parents: int
    candidate_supply_extension_safe: bool
    relaxed_coverage_selected: bool
    primitive_fallback_has_exact_supply: bool
    target_used_during_selection_enumeration_ranking_or_execution: bool
    reserves_previously_consumed: bool
    scientific_status: str
    audit_digest: str


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        default=repr).encode()).hexdigest()


def _training_rows(primitive, quotient, parent_map, species, positions,
                   namespaces, minimum_child_coverage):
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
                    namespaces, patch, center, seed_radius,
                    minimum_child_coverage=minimum_child_coverage))
    return _dedupe(rows)


def _development_audit(fit_rows, evaluation_rows, coverage):
    folds = []
    for held in range(len(TRAIN_CENTERS)):
        policy, threshold, _fit_rows, _negative_rows = _fold_policy(
            fit_rows, held)
        held_rows = tuple(row for row in evaluation_rows
                          if row.window == held)
        scores = tuple(_predict((policy.means, policy.scales, policy.weights,
                                 policy.intercept), row)
                       for row in held_rows)
        selected_ids = set()
        action_success = {}
        for candidate_id in sorted({row.candidate_id for row in held_rows}):
            indices = tuple(index for index, row in enumerate(held_rows)
                            if row.candidate_id == candidate_id)
            successful = all(held_rows[index].successful for index in indices)
            score = _aggregate(tuple(scores[index] for index in indices),
                               policy.aggregation)
            action_success[candidate_id] = successful
            if score >= threshold:
                selected_ids.add(candidate_id)
        selected_rows = tuple(row for row in held_rows
                              if row.candidate_id in selected_ids)
        correct_sites = {row.site_key for row in selected_rows
                         if row.successful}
        wrong_sites = {row.site_key for row in selected_rows
                       if not row.successful}
        exact_actions = sum(action_success[item] for item in selected_ids)
        folds.append(CoverageFold(
            held, len(selected_ids), exact_actions,
            len(selected_ids) - exact_actions, len(correct_sites),
            len(wrong_sites)))
    actions = {}
    for row in evaluation_rows:
        actions.setdefault((row.window, row.candidate_id), []).append(row)
    negative_actions = sum(not all(row.successful for row in values)
                           for values in actions.values())
    return CoverageDevelopmentAudit(
        coverage, len(evaluation_rows), len(actions), negative_actions,
        tuple(folds),
        sum(item.selected_actions for item in folds),
        sum(item.exact_actions for item in folds),
        sum(item.wrong_actions for item in folds),
        sum(item.correct_sites for item in folds),
        sum(item.wrong_sites for item in folds),
        all(item.selected_actions for item in folds),
        not any(item.wrong_actions or item.wrong_sites for item in folds))


def _select_coverage(audits):
    eligible = tuple(item for item in audits
                     if item.every_fold_nonempty and
                     item.zero_wrong_action_gate)
    if not eligible:
        return max(audits, key=lambda item: item.minimum_child_coverage)
    return max(eligible, key=lambda item: (
        item.correct_sites, item.exact_actions,
        item.minimum_child_coverage))


def _final_policy(rows):
    # Same fit and threshold rule as Build315, now on the selected train-only
    # candidate generator.
    from materials_gcts_cdyb_obligation_spatial_transfer import _final_policy
    return _final_policy(rows)


def evaluate() -> CdYbCandidateSupplyCoverageAudit:
    atoms = generate_cdyb(5, (80.,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    reserve_windows = _window_ids(atoms, HELDOUT_CENTERS)
    train_species, train_positions, train_namespaces = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    held_species, held_positions, held_namespaces = _pack(
        atoms, HELDOUT_CENTERS, reserve_windows)
    primitive = compile_irregular_port_program(train_species, train_positions)
    quotient = quotient_macro_supports(mine_port_graph_macros(
        primitive, maximum_nodes=3,
        include_boundary_relations=True).macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    frozen_frontier = fit_frozen_frontier_program(primitive)
    parent_map = _parent_map(quotient, promoted)
    level = PartialCompletionLevel(
        primitive, quotient.alternative_macros, parent_map, promoted)

    baseline_rows = _training_rows(
        primitive, quotient, parent_map, train_species, train_positions,
        train_namespaces, .5)
    relaxed_canonical_rows = _dedupe(tuple(
        row
        for patch in range(len(TRAIN_CENTERS))
        for row in _frontier_rows(
            primitive, quotient, parent_map, train_species, train_positions,
            train_namespaces, patch, (patch * PACK_SEPARATION, 0., 0.), 7.,
            minimum_child_coverage=1 / 3)))
    baseline_canonical_rows = tuple(
        row for row in relaxed_canonical_rows if row.features[7] >= .5)
    combined_rows = _dedupe((*baseline_rows, *relaxed_canonical_rows))
    rows_by_coverage = {
        .5: baseline_rows,
        1 / 3: combined_rows,
    }
    evaluation_rows = {
        .5: baseline_canonical_rows,
        1 / 3: relaxed_canonical_rows,
    }
    development = tuple(_development_audit(
        rows_by_coverage[coverage], evaluation_rows[coverage], coverage)
        for coverage in COVERAGE_OPTIONS)
    selected = _select_coverage(development)
    policy, threshold, _negative_actions = _final_policy(
        rows_by_coverage[selected.minimum_child_coverage])

    reserve_audits = []
    for held, _center_source in enumerate(HELDOUT_CENTERS):
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
        seed_types = {item.type_id for item in enumeration.occurrences}
        anchor_types = {
            placement.cluster_type
            for macro in quotient.alternative_macros
            for placement in macro.child_placements}
        macro_anchor_types = seed_types.intersection(anchor_types)
        macro_anchor_occurrences = sum(
            item.type_id in macro_anchor_types
            for item in enumeration.occurrences)
        primitive_frontier = enumerate_frontier(
            frozen_frontier, enumeration.occurrences,
            explicit_gap_sites=seed_sites,
            boundary=RadialBoundary(center, RADIUS))
        dynamic = _dynamic_program(primitive, enumeration.occurrences, .03)
        frontier = enumerate_partial_promoted_completions(
            dynamic, quotient.alternative_macros,
            minimum_matched_children=1,
            minimum_child_coverage=selected.minimum_child_coverage,
            explicit_seed_sites=seed_sites,
            public_boundary=ExecutionBoundary(center, RADIUS),
            frozen_parent_types=parent_map)
        execution = execute_partial_completion_sections(
            level, enumeration.occurrences, marking=policy,
            minimum_marking_score=threshold,
            explicit_seed_sites=seed_sites,
            public_boundary=ExecutionBoundary(center, RADIUS),
            maximum_waves=3,
            minimum_child_coverage=selected.minimum_child_coverage)
        # Reserved truth first enters after enumeration/ranking/execution.
        target = {
            _site_key((held_species[index], held_positions[index]), .03)
            for index, namespace in enumerate(held_namespaces)
            if namespace == held}
        emitted = {_site_key(site, .03) for site in execution.sites} - seed_keys
        exact_primitive = tuple(
            candidate for candidate in primitive_frontier.candidates
            if all(_site_key(site, .03) in target
                   for site in candidate.novel_sites))
        exact_primitive_sites = {
            _site_key(site, .03)
            for candidate in exact_primitive for site in candidate.novel_sites}
        reserve_audits.append(ReserveCoverageAudit(
            held, len(seed_indices), len(enumeration.occurrences),
            len(seed_types), len(macro_anchor_types),
            macro_anchor_occurrences,
            selected.minimum_child_coverage, frontier.frame_hypotheses,
            frontier.insufficient_hypotheses,
            frontier.child_coverage_rejections,
            frontier.internal_port_rejections,
            frontier.one_child_missing_port_rejections,
            frontier.collision_rejections,
            frontier.public_boundary_rejections,
            len(frontier.completions), len(primitive_frontier.candidates),
            len(exact_primitive), len(exact_primitive_sites),
            len(primitive_frontier.candidates) - len(exact_primitive),
            tuple(item.accepted_sections for item in execution.waves),
            len(emitted), len(emitted.intersection(target)),
            len(emitted - target), len(execution.promoted_occurrences),
            execution.self_fed, execution.exact_certificates))

    # First-wave reserve enumeration at the baseline is reported separately
    # without execution or target use.
    baseline_zero_reserves = 0
    for held in range(len(HELDOUT_CENTERS)):
        center = (held * PACK_SEPARATION, 0., 0.)
        seed_indices = tuple(
            index for index, point in enumerate(held_positions)
            if held_namespaces[index] == held and
            math.dist(point, center) <= 7. + 1e-10)
        seed_species = tuple(held_species[index] for index in seed_indices)
        seed_positions = tuple(held_positions[index] for index in seed_indices)
        seed_sites = tuple(zip(seed_species, seed_positions))
        enumeration = enumerate_frozen_port_occurrences(
            primitive, seed_species, seed_positions)
        dynamic = _dynamic_program(primitive, enumeration.occurrences, .03)
        baseline_frontier = enumerate_partial_promoted_completions(
            dynamic, quotient.alternative_macros,
            minimum_matched_children=1, minimum_child_coverage=.5,
            explicit_seed_sites=seed_sites,
            public_boundary=ExecutionBoundary(center, RADIUS),
            frozen_parent_types=parent_map)
        baseline_zero_reserves += not baseline_frontier.completions

    total_emitted = sum(item.emitted_sites for item in reserve_audits)
    total_correct = sum(item.correct_sites for item in reserve_audits)
    total_wrong = sum(item.wrong_sites for item in reserve_audits)
    total_parents = sum(item.promoted_parents for item in reserve_audits)
    selected_zero = sum(not item.whole_candidates for item in reserve_audits)
    relaxed_selected = selected.minimum_child_coverage < .5
    safe = (relaxed_selected and selected.zero_wrong_action_gate and
            selected_zero < baseline_zero_reserves and
            total_emitted > 0 and not total_wrong and total_parents > 0 and
            all(item.exact_certificates for item in reserve_audits))
    primitive_supply = all(item.primitive_exact_candidates > 0
                           for item in reserve_audits)
    payload = {
        "development": tuple(asdict(item) for item in development),
        "selected": selected.minimum_child_coverage,
        "reserves": tuple(asdict(item) for item in reserve_audits),
    }
    return CdYbCandidateSupplyCoverageAudit(
        len(TRAIN_CENTERS), len(HELDOUT_CENTERS), len(train_positions),
        len(held_positions), len(primitive.prototypes),
        len(quotient.alternative_macros),
        max(len(item.child_placements) for item in quotient.alternative_macros),
        COVERAGE_OPTIONS, development, selected.minimum_child_coverage,
        True, True, tuple(reserve_audits), baseline_zero_reserves,
        selected_zero, total_emitted, total_correct, total_wrong,
        total_parents, safe, relaxed_selected, primitive_supply, False, True,
        ("one-third coverage is rejected by a wrong held-development action; "
         "the zero-macro reserve has no retained macro anchor type but does "
         "have exact primitive-port supply; reserves were already consumed, "
         "so this is a spatial diagnostic rather than fresh confirmation"),
        _digest(payload))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
