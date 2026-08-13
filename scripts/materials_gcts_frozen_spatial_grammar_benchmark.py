#!/usr/bin/env python3
"""Sealed spatial-sector replay of the learned IQC cover grammar."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_frontier_attachment_benchmark import evaluate as frontier
from materials_gcts_frozen_spatial_grammar import (
    fit_frozen_spatial_grammar, replay_frozen_spatial_grammar)
from materials_gcts_spatial_support_hierarchy import guarded_octants


@dataclass(frozen=True)
class FrozenSpatialGrammarBenchmark:
    exact_frontier_atoms: int
    training_domains: int
    heldout_domains: int
    training_atoms: int
    heldout_atoms: int
    frozen_length_unit: float
    type_vocabulary_sizes: Tuple[int, ...]
    production_rules: int
    production_alternatives: int
    heldout_occurrence_coverage: Tuple[float, ...]
    heldout_atom_coverage: Tuple[float, ...]
    heldout_production_agreement: Tuple[float, ...]
    heldout_unseen_types: Tuple[int, ...]
    heldout_unseen_productions: Tuple[int, ...]
    heldout_geometry_used_for_fitting: bool
    three_levels_transfer: bool
    benchmark_passed: bool


def evaluate(waves=16):
    growth = frontier(regenerative_wave_count=waves)
    positions = tuple(point for trace in growth.regenerative_growth_traces
                      for point in trace.positions)
    species = tuple(color for trace in growth.regenerative_growth_traces
                    for color in trace.species)
    if any(wave.false_sites for wave in growth.regenerative_growth_waves):
        raise RuntimeError("frozen grammar benchmark requires exact growth")
    domains = guarded_octants(
        positions, .08 * growth.learned_minimum_separation,
        center=(0.0, 0.0, 0.0))
    training = {key: indices for key, indices in domains.items() if not key[0]}
    heldout = {key: indices for key, indices in domains.items() if key[0]}
    grammar, fitted = fit_frozen_spatial_grammar(
        positions, species, training)
    replay, _ = replay_frozen_spatial_grammar(
        grammar, positions, species, heldout)
    three = len(replay.levels) == 3 and replay.all_types_known and (
        replay.all_productions_transfer and
        replay.all_atoms_covered_by_known_types)
    passed = three and not replay.heldout_geometry_used_for_fitting
    return FrozenSpatialGrammarBenchmark(
        len(positions), len(training), len(heldout), fitted.assigned_atoms,
        sum(len(indices) for indices in heldout.values()),
        grammar.length_unit,
        tuple(len(items) for items in grammar.type_vocabularies),
        len(grammar.productions),
        sum(len(item.child_alternatives) for item in grammar.productions),
        tuple(item.known_type_occurrence_fraction for item in replay.levels),
        tuple(item.known_type_atom_fraction for item in replay.levels),
        tuple(item.production_agreement_fraction for item in replay.levels),
        tuple(item.unseen_types for item in replay.levels),
        tuple(item.unseen_productions for item in replay.levels),
        replay.heldout_geometry_used_for_fitting, three, passed)


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
