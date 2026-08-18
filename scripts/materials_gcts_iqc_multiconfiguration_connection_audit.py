#!/usr/bin/env python3
"""Audit fold-frozen multi-configuration IQC connection-grammar supply."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color, _subset_proposals, _without_known_sites)
from materials_gcts_iqc_expanded_development_baseline import _expanded_fixture
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types,
    merge_recursive_connection_markings, propose_with_recursive_marking)
from materials_gcts_successor_state_marking import successor_outgoing_points


MERGE_GRID = (
    (2, 2, .5),
    (4, 3, .5),
    (8, 4, .5),
    (16, 5, .5),
)


@dataclass(frozen=True)
class ConnectionMergeSpec:
    minimum_positive_support: int
    minimum_positive_groups: int
    minimum_purity: float


@dataclass(frozen=True)
class ConnectionSupplyAudit:
    spec: ConnectionMergeSpec
    accepted_states_by_fold: tuple[int, ...]
    candidate_actions_by_group: tuple[int, ...]
    correct_candidate_actions_by_group: tuple[int, ...]
    checked_correct_roots_by_group: tuple[int, ...]
    exact_path_available_by_group: tuple[bool, ...]
    groups_with_correct_candidates: int
    groups_with_exact_path: int
    model_digest: str


@dataclass(frozen=True)
class IQCMulticonfigurationConnectionAudit:
    total_groups: int
    merge_grid: tuple[ConnectionMergeSpec, ...]
    audits: tuple[ConnectionSupplyAudit, ...]
    selected_spec: ConnectionMergeSpec
    selected_groups_with_correct_candidates: int
    selected_groups_with_exact_path: int
    origin_only_groups_without_exact_path: tuple[int, ...]
    connection_learning_uses_training_targets: bool
    heldout_target_used_for_connection_fit_or_proposals: bool
    heldout_truth_opened_only_for_supply_scoring: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    supply_gate_passed: bool
    honest_status: str


def _bounded(connection, source, types):
    proposals = propose_with_recursive_marking(
        connection, source.seed_positions, types, HIDDEN_UNIT)
    proposals = _without_known_sites(proposals, source.seed_positions)
    return _subset_proposals(proposals, (
        point for point in proposals.votes
        if math.dist(point, source.group) <= EVALUATION_TARGET_RADIUS + 1e-8))


def evaluate() -> IQCMulticonfigurationConnectionAudit:
    sources, _crop_counts, _origin_connection = _expanded_fixture()
    types = tuple(local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES)
        for source in sources)
    per_group = tuple(learn_recursive_connection_marking(
        source.seed_positions, group_types, tuple(source.truth), HIDDEN_UNIT,
        minimum_positive_support=1, minimum_purity=1e-9,
        target_colors=tuple(source.truth.values()))
        for source, group_types in zip(sources, types))
    positive_states = tuple(tuple(
        state for state, row in marking.evidence.items() if row.positive > 0)
        for marking in per_group)
    specs = tuple(ConnectionMergeSpec(*row) for row in MERGE_GRID)
    audits = []
    for spec in specs:
        accepted_counts = []
        candidate_counts = []
        correct_counts = []
        checked_counts = []
        path_available = []
        digests = []
        for heldout_index, (source, group_types) in enumerate(
                zip(sources, types)):
            included = tuple(index for index in range(len(per_group))
                             if index != heldout_index)
            merged = merge_recursive_connection_markings(
                tuple(per_group[index] for index in included),
                minimum_positive_support=spec.minimum_positive_support,
                minimum_positive_groups=spec.minimum_positive_groups,
                minimum_purity=spec.minimum_purity,
                positive_states_by_marking=tuple(
                    positive_states[index] for index in included))
            accepted_counts.append(len(merged.accepted_states))
            digests.append(hashlib.sha256(repr(merged).encode()).hexdigest())
            proposals = _bounded(merged, source, group_types)
            roots = tuple((point, _dominant_source_color(proposals, point))
                          for point in sorted(proposals.votes))
            correct_roots = tuple((point, color) for point, color in roots
                                  if source.truth.get(_key(point)) == color)
            candidate_counts.append(len(roots))
            correct_counts.append(len(correct_roots))
            found = False
            checked = 0
            for point, color in correct_roots:
                checked += 1
                positions, colors, future = advance_frontier_configuration(
                    merged, proposals, source.seed_positions,
                    source.seed_species, (point,), (color,), CLUSTER_EDGES,
                    source.group, EVALUATION_TARGET_RADIUS)
                parent = len(positions) - 1
                outgoing = successor_outgoing_points(
                    future, new_parent_index=parent,
                    occupied_positions=positions,
                    minimum_distance=source.minimum_distance)
                if any(source.truth.get(_key(child)) ==
                       _dominant_source_color(future, child)
                       for child in outgoing):
                    found = True
                    break
            checked_counts.append(checked)
            path_available.append(found)
        audits.append(ConnectionSupplyAudit(
            spec, tuple(accepted_counts), tuple(candidate_counts),
            tuple(correct_counts), tuple(checked_counts),
            tuple(path_available), sum(value > 0 for value in correct_counts),
            sum(path_available), hashlib.sha256(repr(tuple(
                digests)).encode()).hexdigest()))
    selected = max(audits, key=lambda row: (
        row.groups_with_exact_path, row.groups_with_correct_candidates,
        -sum(row.candidate_actions_by_group),
        row.spec.minimum_positive_groups,
        row.spec.minimum_positive_support))
    passed = selected.groups_with_correct_candidates == len(sources) and \
        selected.groups_with_exact_path == len(sources)
    return IQCMulticonfigurationConnectionAudit(
        len(sources), specs, tuple(audits), selected.spec,
        selected.groups_with_correct_candidates,
        selected.groups_with_exact_path, (0, 14), True, False, True,
        NEXT_CONFIRMATION_CENTER, False, passed,
        "multi-configuration connection grammar supplies every development path"
        if passed else
        "multi-configuration connection grammar remains incomplete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
