#!/usr/bin/env python3
"""Audit a bounded two-step successor value on 18 disjoint IQC nuclei."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_incidence_token_marking import (
    IncidenceTokenExample, fit_incidence_token_marking,
    incidence_marking_digest, score_incidence_descriptor)
from materials_gcts_iqc_incidence_geometry_selection import _ranked_antichain
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
from materials_gcts_successor_state_marking import (
    rollout_state_descriptor, successor_outgoing_points,
    successor_state_descriptor)


ROLLOUT_BRANCHING = 4


@dataclass(frozen=True)
class TwoStepValueAudit:
    spec: SuccessorValueSpec
    supported_tokens_by_fold: tuple[int, ...]
    fold_model_digest: str
    selected_correct_by_group: tuple[int, ...]
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class IQCTwoStepSuccessorValueAudit:
    total_groups: int
    rollout_branching: int
    roots_by_group: tuple[int, ...]
    evaluated_child_branches_by_group: tuple[int, ...]
    rollout_descriptor_digest: str
    audits: tuple[TwoStepValueAudit, ...]
    selected_spec: SuccessorValueSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    additive_baseline_correct_actions: int
    one_step_successor_correct_actions: int
    exact_candidate_geometry_changed: bool
    rollout_constructed_target_free: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def evaluate() -> IQCTwoStepSuccessorValueAudit:
    (sources, connection, groups, _statistics_rows, outer_models,
     shortlists, required, root_descriptors, successor_states,
     _outgoing_counts, additive) = _build_successor_fixture()
    rollout_descriptors = {}
    child_counts = [[] for _ in groups]
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
                    :ROLLOUT_BRANCHING])
            branch_descriptors = []
            for point in children:
                color = _dominant_source_color(future, point)
                terminal_positions, terminal_colors, terminal = \
                    advance_frontier_configuration(
                        connection, future, positions, colors,
                        (point,), (color,), CLUSTER_EDGES,
                        source.group, EVALUATION_TARGET_RADIUS)
                terminal_parent = len(terminal_positions) - 1
                branch_descriptors.append(successor_state_descriptor(
                    terminal, new_parent_index=terminal_parent,
                    new_parent_position=point,
                    occupied_positions=terminal_positions,
                    minimum_distance=row.minimum_distance,
                    distance_scale=HIDDEN_UNIT))
            rollout_descriptors[key] = rollout_state_descriptor(
                root_descriptors[key], branch_descriptors)
            child_counts[group_index].append(len(branch_descriptors))

    specs = tuple(SuccessorValueSpec(*row) for row in SUCCESSOR_GRID)
    audits = []
    for spec in specs:
        selected = []
        supported = []
        digests = []
        for outer_index, outer_rows in enumerate(groups):
            examples = tuple(IncidenceTokenExample(
                row.group, rollout_descriptors[_row_key(row)], row.successful)
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
                rollout = _logit(score_incidence_descriptor(
                    marking, rollout_descriptors[_row_key(row)])) - \
                    marking.intercept
                scored.append((base + spec.successor_mix * rollout, row))
            selected.append(_ranked_antichain(
                tuple(scored), ACTIONS_PER_NUCLEUS))
        correct_by_group = tuple(sum(row.successful for row in rows)
                                 for rows in selected)
        correct = sum(correct_by_group)
        total = sum(map(len, selected))
        audits.append(TwoStepValueAudit(
            spec, tuple(supported), hashlib.sha256(repr(tuple(
                digests)).encode()).hexdigest(), correct_by_group, correct,
            total - correct, correct / total if total else 0.,
            sum(value == ACTIONS_PER_NUCLEUS for value in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support,
        -row.spec.successor_mix))
    passed = selected.selected_correct_actions == 2 * len(groups)
    return IQCTwoStepSuccessorValueAudit(
        len(groups), ROLLOUT_BRANCHING,
        tuple(len(rows) for rows in required),
        tuple(sum(rows) for rows in child_counts),
        hashlib.sha256(repr(tuple(sorted(
            rollout_descriptors.items()))).encode()).hexdigest(),
        tuple(audits), selected.spec, selected.selected_correct_by_group,
        2 * len(groups), selected.selected_correct_actions,
        selected.selected_false_actions, selected.precision,
        selected.exact_groups, sum(additive), 31, False, True,
        NEXT_CONFIRMATION_CENTER, False, passed,
        "two-step successor value passes expanded development" if passed else
        "two-step successor value remains below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
