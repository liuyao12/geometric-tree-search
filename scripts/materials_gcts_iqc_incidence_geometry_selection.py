#!/usr/bin/env python3
"""Nested selection of local GCTS incidence geometry on nine IQC nuclei.

The bounded grid is the one exposed by the lab: one, two, or three local
shells, each with a coarse or fine distance quantization.  For every outer
held-out nucleus, settings and a complete-score threshold are chosen using
only nested leave-one-nucleus-out predictions from the other eight nuclei.
The reserved confirmation nucleus is neither imported nor constructed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import (
    FrozenIncidenceTokenMarking, TokenEvidence,
    score_incidence_descriptor)
from materials_gcts_iqc_incidence_token_preflight import (
    MINIMUM_ACTION_PRECISION, MINIMUM_TOKEN_GROUPS, MINIMUM_TOKEN_SUPPORT,
    TOKEN_SHRINKAGE, _antichain, _build_candidate_sources,
    _candidate_groups_for_geometry, _threshold)
from materials_gcts_iqc_continuous_section_confirmation import (
    COMPLETED_TRAINING_CENTERS)


@dataclass(frozen=True, order=True)
class GeometrySpec:
    neighborhood_reach: float
    distance_bin_width: float
    maximum_neighbors: int = 8


GEOMETRY_GRID = tuple(
    GeometrySpec(reach, width)
    for reach in (1., 2., 3.) for width in (.25, .5))
REQUIRED_ACTIONS_PER_NUCLEUS = 2


@dataclass(frozen=True)
class InnerSelection:
    outer_index: int
    selected_geometry: GeometrySpec
    threshold: float
    selected_candidates: int
    correct_candidates: int
    precision: float
    exact_groups: int
    model_digest: str


@dataclass(frozen=True)
class NestedGeometrySelectionReport:
    training_centers: tuple[tuple[float, float, float], ...]
    geometry_grid: tuple[GeometrySpec, ...]
    candidate_graph_digest: str
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    outer_selections: tuple[InnerSelection, ...]
    selected_by_group: tuple[int, ...]
    correct_by_group: tuple[int, ...]
    selected_candidates: int
    correct_candidates: int
    false_candidates: int
    precision: float
    exact_groups: int
    minimum_selected_per_group: int
    rank_two_correct_by_group: tuple[int, ...]
    rank_two_correct_candidates: int
    rank_two_precision: float
    reserved_confirmation_center_imported_or_accessed: bool
    nested_gate_passed: bool
    honest_status: str


def _statistics(groups):
    labels = []
    tokens = []
    for group in groups:
        positive = sum(row.successful for row in group)
        labels.append((positive, len(group)))
        counts = defaultdict(lambda: [0, 0])
        for row in group:
            for token in set(row.descriptor.tokens):
                counts[token][0] += int(row.successful)
                counts[token][1] += 1
        tokens.append(dict(counts))
    return tuple(labels), tuple(tokens)


def _fit_from_groups(statistics, included):
    labels, group_tokens = statistics
    positive = sum(labels[index][0] for index in included)
    total = sum(labels[index][1] for index in included)
    if not 0 < positive < total:
        raise ValueError("nested token marking requires both labels")
    prior = (positive + 1.) / (total + 2.)
    intercept = math.log(prior / (1. - prior))
    aggregate = defaultdict(lambda: [0, 0, 0])
    for index in included:
        for token, (token_positive, token_total) in group_tokens[index].items():
            aggregate[token][0] += token_positive
            aggregate[token][1] += token_total
            aggregate[token][2] += 1
    evidence = {
        token: TokenEvidence(item[0], item[1], item[2])
        for token, item in aggregate.items()
    }
    weights = {}
    for token, item in evidence.items():
        if (item.total < MINIMUM_TOKEN_SUPPORT or
                item.independent_groups < MINIMUM_TOKEN_GROUPS):
            continue
        probability = (item.positive + 1.) / (item.total + 2.)
        logit = math.log(probability / (1. - probability))
        weights[token] = max(
            -4., min(4., TOKEN_SHRINKAGE * (logit - intercept)))
    return FrozenIncidenceTokenMarking(
        intercept, weights, evidence, MINIMUM_TOKEN_SUPPORT,
        MINIMUM_TOKEN_GROUPS, TOKEN_SHRINKAGE)


def _score_group(marking, group):
    return tuple((score_incidence_descriptor(marking, row.descriptor), row)
                 for row in group)


def _ranked_antichain(rows, limit):
    accepted = []
    for _score, row in sorted(rows, key=lambda item: (
            -item[0], item[1].point, item[1].color)):
        if any(math.dist(row.point, prior.point) <
               row.minimum_distance - 1e-8 for prior in accepted):
            continue
        accepted.append(row)
        if len(accepted) == limit:
            break
    return tuple(accepted)


def _inner_result(groups, statistics, outer_index):
    train = tuple(index for index in range(len(groups))
                  if index != outer_index)
    scored = []
    for inner_index in train:
        model = _fit_from_groups(
            statistics, tuple(index for index in train
                              if index != inner_index))
        scored.append(_score_group(model, groups[inner_index]))
    threshold, _raw_selected, _raw_correct, _raw_precision = _threshold(
        tuple(item for group in scored for item in group))
    selected = tuple(_antichain(group, threshold) for group in scored)
    selected_total = sum(map(len, selected))
    correct_total = sum(row.successful for group in selected for row in group)
    precision = correct_total / selected_total if selected_total else 0.
    exact = sum(bool(group) and all(row.successful for row in group)
                for group in selected)
    return threshold, selected_total, correct_total, precision, exact


def _selection_objective(spec, result):
    threshold, selected, correct, precision, exact = result
    if not math.isfinite(threshold) or precision < MINIMUM_ACTION_PRECISION:
        return (-1, -1, -1, -1., -math.inf, -math.inf)
    # Coverage precedes throughput.  Smaller reach and coarser bins win only
    # exact ties, keeping the choice deterministic without using outer labels.
    return (exact, correct, selected, precision,
            -spec.neighborhood_reach, spec.distance_bin_width)


def evaluate():
    sources = _build_candidate_sources()
    by_geometry = {}
    statistics = {}
    graph_rows = None
    for spec in GEOMETRY_GRID:
        groups = _candidate_groups_for_geometry(
            sources, neighborhood_reach=spec.neighborhood_reach,
            distance_bin_width=spec.distance_bin_width,
            maximum_neighbors=spec.maximum_neighbors)
        rows = tuple((row.group, row.point, row.color, row.successful)
                     for group in groups for row in group)
        if graph_rows is None:
            graph_rows = rows
        elif rows != graph_rows:
            raise AssertionError("geometry changed the exact candidate graph")
        by_geometry[spec] = groups
        statistics[spec] = _statistics(groups)

    outer_selections = []
    selected_groups = []
    rank_two_groups = []
    for outer_index in range(len(COMPLETED_TRAINING_CENTERS)):
        results = {
            spec: _inner_result(by_geometry[spec], statistics[spec],
                                outer_index)
            for spec in GEOMETRY_GRID
        }
        spec = max(GEOMETRY_GRID,
                   key=lambda item: _selection_objective(item, results[item]))
        threshold, inner_selected, inner_correct, inner_precision, inner_exact = \
            results[spec]
        train = tuple(index for index in range(len(COMPLETED_TRAINING_CENTERS))
                      if index != outer_index)
        model = _fit_from_groups(statistics[spec], train)
        scored = _score_group(model, by_geometry[spec][outer_index])
        selected = _antichain(scored, threshold)
        selected_groups.append(selected)
        rank_two_groups.append(_ranked_antichain(
            scored, REQUIRED_ACTIONS_PER_NUCLEUS))
        outer_selections.append(InnerSelection(
            outer_index, spec, threshold, inner_selected, inner_correct,
            inner_precision, inner_exact,
            hashlib.sha256(repr(model).encode()).hexdigest()))

    selected_counts = tuple(map(len, selected_groups))
    correct_counts = tuple(sum(row.successful for row in group)
                           for group in selected_groups)
    selected_total = sum(selected_counts)
    correct_total = sum(correct_counts)
    precision = correct_total / selected_total if selected_total else 0.
    exact_groups = sum(bool(group) and all(row.successful for row in group)
                       for group in selected_groups)
    minimum_selected = min(selected_counts)
    rank_two_correct = tuple(sum(row.successful for row in group)
                             for group in rank_two_groups)
    rank_two_total_correct = sum(rank_two_correct)
    rank_two_total = sum(map(len, rank_two_groups))
    passed = bool(
        precision >= MINIMUM_ACTION_PRECISION and
        exact_groups == len(COMPLETED_TRAINING_CENTERS) and
        minimum_selected >= REQUIRED_ACTIONS_PER_NUCLEUS)
    return NestedGeometrySelectionReport(
        training_centers=COMPLETED_TRAINING_CENTERS,
        geometry_grid=GEOMETRY_GRID,
        candidate_graph_digest=hashlib.sha256(
            repr(graph_rows).encode()).hexdigest(),
        candidates_by_group=tuple(
            len(group) for group in by_geometry[GEOMETRY_GRID[0]]),
        positives_by_group=tuple(
            sum(row.successful for row in group)
            for group in by_geometry[GEOMETRY_GRID[0]]),
        outer_selections=tuple(outer_selections),
        selected_by_group=selected_counts,
        correct_by_group=correct_counts,
        selected_candidates=selected_total,
        correct_candidates=correct_total,
        false_candidates=selected_total - correct_total,
        precision=precision,
        exact_groups=exact_groups,
        minimum_selected_per_group=minimum_selected,
        rank_two_correct_by_group=rank_two_correct,
        rank_two_correct_candidates=rank_two_total_correct,
        rank_two_precision=(rank_two_total_correct / rank_two_total
                            if rank_two_total else 0.),
        reserved_confirmation_center_imported_or_accessed=False,
        nested_gate_passed=passed,
        honest_status=(
            "nested geometry selection passes every development nucleus"
            if passed else
            "nested geometry selection remains precise but does not cover "
            "every development nucleus; confirmation stays sealed"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
