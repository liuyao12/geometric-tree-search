#!/usr/bin/env python3
"""Nested train-only search over compatible two-action IQC antichains."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_action_pair_marking import (
    ActionPairExample, action_pair_adjustment, action_pair_descriptor,
    action_pair_marking_digest, fit_action_pair_marking)
from materials_gcts_incidence_token_marking import score_incidence_descriptor
from materials_gcts_iqc_expanded_development_baseline import (
    FROZEN_FIT, _expanded_groups)
from materials_gcts_iqc_incidence_geometry_selection import _statistics
from materials_gcts_iqc_joint_incidence_graph_preflight import _fit
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER)


SHORTLIST_SIZE = 16
PAIR_GRID = (
    (4, 2, .5, .25),
    (4, 2, .5, .5),
    (8, 3, .5, .5),
    (8, 3, 1., 1.),
    (16, 4, 1., 1.),
)


@dataclass(frozen=True)
class JointPairSpec:
    minimum_support: int
    minimum_groups: int
    shrinkage: float
    pair_mix: float


@dataclass(frozen=True)
class JointPairAudit:
    spec: JointPairSpec
    selected_correct_by_group: tuple[int, ...]
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    supported_tokens_by_fold: tuple[int, ...]
    fold_model_digest: str


@dataclass(frozen=True)
class JointActionPairSearch:
    total_groups: int
    shortlist_size: int
    nested_training_pair_examples_by_fold: tuple[int, ...]
    nested_training_positive_pairs_by_fold: tuple[int, ...]
    heldout_pair_candidates_by_group: tuple[int, ...]
    heldout_exact_pairs_by_group: tuple[int, ...]
    pair_grid: tuple[JointPairSpec, ...]
    audits: tuple[JointPairAudit, ...]
    selected_spec: JointPairSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    additive_baseline_correct_actions: int
    exact_candidate_geometry_changed: bool
    order_independent_antichain_search: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _logit(probability):
    probability = min(1. - 1e-12, max(1e-12, probability))
    return math.log(probability / (1. - probability))


def _ranked(rows, model, limit=SHORTLIST_SIZE):
    return tuple(row for _score, row in sorted((
        (score_incidence_descriptor(model, row.descriptor), row)
        for row in rows), key=lambda item: (
            -item[0], item[1].point, item[1].color))[:limit])


def _compatible(left, right):
    return math.dist(left.point, right.point) >= max(
        left.minimum_distance, right.minimum_distance) - 1e-8


def _pairs(rows):
    return tuple((rows[left], rows[right])
                 for left in range(len(rows))
                 for right in range(left + 1, len(rows))
                 if _compatible(rows[left], rows[right]))


def evaluate() -> JointActionPairSearch:
    groups, _crop_counts = _expanded_groups()
    statistics = _statistics(groups)
    specs = tuple(JointPairSpec(*row) for row in PAIR_GRID)
    training_examples = []
    heldout_pairs = []
    outer_models = []
    additive_correct = []
    for outer_index, outer_rows in enumerate(groups):
        included = tuple(index for index in range(len(groups))
                         if index != outer_index)
        examples = []
        for inner_index in included:
            nested = tuple(index for index in included
                           if index != inner_index)
            model = _fit(statistics, nested, FROZEN_FIT)
            for left, right in _pairs(_ranked(groups[inner_index], model)):
                examples.append(ActionPairExample(
                    inner_index, action_pair_descriptor(left, right),
                    left.successful and right.successful))
        training_examples.append(tuple(examples))
        model = _fit(statistics, included, FROZEN_FIT)
        outer_models.append(model)
        pairs = _pairs(_ranked(outer_rows, model))
        heldout_pairs.append(pairs)
        # The pre-existing greedy baseline is reconstructed for comparison.
        accepted = []
        for row in _ranked(outer_rows, model, len(outer_rows)):
            if any(not _compatible(row, prior) for prior in accepted):
                continue
            accepted.append(row)
            if len(accepted) == 2:
                break
        additive_correct.append(sum(row.successful for row in accepted))

    audits = []
    for spec in specs:
        selected = []
        supported = []
        digests = []
        for outer_index, pairs in enumerate(heldout_pairs):
            marking = fit_action_pair_marking(
                training_examples[outer_index],
                minimum_support=spec.minimum_support,
                minimum_groups=spec.minimum_groups,
                shrinkage=spec.shrinkage)
            supported.append(len(marking.weights))
            digests.append(action_pair_marking_digest(marking))
            scored = []
            for left, right in pairs:
                individual = _logit(score_incidence_descriptor(
                    outer_models[outer_index], left.descriptor)) + _logit(
                    score_incidence_descriptor(
                        outer_models[outer_index], right.descriptor))
                joint = action_pair_adjustment(
                    marking, action_pair_descriptor(left, right))
                scored.append((individual + spec.pair_mix * joint,
                               left, right))
            if not scored:
                raise AssertionError("heldout shortlist has no compatible pair")
            _score, left, right = max(scored, key=lambda item: (
                item[0], tuple(-value for value in item[1].point),
                str(item[1].color), tuple(-value for value in item[2].point),
                str(item[2].color)))
            selected.append((left, right))
        correct_by_group = tuple(sum(row.successful for row in pair)
                                 for pair in selected)
        correct = sum(correct_by_group)
        audits.append(JointPairAudit(
            spec, correct_by_group, correct, 2 * len(groups) - correct,
            correct / (2 * len(groups)),
            sum(value == 2 for value in correct_by_group), tuple(supported),
            hashlib.sha256(repr(tuple(digests)).encode()).hexdigest()))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support,
        -row.spec.pair_mix))
    passed = selected.selected_correct_actions == 2 * len(groups)
    return JointActionPairSearch(
        len(groups), SHORTLIST_SIZE,
        tuple(len(rows) for rows in training_examples),
        tuple(sum(row.successful for row in rows)
              for rows in training_examples),
        tuple(len(rows) for rows in heldout_pairs),
        tuple(sum(left.successful and right.successful
                  for left, right in rows) for rows in heldout_pairs),
        specs, tuple(audits), selected.spec,
        selected.selected_correct_by_group, 2 * len(groups),
        selected.selected_correct_actions, selected.selected_false_actions,
        selected.precision, selected.exact_groups, sum(additive_correct),
        False, True, NEXT_CONFIRMATION_CENTER, False, passed,
        "joint two-action GCTS search passes expanded development" if passed
        else "joint two-action GCTS search remains below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
