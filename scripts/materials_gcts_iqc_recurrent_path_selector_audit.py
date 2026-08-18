#!/usr/bin/env python3
"""Group-heldout autonomous path values on the recurrent IQC quotient."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cluster_prototype_compatibility import (
    fit_prototype_compatibility_context, score_prototype_insertions)
from materials_gcts_frontier_band_marking import (
    BandTrainingExample, _fit as fit_linear_section, score_band)
from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample,
    candidate_incidence_descriptors,
    fit_incidence_token_marking, incidence_marking_digest,
    score_incidence_descriptor, score_incidence_descriptor_by_channel)
from materials_gcts_iqc_expanded_development_baseline import _expanded_fixture
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_port_incidence_search import (
    port_incidence_patterns, port_incidence_state)
from materials_gcts_recursive_connections import (
    learn_recurrent_cluster_prototypes, learn_recursive_connection_marking,
    local_cluster_types, map_to_prototypes,
    merge_recursive_connection_markings)
from materials_gcts_successor_state_marking import (
    successor_outgoing_points, successor_state_descriptor)


TRAINING_GROUPS = 10
ROOT_SHORTLISTS = (64, 128, 256)
CHILD_BRANCHING = 16
MARKING_GRID = (
    (4, 2, .5), (8, 3, .5), (16, 4, 1.), (24, 5, 1.))
COMPATIBILITY_NEGATIVE_RATIO = 8
COMPATIBILITY_RIDGE = .1
COMPATIBILITY_FIT_STEPS = 400
COMPATIBILITY_FEATURE_NAMES = (
    "token_score", "channel_score", "root_rank", "child_rank",
    "root_prototype_residual", "child_prototype_residual",
    "existing_residual_delta", "total_residual_delta", "affected_atoms",
    "local_frontier_angle", "local_frontier_gain", "same_color",
    "root_child_distance")


@dataclass(frozen=True)
class SelectorAudit:
    root_shortlist: int
    minimum_support: int
    minimum_groups: int
    shrinkage: float
    path_candidates_by_group: tuple[int, ...]
    exact_paths_by_group: tuple[int, ...]
    selected_exact_by_group: tuple[bool, ...]
    selected_exact_paths: int
    first_exact_ranks_by_group: tuple[int, ...]
    supported_tokens_by_fold: tuple[int, ...]
    fold_model_digest: str


@dataclass(frozen=True)
class IQCRecurrentPathSelectorAudit:
    training_groups: int
    validation_groups: int
    recurrent_prototypes: int
    accepted_connection_states: int
    child_branching: int
    audits: tuple[SelectorAudit, ...]
    selected_root_shortlist: int
    selected_marking: tuple[int, int, float]
    selected_exact_by_group: tuple[bool, ...]
    selected_exact_paths: int
    candidate_supply_complete: bool
    autonomous_development_gate_passed: bool
    descriptors_frozen_before_labels: bool
    target_used_for_candidate_generation: bool
    candidate_digest: str
    cluster_compatibility_feature_names: tuple[str, ...]
    cluster_compatibility_negative_ratio: int
    cluster_compatibility_ridge: float
    compatibility_selected_exact_by_group: tuple[bool, ...]
    compatibility_first_exact_ranks: tuple[int, ...]
    compatibility_selected_exact_paths: int
    compatibility_failed_rank_reduction: float
    compatibility_feature_digest: str
    compatibility_model_digest: str
    cluster_compatibility_target_used: bool
    clusters_of_clusters_gate_passed: bool
    honest_status: str


def _obligation_descriptor(action, root, *, root_color, child_color,
                           distance_bin, incoming, patterns):
    tokens = {
        ("obligation-colors", str(root_color), str(child_color)),
        ("obligation-distance", int(distance_bin)),
    }
    tokens.update(("obligation-action", token) for token in action.tokens)
    tokens.update(("obligation-root", token) for token in root.tokens)
    tokens.update(("obligation-role", role, count)
                  for role, count in incoming.roles)
    tokens.update(("obligation-pattern", pattern) for pattern in patterns)
    return CandidateIncidenceDescriptor(tuple(sorted(tokens, key=repr)))


def _program(sources):
    raw = tuple(local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES)
        for source in sources[:TRAINING_GROUPS])
    prototypes = learn_recurrent_cluster_prototypes(raw, minimum_groups=2)
    markings = tuple(learn_recursive_connection_marking(
        source.seed_positions, map_to_prototypes(types, prototypes),
        tuple(source.truth), HIDDEN_UNIT, minimum_positive_support=1,
        minimum_purity=1e-9, target_colors=tuple(source.truth.values()))
        for source, types in zip(sources[:TRAINING_GROUPS], raw))
    positives = tuple(tuple(state for state, row in marking.evidence.items()
                             if row.positive > 0) for marking in markings)
    connection = merge_recursive_connection_markings(
        markings, minimum_positive_support=2, minimum_positive_groups=2,
        minimum_purity=.5, positive_states_by_marking=positives)
    return prototypes, connection


def _all_paths(sources, prototypes, connection):
    groups = []
    for source in sources:
        types = local_cluster_types(
            source.seed_positions, source.seed_species, CLUSTER_EDGES)
        proposals = _bounded(connection, source, types)
        action_descriptors = candidate_incidence_descriptors(
            proposals, distance_scale=HIDDEN_UNIT,
            neighborhood_reach=3., distance_bin_width=.25,
            maximum_neighbors=8,
            occupied_positions=source.seed_positions,
            occupied_species=source.seed_species)
        ordered_roots = tuple(sorted(proposals.votes, key=lambda point: (
            -proposals.votes[point],
            -sum(proposals.parent_votes.get(point, {}).values()), point)))
        rows = []
        for root_rank, root in enumerate(ordered_roots, 1):
            if root_rank > max(ROOT_SHORTLISTS):
                break
            root_color = _dominant_source_color(proposals, root)
            positions, colors, future = advance_frontier_configuration(
                connection, proposals, source.seed_positions,
                source.seed_species, (root,), (root_color,), CLUSTER_EDGES,
                source.group, EVALUATION_TARGET_RADIUS)
            root_index = len(positions) - 1
            root_descriptor = successor_state_descriptor(
                future, new_parent_index=root_index,
                new_parent_position=root, occupied_positions=positions,
                minimum_distance=source.minimum_distance,
                distance_scale=HIDDEN_UNIT)
            dependency = (future.causal_endpoint_votes
                          if future.causal_endpoint_votes is not None
                          else future.parent_votes)
            outgoing = successor_outgoing_points(
                future, new_parent_index=root_index,
                occupied_positions=positions,
                minimum_distance=source.minimum_distance)
            children = tuple(sorted(outgoing, key=lambda point: (
                -future.votes[point],
                -dependency.get(point, {}).get(root_index, 0), point))[
                    :CHILD_BRANCHING])
            for child_rank, child in enumerate(children, 1):
                child_color = _dominant_source_color(future, child)
                incoming = port_incidence_state(
                    future, (child,), maximum_roles=8,
                    minimum_multiplicity=1)
                patterns = port_incidence_patterns(
                    future, (child,), maximum_order=2,
                    maximum_patterns=32, roles_per_site=4)
                descriptor = _obligation_descriptor(
                    action_descriptors[root], root_descriptor,
                    root_color=root_color,
                    child_color=child_color,
                    distance_bin=round(
                        math.dist(root, child) / (HIDDEN_UNIT * .5)),
                    incoming=incoming, patterns=patterns)
                rows.append((root_rank, child_rank, root, root_color,
                             child, child_color, descriptor))
        groups.append(tuple(rows))
    return tuple(groups)


def _compatibility_geometry(sources, paths, prototypes):
    """Freeze local clusters-of-clusters features before path labels exist."""
    groups = []
    for source, rows in zip(sources, paths):
        context = fit_prototype_compatibility_context(
            source.seed_positions, source.seed_species, CLUSTER_EDGES,
            prototypes)
        features = []
        for row in rows:
            compatibility = score_prototype_insertions(
                context, (row[2], row[4]), (row[3], row[5]))
            nearest = tuple(sorted(
                source.seed_positions,
                key=lambda point: (math.dist(row[2], point), point))[:8])
            local_center = tuple(sum(point[axis] for point in nearest) /
                                 len(nearest) for axis in range(3))
            normal = tuple(row[2][axis] - local_center[axis]
                           for axis in range(3))
            direction = tuple(row[4][axis] - row[2][axis]
                              for axis in range(3))
            denominator = math.sqrt(sum(value * value for value in normal) *
                                    sum(value * value
                                        for value in direction))
            cosine = (sum(left * right for left, right
                          in zip(normal, direction)) / denominator
                      if denominator > 1e-12 else 0.)
            gain = (math.dist(row[4], local_center) -
                    math.dist(row[2], local_center)) / (HIDDEN_UNIT * .5)
            features.append((
                row[0] / max(ROOT_SHORTLISTS), row[1] / CHILD_BRANCHING,
                *compatibility.inserted_residuals,
                compatibility.existing_residual_delta,
                compatibility.total_residual_delta,
                compatibility.affected_existing_atoms,
                round(cosine / .1), round(gain),
                float(row[3] == row[5]), math.dist(row[2], row[4])))
        groups.append(tuple(features))
    return tuple(groups)


def _compatibility_value(paths, geometry, labels):
    validation_paths = paths[TRAINING_GROUPS:]
    validation_geometry = geometry[TRAINING_GROUPS:]
    validation_labels = labels[TRAINING_GROUPS:]
    base_cache = {}

    def base_marking(excluded):
        key = frozenset(excluded)
        if key not in base_cache:
            examples = tuple(IncidenceTokenExample(
                group, row[6], label)
                for group, (rows, truth) in enumerate(zip(
                    validation_paths, validation_labels))
                if group not in key for row, label in zip(rows, truth))
            base_cache[key] = fit_incidence_token_marking(
                examples, minimum_support=24,
                minimum_groups=max(2, 6 - len(key)), shrinkage=1.)
        return base_cache[key]

    def features(group, index, marking):
        row = validation_paths[group][index]
        return (
            score_incidence_descriptor(marking, row[6]),
            score_incidence_descriptor_by_channel(marking, row[6]),
            *validation_geometry[group][index])

    selected = []
    exact_ranks = []
    models = []
    all_features = []
    for heldout in range(len(validation_paths)):
        examples = []
        for group in range(len(validation_paths)):
            if group == heldout:
                continue
            marking = base_marking((heldout, group))
            rows = tuple((features(group, index, marking), label, index)
                         for index, label in enumerate(
                             validation_labels[group]))
            positive = tuple(row for row in rows if row[1])
            negative = tuple(sorted(
                (row for row in rows if not row[1]),
                key=lambda row: (-row[0][0], row[0][7], row[2]))[
                    :max(8, COMPATIBILITY_NEGATIVE_RATIO * len(positive))])
            examples.extend(BandTrainingExample(
                group, row, label, 1)
                for row, label, _index in (*positive, *negative))
        model = fit_linear_section(
            tuple(examples), COMPATIBILITY_RIDGE,
            COMPATIBILITY_FEATURE_NAMES, steps=COMPATIBILITY_FIT_STEPS)
        models.append((model.means, model.scales, model.weights,
                       model.intercept, model.ridge))
        heldout_marking = base_marking((heldout,))
        heldout_features = tuple(features(
            heldout, index, heldout_marking)
            for index in range(len(validation_paths[heldout])))
        all_features.extend((heldout, index, row)
                            for index, row in enumerate(heldout_features))
        order = tuple(sorted(range(len(heldout_features)), key=lambda index: (
            -score_band(model, heldout_features[index]), index)))
        selected.append(validation_labels[heldout][order[0]])
        exact_ranks.append(next(rank for rank, index in enumerate(order, 1)
                                if validation_labels[heldout][index]))
    return (tuple(selected), tuple(exact_ranks),
            hashlib.sha256(repr(tuple(all_features)).encode()).hexdigest(),
            hashlib.sha256(repr(tuple(models)).encode()).hexdigest())


def evaluate() -> IQCRecurrentPathSelectorAudit:
    sources, _counts, _origin = _expanded_fixture()
    prototypes, connection = _program(sources)
    paths = _all_paths(sources, prototypes, connection)
    compatibility_geometry = _compatibility_geometry(
        sources, paths, prototypes)
    # Labels enter only after every target-free descriptor and compatibility
    # feature above is frozen.
    labels = tuple(tuple(
        source.truth.get(_key(row[2])) == row[3] and
        source.truth.get(_key(row[4])) == row[5]
        for row in rows) for source, rows in zip(sources, paths))
    audits = []
    for root_limit in ROOT_SHORTLISTS:
        limited = tuple(tuple((row, label) for row, label in zip(rows, truth)
                              if row[0] <= root_limit)
                        for rows, truth in zip(paths, labels))
        for minimum_support, minimum_groups, shrinkage in MARKING_GRID:
            selected = []
            exact_ranks = []
            supported = []
            digests = []
            for heldout in range(TRAINING_GROUPS, len(limited)):
                examples = tuple(IncidenceTokenExample(
                    index, row[6], label)
                    for index, group in enumerate(limited[TRAINING_GROUPS:],
                                                  TRAINING_GROUPS)
                    if index != heldout for row, label in group)
                marking = fit_incidence_token_marking(
                    examples, minimum_support=minimum_support,
                    minimum_groups=minimum_groups, shrinkage=shrinkage)
                supported.append(len(marking.token_weights))
                digests.append(incidence_marking_digest(marking))
                ranked = sorted(limited[heldout], key=lambda item: (
                    -score_incidence_descriptor(marking, item[0][6]),
                    item[0][0], item[0][1], item[0][2], item[0][4]))
                selected.append(bool(ranked and ranked[0][1]))
                exact_ranks.append(next((
                    rank for rank, (_row, label) in enumerate(ranked, 1)
                    if label), len(ranked) + 1))
            validation_limited = limited[TRAINING_GROUPS:]
            exact_counts = tuple(sum(label for _row, label in group)
                                 for group in validation_limited)
            audits.append(SelectorAudit(
                root_limit, minimum_support, minimum_groups, shrinkage,
                tuple(len(group) for group in validation_limited), exact_counts,
                tuple(selected), sum(selected), tuple(exact_ranks),
                tuple(supported),
                hashlib.sha256(repr(tuple(digests)).encode()).hexdigest()))
    selected = max(audits, key=lambda row: (
        all(value > 0 for value in row.exact_paths_by_group),
        row.selected_exact_paths, min(row.exact_paths_by_group),
        -row.root_shortlist, row.minimum_groups, row.minimum_support))
    supply = all(value > 0 for value in selected.exact_paths_by_group)
    validation_groups = len(sources) - TRAINING_GROUPS
    passed = supply and selected.selected_exact_paths == validation_groups
    (compatibility_selected, compatibility_ranks, compatibility_digest,
     compatibility_model_digest) = _compatibility_value(
         paths, compatibility_geometry, labels)
    compatibility_passed = (
        supply and sum(compatibility_selected) == validation_groups)
    baseline_failed_rank = selected.first_exact_ranks_by_group[4]
    compatibility_failed_rank = compatibility_ranks[4]
    digest = hashlib.sha256(repr(tuple(tuple(
        (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        for row in group) for group in paths)).encode()).hexdigest()
    return IQCRecurrentPathSelectorAudit(
        TRAINING_GROUPS, validation_groups, len(prototypes),
        len(connection.accepted_states), CHILD_BRANCHING, tuple(audits),
        selected.root_shortlist,
        (selected.minimum_support, selected.minimum_groups,
         selected.shrinkage), selected.selected_exact_by_group,
        selected.selected_exact_paths, supply, passed, True, False, digest,
        COMPATIBILITY_FEATURE_NAMES, COMPATIBILITY_NEGATIVE_RATIO,
        COMPATIBILITY_RIDGE, compatibility_selected, compatibility_ranks,
        sum(compatibility_selected),
        baseline_failed_rank / compatibility_failed_rank,
        compatibility_digest, compatibility_model_digest, False,
        compatibility_passed,
        ("recurrent path value selects every heldout IQC continuation"
         if passed else
         "recurrent path value does not yet select every IQC continuation"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
