#!/usr/bin/env python3
"""Perturbation and false-positive gates for parametric recursive GCTS."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Optional, Tuple

from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import (
    AtomicConfiguration, benchmark_systems, perturb)
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_parametric_recursive import apply_rule, discover_rule
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class NoiseCase:
    system: str
    sigma: float
    discovered_family: str
    hierarchy_supports: Tuple[int, ...]
    rule_residual: Optional[float]
    output_atoms: int
    deterministic: bool


@dataclass(frozen=True)
class NoiseRobustnessBenchmark:
    retained_at_half_percent: Tuple[NoiseCase, ...]
    rejected_at_one_percent: Tuple[NoiseCase, ...]
    amorphous_false_positive_seeds: int
    amorphous_false_positives: int


def _case(configuration: AtomicConfiguration, sigma: float) -> NoiseCase:
    noisy = perturb(configuration, sigma, 123)
    # Deliberately remove periodic metadata from the crystal control.
    noisy = AtomicConfiguration(
        noisy.name, noisy.positions, noisy.species, None, False,
        noisy.provenance)
    rule = discover_rule(noisy)
    output = apply_rule(noisy, rule) if rule.deterministic else noisy
    return NoiseCase(
        configuration.name, sigma, rule.family, rule.hierarchy_supports,
        rule.residual, len(output.positions), rule.deterministic)


def evaluate() -> NoiseRobustnessBenchmark:
    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    iqc, _ = oracle_patch(3, 9.0)
    substitution = make_input(9)
    deterministic = (crystal, iqc, substitution)
    retained = tuple(_case(configuration, 0.005)
                     for configuration in deterministic)
    rejected = tuple(_case(configuration, 0.01)
                     for configuration in (iqc, substitution))
    false_positives = 0
    seeds = 4
    for seed in range(seeds):
        sample = amorphous_hard_core_point_set(atom_count=507, seed=37 + seed)
        configuration = AtomicConfiguration(
            sample.name, sample.positions, sample.species)
        false_positives += discover_rule(configuration).deterministic
    return NoiseRobustnessBenchmark(
        retained, rejected, seeds, false_positives)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
