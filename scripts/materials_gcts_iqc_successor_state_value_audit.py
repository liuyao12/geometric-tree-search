#!/usr/bin/env python3
"""Learn a bounded successor-frontier value on 18 disjoint IQC nuclei."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import (
    IncidenceTokenExample, fit_incidence_token_marking,
    incidence_marking_digest, score_incidence_descriptor)
from materials_gcts_iqc_expanded_development_baseline import (
    FROZEN_FIT, FROZEN_QUOTIENT, _expanded_fixture)
from materials_gcts_iqc_incidence_geometry_selection import (
    _ranked_antichain, _statistics)
from materials_gcts_iqc_incidence_token_preflight import (
    _candidate_groups_for_geometry)
from materials_gcts_iqc_joint_incidence_graph_preflight import _fit
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_successor_state_marking import (
    successor_outgoing_points, successor_state_descriptor)


SHORTLIST_SIZE = 16
SUCCESSOR_GRID = (
    (4, 2, .5, .25),
    (4, 2, .5, .5),
    (8, 3, .5, .5),
    (8, 3, 1., 1.),
    (16, 4, 1., 1.),
)


@dataclass(frozen=True)
class SuccessorValueSpec:
    minimum_support: int
    minimum_groups: int
    shrinkage: float
    successor_mix: float


@dataclass(frozen=True)
class SuccessorValueAudit:
    spec: SuccessorValueSpec
    supported_tokens_by_fold: tuple[int, ...]
    fold_model_digest: str
    selected_correct_by_group: tuple[int, ...]
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class IQCSuccessorStateValueAudit:
    total_groups: int
    shortlist_size: int
    unique_successors_by_group: tuple[int, ...]
    outgoing_minimum_by_group: tuple[int, ...]
    outgoing_maximum_by_group: tuple[int, ...]
    successor_descriptor_digest: str
    successor_grid: tuple[SuccessorValueSpec, ...]
    audits: tuple[SuccessorValueAudit, ...]
    selected_spec: SuccessorValueSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    additive_baseline_correct_actions: int
    exact_candidate_geometry_changed: bool
    successor_constructed_target_free: bool
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


def _row_key(row):
    return row.group, row.point, row.color


def evaluate() -> IQCSuccessorStateValueAudit:
    sources, _crop_counts, connection = _expanded_fixture()
    groups = _candidate_groups_for_geometry(
        sources, neighborhood_reach=3., distance_bin_width=.25,
        maximum_neighbors=8, joint_role_geometry=True,
        message_passing_rounds=1,
        message_distance_divisor=FROZEN_QUOTIENT[0],
        message_role_mode=FROZEN_QUOTIENT[1],
        message_encoding=FROZEN_QUOTIENT[2])
    statistics = _statistics(groups)
    outer_models = []
    shortlists = []
    required = [dict() for _ in groups]
    additive = []
    for outer_index, outer_rows in enumerate(groups):
        included = tuple(index for index in range(len(groups))
                         if index != outer_index)
        model = _fit(statistics, included, FROZEN_FIT)
        outer_models.append(model)
        fold_shortlists = tuple(_ranked(rows, model) for rows in groups)
        shortlists.append(fold_shortlists)
        for group_index, rows in enumerate(fold_shortlists):
            for row in rows:
                required[group_index][_row_key(row)] = row
        additive.append(sum(row.successful for row in
            _ranked_antichain(tuple((score_incidence_descriptor(
                model, row.descriptor), row) for row in outer_rows),
                              ACTIONS_PER_NUCLEUS)))

    descriptors = {}
    outgoing_counts = [[] for _ in groups]
    for group_index, (source, rows) in enumerate(zip(sources, required)):
        for key, row in rows.items():
            positions, colors, future = advance_frontier_configuration(
                connection, source.proposals, source.seed_positions,
                source.seed_species, (row.point,), (row.color,), CLUSTER_EDGES,
                source.group, EVALUATION_TARGET_RADIUS)
            new_parent = len(positions) - 1
            descriptor = successor_state_descriptor(
                future, new_parent_index=new_parent,
                new_parent_position=row.point, occupied_positions=positions,
                minimum_distance=row.minimum_distance,
                distance_scale=HIDDEN_UNIT)
            descriptors[key] = descriptor
            outgoing_counts[group_index].append(len(successor_outgoing_points(
                future, new_parent_index=new_parent,
                occupied_positions=positions,
                minimum_distance=row.minimum_distance)))

    specs = tuple(SuccessorValueSpec(*row) for row in SUCCESSOR_GRID)
    audits = []
    for spec in specs:
        selected = []
        supported = []
        digests = []
        for outer_index, outer_rows in enumerate(groups):
            examples = tuple(IncidenceTokenExample(
                row.group, descriptors[_row_key(row)], row.successful)
                for group_index, rows in enumerate(shortlists[outer_index])
                if group_index != outer_index for row in rows)
            marking = fit_incidence_token_marking(
                examples, minimum_support=spec.minimum_support,
                minimum_groups=spec.minimum_groups,
                shrinkage=spec.shrinkage)
            supported.append(len(marking.token_weights))
            digests.append(incidence_marking_digest(marking))
            scored = []
            for row in shortlists[outer_index][outer_index]:
                base = _logit(score_incidence_descriptor(
                    outer_models[outer_index], row.descriptor))
                future = _logit(score_incidence_descriptor(
                    marking, descriptors[_row_key(row)])) - marking.intercept
                scored.append((base + spec.successor_mix * future, row))
            selected.append(_ranked_antichain(
                tuple(scored), ACTIONS_PER_NUCLEUS))
        correct_by_group = tuple(sum(row.successful for row in rows)
                                 for rows in selected)
        correct = sum(correct_by_group)
        total = sum(map(len, selected))
        audits.append(SuccessorValueAudit(
            spec, tuple(supported), hashlib.sha256(repr(tuple(
                digests)).encode()).hexdigest(), correct_by_group, correct,
            total - correct, correct / total if total else 0.,
            sum(value == ACTIONS_PER_NUCLEUS for value in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support,
        -row.spec.successor_mix))
    passed = selected.selected_correct_actions == 2 * len(groups)
    return IQCSuccessorStateValueAudit(
        len(groups), SHORTLIST_SIZE, tuple(len(rows) for rows in required),
        tuple(min(rows) for rows in outgoing_counts),
        tuple(max(rows) for rows in outgoing_counts),
        hashlib.sha256(repr(tuple(sorted(descriptors.items()))).encode()
                       ).hexdigest(), specs, tuple(audits), selected.spec,
        selected.selected_correct_by_group, 2 * len(groups),
        selected.selected_correct_actions, selected.selected_false_actions,
        selected.precision, selected.exact_groups, sum(additive), False, True,
        NEXT_CONFIRMATION_CENTER, False, passed,
        "successor-state value passes expanded development" if passed else
        "successor-state value remains below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
