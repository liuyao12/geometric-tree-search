#!/usr/bin/env python3
"""Common benchmark for the learned cluster-of-clusters cover grammar."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_cover_grammar import compile_cover_grammar
from materials_gcts_generic import benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class HierarchicalCoverCase:
    system: str
    atoms: int
    productions: int
    exact_productions: int
    exact_geometric_productions: int
    hierarchy_supports: Tuple[int, ...]
    support_amplification: Tuple[float, ...]
    largest_macro_atoms: int
    minimum_child_covered_fraction: float
    minimum_production_agreement: float
    maximum_macro_reference_compression: float
    overlapping_productions: int
    gap_cluster_types: int
    prototype_replay_exact: bool
    reusable_production_gate: bool
    deterministic_hierarchy: bool


@dataclass(frozen=True)
class HierarchicalCoverBenchmark:
    crystal: HierarchicalCoverCase
    quasicrystal: HierarchicalCoverCase
    amorphous: HierarchicalCoverCase
    structured_exact: bool
    structured_prototypes_replay: bool
    structured_uses_overlaps: bool
    structured_has_three_levels: bool
    disorder_rejected: bool
    reusable_production_gate_passed: bool
    benchmark_passed: bool


def _case(configuration) -> HierarchicalCoverCase:
    hierarchy, grammar = compile_cover_grammar(
        configuration.name, configuration.positions, configuration.species,
        maximum_levels=4, first_descriptor_bin_scale=.02,
        first_angle_bin=.03, macro_distance_bin_scale=.20,
        macro_angle_bin=.08)
    supports = tuple(level.largest_recurring_support
                     for level in hierarchy.levels)
    return HierarchicalCoverCase(
        configuration.name, len(configuration.positions),
        grammar.recurring_productions, grammar.exact_productions,
        grammar.exact_geometric_productions,
        supports, hierarchy.support_amplification,
        grammar.largest_macro_atoms, grammar.minimum_child_covered_fraction,
        grammar.minimum_production_agreement,
        grammar.maximum_macro_reference_compression,
        grammar.overlapping_productions, grammar.gap_cluster_types,
        grammar.exact_geometric_productions == grammar.recurring_productions,
        grammar.minimum_production_agreement >= .90,
        hierarchy.geometric_amplification and grammar.recurring_productions > 0
        and grammar.minimum_production_agreement >= .90)


def evaluate() -> HierarchicalCoverBenchmark:
    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    quasicrystal, _ = oracle_patch(3, 9.0)
    disorder = amorphous_hard_core_point_set(atom_count=507)
    cases = _case(crystal), _case(quasicrystal), _case(disorder)
    structured = cases[:2]
    exact = all(case.productions == case.exact_productions
                and case.productions > 0 for case in structured)
    replay = all(case.prototype_replay_exact for case in structured)
    overlaps = all(case.overlapping_productions > 0 for case in structured)
    depth = all(len(case.hierarchy_supports) == 4 and
                case.largest_macro_atoms > case.hierarchy_supports[0]
                for case in structured)
    rejected = not cases[2].deterministic_hierarchy
    reusable = all(case.reusable_production_gate for case in structured)
    passed = exact and replay and overlaps and depth and rejected and reusable
    return HierarchicalCoverBenchmark(
        *cases, exact, replay, overlaps, depth, rejected, reusable, passed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
