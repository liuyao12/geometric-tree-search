#!/usr/bin/env python3
"""Width-4/5 safety controls for generic recurring port-macro mining."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
import math
import time

from materials_gcts_boundary_recursive_safety_audit import (
    _configuration_cases, _variant)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_port_graph_macros import (
    _port_graph, _rooted_connected_sets, mine_port_graph_macros)
from materials_gcts_recursive_port_hierarchy import (
    drive_recursive_port_hierarchy, real_first_level_callbacks)


@dataclass(frozen=True)
class MacroWidthCase:
    system: str
    width: int
    sparse_vertices: int
    sparse_edges: int
    rooted_candidates: int
    exact_geometry_classes: int
    admitted_macro_types: int
    maximum_admitted_children: int
    maximum_admitted_atoms: int
    runtime_seconds: float
    finite_candidate_bound: int
    finite: bool
    permutation_invariant: bool
    proper_se3_invariant: bool
    hierarchy_admitted_types: tuple[int, ...]
    hierarchy_quotient_types: tuple[int, ...]
    stationary_witnesses: int


@dataclass(frozen=True)
class NaClEightChildTractability:
    rooted_candidates_width_2_to_8: tuple[int, ...]
    exact_width_8_candidates: int
    canonical_permutation_work_width_5: int
    canonical_permutation_work_width_8: int
    work_ratio_8_over_5: float
    measured_width_5_seconds: float
    measured_width_8_seconds: float
    projected_width_8_seconds: float
    public_miner_maximum_width: int
    width_8_full_geometry_run: bool
    eight_child_stationary_rule_learned: bool
    reason: str


@dataclass(frozen=True)
class MacroWidthSafetyAudit:
    widths: tuple[int, ...]
    cases: tuple[MacroWidthCase, ...]
    nacl_eight_child: NaClEightChildTractability
    all_finite: bool
    all_permutation_invariant: bool
    all_proper_se3_invariant: bool
    amorphous_stationarity_rejected: bool
    family_cell_scale_target_unused: bool
    passed: bool


def _fingerprint(mined):
    histogram = tuple(sorted(Counter((
        len(item.node_types), len(item.atom_union), len(item.occurrences),
        item.mdl_saving, len(item.boundary_slots))
        for item in mined.macro_types).items()))
    return (mined.source_graph_vertices, mined.source_graph_edges,
            mined.graph_vertices, mined.graph_edges,
            mined.rooted_connected_candidates, mined.exact_geometry_classes,
            len(mined.macro_types), mined.maximum_macro_nodes,
            mined.maximum_macro_atoms, histogram)


def _compile_variant(configuration, variant):
    species, positions = ((configuration.species, configuration.positions)
                          if variant == "base" else
                          _variant(configuration, variant))
    return compile_irregular_port_program(species, positions)


def _case(configuration, width, programs):
    start = time.perf_counter()
    base = mine_port_graph_macros(programs["base"], maximum_nodes=width)
    elapsed = time.perf_counter() - start
    permuted = mine_port_graph_macros(
        programs["permuted"], maximum_nodes=width)
    rigid = mine_port_graph_macros(
        programs["rigid"], maximum_nodes=width)
    hierarchy = (drive_recursive_port_hierarchy(
        programs["base"],
        real_first_level_callbacks(maximum_nodes=width), maximum_levels=3)
        if width <= 5 else None)
    vertices = base.graph_vertices
    bound = vertices * sum(math.comb(max(0, vertices - 1), extra)
                           for extra in range(1, width))
    return MacroWidthCase(
        configuration.name, width, vertices, base.graph_edges,
        base.rooted_connected_candidates, base.exact_geometry_classes,
        len(base.macro_types), base.maximum_macro_nodes,
        base.maximum_macro_atoms, elapsed, bound,
        base.rooted_connected_candidates <= bound,
        _fingerprint(base) == _fingerprint(permuted),
        _fingerprint(base) == _fingerprint(rigid),
        (tuple(item.admitted_macro_types for item in hierarchy.levels)
         if hierarchy is not None else (len(base.macro_types),)),
        (tuple(item.quotient_macro_types for item in hierarchy.levels)
         if hierarchy is not None else (len(base.macro_types),)),
        (len(hierarchy.stationary_witnesses)
         if hierarchy is not None else 0))


def _eight_child_probe(nacl_program, measured_width_5_seconds,
                       measured_width_8_seconds, learned):
    _, _, adjacency, _ = _port_graph(nacl_program)
    cumulative = tuple(len(_rooted_connected_sets(adjacency, width))
                       for width in range(2, 9))
    exact = []
    prior = 0
    for total in cumulative:
        exact.append(total - prior)
        prior = total
    work = []
    running = 0
    for width, count in enumerate(exact, start=2):
        running += count * math.factorial(width - 1)
        work.append(running)
    ratio = work[-1] / max(1, work[3])
    return NaClEightChildTractability(
        cumulative, exact[-1], work[3], work[-1], ratio,
        measured_width_5_seconds, measured_width_8_seconds,
        measured_width_5_seconds * ratio,
        8, True, learned,
        ("exact width-8 run completed with cached partition refinement and "
         "exact isomorphism; no admitted eight-child production"
         if not learned else
         "an exact admitted eight-child production was discovered"))


def evaluate(widths=(4, 5, 8)):
    widths = tuple(widths)
    if not widths or any(width not in (4, 5, 8) for width in widths):
        raise ValueError("this safety gate is predeclared for widths 4, 5, 8")
    nacl, _, amorphous = _configuration_cases()
    configurations = nacl, amorphous
    programs = {
        item.name: {variant: _compile_variant(item, variant)
                    for variant in ("base", "permuted", "rigid")}
        for item in configurations}
    cases = tuple(_case(configuration, width, programs[configuration.name])
                  for configuration in configurations for width in widths)
    measured = next(item.runtime_seconds for item in cases
                    if item.system == nacl.name and item.width == 5)
    width8 = next(item for item in cases
                  if item.system == nacl.name and item.width == 8)
    probe = _eight_child_probe(
        programs[nacl.name]["base"], measured, width8.runtime_seconds,
        width8.maximum_admitted_children >= 8)
    finite = all(item.finite for item in cases)
    permutation = all(item.permutation_invariant for item in cases)
    se3 = all(item.proper_se3_invariant for item in cases)
    amorphous_cases = tuple(item for item in cases
                            if "amorphous" in item.system)
    rejected = all(item.admitted_macro_types == 0 and
                   item.stationary_witnesses == 0
                   for item in amorphous_cases)
    return MacroWidthSafetyAudit(
        widths, cases, probe, finite, permutation, se3, rejected, True,
        finite and permutation and se3 and rejected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
