#!/usr/bin/env python3
"""Sealed GCTS marking ablation for Cd--Yb partial macro completions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import _pack, _window_ids
from materials_gcts_cdyb_hierarchical_growth_design import EVAL_CENTER, _ids
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_iqc_reclustered_transfer_audit import _frozen_heldout_program
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_derivation import _site_key
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_completion_marking import (
    CompletionMarkTrace, FrozenCompletionMarking, fit_completion_marking,
    freeze_completion_candidate, rank_completion_candidates,
    shuffle_completion_traces_within_strata)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


TRAIN_SEED_RADIUS = 7.
TRAIN_TARGET_RADIUS = 14.
EVAL_SEED_RADIUS = 14.
EVAL_TARGET_RADIUS = 25.
THRESHOLDS = (0., .25, .4, .5, .6, .75)
BUDGETS = (5, 10, 20, 40)


@dataclass(frozen=True)
class PolicyScore:
    name: str
    selected_actions: int
    exact_actions: int
    wrong_actions: int
    action_precision: float
    action_recall_among_exact_candidates: float
    proposed_novel_sites: int
    correct_novel_sites: int
    wrong_novel_sites: int
    site_precision: float
    outer_recall: float
    proposal_checks: int
    geometric_backtracks: int
    matched_correct_site_budget: int
    matched_budget_proposal_checks: int
    matched_budget_wrong_actions: int


@dataclass(frozen=True)
class CdYbPartialCompletionMarkingAblation:
    train_atoms: int
    training_frontiers: int
    training_candidates: int
    training_candidates_by_frontier: tuple[int, ...]
    training_positive_actions: int
    training_positives_by_frontier: tuple[int, ...]
    training_negative_actions: int
    lopo_threshold: float
    lopo_top_budget: int
    lopo_selected_actions: int
    lopo_exact_actions: int
    eval_candidates: int
    eval_exact_candidates_posthoc: int
    eval_candidate_precision_posthoc: float
    eval_candidate_digest: str
    identical_candidate_ids_all_arms: bool
    marked: PolicyScore
    constant: PolicyScore
    frequency: PolicyScore
    shuffle_trials: int
    shuffled_median_exact_actions: float
    shuffled_best_exact_actions: int
    shuffled_median_correct_sites: float
    shuffled_best_correct_sites: int
    marked_empirical_p: float
    train_eval_raw_id_intersection: int
    minimum_train_eval_center_separation: float
    domains_disjoint: bool
    target_opened_after_all_eval_rankings_frozen: bool
    target_used_for_candidate_enumeration_or_ranking: bool
    descriptor_only_no_family_cell_origin_or_target_features: bool
    marking_gate_passed: bool


@dataclass(frozen=True)
class _FrozenRow:
    candidate: object
    emitted: frozenset
    exact: bool


def _compile():
    atoms = generate_cdyb(6, (120.,) * 3)
    windows = _window_ids(atoms, TRAIN_CENTERS)
    species, positions, _ = _pack(atoms, TRAIN_CENTERS, windows)
    primitive = compile_irregular_port_program(species, positions)
    quotient = quotient_macro_supports(mine_port_graph_macros(
        primitive, maximum_nodes=3,
        include_boundary_relations=True).macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    parent_by_geometry = {macro_id: prototype_id for prototype_id, macro_id
                          in promoted.prototype_macro_types}
    parent_map = []
    cursor = 0
    for geometry in quotient.derivation_classes:
        for _alternative in geometry.alternatives:
            macro = quotient.alternative_macros[cursor]
            parent_map.append((macro.macro_id,
                               parent_by_geometry[geometry.geometry_class_id]))
            cursor += 1
    if cursor != len(quotient.alternative_macros):
        raise AssertionError("incomplete alternative-to-parent map")
    return atoms, windows, species, positions, primitive, quotient, tuple(parent_map)


def _frontier(atoms, primitive, quotient, parent_map, center, seed_radius,
              target_radius, *, open_training_target):
    seed_ids = _ids(atoms, center, seed_radius)
    seed_species = tuple(atoms.symbols[index] for index in seed_ids)
    seed_positions = tuple(atoms.positions[index] for index in seed_ids)
    seed_sites = tuple(zip(seed_species, seed_positions))
    enumeration = enumerate_frozen_port_occurrences(
        primitive, seed_species, seed_positions)
    lower = _frozen_heldout_program(primitive, enumeration)
    raw = enumerate_partial_promoted_completions(
        lower, quotient.alternative_macros,
        minimum_matched_children=1, minimum_child_coverage=.5,
        explicit_seed_sites=seed_sites,
        public_boundary=ExecutionBoundary(center, target_radius),
        frozen_parent_types=parent_map)
    macro_by_id = {item.macro_id: item for item in quotient.alternative_macros}
    frozen = tuple(freeze_completion_candidate(
        lower, macro_by_id[item.macro_id], item,
        live_overlap_support=len(item.matched_occurrence_ids),
        live_collision_support=0) for item in raw.completions)
    seed_keys = {_site_key(site, .03) for site in seed_sites}
    emitted = {item.macro_id: None for item in ()}  # type anchor for mypy-free py3.9
    del emitted
    emitted_by_id = {
        candidate.candidate_id: frozenset(
            _site_key(site, .03)
            for child in completion.missing_children for site in child.sites
            if _site_key(site, .03) not in seed_keys)
        for candidate, completion in zip(frozen, raw.completions)}
    if not open_training_target:
        return lower, raw, frozen, emitted_by_id, seed_ids, None
    target_ids = _ids(atoms, center, target_radius)
    target = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
              for index in target_ids}
    rows = tuple(_FrozenRow(candidate, emitted_by_id[candidate.candidate_id],
                            bool(emitted_by_id[candidate.candidate_id]) and
                            emitted_by_id[candidate.candidate_id].issubset(target))
                 for candidate in frozen)
    return lower, raw, frozen, emitted_by_id, seed_ids, rows


def _selected(ranking, threshold, budget):
    selected = []
    checks = 0
    for item in ranking.ranked:
        checks += 1
        if item.marking_score + 1e-15 < threshold:
            continue
        selected.append(item.candidate.candidate_id)
        if len(selected) == budget:
            break
    return tuple(selected), checks


def _lopo(train_rows):
    choices = []
    for threshold in THRESHOLDS:
        for budget in BUDGETS:
            total_selected = exact = correct_sites = wrong_sites = checks = 0
            valid = True
            for held in range(len(train_rows)):
                fit = tuple(CompletionMarkTrace(
                                row.candidate.descriptor, row.exact, True,
                                row.candidate.frozen_parent_type)
                            for index, rows in enumerate(train_rows)
                            if index != held for row in rows)
                if not fit:
                    valid = False
                    break
                marking = fit_completion_marking(fit)
                ranking = rank_completion_candidates(
                    tuple(row.candidate for row in train_rows[held]), marking)
                selected, fold_checks = _selected(ranking, threshold, budget)
                if not selected:
                    valid = False
                    break
                by_id = {row.candidate.candidate_id: row
                         for row in train_rows[held]}
                chosen = tuple(by_id[item] for item in selected)
                total_selected += len(chosen)
                exact += sum(item.exact for item in chosen)
                correct_sites += len(set().union(*(
                    set(item.emitted) for item in chosen if item.exact)))
                wrong_sites += len(set().union(*(
                    set(item.emitted) for item in chosen if not item.exact)))
                checks += fold_checks
            if valid:
                utility = correct_sites - 4 * wrong_sites
                choices.append(((utility, exact, -wrong_sites,
                                 -checks, threshold, -budget),
                                threshold, budget, total_selected, exact))
    if not choices:
        raise AssertionError("no LOPO marking policy deploys on every patch")
    return max(choices)


def _frequency_ranking(candidates, traces):
    counts = {}
    for row in traces:
        counts.setdefault(row.candidate.macro_id, Counter())[row.exact] += 1
    def score(item):
        values = counts.get(item.macro_id, Counter())
        return (values[True] + 1) / (sum(values.values()) + 2)
    return tuple(sorted(candidates, key=lambda item: (
        -score(item), item.stable_key)))


def _score(name, ordered_ids, checks, emitted_by_id, target, outer_target,
           exact_ids, matched_budget=0):
    proposed = set().union(*(set(emitted_by_id[item]) for item in ordered_ids)) \
        if ordered_ids else set()
    correct = proposed.intersection(target)
    exact = sum(item in exact_ids for item in ordered_ids)
    matched_checks = matched_wrong = 0
    recovered = set()
    for index, item in enumerate(ordered_ids, 1):
        if item in exact_ids:
            recovered.update(emitted_by_id[item])
        else:
            matched_wrong += 1
        matched_checks = index
        if len(recovered) >= matched_budget:
            break
    return PolicyScore(
        name, len(ordered_ids), exact, len(ordered_ids) - exact,
        exact / max(1, len(ordered_ids)), exact / max(1, len(exact_ids)),
        len(proposed), len(correct),
        len(proposed - target), len(correct) / max(1, len(proposed)),
        len(correct) / max(1, len(outer_target)), checks,
        len(ordered_ids) - exact, matched_budget,
        matched_checks if matched_budget else 0,
        matched_wrong if matched_budget else 0)


def evaluate(shuffle_trials=31):
    if shuffle_trials != 31:
        raise ValueError("confirmatory ablation uses exactly 31 shuffles")
    (atoms, train_windows, train_species, train_positions, primitive,
     quotient, parent_map) = _compile()
    train_rows = []
    for center in TRAIN_CENTERS:
        payload = _frontier(
            atoms, primitive, quotient, parent_map, center,
            TRAIN_SEED_RADIUS, TRAIN_TARGET_RADIUS,
            open_training_target=True)
        train_rows.append(payload[-1])
    train_rows = tuple(train_rows)
    choice, threshold, budget, lopo_selected, lopo_exact = _lopo(train_rows)
    all_train_rows = tuple(row for rows in train_rows for row in rows)
    marking = fit_completion_marking(tuple(
        CompletionMarkTrace(row.candidate.descriptor, row.exact, True,
                            row.candidate.frozen_parent_type)
        for row in all_train_rows))
    training_traces = tuple(
        CompletionMarkTrace(row.candidate.descriptor, row.exact, True,
                            row.candidate.frozen_parent_type)
        for row in all_train_rows)

    lower, raw, candidates, emitted_by_id, seed_ids, _ = _frontier(
        atoms, primitive, quotient, parent_map, EVAL_CENTER,
        EVAL_SEED_RADIUS, EVAL_TARGET_RADIUS, open_training_target=False)
    marked_ranking = rank_completion_candidates(candidates, marking)
    marked_ids, marked_checks = _selected(marked_ranking, threshold, budget)
    matched_output = len(marked_ids)
    constant_ranking = rank_completion_candidates(candidates, None)
    constant_ids = tuple(item.candidate.candidate_id
                         for item in constant_ranking.ranked[:matched_output])
    frequency_order = _frequency_ranking(candidates, all_train_rows)
    frequency_ids = tuple(item.candidate_id
                          for item in frequency_order[:matched_output])
    shuffled = []
    for trial in range(shuffle_trials):
        shuffled_marking = fit_completion_marking(
            shuffle_completion_traces_within_strata(
                training_traces, 912_701 + trial))
        ranking = rank_completion_candidates(
            candidates, shuffled_marking)
        shuffled.append(tuple(item.candidate.candidate_id
                              for item in ranking.ranked[:matched_output]))
    eval_digest = marked_ranking.candidate_digest
    identical = (eval_digest == constant_ranking.candidate_digest and
                 all({*ids}.issubset(emitted_by_id) for ids in shuffled) and
                 set(item.candidate_id for item in frequency_order) ==
                 set(item.candidate_id for item in candidates))

    # Sole heldout scorer boundary: every arm above is already immutable.
    target_ids = _ids(atoms, EVAL_CENTER, EVAL_TARGET_RADIUS)
    target = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
              for index in target_ids}
    seed_keys = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
                 for index in seed_ids}
    outer = target - seed_keys
    exact_ids = {item for item, emitted in emitted_by_id.items()
                 if emitted and emitted.issubset(target)}
    prelim = []
    for name, ids, checks in (("marked", marked_ids, marked_checks),
                              ("constant", constant_ids, matched_output),
                              ("frequency", frequency_ids, matched_output)):
        prelim.append(_score(name, ids, checks, emitted_by_id, target, outer,
                             exact_ids))
    shuffle_scores = tuple(_score(
        f"shuffle-{index}", ids, matched_output, emitted_by_id, target, outer,
        exact_ids) for index, ids in enumerate(shuffled))
    matched_budget = min((item.correct_novel_sites for item in
                          (*prelim, *shuffle_scores)), default=0)
    marked, constant, frequency = tuple(_score(
        item.name, ids, checks, emitted_by_id, target, outer, exact_ids,
        matched_budget) for item, ids, checks in zip(
            prelim, (marked_ids, constant_ids, frequency_ids),
            (marked_checks, matched_output, matched_output)))
    shuffle_scores = tuple(_score(
        item.name, ids, matched_output, emitted_by_id, target, outer,
        exact_ids, matched_budget) for item, ids in zip(shuffle_scores, shuffled))
    successes = sum((item.exact_actions >= marked.exact_actions and
                     item.correct_novel_sites >= marked.correct_novel_sites and
                     item.wrong_novel_sites <= marked.wrong_novel_sites)
                    for item in shuffle_scores)
    p_value = (successes + 1) / (shuffle_trials + 1)
    sorted_exact = sorted(item.exact_actions for item in shuffle_scores)
    sorted_correct = sorted(item.correct_novel_sites for item in shuffle_scores)
    train_ids = set().union(*map(set, train_windows))
    separation = min(math.dist(EVAL_CENTER, center) for center in TRAIN_CENTERS)
    gate = (marked.site_precision >= .99 and p_value <= .05 and
            (marked.correct_novel_sites > constant.correct_novel_sites or
             marked.matched_budget_proposal_checks <
             constant.matched_budget_proposal_checks))
    return CdYbPartialCompletionMarkingAblation(
        len(train_positions), len(train_rows), len(all_train_rows),
        tuple(len(rows) for rows in train_rows),
        sum(row.exact for row in all_train_rows),
        tuple(sum(row.exact for row in rows) for rows in train_rows),
        sum(not row.exact for row in all_train_rows), threshold, budget,
        lopo_selected, lopo_exact, len(candidates), len(exact_ids),
        len(exact_ids) / max(1, len(candidates)), eval_digest, identical,
        marked, constant, frequency, shuffle_trials,
        sorted_exact[len(sorted_exact) // 2], max(sorted_exact, default=0),
        sorted_correct[len(sorted_correct) // 2],
        max(sorted_correct, default=0), p_value,
        len(train_ids.intersection(target_ids)), separation,
        separation > TRAIN_TARGET_RADIUS + EVAL_TARGET_RADIUS, True, False,
        True, gate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
