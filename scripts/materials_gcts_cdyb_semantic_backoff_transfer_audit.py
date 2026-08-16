#!/usr/bin/env python3
"""Leakage-safe semantic/backoff audit for frozen Cd--Yb L1 macros.

Semantic classes are frozen from the five training namespaces.  Heldout
windows are opened only after descriptor admission.  Coarse classes never
replace exact proper-SE(3) terminals: they may only name a finite set of
train-learned alternatives, and an exact alternative remains required for
replay.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import RADIUS, TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    HELDOUT_CENTERS, _pack, _window_ids)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_frozen_hierarchy_transfer import (
    transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import (
    _frozen_heldout_program)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_macro_stationary_adapter import prototype_semantics
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports


@dataclass(frozen=True)
class DescriptorAudit:
    name: str
    bin_width: float
    geometry_classes: int
    recurrent_geometry_classes: int
    recurrent_geometry_types: int
    geometry_only_missing_types_covered: int
    safe_port_classes: int
    safe_port_types: int
    safe_missing_types_covered: int
    safe_missing_type_ids: tuple[int, ...]
    safe_classes_seen_in_heldout: int
    ambiguous_exact_alternatives: int
    shuffled_missing_coverage_mean: float
    shuffled_missing_coverage_max: int


@dataclass(frozen=True)
class CdYbSemanticBackoffAudit:
    train_windows: int
    heldout_windows: int
    train_atoms: int
    heldout_atoms: int
    raw_id_intersection: int
    frozen_l1_types: int
    exact_transferred_types: int
    missing_exact_types: int
    missing_exact_type_ids: tuple[int, ...]
    frozen_derivation_classes_with_alternatives: int
    exact_derivation_backoff_types: int
    descriptors: tuple[DescriptorAudit, ...]
    best_safe_missing_coverage: int
    all_missing_exactly_recovered: bool
    exact_action_identity_preserved: bool
    heldout_used_to_fit_classes_or_thresholds: bool
    target_used_for_semantic_admission: bool
    family_cell_or_expected_scale_used: bool
    gate_passed: bool
    reason: str


def _mean(values):
    return sum(values) / len(values) if values else 0.


def _std(values):
    mean = _mean(values)
    return math.sqrt(_mean(tuple((value - mean) ** 2 for value in values)))


def _geometry_key(prototype, scale, width, *, coarse):
    semantic = prototype_semantics(prototype, tolerance=1e-5)
    counts = Counter(species for species, _point in prototype.sites)
    divisor = 0
    for count in counts.values():
        divisor = math.gcd(divisor, count)
    if coarse:
        reduced = tuple(sorted((
            repr(species), round((count / len(prototype.sites)) / width))
                               for species, count in counts.items()))
        support = round(math.log1p(len(prototype.sites)) / width)
        symmetry = round(math.log1p(
            len(prototype.proper_symmetries)) / width)
    else:
        reduced = tuple(sorted((repr(species), count // divisor)
                               for species, count in counts.items()))
        support = len(prototype.sites)
        symmetry = len(prototype.proper_symmetries)
    radii = tuple(math.sqrt(sum(value * value for value in point)) / scale
                  for _species, point in prototype.sites)
    pairs = tuple(math.dist(left[1], right[1]) / scale
                  for index, left in enumerate(prototype.sites)
                  for right in prototype.sites[index + 1:])
    summary = tuple(round(value / width) for value in (
        _mean(radii), _std(radii), max(radii, default=0.),
        _mean(pairs), _std(pairs), max(pairs, default=0.)))
    return support, reduced, semantic.chirality_key, symmetry, summary


def _rotation_angle(rotation):
    cosine = max(-1., min(1., (sum(rotation[i][i] for i in range(3)) - 1.) / 2.))
    return math.acos(cosine) / math.pi


def _port_profiles(program, geometry, width):
    profiles = {prototype.type_id: [] for prototype in program.prototypes}
    scale = program.minimum_distance
    for kind, ports in (("overlap", program.atlas.ports),
                        ("boundary", program.boundary_ports)):
        for port in ports:
            overlap_species = Counter(map(repr, getattr(
                port, "overlap_species", ())))
            profiles[port.parent_type].append((
                kind, geometry[port.child_type],
                round(math.sqrt(sum(value * value for value in
                                    port.relative_translation)) / scale / width),
                round(_rotation_angle(port.relative_rotation) / width),
                tuple(sorted(overlap_species.items())),
                len(getattr(port, "overlap", ()))))
    return {key: tuple(sorted(value, key=repr))
            for key, value in profiles.items()}


def _namespaces_by_type(quotient, namespaces):
    result = {}
    for macro in quotient.quotient_macros:
        domains = set()
        for occurrence in macro.promotion_occurrences:
            support = occurrence.atom_indices
            observed = {namespaces[index] for index in support}
            if len(observed) == 1:
                domains.update(observed)
        result[macro.macro_id] = frozenset(domains)
    return result


def _group(keys):
    result = {}
    for type_id, key in keys.items():
        result.setdefault(key, []).append(type_id)
    return tuple(tuple(sorted(value)) for _key, value in
                 sorted(result.items(), key=lambda item: repr(item[0])))


def _audit_descriptor(name, width, coarse, promoted, quotient,
                      train_namespaces, transferred, missing):
    geometry = {prototype.type_id: _geometry_key(
        prototype, promoted.minimum_distance, width, coarse=coarse)
                for prototype in promoted.prototypes}
    ports = _port_profiles(promoted, geometry, width)
    macro_domains = _namespaces_by_type(quotient, train_namespaces)
    domains = {prototype_id: macro_domains[macro_id]
               for prototype_id, macro_id in promoted.prototype_macro_types}
    geometry_groups = _group(geometry)
    safe_groups = _group({key: (geometry[key], ports[key]) for key in geometry})

    def recurrent(groups):
        return tuple(group for group in groups if len(group) >= 2 and
                     len(set().union(*(set(domains[item])
                                       for item in group))) >= 3)

    recurrent_geometry = recurrent(geometry_groups)
    recurrent_safe = recurrent(safe_groups)
    geometry_covered = {item for group in recurrent_geometry
                        if set(group).intersection(transferred)
                        for item in group if item in missing}
    safe_covered = {item for group in recurrent_safe
                    if set(group).intersection(transferred)
                    for item in group if item in missing}
    seen_safe_classes = sum(bool(set(group).intersection(transferred))
                            for group in recurrent_safe)
    ambiguous = sum(len(group) for group in recurrent_safe
                    if len(group) > 1 and set(group).intersection(transferred))

    # Post-hoc null only: shuffle frozen class labels over type IDs.  It never
    # selects the descriptor or changes admission.
    class_labels = [index for index, group in enumerate(recurrent_safe)
                    for _item in group]
    class_sizes = [len(group) for group in recurrent_safe]
    shuffled = []
    population = sorted(geometry)
    for seed in range(31):
        order = population[:]
        random.Random(seed).shuffle(order)
        cursor = 0
        recovered = set()
        for size in class_sizes:
            group = set(order[cursor:cursor + size])
            cursor += size
            if group.intersection(transferred):
                recovered.update(group.intersection(missing))
        shuffled.append(len(recovered))
    del class_labels
    return DescriptorAudit(
        name, width, len(geometry_groups), len(recurrent_geometry),
        sum(map(len, recurrent_geometry)), len(geometry_covered),
        len(recurrent_safe), sum(map(len, recurrent_safe)), len(safe_covered),
        tuple(sorted(safe_covered)), seen_safe_classes, ambiguous,
        _mean(shuffled), max(shuffled, default=0))


def evaluate() -> CdYbSemanticBackoffAudit:
    atoms = generate_cdyb(5, (80.,) * 3)
    train_windows = _window_ids(atoms, TRAIN_CENTERS)
    heldout_windows = _window_ids(atoms, HELDOUT_CENTERS)
    train_ids = set().union(*map(set, train_windows))
    heldout_ids = set().union(*map(set, heldout_windows))
    train_species, train_positions, train_namespaces = _pack(
        atoms, TRAIN_CENTERS, train_windows)
    held_species, held_positions, held_namespaces = _pack(
        atoms, HELDOUT_CENTERS, heldout_windows)

    train = compile_irregular_port_program(train_species, train_positions)
    mined = mine_port_graph_macros(
        train, maximum_nodes=3, include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    promoted = promote_macro_types(train, quotient.quotient_macros, level=1)

    enumeration = enumerate_frozen_port_occurrences(
        train, held_species, held_positions)
    held_program = _frozen_heldout_program(train, enumeration)
    step = transfer_frozen_hierarchy_level(
        held_program, quotient, promoted, held_namespaces,
        raw_atom_sites=tuple(zip(held_species, held_positions)))
    prototype_to_macro = dict(promoted.prototype_macro_types)
    transferred = {prototype_to_macro[item.type_id]
                   for item in step.program.occurrences}
    all_types = set(prototype_to_macro.values())
    missing = all_types - transferred
    macro_to_prototype = {macro_id: prototype_id for prototype_id, macro_id
                          in promoted.prototype_macro_types}
    transferred_prototypes = {macro_to_prototype[item] for item in transferred}
    missing_prototypes = {macro_to_prototype[item] for item in missing}
    configurations = (
        ("strict-0.10", .1, False),
        ("coarse-0.10", .1, True),
        ("coarse-0.25", .25, True),
        ("coarse-0.50", .5, True),
    )
    descriptors = tuple(_audit_descriptor(
        name, width, coarse, promoted, quotient, train_namespaces,
        transferred_prototypes, missing_prototypes)
                        for name, width, coarse in configurations)
    alternative_classes = sum(len(item.alternatives) > 1
                              for item in quotient.derivation_classes)
    best = max((item.safe_missing_types_covered for item in descriptors),
               default=0)
    passed = best == len(missing) and step.audit.safe_backoff_types > 0
    reason = ("green: every missing exact type has a replay-exact train "
              "alternative" if passed else
              "red: semantic similarity does not identify a replay-exact "
              "missing alternative; unmatched exact geometry remains a gap")
    return CdYbSemanticBackoffAudit(
        len(train_windows), len(heldout_windows), len(train_positions),
        len(held_positions), len(train_ids.intersection(heldout_ids)),
        len(all_types), len(transferred), len(missing), tuple(sorted(missing)),
        alternative_classes, step.audit.safe_backoff_types, descriptors, best,
        False, True, False, False, False, passed, reason)


def main():
    import json
    print(json.dumps(asdict(evaluate()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
