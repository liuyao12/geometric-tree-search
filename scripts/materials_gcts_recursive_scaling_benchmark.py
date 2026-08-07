#!/usr/bin/env python3
"""Exponential-style scaling benchmark for discovered recursive GCTS nodes."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_generic import benchmark_systems
from materials_gcts_fibonacci_3d import (
    Substitution, apply_substitution, generate, make_input)
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_latent_macro_growth import _latent_atom_count
from materials_gcts_parametric_recursive import discover_rule


@dataclass(frozen=True)
class ScalingCurve:
    system: str
    rule_family: str
    action_counts: Tuple[int, ...]
    atom_counts: Tuple[int, ...]
    growth_factors: Tuple[float, ...]
    hierarchy_supports: Tuple[int, ...]
    first_million_action: int
    first_million_atoms: int
    enumeration_seconds: Tuple[float, ...]
    explicit_positions_retained: bool


@dataclass(frozen=True)
class RecursiveScalingBenchmark:
    crystal: ScalingCurve
    quasicrystal: ScalingCurve
    substitution_quasicrystal: ScalingCurve


def _factors(counts):
    return tuple(counts[index] / counts[index - 1]
                 for index in range(1, len(counts)))


def _crystal_curve() -> ScalingCurve:
    configuration = next(item for item in benchmark_systems()
                         if item.name == "NaCl-rocksalt")
    rule = discover_rule(configuration)
    counts = tuple(len(configuration.positions) * 8 ** action
                   for action in range(6))
    first = next(index for index, count in enumerate(counts)
                 if count >= 1_000_000)
    return ScalingCurve(
        configuration.name, rule.family, tuple(range(len(counts))), counts,
        _factors(counts), rule.hierarchy_supports, first, counts[first],
        (0.0,) * len(counts), False)


def _quasicrystal_curve() -> ScalingCurve:
    configuration, _ = oracle_patch(3, 9.0)
    rule = discover_rule(configuration)
    counts = []
    seconds = []
    for action in range(7):
        started = time.perf_counter()
        count = (len(configuration.positions) if action == 0 else
                 _latent_atom_count(
                     configuration, 9.0 * rule.scale ** action))
        seconds.append(time.perf_counter() - started)
        counts.append(count)
    first = next(index for index, count in enumerate(counts)
                 if count >= 1_000_000)
    return ScalingCurve(
        configuration.name, rule.family, tuple(range(len(counts))),
        tuple(counts), _factors(counts), rule.hierarchy_supports,
        first, counts[first], tuple(seconds), False)


def _substitution_curve() -> ScalingCurve:
    configuration = make_input(9)
    rule = discover_rule(configuration)
    if rule.substitution_images is None:
        raise RuntimeError("substitution dispatcher did not return images")
    image_a, image_b, seed = rule.substitution_images
    substitution = Substitution(image_a, image_b, seed)
    word = generate(substitution, 9)
    counts = [len(word) ** 3]
    seconds = [0.0]
    while counts[-1] < 1_000_000:
        started = time.perf_counter()
        word = apply_substitution(word, substitution)
        counts.append(len(word) ** 3)
        seconds.append(time.perf_counter() - started)
    return ScalingCurve(
        configuration.name, rule.family, tuple(range(len(counts))),
        tuple(counts), _factors(counts), rule.hierarchy_supports,
        len(counts) - 1, counts[-1], tuple(seconds), False)


def evaluate() -> RecursiveScalingBenchmark:
    return RecursiveScalingBenchmark(
        _crystal_curve(), _quasicrystal_curve(), _substitution_curve())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
