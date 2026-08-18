#!/usr/bin/env python3
"""Train recurrent IQC cluster prototypes before learning connection ports."""

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
    learn_recurrent_cluster_prototypes, learn_recursive_connection_marking,
    local_cluster_types, map_to_prototypes,
    merge_recursive_connection_markings, propose_with_recursive_marking)
from materials_gcts_successor_state_marking import successor_outgoing_points


TRAINING_GROUPS = 10
PROTOTYPE_GROUP_FLOORS = (2, 3, 4, 5)


@dataclass(frozen=True)
class RecurrentPrototypeSupply:
    prototype_minimum_groups: int
    recurrent_prototypes: int
    accepted_connection_states: int
    candidate_actions_by_validation_group: tuple[int, ...]
    correct_candidates_by_validation_group: tuple[int, ...]
    checked_correct_roots_by_validation_group: tuple[int, ...]
    exact_path_available_by_validation_group: tuple[bool, ...]
    groups_with_correct_candidates: int
    groups_with_exact_path: int
    model_digest: str


@dataclass(frozen=True)
class IQCRecurrentPrototypeConnectionAudit:
    training_groups: int
    validation_groups: int
    prototype_group_floors: tuple[int, ...]
    audits: tuple[RecurrentPrototypeSupply, ...]
    selected_prototype_minimum_groups: int
    selected_groups_with_correct_candidates: int
    selected_groups_with_exact_path: int
    cluster_vocabulary_fit_on_training_seeds_only: bool
    connection_fit_uses_training_targets_only: bool
    validation_targets_used_only_for_supply_scoring: bool
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


def evaluate() -> IQCRecurrentPrototypeConnectionAudit:
    sources, _crop_counts, _origin = _expanded_fixture()
    raw_types = tuple(local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES)
        for source in sources)
    train_sources = sources[:TRAINING_GROUPS]
    validation_sources = sources[TRAINING_GROUPS:]
    audits = []
    for prototype_floor in PROTOTYPE_GROUP_FLOORS:
        prototypes = learn_recurrent_cluster_prototypes(
            raw_types[:TRAINING_GROUPS], minimum_groups=prototype_floor)
        markings = tuple(learn_recursive_connection_marking(
            source.seed_positions, map_to_prototypes(group_types, prototypes),
            tuple(source.truth), HIDDEN_UNIT, minimum_positive_support=1,
            minimum_purity=1e-9, target_colors=tuple(source.truth.values()))
            for source, group_types in zip(
                train_sources, raw_types[:TRAINING_GROUPS]))
        positive_states = tuple(tuple(
            state for state, row in marking.evidence.items()
            if row.positive > 0) for marking in markings)
        merged = merge_recursive_connection_markings(
            markings, minimum_positive_support=2,
            minimum_positive_groups=2, minimum_purity=.5,
            positive_states_by_marking=positive_states)
        candidate_counts = []
        correct_counts = []
        checked_counts = []
        paths = []
        for source, group_types in zip(
                validation_sources, raw_types[TRAINING_GROUPS:]):
            proposals = _bounded(merged, source, group_types)
            roots = tuple((point, _dominant_source_color(proposals, point))
                          for point in sorted(proposals.votes))
            correct_roots = tuple((point, color) for point, color in roots
                                  if source.truth.get(_key(point)) == color)
            candidate_counts.append(len(roots))
            correct_counts.append(len(correct_roots))
            checked = 0
            found = False
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
            paths.append(found)
        audits.append(RecurrentPrototypeSupply(
            prototype_floor, len(prototypes), len(merged.accepted_states),
            tuple(candidate_counts), tuple(correct_counts),
            tuple(checked_counts), tuple(paths),
            sum(value > 0 for value in correct_counts), sum(paths),
            hashlib.sha256(repr((prototypes, merged)).encode()).hexdigest()))
    selected = max(audits, key=lambda row: (
        row.groups_with_exact_path, row.groups_with_correct_candidates,
        -sum(row.candidate_actions_by_validation_group),
        row.prototype_minimum_groups))
    passed = selected.groups_with_correct_candidates == len(validation_sources) \
        and selected.groups_with_exact_path == len(validation_sources)
    return IQCRecurrentPrototypeConnectionAudit(
        TRAINING_GROUPS, len(validation_sources), PROTOTYPE_GROUP_FLOORS,
        tuple(audits), selected.prototype_minimum_groups,
        selected.groups_with_correct_candidates,
        selected.groups_with_exact_path, True, True, True,
        NEXT_CONFIRMATION_CENTER, False, passed,
        "recurrent prototype quotient supplies every validation path"
        if passed else
        "recurrent prototype quotient leaves validation supply gaps")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
