#!/usr/bin/env python3
"""Audit whether exact regenerative IQC macros are exponentially amplifying."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_frontier_attachment_benchmark import evaluate as frontier


@dataclass(frozen=True)
class RegenerativeScalingAudit:
    wave_sizes: Tuple[int, ...]
    cumulative_sites: Tuple[int, ...]
    frontier_candidates: Tuple[int, ...]
    all_sites_exact: bool
    frontier_supply_grows: bool
    largest_macro_sites: int
    median_macro_sites: float
    macro_growth_factors: Tuple[float, ...]
    two_wave_supermacros: Tuple[int, ...]
    four_wave_supermacros: Tuple[int, ...]
    geometric_mean_growth_factor: float
    log_sites_vs_wave_r_squared: float
    represented_sites_per_wave_grow_by_two: bool
    exponential_gate_passed: bool
    honest_status: str


def _r_squared(xs, ys):
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    covariance = sum((x - x_mean) * (y - y_mean)
                     for x, y in zip(xs, ys))
    variance = sum((x - x_mean) ** 2 for x in xs)
    slope = covariance / variance
    intercept = y_mean - slope * x_mean
    residual = sum((y - (intercept + slope * x)) ** 2
                   for x, y in zip(xs, ys))
    total = sum((y - y_mean) ** 2 for y in ys)
    return 1.0 - residual / total if total else 1.0


def evaluate(waves=16):
    result = frontier(regenerative_wave_count=waves)
    waves = result.regenerative_growth_waves
    sizes = tuple(wave.plateau_sites for wave in waves)
    cumulative = tuple(wave.cumulative_sites for wave in waves)
    supply = tuple(wave.frontier_candidates for wave in waves)
    factors = tuple(sizes[index] / sizes[index - 1]
                    for index in range(1, len(sizes)))
    geometric = math.exp(sum(math.log(value) for value in factors) /
                         len(factors))
    r_squared = _r_squared(tuple(range(1, len(waves) + 1)),
                           tuple(math.log(value) for value in cumulative))
    doubling = all(value >= 2.0 for value in factors[-3:])
    exact = all(wave.false_sites == 0 for wave in waves)
    exponential = exact and doubling and r_squared >= .98
    grouped = lambda width: tuple(sum(sizes[index:index + width])
                                  for index in range(0, len(sizes), width)
                                  if len(sizes[index:index + width]) == width)
    return RegenerativeScalingAudit(
        sizes, cumulative, supply, exact, supply[-1] > supply[0], max(sizes),
        (sorted(sizes)[len(sizes) // 2 - 1] +
         sorted(sizes)[len(sizes) // 2]) / 2, factors,
        grouped(2), grouped(4), geometric,
        r_squared, doubling, exponential,
        ("exact regenerative continuation, but macro sizes oscillate and do "
         "not pass exponential amplification" if not exponential else
         "exact exponential macro amplification"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--waves", type=int, default=16)
    arguments = parser.parse_args()
    result = evaluate(arguments.waves)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
