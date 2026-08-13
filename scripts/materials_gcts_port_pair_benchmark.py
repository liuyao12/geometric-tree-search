#!/usr/bin/env python3
"""Regenerative higher-order incoming-port section benchmark."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_metric_port_atlas import (
    fit_metric_port_atlas, fit_port_pair_section, pair_section_sites,
    propose_with_metric_ports)
from materials_gcts_recursive_connections import (
    infer_recursive_scale, local_cluster_types, point_key)


@dataclass(frozen=True)
class PortPairWave:
    wave: int
    atoms_before: int
    proposed_sites: int
    true_sites: int
    precision: float


@dataclass(frozen=True)
class PortPairBenchmark:
    training_atoms: int
    initial_atoms: int
    accepted_metric_ports: int
    accepted_port_pairs: int
    waves: Tuple[PortPairWave, ...]
    exact_nonempty_waves: int
    exact_added_atoms: int
    final_atoms: int
    target_recall: float
    stalled: bool
    heldout_geometry_used_for_fitting: bool
    oracle_colors_used_for_insertion: bool
    regenerative_growth: bool
    exponential_growth: bool
    benchmark_passed: bool


def evaluate(maximum_waves=8):
    seed, _ = oracle_patch(3, 9.0)
    initial, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    target, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    scale = infer_recursive_scale(seed.positions, maximum_distance=9.0).scale
    edges = (1.4, 2.1, 2.8, 3.81)
    seed_types = local_cluster_types(seed.positions, seed.species, edges)
    atlas = fit_metric_port_atlas(
        seed.positions, seed_types, seed.positions, scale,
        target_colors=seed.species, observable_radius=9.0)
    section = fit_port_pair_section(
        atlas, seed.positions, seed_types, seed.positions)
    target_colors = {point_key(point): chemical for point, chemical in
                     zip(target.positions, target.species)}
    positions = list(initial.positions)
    species = list(initial.species)
    known = {point_key(point) for point in positions}
    initial_known = set(known)
    waves = []
    for wave in range(1, maximum_waves + 1):
        types = local_cluster_types(positions, species, edges)
        maximum_radius = max(math.dist(point, (0.0, 0.0, 0.0))
                             for point in positions)
        frontier = tuple(
            index for index, point in enumerate(positions)
            if math.dist(point, (0.0, 0.0, 0.0)) >= maximum_radius - 6.5)
        accepted = pair_section_sites(
            section, atlas, positions, types, level_scale=scale,
            parent_indices=frontier) - known
        true = accepted & set(target_colors)
        waves.append(PortPairWave(
            wave, len(positions), len(accepted), len(true),
            len(true) / max(1, len(accepted))))
        if not accepted:
            break
        proposals = propose_with_metric_ports(
            atlas, positions, types, level_scale=scale,
            parent_indices=frontier)
        for point in accepted:
            votes = proposals.target_color_votes[point]
            maximum = max(votes.values())
            chemical = min(color for color, count in votes.items()
                           if count == maximum)
            positions.append(point)
            species.append(chemical)
            known.add(point)
    nonempty = tuple(wave for wave in waves if wave.proposed_sites)
    exact_waves = sum(wave.precision == 1.0 for wave in nonempty)
    exact_added = len((known - initial_known) & set(target_colors))
    target_new = len(set(target_colors) - initial_known)
    regenerative = len(nonempty) >= 2 and exact_waves == len(nonempty)
    factors = tuple(nonempty[index].proposed_sites /
                    nonempty[index - 1].proposed_sites
                    for index in range(1, len(nonempty)))
    exponential = regenerative and factors and min(factors) > 1.0
    return PortPairBenchmark(
        len(seed.positions), len(initial.positions), len(atlas.accepted_ports),
        len(section.accepted_pairs), tuple(waves), exact_waves, exact_added,
        len(positions), exact_added / target_new,
        bool(waves and not waves[-1].proposed_sites), False, False,
        regenerative, bool(exponential), regenerative)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
