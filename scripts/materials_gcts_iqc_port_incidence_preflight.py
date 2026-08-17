#!/usr/bin/env python3
"""Group-heldout IQC preflight for explicit carried-port GCTS search.

Only the nine completed training nuclei are opened.  Each fold fits a finite
role table on eight nuclei, then searches an immutable two-action graph on the
ninth.  The reserved confirmation centre is neither imported nor constructed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_frontier_band_marking import frontier_score_bands
from materials_gcts_iqc_continuous_section_confirmation import (
    COMPLETED_TRAINING_CENTERS)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_self_fed_section_confirmation import (
    _band_truth)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_port_incidence_search import (
    PortIncidenceAction, fit_port_incidence_policy, port_incidence_patterns,
    port_incidence_state, search_port_incidence_paths)
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types)


ROOT_BANDS = 8
CHILD_BANDS = 6
MAXIMUM_ROLES = 8
MINIMUM_ROLE_MULTIPLICITY = 2
MINIMUM_POSITIVE_SUPPORT = 4
MINIMUM_ROLE_PURITY = .9
MINIMUM_ACTION_PRECISION = .95
REQUIRED_SELECTED_ACTIONS = 2 * len(COMPLETED_TRAINING_CENTERS)


@dataclass(frozen=True)
class _ActionRecord:
    group: tuple[float, float, float]
    action: PortIncidenceAction
    successful: bool
    correct_sites: int
    false_sites: int
    children: tuple[str, ...]


@dataclass(frozen=True)
class PortIncidencePreflight:
    training_centers: tuple[tuple[float, float, float], ...]
    root_bands: int
    child_bands: int
    maximum_roles: int
    minimum_role_multiplicity: int
    minimum_positive_support: int
    minimum_role_purity: float
    action_graph_digest: str
    total_actions: int
    positive_actions: int
    fold_policy_digests: tuple[str, ...]
    selected_paths: tuple[tuple[str, ...], ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    selected_correct_sites: int
    selected_false_sites: int
    selected_action_precision: float
    complete_two_action_paths: int
    explored_actions: int
    backtracks: int
    heldout_role_mass: int
    heldout_seen_role_mass: int
    heldout_admitted_role_mass: int
    heldout_seen_role_fraction: float
    heldout_admitted_role_fraction: float
    reserved_confirmation_center_imported_or_accessed: bool
    preflight_passed: bool
    honest_status: str


def _compatible(positions, band):
    minimum = min(math.dist(point, other)
                  for index, point in enumerate(positions)
                  for other in positions[index + 1:])
    return not any(
        math.dist(point, other) < minimum - 1e-8
        for index, point in enumerate(band)
        for other in tuple(positions) + tuple(band[index + 1:]))


def _action(action_id, proposals, band, future, successful,
            future_points=None):
    return PortIncidenceAction(
        action_id,
        port_incidence_state(
            proposals, band.positions, maximum_roles=MAXIMUM_ROLES,
            minimum_multiplicity=MINIMUM_ROLE_MULTIPLICITY),
        port_incidence_state(
            future, future_points, maximum_roles=MAXIMUM_ROLES,
            minimum_multiplicity=MINIMUM_ROLE_MULTIPLICITY),
        float(band.score), len(band.positions),
        {"successful": bool(successful), "positions": band.positions},
        port_incidence_patterns(
            proposals, band.positions, maximum_order=2,
            maximum_patterns=32, roles_per_site=4))


def _connection_scores(proposals):
    """Deterministic target-free ordering from the frozen port incidences."""
    scores = {}
    for point, votes in proposals.votes.items():
        state_rows = proposals.state_votes.get(point, {})
        evidence_mass = sum(state_rows.values())
        parent_mass = sum(proposals.parent_votes.get(point, {}).values())
        source = proposals.color_votes.get(point, {})
        target = proposals.target_color_votes.get(point, {})
        source_purity = max(source.values(), default=0) / max(1, sum(source.values()))
        target_purity = max(target.values(), default=0) / max(1, sum(target.values()))
        # Multiplicity is primary; the remaining bounded terms split equal-vote
        # bands without coordinates, raw IDs, or learned target labels.
        scores[point] = (float(votes) + .01 * evidence_mass /
                         max(1, votes) + .001 * parent_mass /
                         max(1, votes) + .0001 * source_purity +
                         .00001 * target_purity)
    return scores


def _scored_bands(proposals, maximum):
    scores = _connection_scores(proposals)
    return frontier_score_bands(
        proposals, scores, maximum_bands=maximum)


def _build_graphs():
    origin_seed, _ = oracle_patch(3, 9.)
    origin_target, _ = oracle_patch(4, EVALUATION_TARGET_RADIUS)
    prototypes = local_cluster_types(
        origin_seed.positions, origin_seed.species, CLUSTER_EDGES)
    connection = learn_recursive_connection_marking(
        origin_seed.positions, prototypes, origin_target.positions,
        HIDDEN_UNIT, minimum_purity=.5,
        target_colors=origin_target.species)
    seeds = (origin_seed,) + tuple(
        _seed_crop(center) for center in COMPLETED_TRAINING_CENTERS[1:])
    targets = (origin_target,) + tuple(
        _open_target(center) for center in COMPLETED_TRAINING_CENTERS[1:])
    records = {}
    roots_by_group = {}
    for group_index, (center, seed, target) in enumerate(zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets)):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        roots = []
        for band in _scored_bands(proposals, ROOT_BANDS):
            if not _compatible(seed.positions, band.positions):
                continue
            colors = tuple(_dominant_source_color(proposals, point)
                           for point in band.positions)
            positions, next_colors, future = advance_frontier_configuration(
                connection, proposals, seed.positions, seed.species,
                band.positions, colors, CLUSTER_EDGES, center,
                EVALUATION_TARGET_RADIUS)
            correct, false = _band_truth(proposals, band.positions, target)
            root_id = f"g{group_index}:r{band.rank}"
            child_ids = []
            child_frontier_points = set()
            if future.votes:
                for child_band in _scored_bands(future, CHILD_BANDS):
                    if not _compatible(positions, child_band.positions):
                        continue
                    child_colors = tuple(_dominant_source_color(
                        future, point) for point in child_band.positions)
                    child_positions, child_next_colors, child_future = \
                        advance_frontier_configuration(
                            connection, future, positions, next_colors,
                            child_band.positions, child_colors, CLUSTER_EDGES,
                            center, EVALUATION_TARGET_RADIUS)
                    child_correct, child_false = _band_truth(
                        future, child_band.positions, target)
                    child_id = f"{root_id}:c{child_band.rank}"
                    child_frontier_points.update(child_band.positions)
                    child_action = _action(
                        child_id, future, child_band, child_future,
                        bool(child_correct and not child_false))
                    records[child_id] = _ActionRecord(
                        center, child_action,
                        bool(child_correct and not child_false),
                        child_correct, child_false, ())
                    child_ids.append(child_id)
            root_action = _action(
                root_id, proposals, band, future,
                bool(correct and not false), child_frontier_points)
            records[root_id] = _ActionRecord(
                center, root_action, bool(correct and not false),
                correct, false, tuple(child_ids))
            roots.append(root_id)
        roots_by_group[center] = tuple(roots)
    return records, roots_by_group


def evaluate():
    records, roots_by_group = _build_graphs()
    action_digest = hashlib.sha256(repr(tuple(sorted(
        (action_id, record.group, record.action.required,
         record.action.produced, record.action.patterns,
         record.action.marking_score, record.action.emitted_sites,
         record.children)
        for action_id, record in records.items()))).encode()).hexdigest()
    selected_paths = []
    policy_digests = []
    selected_records = []
    explored = backtracks = 0
    role_mass = seen_mass = admitted_mass = 0
    for heldout in COMPLETED_TRAINING_CENTERS:
        training = tuple(
            (record.action, record.successful)
            for record in records.values() if record.group != heldout)
        policy = fit_port_incidence_policy(
            training,
            minimum_positive_support=MINIMUM_POSITIVE_SUPPORT,
            minimum_purity=MINIMUM_ROLE_PURITY)
        policy_digests.append(hashlib.sha256(repr(policy).encode()).hexdigest())
        held_records = tuple(
            record for record in records.values()
            if record.group == heldout)
        for record in held_records:
            for role, count in record.action.produced.roles:
                role_mass += count
                if role in policy.evidence:
                    seen_mass += count
                if role in policy.admitted_roles:
                    admitted_mass += count
        roots = tuple(records[action_id].action
                      for action_id in roots_by_group[heldout])
        trace = search_port_incidence_paths(
            roots,
            lambda action: tuple(records[child].action
                                 for child in records[action.action_id].children),
            policy, maximum_depth=2, beam_width=8,
            maximum_roles=MAXIMUM_ROLES,
            require_admitted_produced_roles=False,
            require_admitted_action_pattern=False)
        selected_paths.append(tuple(map(str, trace.selected_ids)))
        explored += trace.explored_actions
        backtracks += trace.backtracks
        selected_records.extend(records[action_id]
                                for action_id in trace.selected_ids)
    correct_actions = sum(record.successful for record in selected_records)
    false_actions = len(selected_records) - correct_actions
    precision = correct_actions / len(selected_records) \
        if selected_records else 0.
    complete_paths = sum(len(path) == 2 for path in selected_paths)
    passed = bool(
        len(selected_records) >= REQUIRED_SELECTED_ACTIONS and
        precision >= MINIMUM_ACTION_PRECISION and
        complete_paths == len(COMPLETED_TRAINING_CENTERS))
    return PortIncidencePreflight(
        COMPLETED_TRAINING_CENTERS, ROOT_BANDS, CHILD_BANDS, MAXIMUM_ROLES,
        MINIMUM_ROLE_MULTIPLICITY, MINIMUM_POSITIVE_SUPPORT,
        MINIMUM_ROLE_PURITY, action_digest, len(records),
        sum(record.successful for record in records.values()),
        tuple(policy_digests), tuple(selected_paths), len(selected_records),
        correct_actions, false_actions,
        sum(record.correct_sites for record in selected_records),
        sum(record.false_sites for record in selected_records), precision,
        complete_paths, explored, backtracks, role_mass, seen_mass,
        admitted_mass, seen_mass / role_mass if role_mass else 0.,
        admitted_mass / role_mass if role_mass else 0., False, passed,
        ("explicit carried-port incidence passes the train-only two-action gate"
         if passed else
         "explicit carried-port incidence remains below the train-only two-action gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
