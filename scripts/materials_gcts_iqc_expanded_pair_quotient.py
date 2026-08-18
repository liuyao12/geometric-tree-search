#!/usr/bin/env python3
"""Audit bounded pair-interaction graph values on 18 disjoint IQC nuclei."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_incidence_pair_marking import (
    IncidencePairSpec, fit_incidence_pair_group_statistics,
    incidence_pair_adjustment, incidence_pair_group_statistics,
    incidence_pair_marking_digest)
from materials_gcts_incidence_token_marking import (
    IncidenceTokenExample, score_incidence_descriptor)
from materials_gcts_iqc_expanded_development_baseline import (
    FROZEN_FIT, _expanded_groups)
from materials_gcts_iqc_incidence_geometry_selection import (
    _ranked_antichain, _statistics)
from materials_gcts_iqc_joint_incidence_graph_preflight import _fit
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


SUMMARY_FAMILY_PAIRS = (
    ("coarse-role", "role-occupied-message-graph"),
    ("predicted-colors", "role-occupied-message-graph"),
    ("occupied-count", "role-occupied-message-graph"),
    ("coarse-role", "predicted-colors"),
    ("coarse-role", "occupied-count"),
    ("predicted-colors", "occupied-count"),
    ("neighbor-colors", "role-occupied-message-graph"),
    ("role-support", "role-occupied-message-graph"),
)
PAIR_GRID = tuple(IncidencePairSpec(
    SUMMARY_FAMILY_PAIRS, support, groups, shrinkage, 1., mix)
    for support, groups, shrinkage, mix in (
        (4, 2, .5, .25),
        (8, 3, .5, .5),
        (16, 3, .5, .5),
        (32, 4, .5, 1.),
        (64, 5, .5, 1.),
    ))


@dataclass(frozen=True)
class PairAudit:
    spec: IncidencePairSpec
    supported_pairs_by_fold: tuple[int, ...]
    fold_model_digest: str
    selected_correct_by_group: tuple[int, ...]
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class ExpandedPairQuotient:
    total_groups: int
    pair_grid: tuple[IncidencePairSpec, ...]
    audits: tuple[PairAudit, ...]
    selected_spec: IncidencePairSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    additive_baseline_correct_actions: int
    additive_baseline_exact_groups: int
    exact_candidate_geometry_changed: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _logit(probability):
    probability = min(1. - 1e-12, max(1e-12, probability))
    return math.log(probability / (1. - probability))


def evaluate() -> ExpandedPairQuotient:
    groups, _crop_counts = _expanded_groups()
    token_statistics = _statistics(groups)
    examples = tuple(tuple(IncidenceTokenExample(
        row.group, row.descriptor, row.successful) for row in group)
        for group in groups)
    pair_statistics = incidence_pair_group_statistics(
        examples, family_pairs=SUMMARY_FAMILY_PAIRS)
    audits = []
    additive_correct = []
    for spec in PAIR_GRID:
        selected = []
        supported = []
        digests = []
        for heldout_index, rows in enumerate(groups):
            included = tuple(index for index in range(len(groups))
                             if index != heldout_index)
            additive = _fit(token_statistics, included, FROZEN_FIT)
            pairs = fit_incidence_pair_group_statistics(
                pair_statistics, included, spec=spec)
            supported.append(sum(
                row.total >= spec.minimum_support and
                row.independent_groups >= spec.minimum_groups
                for row in pairs.evidence.values()))
            digests.append(incidence_pair_marking_digest(pairs))
            scored = tuple((
                _logit(score_incidence_descriptor(
                    additive, row.descriptor)) +
                incidence_pair_adjustment(pairs, row.descriptor), row)
                for row in rows)
            selected.append(_ranked_antichain(scored, ACTIONS_PER_NUCLEUS))
            if spec == PAIR_GRID[0]:
                additive_correct.append(sum(row.successful for row in
                    _ranked_antichain(tuple((score_incidence_descriptor(
                        additive, row.descriptor), row) for row in rows),
                                      ACTIONS_PER_NUCLEUS)))
        correct_by_group = tuple(sum(row.successful for row in group)
                                 for group in selected)
        correct = sum(correct_by_group)
        total = sum(map(len, selected))
        audits.append(PairAudit(
            spec, tuple(supported), hashlib.sha256(repr(tuple(
                digests)).encode()).hexdigest(), correct_by_group, correct,
            total - correct, correct / total if total else 0.,
            sum(value == ACTIONS_PER_NUCLEUS for value in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support,
        -row.spec.additive_mix))
    total = 2 * len(groups)
    passed = selected.selected_correct_actions == total
    return ExpandedPairQuotient(
        len(groups), PAIR_GRID, tuple(audits), selected.spec,
        selected.selected_correct_by_group, total,
        selected.selected_correct_actions, selected.selected_false_actions,
        selected.precision, selected.exact_groups, sum(additive_correct),
        sum(value == ACTIONS_PER_NUCLEUS for value in additive_correct),
        False, NEXT_CONFIRMATION_CENTER, False, passed,
        "pair-interaction graph value passes expanded development" if passed
        else "pair-interaction graph value remains below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
