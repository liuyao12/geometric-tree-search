#!/usr/bin/env python3
"""Causal local species/absence section on frozen recurrent macro actions."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

from materials_gcts_macro_derivation import _site_key
from materials_gcts_recurrent_macro_diversity_benchmark import (
    _one_boundary_occurrence_per_type)
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)
from materials_gcts_recurrent_macro_executor import (
    FrozenExecutionPolicy, execute_recurrent_macro_program,
    score_recurrent_macro_execution)


ABSENT = "<ABSENT>"


@dataclass(frozen=True)
class SiteSectionSpec:
    neighbors: int
    distance_bin_width: float
    minimum_support: int = 2


@dataclass(frozen=True)
class SiteRecord:
    patch_id: int
    exact: tuple
    shell: tuple
    proposed: tuple
    features: tuple[float, ...]
    label: str


@dataclass(frozen=True)
class SiteSectionAudit:
    training_atoms: int
    fit_patches: tuple[int, ...]
    calibration_patch: int
    specifications_compared: int
    selected_spec: SiteSectionSpec
    selected_train_only: bool
    fit_site_records: int
    fit_label_histogram: tuple[tuple[str, int], ...]
    fit_recolor_or_absence_records: int
    calibration_records: int
    calibration_precision: float
    calibration_recall: float
    selected_alternative_margin: float
    evaluation_macro_placements_frozen_before_target: int
    evaluation_candidate_digest: str
    target_factory_calls: int
    target_opened_after_execution_and_site_prediction: bool
    baseline_correct_atoms: int
    baseline_wrong_atoms: int
    baseline_precision: float
    marked_correct_atoms: int
    marked_wrong_atoms: int
    marked_precision: float
    marked_recall: float
    predicted_recolors: int
    predicted_absences: int
    exact_descriptor_uses: int
    nearest_environment_uses: int
    proposed_backoff_uses: int
    unseen_uses: int
    precision_gate: bool
    improves_baseline: bool
    benchmark_passed: bool
    target_used_during_fit_execution_or_prediction: bool
    descriptor_uses_absolute_frame_family_cell_or_raw_ids: bool
    limitation: str


def _coordinate(key):
    return tuple(value * .03 for value in key[1:])


def _label(species):
    return _site_key((species, (0., 0., 0.)), .03)[0]


def _descriptor(proposed, coordinate, placed, spec, scale):
    nearest = sorted((math.dist(coordinate, point) / scale, species)
                     for species, point in placed)[:spec.neighbors]
    exact = tuple((round(distance / spec.distance_bin_width), species)
                  for distance, species in nearest)
    shells = defaultdict(Counter)
    for distance, species in nearest:
        shells[min(3, int(distance))][species] += 1
    shell = tuple((index, tuple(sorted(counts.items())))
                  for index, counts in sorted(shells.items()))
    vocabulary = tuple(sorted({species for species, _point in placed} |
                              {proposed}))
    features = []
    for species in vocabulary:
        distances = sorted(math.dist(coordinate, point) / scale
                           for label, point in placed if label == species)[:4]
        features.extend(distances + [8.] * (4 - len(distances)))
    return ((proposed, exact), (proposed, shell), (proposed,),
            vocabulary, tuple(features))


def _selection(fixture):
    patch_specific, _minimum, _patch = \
        _one_boundary_occurrence_per_type(fixture)
    calibration_patch = max(item.patch_id
                            for item in fixture.training_frontiers)
    fit = {}
    calibration = []
    for (type_id, patch_id), value in patch_specific.items():
        item = (value[0], patch_id, value[1], value[2], value[3])
        if patch_id == calibration_patch:
            calibration.append(item)
        elif type_id not in fit or item[:3] < fit[type_id][:3]:
            fit[type_id] = item
    return (tuple(fit[key] for key in sorted(fit)),
            tuple(sorted(calibration)), calibration_patch)


def _frontier_records(fixture, selected, spec):
    supports = dict(fixture.program.occurrence_supports)
    outer = {item.patch_id: item for item in fixture.training_frontiers}
    result = []
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
        seed_occurrences = (occurrence,) + neighboring
        seed_sites = tuple(fixture.training_sites[index]
                           for index in sorted(seed_atoms))
        placed = tuple((_label(species), point) for species, point in seed_sites)
        execution = execute_recurrent_macro_program(
            fixture.program, seed_occurrences,
            explicit_seed_sites=seed_sites, boundary=frontier.boundary,
            maximum_waves=1, maximum_accepted_per_wave=256,
            policy=FrozenExecutionPolicy(), trace_rejections=False)
        target = {_site_key(site, .03)[1:]: _site_key(site, .03)[0]
                  for site in frontier.known_target_sites}
        for candidate in execution.eligible_candidates:
            for key in candidate.emitted_site_keys:
                coordinate = _coordinate(key)
                exact, shell, proposed, _vocabulary, features = _descriptor(
                    key[0], coordinate, placed, spec,
                    fixture.program.minimum_distance)
                result.append(SiteRecord(
                    patch_id, exact, shell, proposed, features,
                    target.get(key[1:], ABSENT)))
    return tuple(sorted(set(result), key=repr))


def _fit(records, minimum_support):
    counts = defaultdict(Counter)
    for record in records:
        for key in {record.exact, record.shell, record.proposed}:
            counts[key][record.label] += 1
    table = []
    for key, values in counts.items():
        if sum(values.values()) < minimum_support:
            continue
        label, count = max(values.items(), key=lambda item: (
            item[1], item[0] != ABSENT, item[0]))
        table.append((key, label, count, sum(values.values())))
    return tuple(sorted(table, key=lambda item: repr(item[0])))


def _predict(table, exact, shell, proposed):
    mapping = {key: label for key, label, _count, _total in table}
    for level, key in enumerate((exact, shell, proposed)):
        if key in mapping:
            return mapping[key], level
    return proposed[0], 3


def _distance(left, right):
    if len(left) != len(right):
        return math.inf
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _environment_predict(fit, record, alternative_margin):
    same_proposal = tuple(item for item in fit
                          if item.proposed == record.proposed)
    if not same_proposal:
        return record.proposed[0], False
    nearest = {}
    for item in same_proposal:
        distance = _distance(item.features, record.features)
        prior = nearest.get(item.label)
        if prior is None or distance < prior:
            nearest[item.label] = distance
    proposed = record.proposed[0]
    proposed_distance = nearest.get(proposed, math.inf)
    alternatives = tuple((distance, label) for label, distance in
                         nearest.items() if label != proposed)
    if not alternatives:
        return proposed, False
    alternative_distance, alternative = min(alternatives)
    if alternative_distance < alternative_margin * proposed_distance:
        return alternative, True
    return proposed, True


def _section_predict(fit, table, record, alternative_margin):
    mapping = {key: label for key, label, _count, _total in table}
    if record.exact in mapping:
        return mapping[record.exact], 0
    label, compared = _environment_predict(fit, record, alternative_margin)
    return label, 1 if compared else 3


def _validate(records, fit, table, alternative_margin):
    predicted = tuple(_section_predict(
        fit, table, item, alternative_margin)[0] for item in records)
    accepted = tuple((prediction, item.label)
                     for prediction, item in zip(predicted, records)
                     if prediction != ABSENT)
    correct = sum(left == right for left, right in accepted)
    possible = sum(item.label != ABSENT for item in records)
    return (correct / max(1, len(accepted)),
            correct / max(1, possible))


def _select_spec(fixture, fit_selected, calibration_selected):
    # Predeclared bounded section: eight radial neighbours at quarter-NN
    # resolution.  Calibration evaluates transfer but does not choose among a
    # target-tuned grid; later work can cache raw environments before a wider
    # train-only model-selection sweep.
    options = (SiteSectionSpec(8, .25),)
    evaluated = []
    for spec in options:
        fit = _frontier_records(fixture, fit_selected, spec)
        calibration = _frontier_records(
            fixture, calibration_selected, spec)
        table = _fit(fit, spec.minimum_support)
        for alternative_margin in (.5, .75, 1., 1.25):
            precision, recall = _validate(
                calibration, fit, table, alternative_margin)
            evaluated.append((-precision, -recall, len(table),
                              -alternative_margin, repr(spec), spec, fit,
                              calibration, table))
    (_p, _r, _size, negative_margin, _name, spec, fit, calibration,
     table) = min(evaluated)
    alternative_margin = -negative_margin
    precision, recall = _validate(
        calibration, fit, table, alternative_margin)
    return (options, spec, fit, calibration, table, precision, recall,
            alternative_margin)


def _apply(execution, seed_sites, fit, table, spec, alternative_margin):
    candidates = {item.candidate_id: item
                  for item in execution.eligible_candidates}
    placed = [(_label(species), point) for species, point in seed_sites]
    seed_coordinates = {_site_key(site, .03)[1:] for site in seed_sites}
    emitted = {}
    levels = Counter()
    recolors = absences = 0
    for accepted in execution.accepted:
        candidate = candidates[accepted.candidate_id]
        for key in candidate.emitted_site_keys:
            coordinate_key = key[1:]
            if coordinate_key in seed_coordinates or coordinate_key in emitted:
                continue
            coordinate = _coordinate(key)
            exact, shell, proposed, _vocabulary, features = _descriptor(
                key[0], coordinate, placed, spec,
                execution.frozen_geometry_length_scale)
            record = SiteRecord(-1, exact, shell, proposed, features, ABSENT)
            prediction, level = _section_predict(
                fit, table, record, alternative_margin)
            levels[level] += 1
            if prediction == ABSENT:
                absences += 1
                continue
            recolors += prediction != key[0]
            emitted[coordinate_key] = prediction
            placed.append((prediction, coordinate))
    return emitted, recolors, absences, levels


def evaluate():
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    fit_selected, calibration_selected, calibration_patch = \
        _selection(fixture)
    (options, spec, fit, calibration, table, calibration_precision,
     calibration_recall, alternative_margin) = _select_spec(
            fixture, fit_selected, calibration_selected)
    execution = execute_recurrent_macro_program(
        fixture.program, fixture.seed_occurrences,
        explicit_seed_sites=fixture.explicit_seed_sites,
        boundary=fixture.boundary, maximum_waves=fixture.maximum_waves,
        maximum_accepted_per_wave=fixture.maximum_accepted_per_wave,
        policy=FrozenExecutionPolicy())
    emitted, recolors, absences, levels = _apply(
        execution, fixture.explicit_seed_sites, fit, table, spec,
        alternative_margin)
    frozen_digest = execution.waves[0].candidate_digest
    target_calls = []
    target_calls.append("open")
    target = open_target()
    baseline = score_recurrent_macro_execution(
        execution, target.species, target.positions)
    target_map = {_site_key((species, point), .03)[1:]:
                  _site_key((species, point), .03)[0]
                  for species, point in zip(target.species,
                                             target.positions)}
    seed_coordinates = {_site_key(site, .03)[1:]
                        for site in fixture.explicit_seed_sites}
    target_novel = {key: value for key, value in target_map.items()
                    if key not in seed_coordinates}
    correct = sum(target_novel.get(key) == label
                  for key, label in emitted.items())
    wrong = len(emitted) - correct
    precision = correct / max(1, len(emitted))
    recall = correct / max(1, len(target_novel))
    precision_gate = precision >= .99
    improves = (precision > baseline.precision and
                correct >= baseline.correct_novel_atoms * .9)
    return SiteSectionAudit(
        fixture.training_atoms,
        tuple(sorted({item[1] for item in fit_selected})),
        calibration_patch, len(options), spec, True, len(fit),
        tuple(sorted(Counter(item.label for item in fit).items())),
        sum(item.label != item.proposed[0] for item in fit),
        len(calibration), calibration_precision, calibration_recall,
        alternative_margin,
        len(execution.accepted), frozen_digest, len(target_calls), True,
        baseline.correct_novel_atoms, baseline.wrong_novel_atoms,
        baseline.precision, correct, wrong, precision, recall, recolors,
        absences, levels[0], levels[1], levels[2], levels[3],
        precision_gate, improves, precision_gate and improves,
        execution.target_used_for_proposals_or_ranking, False,
        "The site section changes only colored terminals of an already "
        "frozen macro trace. It is a causal diagnostic, not yet integrated "
        "into branch generation or overlap certificates. A future green "
        "executor must replay the marked terminals self-fed and compare "
        "against label-shuffled sections.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
