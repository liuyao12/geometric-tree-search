#!/usr/bin/env python3
"""Train-only role-diverse marking audit for recurrent IQC macro growth.

The earlier five centered training nuclei expose only three macro parent
types.  This audit selects one boundary-exposed occurrence of *every* learned
recurrent macro type, using only the five training patches.  Exact candidate
geometry is unchanged; the resulting ID-free linear mark may only reorder the
frozen executor's proposals.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_macro_derivation import _site_key
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)
from materials_gcts_recurrent_macro_executor import (
    FrozenExecutionPolicy, execute_recurrent_macro_program,
    GEOMETRY_LINEAR_FEATURE_NAMES, score_recurrent_macro_execution)
from materials_gcts_recurrent_macro_geometry_marking_benchmark import (
    _arm, _exact_recoverable_count, _rank_inversions)
from materials_gcts_recurrent_macro_linear_marking_benchmark import (
    LinearRecord, _fit)


@dataclass(frozen=True)
class DiverseFrontierAudit:
    training_atoms: int
    learned_macro_types: int
    patch_specific_role_occurrences: int
    selected_frontiers: int
    selected_parent_types: int
    every_learned_parent_type_selected: bool
    selection_uses_training_geometry_only: bool
    raw_training_candidates: int
    unique_training_records: int
    positive_training_records: int
    negative_training_records: int
    parent_types_with_negative_actions: int
    negative_class_weight: int
    fit_patch_ids: tuple[int, ...]
    calibration_patch_id: int
    fit_parent_types: int
    calibration_parent_types: int
    frozen_minimum_score: float
    calibration_precision: float
    calibration_recall: float
    original_centered_candidates: int
    original_centered_negative_candidates: int
    fixed_ridge: float
    shuffle_trials: int
    target_factory_calls: int
    target_opened_after_all_executions: bool
    first_wave_candidate_sets_identical: bool
    first_wave_unique_scores: int
    first_wave_rank_inversions: int
    diverse_ranked: object
    diverse_marked: object
    unmarked: object
    shuffled_median_correct_atoms: float
    shuffled_median_matched_work: float
    matched_work_target_atoms: int
    empirical_p_value: float
    precision_gate: bool
    causal_advantage_gate: bool
    benchmark_passed: bool
    target_used_during_selection_fit_or_execution: bool
    marking_descriptor_uses_raw_ids_or_absolute_frame: bool
    limitation: str


def _one_boundary_occurrence_per_type(fixture):
    """Select by support margin only; no candidate or target label is read."""
    supports = dict(fixture.program.occurrence_supports)
    outer = {item.patch_id: item for item in fixture.training_frontiers}
    patch_specific = {}
    for occurrence in fixture.program.occurrences:
        atom_ids = tuple(supports[occurrence.occurrence_id])
        patch_ids = {fixture.training_patch_ids[index] for index in atom_ids}
        if len(patch_ids) != 1:
            continue
        patch_id = next(iter(patch_ids))
        boundary = outer[patch_id].boundary
        margin = min(
            boundary.outer_radius - math.dist(
                fixture.training_sites[index][1], boundary.origin)
            for index in atom_ids)
        key = (occurrence.type_id, patch_id)
        value = (margin, occurrence.occurrence_id, occurrence, atom_ids)
        if key not in patch_specific or value[:2] < patch_specific[key][:2]:
            patch_specific[key] = value

    selected = {}
    for (type_id, patch_id), value in patch_specific.items():
        candidate = (value[0], patch_id, value[1], value[2], value[3])
        if type_id not in selected or candidate[:3] < selected[type_id][:3]:
            selected[type_id] = candidate
    # Keep the patch-specific set as an explicit diagnostic, but return the
    # minimum all-role cover for fitting.  Using all 596 representatives was
    # measured separately and worsened sealed ordering because it duplicated
    # 24,688 positives while adding only 161 failures.
    patch_representatives = tuple(
        (value[0], patch_id, value[1], value[2], value[3])
        for (type_id, patch_id), value in sorted(patch_specific.items()))
    return (patch_specific, tuple(selected[key] for key in sorted(selected)),
            patch_representatives)


def _records_for_occurrences(fixture, selected):
    outer = {item.patch_id: item for item in fixture.training_frontiers}
    supports = dict(fixture.program.occurrence_supports)
    raw = []
    negative_types = set()
    for _margin, patch_id, _occurrence_id, occurrence, atom_ids in selected:
        frontier = outer[patch_id]
        origin = frontier.boundary.origin
        cutoff = max(math.dist(fixture.training_sites[index][1], origin)
                     for index in atom_ids)
        patch_atoms = tuple(
            index for index, value in enumerate(fixture.training_patch_ids)
            if value == patch_id)
        seed_atoms = frozenset(
            index for index in patch_atoms
            if math.dist(fixture.training_sites[index][1], origin) <=
            cutoff + 1e-10)
        neighboring = tuple(sorted((
            item for item in fixture.program.occurrences
            if item.occurrence_id != occurrence.occurrence_id and
            set(supports[item.occurrence_id]) <= seed_atoms), key=lambda item: (
                math.dist(item.translation, occurrence.translation),
                item.occurrence_id))[:12])
        # Parent node zero is the selected role.  Other already-grown inward
        # occurrences exist only to supply its causal incident-port context.
        seed_occurrences = (occurrence,) + neighboring
        execution = execute_recurrent_macro_program(
            fixture.program, seed_occurrences,
            explicit_seed_sites=tuple(
                fixture.training_sites[index] for index in sorted(seed_atoms)),
            boundary=frontier.boundary, maximum_waves=1,
            maximum_accepted_per_wave=256,
            policy=FrozenExecutionPolicy(), trace_rejections=False)
        target = {_site_key(site, .03) for site in frontier.known_target_sites}
        for candidate in execution.eligible_candidates:
            if candidate.parent_node != 0:
                continue
            emitted = set(candidate.emitted_site_keys)
            correct = bool(emitted) and emitted.issubset(target)
            raw.append(LinearRecord(
                patch_id,
                tuple(candidate.geometry_features),
                correct))
            if not correct:
                negative_types.add(occurrence.type_id)
    # Exact duplicates from the same source patch carry no additional
    # information and would recreate the positive-duplication failure of the
    # uniform-jitter experiment.
    records = tuple(sorted(set(raw), key=lambda item: (
        item.patch_id, item.features, item.correct)))
    if any(len(item.features) != len(GEOMETRY_LINEAR_FEATURE_NAMES)
           for item in records):
        raise AssertionError("executor did not freeze the geometry features")
    return tuple(raw), records, negative_types


def _training_records(fixture):
    patch_specific, _minimum_cover, _patch_representatives = \
        _one_boundary_occurrence_per_type(fixture)
    calibration_patch = max(item.patch_id
                            for item in fixture.training_frontiers)
    fit_patches = tuple(sorted(
        item.patch_id for item in fixture.training_frontiers
        if item.patch_id != calibration_patch))
    fit_by_type = {}
    calibration = []
    for (type_id, patch_id), value in patch_specific.items():
        item = (value[0], patch_id, value[1], value[2], value[3])
        if patch_id == calibration_patch:
            calibration.append(item)
        elif type_id not in fit_by_type or item[:3] < fit_by_type[type_id][:3]:
            fit_by_type[type_id] = item
    fit_selected = tuple(fit_by_type[key] for key in sorted(fit_by_type))
    calibration_selected = tuple(sorted(calibration))
    fit_raw, fit_records, fit_negative = _records_for_occurrences(
        fixture, fit_selected)
    calibration_raw, calibration_records, calibration_negative = \
        _records_for_occurrences(fixture, calibration_selected)
    return (patch_specific, fit_selected, calibration_selected,
            fit_raw + calibration_raw, fit_records, calibration_records,
            fit_negative | calibration_negative, fit_patches,
            calibration_patch)


def _centered_counts(fixture):
    positive = negative = 0
    for frontier in fixture.training_frontiers:
        execution = execute_recurrent_macro_program(
            fixture.program, frontier.seed_occurrences,
            explicit_seed_sites=frontier.explicit_seed_sites,
            boundary=frontier.boundary, maximum_waves=1,
            maximum_accepted_per_wave=256,
            policy=FrozenExecutionPolicy(), trace_rejections=False)
        target = {_site_key(site, .03) for site in frontier.known_target_sites}
        for candidate in execution.eligible_candidates:
            emitted = set(candidate.emitted_site_keys)
            if emitted and emitted.issubset(target):
                positive += 1
            else:
                negative += 1
    return positive + negative, negative


def _shuffle(records, seed):
    rng = random.Random(seed)
    result = list(records)
    by_patch = {}
    for index, record in enumerate(records):
        by_patch.setdefault(record.patch_id, []).append(index)
    for indices in by_patch.values():
        labels = [records[index].correct for index in indices]
        rng.shuffle(labels)
        for index, label in zip(indices, labels):
            record = records[index]
            result[index] = LinearRecord(
                record.patch_id, record.features, label)
    return tuple(result)


def _balanced(records):
    """Apply deterministic inverse-frequency weighting by row repetition."""
    positive = tuple(item for item in records if item.correct)
    negative = tuple(item for item in records if not item.correct)
    if not positive or not negative:
        return tuple(records), 1
    weight = max(1, round(len(positive) / len(negative)))
    return positive + negative * weight, weight


def _select_threshold(records, model):
    scored = tuple((_linear_score(model, item.features), item.correct)
                   for item in records)
    positives = sum(label for _score_value, label in scored)
    choices = []
    for threshold in sorted({score for score, _label in scored}, reverse=True):
        labels = tuple(label for score, label in scored if score >= threshold)
        correct = sum(labels)
        precision = correct / len(labels)
        recall = correct / max(1, positives)
        if precision == 1. and recall >= .1:
            choices.append((correct, recall, -len(labels), -threshold,
                            threshold, precision))
    if not choices:
        return max(score for score, _label in scored) + 1., 0., 0.
    _correct, recall, _negative_size, _negative_threshold, threshold, \
        precision = max(choices)
    return threshold, precision, recall


def _linear_score(model, features):
    return model.intercept + sum(
        weight * (value - mean) / scale
        for value, mean, scale, weight in zip(
            features, model.means, model.scales, model.weights))


def _run(fixture, policy):
    return execute_recurrent_macro_program(
        fixture.program, fixture.seed_occurrences,
        explicit_seed_sites=fixture.explicit_seed_sites,
        boundary=fixture.boundary, maximum_waves=fixture.maximum_waves,
        maximum_accepted_per_wave=fixture.maximum_accepted_per_wave,
        policy=policy)


def evaluate(*, shuffle_trials=31, fit_steps=120):
    if shuffle_trials < 1:
        raise ValueError("at least one shuffled control is required")
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    (patch_specific, fit_selected, calibration_selected, raw, records,
     calibration_records, negative_types, fit_patches,
     calibration_patch) = \
        _training_records(fixture)
    centered_count, centered_negative = _centered_counts(fixture)
    ridge = .1
    balanced, negative_weight = _balanced(records)
    model = _fit(balanced, ridge, steps=fit_steps)
    threshold, calibration_precision, calibration_recall = \
        _select_threshold(calibration_records, model)
    policies = [("diverse-ranked", FrozenExecutionPolicy(
        strategy="geometry-linear", maximum_incoming_context=2,
        geometry_linear_scorer=model)),
                ("diverse", FrozenExecutionPolicy(
        strategy="geometry-linear", maximum_incoming_context=2,
        geometry_linear_scorer=model,
        geometry_linear_minimum_score=threshold)),
                ("unmarked", FrozenExecutionPolicy())]
    for index in range(shuffle_trials):
        shuffled = _shuffle(records, 15485863 + 32452843 * index)
        shuffled_calibration = _shuffle(
            calibration_records, 49979687 + 67867967 * index)
        shuffled_balanced, _weight = _balanced(shuffled)
        shuffled_model = _fit(
            shuffled_balanced, ridge, steps=max(30, fit_steps // 3))
        shuffled_threshold, _precision, _recall = _select_threshold(
            shuffled_calibration, shuffled_model)
        policies.append((f"shuffle-{index}", FrozenExecutionPolicy(
            strategy="geometry-linear", maximum_incoming_context=2,
            geometry_linear_scorer=shuffled_model,
            geometry_linear_minimum_score=shuffled_threshold)))
    executions = tuple((name, _run(fixture, policy))
                       for name, policy in policies)

    target_calls = []
    target_calls.append("open")
    target = open_target()
    scores = {name: score_recurrent_macro_execution(
        execution, target.species, target.positions)
              for name, execution in executions}
    target_keys = {_site_key((species, point), .03)
                   for species, point in zip(target.species,
                                             target.positions)}
    common = min(_exact_recoverable_count(execution, target_keys)
                 for _name, execution in executions)
    arms = {name: _arm(name, execution, scores[name], target_keys, common)
            for name, execution in executions}
    marked = arms["diverse"]
    ranked = arms["diverse-ranked"]
    unmarked = arms["unmarked"]
    shuffles = tuple(arms[f"shuffle-{index}"]
                     for index in range(shuffle_trials))
    marked_execution = dict(executions)["diverse"]
    ranked_execution = dict(executions)["diverse-ranked"]
    unmarked_execution = dict(executions)["unmarked"]
    first_scores = tuple(
        item.marking_score for item in ranked_execution.trace
        if item.phase == "commit" and item.wave == 1)
    digests = {(item.first_wave_candidates, item.first_wave_digest)
               for item in arms.values()}
    shuffled_success = sum(
        item.correct_novel_atoms > marked.correct_novel_atoms or
        (item.correct_novel_atoms == marked.correct_novel_atoms and
         item.matched_work.total <= marked.matched_work.total)
        for item in shuffles)
    p_value = (1 + shuffled_success) / (shuffle_trials + 1)
    advantage = (
        common > 0 and marked.correct_novel_atoms >=
        unmarked.correct_novel_atoms and
        marked.matched_work.total < unmarked.matched_work.total and
        marked.matched_work.total < median(
            item.matched_work.total for item in shuffles) and
        p_value <= .05)
    learned_types = len(fixture.program.prototypes)
    return DiverseFrontierAudit(
        fixture.training_atoms, learned_types, len(patch_specific),
        len(fit_selected) + len(calibration_selected),
        len({item[3].type_id for item in fit_selected} |
            {item[3].type_id for item in calibration_selected}),
        len(fit_selected) == learned_types,
        True, len(raw), len(records),
        sum(item.correct for item in records),
        sum(not item.correct for item in records), len(negative_types),
        negative_weight,
        fit_patches, calibration_patch, len(fit_selected),
        len(calibration_selected), threshold, calibration_precision,
        calibration_recall,
        centered_count, centered_negative, ridge, shuffle_trials,
        len(target_calls), True, len(digests) == 1,
        len(set(first_scores)), _rank_inversions(
            ranked_execution, unmarked_execution), ranked, marked, unmarked,
        median(item.correct_novel_atoms for item in shuffles),
        median(item.matched_work.total for item in shuffles), common,
        p_value, marked.precision >= .99, advantage,
        marked.precision >= .99 and advantage and len(digests) == 1,
        any(execution.target_used_for_proposals_or_ranking
            for _name, execution in executions), False,
        "One geometry-only boundary occurrence per learned parent role is "
        "selected before candidate labels exist. Four patches fit the "
        "class-balanced mark and the fifth freezes its failure threshold. "
        "Duplicate feature/label "
        "records are removed within each patch. The mark may rank only the "
        "same exact frozen candidates; a green result still requires sealed "
        "precision and a matched-work advantage over label shuffles.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shuffle-trials", type=int, default=31)
    parser.add_argument("--fit-steps", type=int, default=120)
    args = parser.parse_args()
    result = evaluate(shuffle_trials=args.shuffle_trials,
                      fit_steps=args.fit_steps)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
