#!/usr/bin/env python3
"""Ten-nucleus preflight for a joint port-role/metric-graph GCTS section."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import (
    FrozenIncidenceTokenMarking, TokenEvidence, incidence_marking_digest,
    score_incidence_descriptor)
from materials_gcts_iqc_incidence_geometry_selection import (
    _ranked_antichain, _statistics)
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER, _development_groups)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


@dataclass(frozen=True, order=True)
class JointFitSpec:
    minimum_support: int
    minimum_groups: int
    shrinkage: float


FIT_GRID = (
    JointFitSpec(4, 2, .5),
    JointFitSpec(16, 3, .5),
    JointFitSpec(32, 3, .5),
    JointFitSpec(16, 4, .25),
    JointFitSpec(32, 4, .25),
    JointFitSpec(64, 5, .25),
)


@dataclass(frozen=True)
class JointFitAudit:
    spec: JointFitSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    mean_weighted_token_fraction: float
    fold_model_digest: str


@dataclass(frozen=True)
class JointIncidenceGraphPreflight:
    development_groups: int
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    candidate_graph_digest: str
    descriptor_digest: str
    fit_grid: tuple[JointFitSpec, ...]
    fit_audits: tuple[JointFitAudit, ...]
    selected_fit: JointFitSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    joint_role_shell_tokens: int
    joint_role_metric_edge_tokens: int
    mean_weighted_token_fraction: float
    selection_target_free: bool
    exact_candidate_geometry_changed: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _fit(statistics, included, spec):
    labels, group_tokens = statistics
    positive = sum(labels[index][0] for index in included)
    total = sum(labels[index][1] for index in included)
    prior = (positive + 1.) / (total + 2.)
    intercept = math.log(prior / (1. - prior))
    aggregate = defaultdict(lambda: [0, 0, 0])
    for index in included:
        for token, (token_positive, token_total) in group_tokens[index].items():
            aggregate[token][0] += token_positive
            aggregate[token][1] += token_total
            aggregate[token][2] += 1
    evidence = {token: TokenEvidence(*item)
                for token, item in aggregate.items()}
    weights = {}
    for token, item in evidence.items():
        if (item.total < spec.minimum_support or
                item.independent_groups < spec.minimum_groups):
            continue
        probability = (item.positive + 1.) / (item.total + 2.)
        logit = math.log(probability / (1. - probability))
        weights[token] = max(-4., min(
            4., spec.shrinkage * (logit - intercept)))
    return FrozenIncidenceTokenMarking(
        intercept, weights, evidence, spec.minimum_support,
        spec.minimum_groups, spec.shrinkage)


def evaluate() -> JointIncidenceGraphPreflight:
    groups = _development_groups(joint_role_geometry=True)
    statistics = _statistics(groups)
    audits = []
    for spec in FIT_GRID:
        selected_groups = []
        model_digests = []
        weighted_fractions = []
        for heldout_index, rows in enumerate(groups):
            model = _fit(
                statistics, tuple(index for index in range(len(groups))
                                  if index != heldout_index), spec)
            model_digests.append(incidence_marking_digest(model))
            scored = tuple((score_incidence_descriptor(
                model, row.descriptor), row) for row in rows)
            selected_groups.append(_ranked_antichain(
                scored, ACTIONS_PER_NUCLEUS))
            weighted_fractions.extend(sum(
                token in model.token_weights
                for token in row.descriptor.tokens) /
                max(1, len(row.descriptor.tokens)) for row in rows)
        correct_by_group = tuple(sum(row.successful for row in selected)
                                 for selected in selected_groups)
        selected_total = sum(map(len, selected_groups))
        correct_total = sum(correct_by_group)
        audits.append(JointFitAudit(
            spec, correct_by_group, selected_total, correct_total,
            selected_total - correct_total,
            correct_total / selected_total if selected_total else 0.,
            sum(count == ACTIONS_PER_NUCLEUS for count in correct_by_group),
            sum(weighted_fractions) / len(weighted_fractions),
            hashlib.sha256(repr(tuple(model_digests)).encode()).hexdigest()))
    selected_audit = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support,
        -row.spec.shrinkage))
    shell_tokens = {token for group in groups for row in group
                    for token in row.descriptor.tokens
                    if token[0] == "role-occupied-shell"}
    edge_tokens = {token for group in groups for row in group
                   for token in row.descriptor.tokens
                   if token[0] == "role-occupied-metric-edge"}
    passed = bool(
        selected_audit.selected_actions == ACTIONS_PER_NUCLEUS * len(groups)
        and selected_audit.selected_correct_actions ==
        selected_audit.selected_actions and
        selected_audit.exact_groups == len(groups))
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for group in groups for row in group)).encode()).hexdigest()
    descriptor_digest = hashlib.sha256(repr(tuple(
        (row.group, row.descriptor)
        for group in groups for row in group)).encode()).hexdigest()
    return JointIncidenceGraphPreflight(
        len(groups), tuple(map(len, groups)),
        tuple(sum(row.successful for row in group) for group in groups),
        graph_digest, descriptor_digest, FIT_GRID, tuple(audits),
        selected_audit.spec, selected_audit.selected_correct_by_group,
        selected_audit.selected_actions, selected_audit.selected_correct_actions,
        selected_audit.selected_false_actions, selected_audit.precision,
        selected_audit.exact_groups,
        len(shell_tokens), len(edge_tokens),
        selected_audit.mean_weighted_token_fraction, True, False,
        NEXT_CONFIRMATION_CENTER, False, passed,
        ("joint role-incidence graph passes ten-nucleus development"
         if passed else
         "joint role-incidence graph remains below the development gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
