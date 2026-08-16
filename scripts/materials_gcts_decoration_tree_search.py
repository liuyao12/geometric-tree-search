#!/usr/bin/env python3
"""Bounded target-blind tree search over optional cluster decorations.

Geometry and the finite decoration alternatives are frozen before this module
is called.  The search API has no reference species/target argument: it can
use seed labels, exact overlap equality, and a train-fitted bounded marking.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass

from materials_gcts_decoration_cover_solver_benchmark import _domain, _local_atoms


@dataclass(frozen=True)
class DecorationAction:
    action_id: int
    occurrence_id: int
    geometry_type: int
    decoration_id: int
    atom_labels: tuple[tuple[int, str], ...]
    train_observations: int


@dataclass(frozen=True)
class FrozenDecorationMarking:
    decoration_counts: tuple[tuple[int, tuple[tuple[int, int], ...]], ...]
    exact_connection_counts: tuple[
        tuple[tuple[int, int, int, object], tuple[tuple[int, int], ...]], ...]
    connection_counts: tuple[
        tuple[tuple[int, int, object], tuple[tuple[int, int], ...]], ...]
    minimum_support: int = 2
    maximum_incoming: int = 2


@dataclass(frozen=True)
class FrozenDecorationProblem:
    atom_count: int
    actions: tuple[DecorationAction, ...]
    incoming_relations: tuple[
        tuple[int, tuple[tuple[int, int, int, object], ...]], ...]
    candidate_digest: str


@dataclass(frozen=True)
class DecorationSearchPolicy:
    strategy: str = "gcts"
    beam_width: int = 12
    maximum_depth: int = 64
    maximum_branches_per_state: int = 12
    minimum_overlap_atoms: int = 1
    marking_weight: float = .35
    overlap_weight: float = .02
    minimum_marking_probability: float = 0.


@dataclass(frozen=True)
class DecorationSearchStep:
    depth: int
    frontier_states: int
    eligible_actions: int
    generated_branches: int
    retained_states: int
    best_labelled_atoms: int


@dataclass(frozen=True)
class DecorationSearchTrace:
    policy: DecorationSearchPolicy
    candidate_digest: str
    seed_atoms: int
    labelled_species: tuple[tuple[int, str], ...]
    selected_actions: tuple[int, ...]
    selected_occurrences: tuple[tuple[int, int], ...]
    steps: tuple[DecorationSearchStep, ...]
    expanded_nodes: int
    conflict_rejections: int
    beam_pruned_states: int
    reached_fixed_point: bool
    target_used: bool


@dataclass(frozen=True)
class _State:
    labels: tuple[str | None, ...]
    selected: tuple[tuple[int, int], ...]
    action_ids: tuple[int, ...]
    objective: float


def fit_decoration_marking(occurrence_decorations, relations,
                           minimum_support=2, maximum_incoming=2):
    """Fit bounded connection sections from train occurrence decorations."""
    if maximum_incoming not in (1, 2):
        raise ValueError("marking order must be one or two")
    by_type = defaultdict(Counter)
    exact = defaultdict(Counter)
    backoff = defaultdict(Counter)
    occurrence_type = {}
    for occurrence_id, (geometry_type, decoration_id) in \
            occurrence_decorations.items():
        occurrence_type[occurrence_id] = geometry_type
        by_type[geometry_type][decoration_id] += 1
    for parent_id, child_id, parent_type, child_type, orbit_key in relations:
        if parent_id not in occurrence_decorations or \
                child_id not in occurrence_decorations:
            continue
        parent_decoration = occurrence_decorations[parent_id][1]
        child_decoration = occurrence_decorations[child_id][1]
        exact[(parent_decoration, parent_type, child_type,
               orbit_key)][child_decoration] += 1
        backoff[(parent_type, child_type, orbit_key)][child_decoration] += 1

    def freeze(table):
        return tuple(sorted(
            ((key, tuple(sorted(counts.items())))
             for key, counts in table.items()
             if sum(counts.values()) >= minimum_support), key=repr))

    return FrozenDecorationMarking(
        tuple(sorted((key, tuple(sorted(value.items())))
                     for key, value in by_type.items())),
        freeze(exact), freeze(backoff), minimum_support, maximum_incoming)


def compile_decoration_problem(positions, occurrences, supports, prototypes,
                               alternatives, decoration_ids,
                               decoration_observations, relations):
    """Compile the immutable action set using geometry and train alternatives."""
    actions = []
    for occurrence in occurrences:
        atoms = _local_atoms(
            prototypes[occurrence.type_id], occurrence,
            supports[occurrence.occurrence_id], positions)
        seen = set()
        for canonical in alternatives[occurrence.type_id]:
            decoration_id = decoration_ids[occurrence.type_id, canonical]
            # `_domain` expands every proper rotational gauge.  Calling it for
            # one canonical alternative preserves the exact terminal identity.
            for assignment in _domain(
                    prototypes[occurrence.type_id], atoms, (canonical,)):
                key = tuple(zip(atoms, assignment))
                if key in seen:
                    continue
                seen.add(key)
                actions.append(DecorationAction(
                    len(actions), occurrence.occurrence_id,
                    occurrence.type_id, decoration_id, key,
                    decoration_observations[occurrence.type_id,
                                            decoration_id]))
    actions.sort(key=lambda item: (
        item.occurrence_id, item.geometry_type, item.decoration_id,
        item.atom_labels))
    actions = tuple(DecorationAction(
        index, item.occurrence_id, item.geometry_type, item.decoration_id,
        item.atom_labels, item.train_observations)
                    for index, item in enumerate(actions))
    incoming = defaultdict(list)
    occurrence_ids = {item.occurrence_id for item in occurrences}
    for parent_id, child_id, parent_type, child_type, orbit_key in relations:
        if parent_id in occurrence_ids and child_id in occurrence_ids:
            incoming[child_id].append(
                (parent_id, parent_type, child_type, orbit_key))
    frozen_incoming = tuple(sorted(
        (key, tuple(sorted(set(value), key=repr)))
        for key, value in incoming.items()))
    payload = tuple((item.occurrence_id, item.geometry_type,
                     item.decoration_id, item.atom_labels)
                    for item in actions)
    digest = hashlib.sha256(repr(payload).encode()).hexdigest()
    return FrozenDecorationProblem(
        len(positions), actions, frozen_incoming, digest)


def _log_probability(counts, label):
    total = sum(counts.values())
    classes = max(1, len(counts))
    return math.log((counts.get(label, 0) + 1.) / (total + classes))


def search_decoration_cover(problem, seed_species, marking, policy):
    if policy.strategy not in ("modal", "gcts"):
        raise ValueError("strategy must be modal or gcts")
    if policy.beam_width <= 0 or policy.maximum_depth <= 0 or \
            policy.maximum_branches_per_state <= 0:
        raise ValueError("search bounds must be positive")
    if not 0. <= policy.minimum_marking_probability <= 1.:
        raise ValueError("marking probability threshold must be in [0, 1]")
    if any(atom < 0 or atom >= problem.atom_count
           for atom in seed_species):
        raise ValueError("seed atom is outside the supplied geometry")

    type_counts = {key: Counter(dict(value))
                   for key, value in marking.decoration_counts}
    exact = {key: Counter(dict(value))
             for key, value in marking.exact_connection_counts}
    backoff = {key: Counter(dict(value))
               for key, value in marking.connection_counts}
    incoming = dict(problem.incoming_relations)
    actions_by_atom = defaultdict(list)
    for action in problem.actions:
        if any(atom in seed_species and seed_species[atom] != species
               for atom, species in action.atom_labels):
            continue
        for atom, _species in action.atom_labels:
            actions_by_atom[atom].append(action)
    initial_labels = [None] * problem.atom_count
    for atom, species in seed_species.items():
        initial_labels[atom] = species
    initial = _State(tuple(initial_labels), (), (), 0.)
    beam = (initial,)
    best = initial
    steps = []
    expanded = conflicts = pruned = 0
    fixed_point = False

    def marking_score(action, selected):
        base = _log_probability(
            type_counts.get(action.geometry_type, Counter()),
            action.decoration_id)
        if policy.strategy == "modal":
            return base
        selected_map = dict(selected)
        values = []
        for parent_id, parent_type, child_type, orbit_key in \
                incoming.get(action.occurrence_id, ()):
            if parent_id not in selected_map:
                continue
            parent_decoration = selected_map[parent_id]
            counts = exact.get((parent_decoration, parent_type, child_type,
                                orbit_key))
            if counts is None:
                counts = backoff.get((parent_type, child_type, orbit_key))
            if counts:
                values.append(_log_probability(counts,
                                               action.decoration_id))
        if not values:
            return base
        values.sort(reverse=True)
        return sum(values[:marking.maximum_incoming]) / \
            min(len(values), marking.maximum_incoming)

    for depth in range(1, policy.maximum_depth + 1):
        next_by_key = {}
        eligible_total = generated = 0
        for state in beam:
            expanded += 1
            selected_occurrences = {key for key, _value in state.selected}
            frontier_ids = set()
            for atom, species in enumerate(state.labels):
                if species is not None:
                    frontier_ids.update(item.action_id
                                        for item in actions_by_atom[atom])
            ranked = []
            for action_id in frontier_ids:
                action = problem.actions[action_id]
                if action.occurrence_id in selected_occurrences:
                    continue
                overlap = new_atoms = 0
                conflict = False
                for atom, species in action.atom_labels:
                    existing = state.labels[atom]
                    if existing is None:
                        new_atoms += 1
                    elif existing == species:
                        overlap += 1
                    else:
                        conflict = True
                        break
                if conflict:
                    conflicts += 1
                    continue
                if overlap < policy.minimum_overlap_atoms or new_atoms == 0:
                    continue
                mark = marking_score(action, state.selected)
                if math.exp(mark) + 1e-15 < \
                        policy.minimum_marking_probability:
                    continue
                increment = (new_atoms + policy.overlap_weight * overlap +
                             policy.marking_weight * mark)
                ranked.append((increment, new_atoms, overlap,
                               action.train_observations, -action.action_id,
                               action))
            ranked.sort(reverse=True, key=lambda item: item[:-1])
            eligible_total += len(ranked)
            for increment, _new, _overlap, _support, _neg_id, action in \
                    ranked[:policy.maximum_branches_per_state]:
                labels = list(state.labels)
                for atom, species in action.atom_labels:
                    labels[atom] = species
                selected = tuple(sorted(
                    state.selected + ((action.occurrence_id,
                                       action.decoration_id),)))
                child = _State(tuple(labels), selected,
                               state.action_ids + (action.action_id,),
                               state.objective + increment)
                key = (child.labels, child.selected)
                previous = next_by_key.get(key)
                if previous is None or child.objective > previous.objective:
                    next_by_key[key] = child
                generated += 1
        if not next_by_key:
            fixed_point = True
            break
        ordered = sorted(next_by_key.values(), key=lambda state: (
            sum(value is not None for value in state.labels),
            state.objective, tuple(-item for item in state.action_ids)),
                         reverse=True)
        pruned += max(0, len(ordered) - policy.beam_width)
        beam = tuple(ordered[:policy.beam_width])
        candidate_best = beam[0]
        if (sum(value is not None for value in candidate_best.labels),
                candidate_best.objective) > \
                (sum(value is not None for value in best.labels),
                 best.objective):
            best = candidate_best
        steps.append(DecorationSearchStep(
            depth, len(beam), eligible_total, generated, len(beam),
            sum(value is not None for value in best.labels)))

    inferred = tuple((atom, species)
                     for atom, species in enumerate(best.labels)
                     if species is not None)
    return DecorationSearchTrace(
        policy, problem.candidate_digest, len(seed_species), inferred,
        best.action_ids, best.selected, tuple(steps), expanded, conflicts,
        pruned, fixed_point, False)
