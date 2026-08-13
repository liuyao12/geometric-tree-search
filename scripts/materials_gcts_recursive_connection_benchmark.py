#!/usr/bin/env python3
"""Frozen clusters-of-clusters GCTS benchmark on an ideal icosahedral set."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    consensus_sites, infer_recursive_scale, learn_recursive_connection_marking,
    local_cluster_types, propose_with_recursive_marking, point_key)


@dataclass(frozen=True)
class ConsensusOperatingPoint:
    minimum_votes: int
    proposed_sites: int
    true_sites: int
    false_sites: int
    precision: float
    coverage: float


@dataclass(frozen=True)
class RecursiveConnectionBenchmark:
    atom_counts: Tuple[int, int, int]
    inflation_scale: float
    scale_inferred_from_seed_only: bool
    scale_absolute_error: float
    one_level_distance_closure: float
    two_level_distance_closure: float
    training_states: int
    accepted_states: int
    heldout_pair_actions: int
    heldout_true_pair_actions: int
    heldout_pair_precision: float
    marked_distinct_sites: int
    marked_true_sites: int
    marked_false_sites: int
    marked_coverage: float
    known_sites_excluded: int
    novel_target_sites: int
    operating_points: Tuple[ConsensusOperatingPoint, ...]
    trained_on_heldout_labels: bool
    lattice_coordinates_used: bool
    physical_potential_used: bool


def evaluate() -> RecursiveConnectionBenchmark:
    first, _ = oracle_patch(3, 9.0)
    second, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    third, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    edges = (1.4, 2.1, 2.8, 3.81)
    first_types = local_cluster_types(first.positions, first.species, edges)
    second_types = local_cluster_types(second.positions, second.species, edges)
    scale = infer_recursive_scale(first.positions, maximum_distance=9.0)
    marking = learn_recursive_connection_marking(
        first.positions, first_types, second.positions, scale.scale)
    result = propose_with_recursive_marking(
        marking, second.positions, second_types, scale.scale, third.positions)
    known = {point_key(point) for point in second.positions}
    targets = ({point_key(point) for point in third.positions} - known)
    novel_votes = Counter({point: votes for point, votes in result.votes.items()
                           if point not in known})
    marked_true = sum(point in targets for point in novel_votes)
    operating_points = []
    for threshold in (1, 2, 4, 8, 16, 32):
        proposed = consensus_sites(novel_votes, threshold)
        true = len(proposed & targets)
        false = len(proposed) - true
        operating_points.append(ConsensusOperatingPoint(
            threshold, len(proposed), true, false,
            true / len(proposed) if proposed else 0.0, true / len(targets)))
    return RecursiveConnectionBenchmark(
        (len(first.positions), len(second.positions), len(third.positions)),
        scale.scale, scale.learned_from_positions_only,
        abs(scale.scale - HIDDEN_UNIT), scale.one_level_closure,
        scale.two_level_closure,
        len(marking.evidence), len(marking.accepted_states),
        result.accepted_pair_actions, result.true_pair_actions or 0,
        (result.true_pair_actions or 0) / result.accepted_pair_actions,
        len(novel_votes), marked_true, len(novel_votes) - marked_true,
        marked_true / len(targets), len(known), len(targets),
        tuple(operating_points), False, False, False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
