#!/usr/bin/env python3
"""Learn and execute finite proper transitions between frontier-state types.

This layer consumes a :mod:`materials_gcts_frontier_state_grammar` and the same
target-free wave snapshots.  It never sees a material label, cell, target, or
prescribed scale.  Child occurrences in wave ``t+1`` are assigned to the
nearest compatible finite parent occurrence in wave ``t``.  The complete child
set is expressed in the parent frame and quotiented jointly by the parent's
proper symmetries and independently by every child's proper symmetries.

A stationary rule needs the identical normalized child production on two
consecutive transitions, at least two independent parent occurrences in each,
and more than one self-similar child.  The executor then applies that frozen
rule to state instances; it has no scoring or target API.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass

from materials_gcts_frontier_state_grammar import (
    FrontierStateGrammar, FrontierStateOccurrence, FrontierStateType,
    FrontierWaveSnapshot)
from materials_gcts_oriented_overlap_ports import (
    ClusterPrototype, IDENTITY, Matrix,
    is_proper_rotation, make_prototype, matmul, matvec, transpose)

Point = tuple[float, float, float]


@dataclass(frozen=True)
class FrontierChildPlacement:
    child_type: int
    relative_scale: float
    relative_rotation: Matrix
    relative_translation: Point


@dataclass(frozen=True)
class FrontierTransitionObservation:
    source_wave: int
    parent_members: tuple[int, ...]
    placements: tuple[FrontierChildPlacement, ...]
    canonical_code: tuple


@dataclass(frozen=True)
class FrontierTransitionRule:
    rule_id: int
    parent_type: int
    child_type: int
    child_placements: tuple[FrontierChildPlacement, ...]
    canonical_code: tuple
    observations: tuple[FrontierTransitionObservation, ...]
    independent_transition_waves: int
    description_saving: int
    stationary: bool


@dataclass(frozen=True)
class FrontierTransitionGrammar:
    rules: tuple[FrontierTransitionRule, ...]
    stationary_rule_ids: tuple[int, ...]
    proper_state_types: int
    packed_occurrences: int
    transition_observations: int
    target_used: bool
    grammar_digest: str


@dataclass(frozen=True)
class GeneratedFrontierState:
    type_id: int
    scale: float
    rotation: Matrix
    translation: Point


@dataclass(frozen=True)
class FrontierTransitionExecution:
    rule_id: int
    parents: tuple[GeneratedFrontierState, ...]
    children: tuple[GeneratedFrontierState, ...]
    sites: tuple[tuple[object, Point], ...]
    exact_colored_union: bool
    collision_free: bool
    target_used: bool


@dataclass(frozen=True)
class SymbolicFrontierExpansion:
    rule_id: int
    action_counts: tuple[int, ...]
    represented_site_counts: tuple[int, ...]
    million_site_action: int | None


def _subtract(left: Point, right: Point) -> Point:
    return tuple(left[axis] - right[axis]
                 for axis in range(3))  # type: ignore[return-value]


def _add(left: Point, right: Point) -> Point:
    return tuple(left[axis] + right[axis]
                 for axis in range(3))  # type: ignore[return-value]


def _scale(factor: float, point: Point) -> Point:
    return tuple(factor * value for value in point)  # type: ignore[return-value]


def _matrix_key(matrix: Matrix, tolerance: float):
    return tuple(round(value / tolerance)
                 for row in matrix for value in row)


def _point_key(point: Point, tolerance: float):
    return tuple(round(value / tolerance) for value in point)


def _prototype(state: FrontierStateType, tolerance: float) -> ClusterPrototype:
    return make_prototype(state.type_id, tuple(zip(
        state.prototype_species, state.prototype_positions)), tolerance)


def _pack_by_type(grammar: FrontierStateGrammar):
    """Keep atom-disjoint occurrences independently for every state type."""
    packed = defaultdict(list)
    for state in grammar.recurring_state_types:
        by_wave = defaultdict(list)
        for occurrence in state.occurrences:
            if occurrence.proper_pose_verified:
                by_wave[occurrence.wave].append(occurrence)
        for wave, occurrences in by_wave.items():
            used = set()
            for occurrence in sorted(
                    occurrences, key=lambda row: row.member_indices):
                if used.intersection(occurrence.member_indices):
                    continue
                used.update(occurrence.member_indices)
                packed[state.type_id, wave].append(occurrence)
    return {key: tuple(value) for key, value in packed.items()}


def _raw_placement(parent: FrontierStateOccurrence,
                   child: FrontierStateOccurrence, child_type: int):
    inverse = transpose(parent.rotation)
    translation = matvec(inverse, _scale(
        1.0 / parent.scale,
        _subtract(child.translation, parent.translation)))
    rotation = matmul(inverse, child.rotation)
    return FrontierChildPlacement(
        child_type, child.scale / parent.scale, rotation, translation)


def _canonical_code(parent_prototype, child_prototype, placements,
                    child_signature, tolerance):
    alternatives = []
    for parent_symmetry in parent_prototype.proper_symmetries:
        inverse_parent = transpose(parent_symmetry)
        records = []
        for placement in placements:
            translation = matvec(
                inverse_parent, placement.relative_translation)
            base_rotation = matmul(
                inverse_parent, placement.relative_rotation)
            rotation = min(
                (matmul(base_rotation, symmetry)
                 for symmetry in child_prototype.proper_symmetries),
                key=lambda value: _matrix_key(value, tolerance))
            records.append((
                child_signature,
                round(placement.relative_scale / tolerance),
                _point_key(translation, tolerance),
                _matrix_key(rotation, tolerance)))
        alternatives.append(tuple(sorted(records, key=repr)))
    return min(alternatives, key=repr)


def _assign_children(parents, children):
    result = defaultdict(list)
    for child in children:
        parent = min(parents, key=lambda candidate: (
            math.dist(candidate.translation, child.translation),
            candidate.member_indices))
        result[parent].append(child)
    return result


def compile_frontier_transition_grammar(
    state_grammar: FrontierStateGrammar,
    snapshots: tuple[FrontierWaveSnapshot, ...], *,
    tolerance: float = 1e-6,
) -> FrontierTransitionGrammar:
    if tolerance <= 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    if state_grammar.target_used or any(wave.target_used for wave in snapshots):
        return FrontierTransitionGrammar(
            (), (), 0, 0, 0, True,
            hashlib.sha256(b"target-tainted-frontier").hexdigest())
    waves = {wave.wave: wave for wave in snapshots}
    if len(waves) != len(snapshots):
        raise ValueError("wave numbers must be unique")
    states = {state.type_id: state
              for state in state_grammar.recurring_state_types}
    proper = {type_id: state for type_id, state in states.items()
              if state.occurrences and all(
                  occurrence.proper_pose_verified
                  for occurrence in state.occurrences)}
    prototypes = {type_id: _prototype(state, tolerance)
                  for type_id, state in proper.items()}
    packed = _pack_by_type(state_grammar)
    observations = []
    wave_numbers = sorted(waves)
    for source_wave in wave_numbers:
        if source_wave + 1 not in waves:
            continue
        for parent_type, parent_state in proper.items():
            parents = packed.get((parent_type, source_wave), ())
            if not parents:
                continue
            for child_type, child_state in proper.items():
                children = packed.get((child_type, source_wave + 1), ())
                if not children:
                    continue
                assigned = _assign_children(parents, children)
                for parent, rows in assigned.items():
                    placements = tuple(_raw_placement(
                        parent, child, child_type) for child in rows)
                    code = _canonical_code(
                        prototypes[parent_type], prototypes[child_type],
                        placements, child_state.normalized_signature,
                        tolerance)
                    observations.append((
                        parent_type, child_type, code,
                        FrontierTransitionObservation(
                            source_wave, parent.member_indices, placements,
                            code)))

    grouped = defaultdict(list)
    for parent_type, child_type, code, observation in observations:
        grouped[parent_type, child_type, code].append(observation)
    rows = []
    for (parent_type, child_type, code), items in grouped.items():
        items = tuple(sorted(items, key=lambda row: (
            row.source_wave, row.parent_members)))
        waves_seen = sorted({item.source_wave for item in items})
        child_count = len(items[0].placements)
        if any(len(item.placements) != child_count for item in items):
            raise AssertionError("canonical production changed child count")
        saving = len(items) * child_count - (child_count + len(items))
        stationary = (
            child_count > 1 and saving > 0 and
            any(wave + 1 in waves_seen for wave in waves_seen) and
            all(sum(item.source_wave == wave for item in items) >= 2
                for wave in waves_seen
                if wave + 1 in waves_seen) and
            all(sum(item.source_wave == wave + 1 for item in items) >= 2
                for wave in waves_seen if wave + 1 in waves_seen))
        rows.append((parent_type, child_type, code, items,
                     len(waves_seen), saving, stationary))
    rows.sort(key=lambda row: (row[0], row[1], repr(row[2])))
    rules = tuple(FrontierTransitionRule(
        rule_id, parent_type, child_type, items[0].placements, code, items,
        independent, saving, stationary)
        for rule_id, (parent_type, child_type, code, items,
                      independent, saving, stationary) in enumerate(rows))
    payload = tuple((
        rule.parent_type, rule.child_type, rule.canonical_code,
        tuple(item.source_wave for item in rule.observations),
        rule.stationary) for rule in rules)
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=repr
    ).encode()).hexdigest()
    return FrontierTransitionGrammar(
        rules, tuple(rule.rule_id for rule in rules if rule.stationary),
        len(proper), sum(len(value) for value in packed.values()),
        len(observations), False, digest)


def as_generated_state(type_id: int, occurrence: FrontierStateOccurrence):
    return GeneratedFrontierState(
        type_id, occurrence.scale, occurrence.rotation,
        occurrence.translation)


def execute_frontier_transition(
    grammar: FrontierTransitionGrammar,
    states: tuple[FrontierStateType, ...], rule_id: int,
    parents: tuple[GeneratedFrontierState, ...], *,
    occupied_sites: tuple[tuple[object, Point], ...] = (),
    tolerance: float = 1e-6,
) -> FrontierTransitionExecution:
    if grammar.target_used:
        raise ValueError("target-tainted transition grammars cannot execute")
    rules = {rule.rule_id: rule for rule in grammar.rules}
    if rule_id not in rules:
        raise ValueError("unknown transition rule")
    rule = rules[rule_id]
    if any(parent.type_id != rule.parent_type for parent in parents):
        raise ValueError("parent state type does not match the rule")
    state_by_id = {state.type_id: state for state in states}
    parent_prototype = _prototype(state_by_id[rule.parent_type], tolerance)
    child_prototype = _prototype(state_by_id[rule.child_type], tolerance)
    if any(placement.relative_scale <= 0 or
           not math.isfinite(placement.relative_scale) or
           not is_proper_rotation(placement.relative_rotation)
           for placement in rule.child_placements):
        raise ValueError("transition placements must be finite proper similarities")
    if _canonical_code(
            parent_prototype, child_prototype, rule.child_placements,
            state_by_id[rule.child_type].normalized_signature,
            tolerance) != rule.canonical_code:
        raise ValueError("transition rule geometry does not match its frozen code")
    children = []
    rendered = {}
    exact = True
    for parent in parents:
        for placement in rule.child_placements:
            child = GeneratedFrontierState(
                placement.child_type,
                parent.scale * placement.relative_scale,
                matmul(parent.rotation, placement.relative_rotation),
                _add(parent.translation, matvec(
                    parent.rotation, _scale(
                        parent.scale, placement.relative_translation))))
            children.append(child)
            prototype = state_by_id[child.type_id]
            for species, local in zip(
                    prototype.prototype_species,
                    prototype.prototype_positions):
                point = _add(child.translation, matvec(
                    child.rotation, _scale(child.scale, local)))
                key = _point_key(point, tolerance)
                if key in rendered and rendered[key][0] != species:
                    exact = False
                rendered[key] = species, point
    sites = tuple(rendered[key] for key in sorted(rendered))
    nominal = min((
        child.scale * math.dist(left, right)
        for child in children
        for index, left in enumerate(
            state_by_id[child.type_id].prototype_positions)
        for right in state_by_id[child.type_id].prototype_positions[index + 1:]
        if math.dist(left, right) > tolerance), default=tolerance)
    exclusion = max(tolerance, nominal * .45)
    collision_free = True
    combined = tuple(occupied_sites) + sites
    for left in range(len(combined)):
        for right in range(left + 1, len(combined)):
            distance = math.dist(combined[left][1], combined[right][1])
            if distance <= tolerance:
                if combined[left][0] != combined[right][0]:
                    collision_free = False
            elif distance < exclusion:
                collision_free = False
    return FrontierTransitionExecution(
        rule_id, parents, tuple(children),
        sites, exact, collision_free, False)


def symbolic_frontier_expansion(
    rule: FrontierTransitionRule, state: FrontierStateType,
    seed_instances: int, actions: int,
) -> SymbolicFrontierExpansion:
    if not rule.stationary:
        raise ValueError("only stationary rules may be expanded symbolically")
    if rule.parent_type != rule.child_type or any(
            placement.child_type != rule.parent_type
            for placement in rule.child_placements):
        raise ValueError("symbolic self-feed needs one recurring state type")
    if seed_instances <= 0 or actions < 0:
        raise ValueError("seed_instances must be positive and actions nonnegative")
    counts = [seed_instances]
    sites = [seed_instances * state.support_size]
    million = 0 if sites[0] >= 1_000_000 else None
    for action in range(1, actions + 1):
        counts.append(counts[-1] * len(rule.child_placements))
        sites.append(counts[-1] * state.support_size)
        if million is None and sites[-1] >= 1_000_000:
            million = action
    return SymbolicFrontierExpansion(
        rule.rule_id, tuple(counts), tuple(sites), million)
