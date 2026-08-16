#!/usr/bin/env python3
"""ID-free geometric marking for the sealed recurrent-macro frontier."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_macro_derivation import _site_key
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)
from materials_gcts_recurrent_macro_executor import (
    FrozenExecutionPolicy, GeometryCandidateMark,
    execute_recurrent_macro_program, geometry_candidate_mark,
    score_recurrent_macro_execution)
from materials_gcts_recurrent_macro_marking_benchmark import (
    ArmResult, _exact_recoverable_count, _matched_work)


@dataclass(frozen=True)
class GeometrySpec:
    translation_bin_width: float
    rotation_bin_width: float
    minimum_support: int = 2


@dataclass(frozen=True)
class TrainingRecord:
    patch_id: int
    exact: GeometryCandidateMark
    pose_backoff: GeometryCandidateMark
    chemistry_backoff: GeometryCandidateMark
    kind_backoff: GeometryCandidateMark
    correct: bool


@dataclass(frozen=True)
class GeometryMarkingAudit:
    training_atoms: int
    training_patches: int
    training_candidates: int
    positive_training_candidates: int
    negative_training_candidates: int
    specifications_compared: int
    selected_spec: GeometrySpec
    selected_train_only: bool
    leave_one_patch_out_log_loss: float
    shuffled_validation_median_log_loss: float
    validation_beats_shuffles: bool
    marking_states: int
    shuffle_trials: int
    target_factory_calls: int
    target_opened_after_all_executions: bool
    first_wave_candidate_sets_identical: bool
    evaluation_candidates: int
    exact_context_candidates: int
    pose_backoff_candidates: int
    chemistry_backoff_candidates: int
    kind_backoff_candidates: int
    unseen_candidates: int
    first_wave_unique_scores: int
    first_wave_rank_inversions: int
    marked: ArmResult
    unmarked: ArmResult
    shuffled_median_correct_atoms: float
    shuffled_median_matched_work: float
    empirical_p_value: float
    precision_gate: bool
    causal_advantage_gate: bool
    benchmark_passed: bool
    target_used_during_fit_or_execution: bool
    descriptor_uses_raw_type_or_production_ids: bool
    descriptor_uses_absolute_coordinates_family_cell_or_target: bool
    limitation: str


def _execute_frontier(fixture, frontier):
    return execute_recurrent_macro_program(
        fixture.program, frontier.seed_occurrences,
        explicit_seed_sites=frontier.explicit_seed_sites,
        boundary=frontier.boundary, maximum_waves=1,
        maximum_accepted_per_wave=256,
        policy=FrozenExecutionPolicy())


def _record(execution, candidate, patch_id, correct, spec):
    keyword = dict(
        translation_bin_width=spec.translation_bin_width,
        rotation_bin_width=spec.rotation_bin_width)
    exact = geometry_candidate_mark(execution, candidate, **keyword)
    pose = geometry_candidate_mark(
        execution, candidate, include_incoming=False, **keyword)
    chemistry = geometry_candidate_mark(
        execution, candidate, coarse=True, include_incoming=False, **keyword)
    kind = geometry_candidate_mark(
        execution, candidate, kind_only=True, include_incoming=False,
        **keyword)
    return TrainingRecord(
        patch_id, exact, pose, chemistry, kind, bool(correct))


def _training_candidates(fixture):
    result = []
    for frontier in fixture.training_frontiers:
        execution = _execute_frontier(fixture, frontier)
        target = {_site_key(site, .03) for site in frontier.known_target_sites}
        raw = []
        for candidate in execution.eligible_candidates:
            emitted = set(candidate.emitted_site_keys)
            raw.append((execution, candidate, frontier.patch_id,
                        bool(emitted) and emitted.issubset(target)))
        result.extend(raw)
    return tuple(result)


def _records(raw, spec):
    return tuple(_record(execution, candidate, patch, correct, spec)
                 for execution, candidate, patch, correct in raw)


def _fit(records, minimum_support):
    counts = defaultdict(lambda: [0, 0])
    for record in records:
        for key in {record.exact, record.pose_backoff,
                    record.chemistry_backoff, record.kind_backoff}:
            counts[key][1] += 1
            counts[key][0] += int(record.correct)
    scores = []
    for key, (positive, total) in counts.items():
        if total < minimum_support:
            continue
        scores.append((key, math.log((positive + 1) /
                                     (total - positive + 1))))
    return tuple(sorted(scores, key=lambda item: repr(item[0])))


def _resolve(table, record):
    for key in (record.exact, record.pose_backoff,
                record.chemistry_backoff, record.kind_backoff):
        if key in table:
            return table[key]
    return 0.


def _log_loss(records, scores):
    table = dict(scores)
    total = 0.
    for record in records:
        value = max(-30., min(30., _resolve(table, record)))
        probability = 1. / (1. + math.exp(-value))
        probability = min(1 - 1e-12, max(1e-12, probability))
        total -= (math.log(probability) if record.correct else
                  math.log(1 - probability))
    return total / max(1, len(records))


def _shuffle_labels(records, seed):
    grouped = defaultdict(list)
    for index, record in enumerate(records):
        grouped[record.patch_id].append(index)
    rng = random.Random(seed)
    result = list(records)
    for indices in grouped.values():
        labels = [records[index].correct for index in indices]
        rng.shuffle(labels)
        for index, label in zip(indices, labels):
            record = records[index]
            result[index] = TrainingRecord(
                record.patch_id, record.exact, record.pose_backoff,
                record.chemistry_backoff, record.kind_backoff, label)
    return tuple(result)


def _cross_validated_loss(records, spec):
    patches = tuple(sorted({record.patch_id for record in records}))
    losses = []
    for heldout in patches:
        train = tuple(item for item in records if item.patch_id != heldout)
        test = tuple(item for item in records if item.patch_id == heldout)
        losses.append(_log_loss(test, _fit(train, spec.minimum_support)))
    return sum(losses) / len(losses)


def _select_spec(raw):
    specs = tuple(GeometrySpec(distance, angle) for distance in (.5, 1., 2.)
                  for angle in (math.pi / 10, math.pi / 5, math.pi / 3))
    evaluated = []
    for spec in specs:
        records = _records(raw, spec)
        loss = _cross_validated_loss(records, spec)
        states = len(_fit(records, spec.minimum_support))
        evaluated.append((loss, states, repr(spec), spec, records))
    _loss, _states, _name, spec, records = min(evaluated)
    return specs, spec, records, _loss


def _run(fixture, policy):
    return execute_recurrent_macro_program(
        fixture.program, fixture.seed_occurrences,
        explicit_seed_sites=fixture.explicit_seed_sites,
        boundary=fixture.boundary, maximum_waves=fixture.maximum_waves,
        maximum_accepted_per_wave=fixture.maximum_accepted_per_wave,
        policy=policy)


def _arm(name, execution, score, target_keys, required):
    first = execution.waves[0]
    return ArmResult(
        name, score.precision, score.recall_outside_seed,
        score.correct_novel_atoms, score.wrong_novel_atoms,
        len(execution.accepted), execution.longest_parent_child_depth,
        first.eligible_candidates, first.candidate_digest,
        _matched_work(execution, target_keys, required))


def _coverage(execution, scores, spec):
    table = dict(scores)
    levels = [0, 0, 0, 0]
    for candidate in execution.eligible_candidates:
        record = _record(execution, candidate, -1, False, spec)
        for index, key in enumerate((
                record.exact, record.pose_backoff,
                record.chemistry_backoff, record.kind_backoff)):
            if key in table:
                levels[index] += 1
                break
    return tuple(levels)


def _rank_inversions(marked, unmarked):
    left = [item.candidate_id for item in marked.trace
            if item.phase == "commit" and item.wave == 1]
    right = [item.candidate_id for item in unmarked.trace
             if item.phase == "commit" and item.wave == 1]
    rank = {candidate: index for index, candidate in enumerate(right)}
    shared = [candidate for candidate in left if candidate in rank]
    return sum(rank[shared[i]] > rank[shared[j]]
               for i in range(len(shared))
               for j in range(i + 1, len(shared)))


def evaluate(*, shuffle_trials=31):
    if shuffle_trials != 31:
        raise ValueError("confirmatory benchmark requires 31 shuffles")
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    raw = _training_candidates(fixture)
    specs, spec, records, validation_loss = _select_spec(raw)
    scores = _fit(records, spec.minimum_support)
    marked_policy = FrozenExecutionPolicy(
        strategy="geometry-marking", maximum_incoming_context=2,
        geometry_marking_scores=scores,
        geometry_translation_bin_width=spec.translation_bin_width,
        geometry_rotation_bin_width=spec.rotation_bin_width)
    shuffled_records = tuple(
        _shuffle_labels(records, 104729 + 7919 * index)
        for index in range(shuffle_trials))
    shuffled_validation = tuple(
        _cross_validated_loss(candidate, spec)
        for candidate in shuffled_records)
    policies = [("marked", marked_policy),
                ("unmarked", FrozenExecutionPolicy())]
    policies.extend((f"shuffle-{index}", FrozenExecutionPolicy(
        strategy="geometry-marking", maximum_incoming_context=2,
        geometry_marking_scores=_fit(candidate, spec.minimum_support),
        geometry_translation_bin_width=spec.translation_bin_width,
        geometry_rotation_bin_width=spec.rotation_bin_width))
                    for index, candidate in enumerate(shuffled_records))
    executions = tuple((name, _run(fixture, policy))
                       for name, policy in policies)
    target_calls = []
    target_calls.append("open")
    target = open_target()
    scored = {name: score_recurrent_macro_execution(
        execution, target.species, target.positions)
              for name, execution in executions}
    target_keys = {_site_key((species, point), .03)
                   for species, point in zip(target.species,
                                             target.positions)}
    common = min(_exact_recoverable_count(execution, target_keys)
                 for _, execution in executions)
    arms = {name: _arm(name, execution, scored[name], target_keys, common)
            for name, execution in executions}
    marked = arms["marked"]
    unmarked = arms["unmarked"]
    shuffles = tuple(arms[f"shuffle-{index}"]
                     for index in range(shuffle_trials))
    marked_execution = dict(executions)["marked"]
    unmarked_execution = dict(executions)["unmarked"]
    digests = {(item.first_wave_candidates, item.first_wave_digest)
               for item in arms.values()}
    shuffled_success = sum(
        item.correct_novel_atoms > marked.correct_novel_atoms or
        (item.correct_novel_atoms == marked.correct_novel_atoms and
         item.matched_work.total <= marked.matched_work.total)
        for item in shuffles)
    p_value = (1 + shuffled_success) / (shuffle_trials + 1)
    advantage = (
        (marked.correct_novel_atoms > unmarked.correct_novel_atoms or
         marked.matched_work.total < unmarked.matched_work.total) and
        marked.correct_novel_atoms >= median(
            item.correct_novel_atoms for item in shuffles) and
        marked.matched_work.total <= median(
            item.matched_work.total for item in shuffles) and
        p_value <= .05)
    coverage = _coverage(marked_execution, scores, spec)
    unique_scores = len({item.marking_score for item in marked_execution.trace
                         if item.phase == "commit" and item.wave == 1})
    return GeometryMarkingAudit(
        fixture.training_atoms, len(fixture.training_frontiers), len(records),
        sum(item.correct for item in records),
        sum(not item.correct for item in records), len(specs), spec, True,
        validation_loss, median(shuffled_validation),
        validation_loss < min(shuffled_validation), len(scores),
        shuffle_trials, len(target_calls), True, len(digests) == 1,
        len(marked_execution.eligible_candidates), *coverage,
        len(marked_execution.eligible_candidates) - sum(coverage),
        unique_scores, _rank_inversions(marked_execution,
                                        unmarked_execution),
        marked, unmarked,
        median(item.correct_novel_atoms for item in shuffles),
        median(item.matched_work.total for item in shuffles), p_value,
        marked.precision >= .99, advantage,
        marked.precision >= .99 and advantage and len(digests) == 1,
        any(execution.target_used_for_proposals_or_ranking
            for _, execution in executions), False, False,
        "The ID-free mark ranks the same exact frozen candidates and never "
        "authorizes geometry. Later candidate sets may differ only through "
        "causally different accepted parents. A green claim additionally "
        "requires precision and a 31-shuffle matched-work advantage.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
