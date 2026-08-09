#!/usr/bin/env python3
"""Frozen clusters-of-clusters GCTS benchmark on an ideal icosahedral set."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    consensus_sites, learn_recursive_connection_marking,
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
    training_states: int
    accepted_states: int
    heldout_pair_actions: int
    heldout_true_pair_actions: int
    heldout_pair_precision: float
    marked_distinct_sites: int
    marked_true_sites: int
    marked_false_sites: int
    marked_coverage: float
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
    marking = learn_recursive_connection_marking(
        first.positions, first_types, second.positions, HIDDEN_UNIT)
    result = propose_with_recursive_marking(
        marking, second.positions, second_types, HIDDEN_UNIT, third.positions)
    targets = {point_key(point) for point in third.positions}
    marked_true = sum(point in targets for point in result.votes)
    operating_points = []
    for threshold in (1, 2, 4, 8, 16, 32):
        proposed = consensus_sites(result.votes, threshold)
        true = len(proposed & targets)
        false = len(proposed) - true
        operating_points.append(ConsensusOperatingPoint(
            threshold, len(proposed), true, false,
            true / len(proposed) if proposed else 0.0, true / len(targets)))
    return RecursiveConnectionBenchmark(
        (len(first.positions), len(second.positions), len(third.positions)),
        HIDDEN_UNIT, len(marking.evidence), len(marking.accepted_states),
        result.accepted_pair_actions, result.true_pair_actions or 0,
        (result.true_pair_actions or 0) / result.accepted_pair_actions,
        len(result.votes), marked_true, len(result.votes) - marked_true,
        marked_true / len(targets), tuple(operating_points), False, False, False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
