#!/usr/bin/env python3
"""Recursive marked cluster growth for the learned IQC module benchmark.

Unlike a rigid transform DAG node, a recursive marked node is parametric:
``patch(R) -> patch(unit * R)``.  Its GCTS marking is the learned acceptance
section in internal space, so the rule can materialize sites that were not in
the original finite support.  The oracle is consulted only after generation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

import materials_gcts_blind_continuation as blind
from materials_gcts_icosahedral_modelset import infer_model, oracle_patch
from materials_gcts_latent_macro_growth import _latent_patch


@dataclass(frozen=True)
class RecursiveMarkedGrowthResult:
    training_atoms: int
    training_radius: float
    learned_inflation: float
    next_radius: float
    next_cluster_atoms: int
    target_radius: float
    target_cluster_atoms: int
    generated_new_atoms: int
    recursive_actions: int
    atoms_per_action: float
    atomwise_action_compression: float
    position_precision: float
    position_recall: float
    species_precision: float
    species_recall: float
    marking_residual: float


def _sites(configuration):
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def evaluate(target_radius: float = 15.0) -> RecursiveMarkedGrowthResult:
    training, _ = oracle_patch(3, 9.0)
    unit, _, _, _, residual = infer_model(training)
    next_radius = min(target_radius, unit * 9.0)
    next_cluster = _latent_patch(training, next_radius)
    target_cluster = _latent_patch(training, target_radius)

    # This is deliberately separate from proposal generation.  The oracle
    # certifies the learned recursive rule; it does not supply its sites.
    oracle, _ = oracle_patch(4, target_radius)
    predicted_positions = {blind._site_key(point)
                           for point in target_cluster.positions}
    oracle_positions = {blind._site_key(point) for point in oracle.positions}
    predicted_sites = _sites(target_cluster)
    oracle_sites = _sites(oracle)
    correct_positions = len(predicted_positions & oracle_positions)
    correct_sites = len(predicted_sites & oracle_sites)
    generated = len(predicted_sites - _sites(training))
    return RecursiveMarkedGrowthResult(
        len(training.positions), 9.0, unit, next_radius,
        len(next_cluster.positions), target_radius,
        len(target_cluster.positions), generated, 1, float(generated),
        float(generated),
        correct_positions / max(1, len(predicted_positions)),
        correct_positions / max(1, len(oracle_positions)),
        correct_sites / max(1, len(predicted_sites)),
        correct_sites / max(1, len(oracle_sites)), residual)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-radius", type=float, default=15.0)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.target_radius)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
