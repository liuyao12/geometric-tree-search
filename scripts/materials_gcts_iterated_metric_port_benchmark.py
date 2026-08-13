#!/usr/bin/env python3
"""Iterate the frozen metric-port atlas without oracle intervention."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_metric_port_atlas import (
    fit_metric_port_atlas, propose_with_metric_ports)
from materials_gcts_recursive_connections import (
    infer_recursive_scale, local_cluster_types, point_key)


@dataclass(frozen=True)
class MetricPortWave:
    wave: int
    atoms_before: int
    one_vote_candidates: int
    accepted_sites: int
    true_accepted_sites: int
    precision: float


@dataclass(frozen=True)
class IteratedMetricPortBenchmark:
    training_atoms: int
    initial_atoms: int
    final_atoms: int
    waves: Tuple[MetricPortWave, ...]
    exact_added_atoms: int
    stalled: bool
    target_atoms: int
    target_recall: float
    oracle_colors_used_for_insertion: bool
    heldout_geometry_used_for_fitting: bool
    regenerative_growth: bool
    benchmark_passed: bool


def evaluate(maximum_waves=5):
    seed, _ = oracle_patch(3, 9.0)
    initial, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    target, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    scale = infer_recursive_scale(seed.positions, maximum_distance=9.0).scale
    edges = (1.4, 2.1, 2.8, 3.81)
    seed_types = local_cluster_types(seed.positions, seed.species, edges)
    training_parents = tuple(range(len(seed.positions)))
    atlas = fit_metric_port_atlas(
        seed.positions, seed_types, seed.positions, scale,
        parent_indices=training_parents, target_colors=seed.species,
        observable_radius=9.0)
    positions = list(initial.positions)
    species = list(initial.species)
    known = {point_key(point) for point in positions}
    target_colors = {point_key(point): chemical for point, chemical in
                     zip(target.positions, target.species)}
    initial_known = set(known)
    waves = []
    for wave in range(1, maximum_waves + 1):
        types = local_cluster_types(positions, species, edges)
        maximum_radius = max(math.dist(point, (0.0, 0.0, 0.0))
                             for point in positions)
        frontier = tuple(
            index for index, point in enumerate(positions)
            if math.dist(point, (0.0, 0.0, 0.0)) >= maximum_radius - 6.5)
        result = propose_with_metric_ports(
            atlas, positions, types, level_scale=scale,
            parent_indices=frontier)
        votes = Counter({point: count for point, count in result.votes.items()
                         if point not in known})
        accepted = tuple(votes)
        true = sum(point in target_colors for point in accepted)
        waves.append(MetricPortWave(
            wave, len(positions), len(votes), len(accepted), true,
            true / max(1, len(accepted))))
        additions = []
        for point in accepted:
            color_votes = result.target_color_votes.get(point)
            if not color_votes:
                continue
            maximum = max(color_votes.values())
            chemical = min(color for color, count in color_votes.items()
                           if count == maximum)
            additions.append((point, chemical))
        if not additions:
            break
        for key, chemical in additions:
            positions.append(key)
            species.append(chemical)
            known.add(key)
    correct_new = len((known - initial_known) & set(target_colors))
    target_new = len(set(target_colors) - initial_known)
    nonempty = tuple(wave for wave in waves if wave.accepted_sites)
    regenerative = (len(nonempty) >= 2 and
                    all(wave.precision >= .99 for wave in nonempty))
    return IteratedMetricPortBenchmark(
        len(seed.positions), len(initial.positions), len(positions),
        tuple(waves), correct_new, bool(waves and not waves[-1].accepted_sites),
        len(target.positions), correct_new / target_new, False, False,
        regenerative, regenerative and correct_new == target_new)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
