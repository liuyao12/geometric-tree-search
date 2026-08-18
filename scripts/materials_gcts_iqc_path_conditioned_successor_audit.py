#!/usr/bin/env python3
"""Learn directed root→child GCTS obligation values on expanded IQC data."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_incidence_token_marking import (
    IncidenceTokenExample, fit_incidence_token_marking,
    incidence_marking_digest, score_incidence_descriptor)
from materials_gcts_iqc_incidence_geometry_selection import _ranked_antichain
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_iqc_successor_state_value_audit import (
    SUCCESSOR_GRID, _build_successor_fixture, _logit, _row_key,
    SuccessorValueSpec)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_port_incidence_search import (
    port_incidence_patterns, port_incidence_state)
from materials_gcts_successor_state_marking import (
    path_state_descriptor, successor_outgoing_points,
    successor_state_descriptor)


PATH_BRANCHING = 4


@dataclass(frozen=True)
class PathValueAudit:
    spec: SuccessorValueSpec
    supported_tokens_by_fold: tuple[int, ...]
    fold_model_digest: str
    selected_correct_by_group: tuple[int, ...]
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class IQCPathConditionedSuccessorAudit:
    total_groups: int
    path_branching: int
    heldout_paths_by_group: tuple[int, ...]
    heldout_exact_paths_by_group: tuple[int, ...]
    path_descriptor_digest: str
    audits: tuple[PathValueAudit, ...]
    selected_spec: SuccessorValueSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    additive_baseline_correct_actions: int
    one_step_successor_correct_actions: int
    pooled_two_step_correct_actions: int
    exact_candidate_geometry_changed: bool
    path_descriptors_constructed_before_labels: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def evaluate() -> IQCPathConditionedSuccessorAudit:
    (sources, connection, groups, _statistics_rows, outer_models,
     shortlists, required, root_descriptors, successor_states,
     _outgoing_counts, additive) = _build_successor_fixture()
    paths = {}
    # Geometry and descriptors are frozen before the truth map labels paths.
    for group_index, (source, rows) in enumerate(zip(sources, required)):
        for key, row in rows.items():
            positions, colors, future, new_parent = successor_states[key]
            outgoing = successor_outgoing_points(
                future, new_parent_index=new_parent,
                occupied_positions=positions,
                minimum_distance=row.minimum_distance)
            children = tuple(sorted(outgoing, key=lambda point: (
                -future.votes[point],
                -sum(future.parent_votes.get(point, {}).values()), point))[
                    :PATH_BRANCHING])
            records = []
            for point in children:
                color = _dominant_source_color(future, point)
                incoming = port_incidence_state(
                    future, (point,), maximum_roles=8,
                    minimum_multiplicity=1)
                patterns = port_incidence_patterns(
                    future, (point,), maximum_order=2,
                    maximum_patterns=32, roles_per_site=4)
                terminal_positions, terminal_colors, terminal = \
                    advance_frontier_configuration(
                        connection, future, positions, colors,
                        (point,), (color,), CLUSTER_EDGES,
                        source.group, EVALUATION_TARGET_RADIUS)
                terminal_parent = len(terminal_positions) - 1
                child_descriptor = successor_state_descriptor(
                    terminal, new_parent_index=terminal_parent,
                    new_parent_position=point,
                    occupied_positions=terminal_positions,
                    minimum_distance=row.minimum_distance,
                    distance_scale=HIDDEN_UNIT)
                descriptor = path_state_descriptor(
                    root_descriptors[key], child_descriptor,
                    root_color=row.color, child_color=color,
                    normalized_distance_bin=round(
                        math.dist(row.point, point) / (HIDDEN_UNIT * .5)),
                    incoming_state=incoming, incoming_patterns=patterns)
                records.append((descriptor, point, color))
            paths[key] = tuple(records)

    # Labels enter only after every path descriptor above is immutable.
    path_labels = {
        key: tuple((descriptor, source.truth.get(_key(point)) == color)
                   for descriptor, point, color in paths[key])
        for source, rows in zip(sources, required)
        for key in rows}
    specs = tuple(SuccessorValueSpec(*row) for row in SUCCESSOR_GRID)
    audits = []
    for spec in specs:
        selected = []
        supported = []
        digests = []
        for outer_index, outer_rows in enumerate(groups):
            examples = tuple(IncidenceTokenExample(
                row.group, descriptor, row.successful and child_successful)
                for group_index, rows in enumerate(shortlists[outer_index])
                if group_index != outer_index for row in rows
                for descriptor, child_successful in path_labels[_row_key(row)])
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
                adjustments = tuple(_logit(score_incidence_descriptor(
                    marking, descriptor)) - marking.intercept
                    for descriptor, _successful in path_labels[_row_key(row)])
                path_value = max(adjustments, default=0.)
                scored.append((base + spec.successor_mix * path_value, row))
            selected.append(_ranked_antichain(
                tuple(scored), ACTIONS_PER_NUCLEUS))
        correct_by_group = tuple(sum(row.successful for row in rows)
                                 for rows in selected)
        correct = sum(correct_by_group)
        total = sum(map(len, selected))
        audits.append(PathValueAudit(
            spec, tuple(supported), hashlib.sha256(repr(tuple(
                digests)).encode()).hexdigest(), correct_by_group, correct,
            total - correct, correct / total if total else 0.,
            sum(value == ACTIONS_PER_NUCLEUS for value in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support,
        -row.spec.successor_mix))
    heldout_paths = tuple(sum(len(paths[_row_key(row)])
                              for row in shortlists[index][index])
                          for index in range(len(groups)))
    heldout_exact = tuple(sum(
        row.successful and child_successful
        for row in shortlists[index][index]
        for _descriptor, child_successful in path_labels[_row_key(row)])
        for index in range(len(groups)))
    passed = selected.selected_correct_actions == 2 * len(groups)
    return IQCPathConditionedSuccessorAudit(
        len(groups), PATH_BRANCHING, heldout_paths, heldout_exact,
        hashlib.sha256(repr(tuple(sorted((key, tuple(
            descriptor for descriptor, _point, _color in rows))
            for key, rows in paths.items()))).encode()).hexdigest(),
        tuple(audits), selected.spec, selected.selected_correct_by_group,
        2 * len(groups), selected.selected_correct_actions,
        selected.selected_false_actions, selected.precision,
        selected.exact_groups, sum(additive), 31, 31, False, True,
        NEXT_CONFIRMATION_CENTER, False, passed,
        "path-conditioned successor value passes expanded development"
        if passed else
        "path-conditioned successor value remains below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
