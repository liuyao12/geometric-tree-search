#!/usr/bin/env python3
"""Held-out IQC benchmark for scale-normalized motif-centre ports."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_metric_port_atlas import (
    fit_metric_port_atlas, propose_with_metric_ports)
from materials_gcts_recursive_connections import (
    infer_recursive_scale, learn_recursive_connection_marking,
    local_cluster_types, point_key, propose_with_recursive_marking)


@dataclass(frozen=True)
class MetricPortBenchmark:
    training_atoms: int
    training_parents: int
    evaluation_atoms: int
    heldout_novel_atoms: int
    inferred_scale: float
    metric_ports: int
    accepted_metric_ports: int
    accepted_actions: int
    proposed_sites: int
    true_sites: int
    precision: float
    recall: float
    minimum_votes: int
    maximum_votes: int
    coarse_proposed_sites: int
    coarse_true_sites: int
    coarse_precision: float
    precision_gain: float
    heldout_geometry_used_for_fitting: bool
    physical_potential_used: bool
    benchmark_passed: bool


def evaluate():
    seed, _ = oracle_patch(3, 9.0)
    state, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    target, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    scale = infer_recursive_scale(seed.positions, maximum_distance=9.0).scale
    edges = (1.4, 2.1, 2.8, 3.81)
    seed_types = local_cluster_types(seed.positions, seed.species, edges)
    state_types = local_cluster_types(state.positions, state.species, edges)
    parents = tuple(index for index, point in enumerate(seed.positions)
                    if math.dist(point, (0.0, 0.0, 0.0)) <= 9.0 / scale)
    frontier = tuple(index for index, point in enumerate(state.positions)
                     if math.dist(point, (0.0, 0.0, 0.0)) >= 8.0)
    known = {point_key(point) for point in state.positions}
    heldout = {point_key(point) for point in target.positions} - known

    atlas = fit_metric_port_atlas(
        seed.positions, seed_types, seed.positions, scale,
        parent_indices=parents, target_colors=seed.species)
    result = propose_with_metric_ports(
        atlas, state.positions, state_types, level_scale=scale,
        parent_indices=frontier)
    votes = Counter({point: count for point, count in result.votes.items()
                     if point not in known})
    true = len(set(votes) & heldout)

    coarse = learn_recursive_connection_marking(
        seed.positions, seed_types, seed.positions, scale,
        parent_indices=parents, target_colors=seed.species,
        minimum_positive_support=2, minimum_purity=.75)
    coarse_result = propose_with_recursive_marking(
        coarse, state.positions, state_types, scale,
        parent_indices=frontier)
    coarse_votes = {point for point in coarse_result.votes if point not in known}
    coarse_true = len(coarse_votes & heldout)
    precision = true / max(1, len(votes))
    coarse_precision = coarse_true / max(1, len(coarse_votes))
    passed = precision >= .99 and true >= 300
    return MetricPortBenchmark(
        len(seed.positions), len(parents), len(state.positions), len(heldout),
        scale, len(atlas.evidence), len(atlas.accepted_ports),
        result.accepted_actions, len(votes), true, precision,
        true / len(heldout), min(votes.values(), default=0),
        max(votes.values(), default=0), len(coarse_votes), coarse_true,
        coarse_precision, precision / max(coarse_precision, 1e-12), False,
        False, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
