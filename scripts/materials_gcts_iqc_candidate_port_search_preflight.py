#!/usr/bin/env python3
"""Two-step IQC GCTS search over individual cluster-placement ports.

Candidate supply is target-free: one canonical representative of each local
incidence descriptor is ranked by the frozen recursive connection score, and
the first 128 classes are expanded.  Each root-to-child edge is then an exact
witnessed port action.  The nine known nuclei are evaluated group-heldout; the
reserved confirmation nucleus is never imported or constructed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, replace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample,
    candidate_incidence_descriptors, fit_incidence_token_marking,
    score_incidence_descriptor)
from materials_gcts_iqc_continuous_section_confirmation import (
    COMPLETED_TRAINING_CENTERS)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_port_incidence_preflight import _connection_scores
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_port_incidence_search import (
    FrozenPortIncidencePolicy, PortIncidenceAction, PortIncidenceState,
    port_incidence_patterns, port_incidence_state,
    search_port_incidence_paths)
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types)


ROOT_DESCRIPTOR_CLASSES = 128
BEAM_WIDTH = 128
# One primary role is the carried edge obligation.  Higher-order role
# incidences remain in ``patterns``; proposal multiplicity must not make an
# otherwise equivalent connection outrank another merely by vote volume.
MAXIMUM_ROLES = 1
MINIMUM_ROLE_MULTIPLICITY = 1
MINIMUM_POSITIVE_SUPPORT = 4
MINIMUM_ROLE_PURITY = .9


@dataclass(frozen=True)
class _Pair:
    group: tuple[float, float, float]
    root: PortIncidenceAction
    child: PortIncidenceAction
    successful: bool
    root_successful: bool
    child_successful: bool
    descriptor: CandidateIncidenceDescriptor
    raw_child_score: float


@dataclass(frozen=True)
class _PairContext:
    center: tuple[float, float, float]
    connection: object
    proposals: object
    seed_positions: tuple[tuple[float, float, float], ...]
    seed_species: tuple[str, ...]
    minimum_distance: float


@dataclass(frozen=True)
class CandidatePortSearchPreflight:
    training_centers: tuple[tuple[float, float, float], ...]
    root_descriptor_classes: int
    beam_width: int
    root_candidates_by_group: tuple[int, ...]
    root_positive_by_group: tuple[int, ...]
    connected_pairs_by_group: tuple[int, ...]
    positive_pairs_by_group: tuple[int, ...]
    candidate_graph_digest: str
    fold_policy_digests: tuple[str, ...]
    explored_actions: int
    backtracks: int
    selected_paths: tuple[tuple[str, ...], ...]
    selected_pairs: int
    selected_correct_pairs: int
    selected_false_pairs: int
    selected_action_precision: float
    exact_two_step_groups: int
    satisfied_obligation_mass: int
    reserved_confirmation_center_imported_or_accessed: bool
    preflight_passed: bool
    honest_status: str


def _key(point):
    return tuple(round(value, 6) for value in point)


def _minimum_distance(positions):
    return min(math.dist(left, right)
               for index, left in enumerate(positions)
               for right in positions[index + 1:])


def _empty_state():
    return PortIncidenceState((), 0, 0)


def _primary_state(state):
    if not state.roles:
        return _empty_state()
    # Vote count is evidence strength, not additional port cardinality.
    return PortIncidenceState(((state.roles[0][0], 1),), 0, 0)


def _transition_descriptor(root_state, child_state, patterns,
                           root_color, child_color):
    incoming = tuple(role for role, _count in root_state.roles)
    outgoing = tuple(role for role, _count in child_state.roles)
    tokens = {
        ("color-transition", str(root_color), str(child_color)),
    }
    tokens.update(("incoming", role) for role in incoming)
    tokens.update(("outgoing", role) for role in outgoing)
    tokens.update(("incidence-pattern", pattern) for pattern in patterns)
    for left in incoming:
        for right in outgoing:
            tokens.add(("transition", left, right))
            tokens.add((
                "coarse-transition", left.parent_color, left.source_color,
                left.separation_bin, right.parent_color, right.source_color,
                right.separation_bin))
            tokens.add((
                "chemical-transition", left.parent_color,
                left.source_color, right.parent_color, right.source_color))
    return CandidateIncidenceDescriptor(tuple(sorted(tokens, key=repr)))


def _build_pairs():
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
    pair_groups = []
    contexts = []
    root_counts = []
    root_positive_counts = []
    for group_index, (center, seed, target) in enumerate(zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets)):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        descriptors = candidate_incidence_descriptors(
            proposals, distance_scale=HIDDEN_UNIT,
            occupied_positions=seed.positions,
            occupied_species=seed.species)
        minimum = _minimum_distance(seed.positions)
        contexts.append(_PairContext(
            center, connection, proposals, tuple(seed.positions),
            tuple(seed.species), minimum))
        classes = defaultdict(list)
        for point, descriptor in descriptors.items():
            if not any(math.dist(point, occupied) < minimum - 1e-8
                       for occupied in seed.positions):
                classes[descriptor].append(point)
        scores = _connection_scores(proposals)
        roots = [min(points) for points in classes.values()]
        roots.sort(key=lambda point: (
            -scores[point], repr(descriptors[point]), point))
        roots = tuple(roots[:ROOT_DESCRIPTOR_CLASSES])
        truth = {_key(point): color for point, color in zip(
            target.positions, target.species)}
        root_counts.append(len(roots))
        root_positive_counts.append(sum(
            truth.get(_key(point)) == _dominant_source_color(proposals, point)
            for point in roots))
        pairs = []
        for root_index, point in enumerate(roots):
            color = _dominant_source_color(proposals, point)
            root_successful = truth.get(_key(point)) == color
            positions, colors, future = advance_frontier_configuration(
                connection, proposals, seed.positions, seed.species,
                (point,), (color,), CLUSTER_EDGES, center,
                EVALUATION_TARGET_RADIUS)
            new_parent = len(positions) - 1
            future_scores = _connection_scores(future)
            children = tuple(sorted(
                child for child in future.votes
                if new_parent in future.parent_votes.get(child, {}) and
                not any(math.dist(child, occupied) < minimum - 1e-8
                        for occupied in positions)))
            for child_index, child in enumerate(children):
                child_color = _dominant_source_color(future, child)
                child_successful = truth.get(_key(child)) == child_color
                pair_id = f"g{group_index}:r{root_index}:c{child_index}"
                child_state = _primary_state(port_incidence_state(
                    future, (child,), maximum_roles=MAXIMUM_ROLES,
                    minimum_multiplicity=MINIMUM_ROLE_MULTIPLICITY))
                root_state = port_incidence_state(
                    proposals, (point,), maximum_roles=MAXIMUM_ROLES,
                    minimum_multiplicity=MINIMUM_ROLE_MULTIPLICITY)
                patterns = port_incidence_patterns(
                    future, (child,), maximum_order=2,
                    maximum_patterns=16, roles_per_site=4)
                root_action = PortIncidenceAction(
                    pair_id, root_state,
                    child_state, scores[point], 1,
                    {"point": point, "color": color},
                    patterns)
                child_action = PortIncidenceAction(
                    pair_id + ":child", child_state, _empty_state(),
                    # The root action's learned descriptor already describes
                    # this exact root->child transition.  Adding the raw child
                    # vote score here would double-count the edge and can
                    # override its train-frozen joint value.
                    0., 1,
                    {"point": child, "color": child_color})
                pairs.append(_Pair(
                    center, root_action, child_action,
                    root_successful and child_successful,
                    root_successful, child_successful,
                    _transition_descriptor(
                        root_state, child_state, patterns,
                        color, child_color), future_scores[child]))
        pair_groups.append(tuple(pairs))
    return (tuple(pair_groups), tuple(root_counts),
            tuple(root_positive_counts), tuple(contexts))


def evaluate():
    groups, root_counts, root_positive, _contexts = _build_pairs()
    graph_digest = hashlib.sha256(repr(tuple(
        (pair.group, pair.root, pair.child)
        for group in groups for pair in group)).encode()).hexdigest()
    records = {pair.root.action_id: pair
               for group in groups for pair in group}
    selected_paths = []
    selected_pairs = []
    policy_digests = []
    explored = backtracks = satisfied = 0
    for heldout_index, heldout in enumerate(groups):
        training = tuple(IncidenceTokenExample(
            pair.group, pair.descriptor, pair.successful)
            for index, group in enumerate(groups) if index != heldout_index
            for pair in group)
        marking = fit_incidence_token_marking(
            training, minimum_support=MINIMUM_POSITIVE_SUPPORT,
            minimum_groups=2, shrinkage=.5)
        policy_digests.append(hashlib.sha256(
            repr(marking).encode()).hexdigest())
        children = {pair.root.action_id: pair.child for pair in heldout}
        roots = tuple(replace(
            pair.root, marking_score=score_incidence_descriptor(
                marking, pair.descriptor)) for pair in heldout)
        # Compatibility is enforced by exact state discharge; this empty
        # policy prevents the already-rejected marginal role score from
        # outranking the learned joint transition section.
        policy = FrozenPortIncidencePolicy(
            {}, frozenset(), {}, frozenset(),
            MINIMUM_POSITIVE_SUPPORT, MINIMUM_ROLE_PURITY)
        trace = search_port_incidence_paths(
            roots, lambda action: ((children[action.action_id],)
                                   if action.action_id in children else ()),
            policy, maximum_depth=2, beam_width=BEAM_WIDTH,
            maximum_roles=MAXIMUM_ROLES,
            require_admitted_produced_roles=False,
            require_admitted_action_pattern=False)
        selected_paths.append(tuple(map(str, trace.selected_ids)))
        explored += trace.explored_actions
        backtracks += trace.backtracks
        satisfied += trace.satisfied_obligation_mass
        if trace.selected_ids:
            selected_pairs.append(records[trace.selected_ids[0]])
    correct = sum(pair.successful for pair in selected_pairs)
    selected = len(selected_pairs)
    precision = correct / selected if selected else 0.
    exact_groups = sum(pair.successful for pair in selected_pairs)
    passed = bool(selected == len(COMPLETED_TRAINING_CENTERS) and
                  correct == selected and
                  all(len(path) == 2 for path in selected_paths))
    return CandidatePortSearchPreflight(
        COMPLETED_TRAINING_CENTERS, ROOT_DESCRIPTOR_CLASSES, BEAM_WIDTH,
        root_counts, root_positive,
        tuple(map(len, groups)),
        tuple(sum(pair.successful for pair in group) for group in groups),
        graph_digest, tuple(policy_digests), explored, backtracks,
        tuple(selected_paths), selected, correct, selected - correct,
        precision, exact_groups, satisfied, False, passed,
        ("individual carried-port search passes every known IQC nucleus"
         if passed else
         "individual carried-port search has exact candidate supply but "
         "does not yet select an exact path in every nucleus"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
