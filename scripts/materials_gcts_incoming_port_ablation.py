#!/usr/bin/env python3
"""Causal incoming-halo ranking of frozen cover alternatives.

All candidate right-hand sides are learned on one guarded half-space.  On the
held-out side the search sees only atoms in the inward half of a bounded halo,
which represents material already grown toward the observation centre.  The
marking ranks the same alternatives as the parent-frequency baseline; its
work is the one-based rank of the correct derivation, so every preceding check
is an immediate failed branch.  A within-parent cyclic label permutation is
the negative control.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import DefaultDict, Optional, Tuple

from materials_gcts_frozen_hierarchy import (
    _SpatialIndex, encode_frozen_hierarchy, fit_frozen_hierarchy)
from materials_gcts_guarded_spatial_split import guarded_center_indices


@dataclass(frozen=True)
class IncomingPortCase:
    system: str
    atoms: int
    hierarchy_level: int
    training_occurrences: int
    heldout_occurrences: int
    parent_types: int
    rhs_alternatives: int
    oracle_seen_fraction: float
    modal_top1_accuracy: float
    marked_top1_accuracy: float
    shuffled_top1_accuracy: float
    modal_proposal_checks: int
    marked_proposal_checks: int
    shuffled_proposal_checks: int
    modal_backtracks: int
    marked_backtracks: int
    shuffled_backtracks: int
    proposal_reduction: float
    backtrack_reduction: Optional[float]
    baseline_has_backtracks: bool
    marking_causal: bool
    heldout_geometry_used_for_ranking: bool


@dataclass(frozen=True)
class IncomingPortAblation:
    crystal: IncomingPortCase
    quasicrystal: IncomingPortCase
    both_markings_causal: bool
    benchmark_passed: bool


def _species(value):
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _rhs(center, parent_support, child_labels, spatial, child_radius,
         species):
    parent = frozenset(index for _, index in parent_support)
    candidates = []
    for _, child_center in parent_support:
        child_type = child_labels[child_center]
        child = frozenset(index for _, index in
                          spatial.within(child_center, child_radius))
        if child.issubset(parent):
            # Geometry-only tie key; never use the occurrence index.
            radial = round(math.dist(spatial.points[center],
                                     spatial.points[child_center]), 6)
            candidates.append((child_type, radial, child))
    remaining = set(parent)
    selected = []
    while remaining:
        viable = [(len(child.intersection(remaining)), child_type, radial, child)
                  for child_type, radial, child in candidates]
        gain, child_type, radial, child = max(
            viable, default=(0, -1, -1.0, frozenset()),
            key=lambda item: (item[0], -item[1], -item[2]))
        if gain == 0:
            break
        selected.append((child_type, child))
        remaining.difference_update(child)
        candidates.remove((child_type, radial, child))
    counts = tuple(sorted(Counter(child_type for child_type, _ in selected).items()))
    gaps = tuple(sorted(Counter(_species(species[index])
                                for index in remaining).items()))
    overlap = sum(len(child) for _, child in selected) - (len(parent) - len(remaining))
    return counts, gaps, len(parent), overlap


def _incoming_tokens(center, spatial, body_radius, marking_outer, species,
                     observation_center, scale):
    point = spatial.points[center]
    inward = tuple(observation_center[axis] - point[axis] for axis in range(3))
    length = math.sqrt(sum(value * value for value in inward))
    if length < 1e-9:
        return ()
    inward = tuple(value / length for value in inward)
    radial_width = max(1e-9, .18 * scale)
    tokens = []
    for distance, index in spatial.within(center, marking_outer):
        if distance <= body_radius + 1e-9 or index == center:
            continue
        displacement = tuple(spatial.points[index][axis] - point[axis]
                             for axis in range(3))
        cosine = sum(displacement[axis] * inward[axis]
                     for axis in range(3)) / distance
        if cosine <= 0.0:
            continue
        tokens.append((_species(species[index]),
                       round((distance - body_radius) / radial_width),
                       round(cosine * 4)))
    return tuple(sorted(Counter(tokens).items()))


def _learn_ranker(rows):
    priors: DefaultDict[tuple, Counter] = defaultdict(Counter)
    token_votes: DefaultDict[tuple, Counter] = defaultdict(Counter)
    supports: Counter = Counter()
    for parent, tokens, rhs in rows:
        priors[parent][rhs] += 1
        supports[(parent, rhs)] += 1
        for token, multiplicity in tokens:
            token_votes[(parent, token)][rhs] += multiplicity
    return priors, token_votes, supports


def _order(parent, tokens, model):
    priors, token_votes, supports = model
    candidates = tuple(priors[parent])
    scores = {}
    for rhs in candidates:
        score = math.log(priors[parent][rhs] + 1.0)
        denominator = supports[(parent, rhs)] + 2.0
        for token, multiplicity in tokens:
            score += multiplicity * math.log(
                (token_votes[(parent, token)][rhs] + 1.0) / denominator)
        scores[rhs] = score
    return tuple(sorted(candidates, key=lambda rhs: (-scores[rhs], repr(rhs))))


def _modal_order(parent, model):
    priors = model[0]
    return tuple(sorted(priors[parent], key=lambda rhs:
                        (-priors[parent][rhs], repr(rhs))))


def _case(configuration, level):
    encoder, _ = fit_frozen_hierarchy(configuration, maximum_levels=level)
    _, labels = encode_frozen_hierarchy(configuration, encoder)
    spatial = _SpatialIndex(configuration.positions,
                            encoder.nearest_neighbor_scale)
    center = tuple(sum(point[axis] for point in configuration.positions) /
                   len(configuration.positions) for axis in range(3))
    rows = {"train": [], "heldout": []}
    parent_level = encoder.levels[level - 1]
    child_level = encoder.levels[level - 2]
    parent_labels = labels[level - 1]
    child_labels = labels[level - 2]
    for side in rows:
        for occurrence in guarded_center_indices(configuration, level, side):
            if parent_labels[occurrence] == parent_level.unknown_label:
                continue
            support = spatial.within(occurrence, parent_level.radius)
            rhs = _rhs(occurrence, support, child_labels, spatial,
                       child_level.radius, configuration.species)
            tokens = _incoming_tokens(
                occurrence, spatial, parent_level.radius,
                parent_level.marking_outer, configuration.species, center,
                encoder.nearest_neighbor_scale)
            rows[side].append((parent_labels[occurrence], tokens, rhs))

    model = _learn_ranker(rows["train"])
    # Negative control: preserve contexts and parent/RHS marginals, but cycle
    # RHS labels within each parent before fitting token associations.
    grouped: DefaultDict[int, list] = defaultdict(list)
    for row in rows["train"]:
        grouped[row[0]].append(row)
    shuffled_rows = []
    for parent, group in grouped.items():
        ordered = sorted(group, key=lambda row: repr(row[1]))
        shifted = [row[2] for row in ordered[1:] + ordered[:1]]
        shuffled_rows.extend((parent, row[1], shifted[index])
                             for index, row in enumerate(ordered))
    shuffled_model = _learn_ranker(shuffled_rows)

    modal_checks = marked_checks = shuffled_checks = 0
    modal_top = marked_top = shuffled_top = seen = scored = 0
    for parent, tokens, rhs in rows["heldout"]:
        candidates = model[0].get(parent)
        if not candidates:
            continue
        scored += 1
        if rhs not in candidates:
            modal_checks += len(candidates) + 1
            marked_checks += len(candidates) + 1
            shuffled_checks += len(candidates) + 1
            continue
        seen += 1
        orders = (_modal_order(parent, model), _order(parent, tokens, model),
                  _order(parent, tokens, shuffled_model))
        checks = tuple(order.index(rhs) + 1 for order in orders)
        modal_checks += checks[0]
        marked_checks += checks[1]
        shuffled_checks += checks[2]
        modal_top += checks[0] == 1
        marked_top += checks[1] == 1
        shuffled_top += checks[2] == 1
    modal_backtracks = modal_checks - seen
    marked_backtracks = marked_checks - seen
    shuffled_backtracks = shuffled_checks - seen
    causal = (seen > 0 and marked_checks < modal_checks and
              marked_checks < shuffled_checks and marked_top >= modal_top)
    alternatives = sum(len(values) for values in model[0].values())
    return IncomingPortCase(
        configuration.name, len(configuration.positions), level,
        len(rows["train"]), scored, len(model[0]), alternatives,
        seen / scored, modal_top / scored, marked_top / scored,
        shuffled_top / scored, modal_checks, marked_checks, shuffled_checks,
        modal_backtracks, marked_backtracks, shuffled_backtracks,
        modal_checks / marked_checks,
        (modal_backtracks / marked_backtracks
         if marked_backtracks else None), modal_backtracks > 0, causal, False)


def evaluate():
    from materials_gcts_generic import benchmark_systems
    from materials_gcts_icosahedral_modelset import oracle_patch
    from materials_gcts_periodic_growth import replicate

    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    crystal = replicate(replicate(crystal))
    unit = (1 + math.sqrt(5)) / 2
    quasicrystal, _ = oracle_patch(6, 9 * unit ** 2)
    cases = _case(crystal, 3), _case(quasicrystal, 2)
    causal = all(case.marking_causal for case in cases)
    return IncomingPortAblation(*cases, causal, causal)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
