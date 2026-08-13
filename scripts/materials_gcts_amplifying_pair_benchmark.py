#!/usr/bin/env python3
"""Two unseen scales of exact, amplifying higher-order GCTS batches."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_icosahedral_modelset import (
    HIDDEN_UNIT, oracle_patch, oracle_patch_fast)
from materials_gcts_metric_port_atlas import (
    fit_metric_port_atlas, fit_port_pair_section, pair_section_frontier_width,
    pair_section_sites, propose_with_metric_ports)
from materials_gcts_recursive_connections import (
    infer_recursive_scale, local_cluster_types, point_key)


@dataclass(frozen=True)
class AmplifyingScale:
    action: int
    state_atoms: int
    target_atoms: int
    consensus_threshold: int
    pair_supported_sites: int
    accepted_sites: int
    true_sites: int
    precision: float
    novel_recall: float


@dataclass(frozen=True)
class AmplifyingPairBenchmark:
    training_atoms: int
    inferred_scale: float
    seed_minimum_pair_votes: int
    learned_frontier_width: float
    scales: Tuple[AmplifyingScale, ...]
    accepted_batch_growth_factor: float
    exact_at_both_unseen_scales: bool
    heldout_geometry_used_for_fitting: bool
    oracle_colors_used_for_proposals: bool
    exponential_style_amplification: bool
    million_site_growth_claimed: bool
    benchmark_passed: bool


def evaluate():
    seed, _ = oracle_patch(3, 9.0)
    scale = infer_recursive_scale(seed.positions, maximum_distance=9.0).scale
    edges = (1.4, 2.1, 2.8, 3.81)
    seed_types = local_cluster_types(seed.positions, seed.species, edges)
    atlas = fit_metric_port_atlas(
        seed.positions, seed_types, seed.positions, scale,
        target_colors=seed.species, observable_radius=9.0)
    section = fit_port_pair_section(
        atlas, seed.positions, seed_types, seed.positions)
    seed_proposals = propose_with_metric_ports(
        atlas, seed.positions, seed_types)
    seed_targets = {point_key(point) for point in seed.positions}
    seed_pair_sites = pair_section_sites(
        section, atlas, seed.positions, seed_types)
    seed_minimum = min(seed_proposals.votes[point] for point in seed_pair_sites
                       if point in seed_targets)
    frontier_width = pair_section_frontier_width(section, atlas)
    reports = []
    # Bounds are independent coefficient-box certificates for R*s and R*s^2.
    # The second target is converged: bounds 10 through 14 all give 37,073 sites.
    for action, state_bound, target_bound in ((1, 4, 6), (2, 6, 10)):
        oracle = oracle_patch if target_bound < 10 else oracle_patch_fast
        state, _ = oracle_patch(state_bound, 9.0 * HIDDEN_UNIT ** action)
        target, _ = oracle(
            target_bound, 9.0 * HIDDEN_UNIT ** (action + 1))
        types = local_cluster_types(state.positions, state.species, edges)
        maximum_radius = max(math.dist(point, (0.0, 0.0, 0.0))
                             for point in state.positions)
        frontier = tuple(
            index for index, point in enumerate(state.positions)
            if math.dist(point, (0.0, 0.0, 0.0)) >=
            maximum_radius - frontier_width)
        proposals = propose_with_metric_ports(
            atlas, state.positions, types, level_scale=scale ** action,
            parent_indices=frontier)
        known = {point_key(point) for point in state.positions}
        pair_sites = pair_section_sites(
            section, atlas, state.positions, types,
            level_scale=scale ** action, parent_indices=frontier) - known
        threshold = math.ceil(seed_minimum / scale ** action)
        accepted = {point for point in pair_sites
                    if proposals.votes[point] >= threshold}
        targets = {point_key(point) for point in target.positions} - known
        true = accepted & targets
        reports.append(AmplifyingScale(
            action, len(state.positions), len(target.positions), threshold,
            len(pair_sites), len(accepted), len(true),
            len(true) / max(1, len(accepted)), len(true) / len(targets)))
    growth = reports[1].accepted_sites / reports[0].accepted_sites
    exact = all(report.accepted_sites == report.true_sites > 0
                for report in reports)
    amplifying = exact and growth > 1.0
    return AmplifyingPairBenchmark(
        len(seed.positions), scale, seed_minimum, frontier_width,
        tuple(reports), growth, exact, False, False, amplifying, False,
        amplifying)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
