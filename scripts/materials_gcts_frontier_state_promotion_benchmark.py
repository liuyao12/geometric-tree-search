#!/usr/bin/env python3
"""Promote the exact 16-wave IQC continuation trace into frontier states."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_frontier_attachment_benchmark import evaluate as frontier
from materials_gcts_frontier_state_grammar import (
    FrontierStateGrammar, FrontierWaveSnapshot,
    compile_frontier_state_grammar)


@dataclass(frozen=True)
class ThreeWaveStateAudit:
    type_id: int
    support_size: int
    waves: tuple[int, int, int]
    occurrence_counts: tuple[int, int, int]
    unique_support_atoms: tuple[int, int, int]
    learned_scales: tuple[float, float, float]
    scale_ratios: tuple[float, float]
    support_ratios: tuple[float, float]
    finite_proper_pose: bool
    equal_expanding_scale: bool
    equal_expanding_support: bool


@dataclass(frozen=True)
class FrontierStatePromotionBenchmark:
    source_waves: int
    emitted_sites: int
    wave_sizes: tuple[int, ...]
    all_source_sites_exact: bool
    source_uses_global_superspace_section: bool
    state_compiler_uses_family_cell_or_target: bool
    candidate_connected_subgraphs: int
    normalized_state_types: int
    recurring_state_types: int
    recurring_type_size_histogram: tuple[tuple[int, int], ...]
    recurring_occurrences: int
    proper_pose_verified_occurrences: int
    repeated_covered_sites: int
    repeated_coverage: float
    explicit_residual_sites: int
    complete_cover: bool
    three_wave_state_audits: tuple[ThreeWaveStateAudit, ...]
    equal_expanding_scale_candidates: int
    proper_equal_expanding_scale_candidates: int
    equal_expanding_support_candidates: int
    strict_stationary_witnesses: int
    state_transition_executor_available: bool
    autonomous_growth_claimed: bool
    old_four_wave_supermacros: tuple[int, ...]
    old_count_only_exponential_gate: bool
    frontier_state_exponential_gate: bool
    improvement: str
    next_blocker: str
    grammar_digest: str


def _three_wave_audits(grammar: FrontierStateGrammar):
    audits = []
    for state in grammar.recurring_state_types:
        by_wave = defaultdict(list)
        for occurrence in state.occurrences:
            by_wave[occurrence.wave].append(occurrence)
        for first in sorted(by_wave):
            triple = first, first + 1, first + 2
            if any(wave not in by_wave for wave in triple):
                continue
            counts = tuple(len(by_wave[wave]) for wave in triple)
            supports = tuple(len(set().union(*(
                set(row.member_indices) for row in by_wave[wave])))
                for wave in triple)
            scales = tuple(median(row.scale for row in by_wave[wave])
                           for wave in triple)
            scale_ratios = scales[1] / scales[0], scales[2] / scales[1]
            support_ratios = supports[1] / supports[0], supports[2] / supports[1]
            audits.append(ThreeWaveStateAudit(
                state.type_id, state.support_size, triple, counts, supports,
                scales, scale_ratios, support_ratios,
                all(row.proper_pose_verified
                    for wave in triple for row in by_wave[wave]),
                scale_ratios[0] > 1. and
                abs(scale_ratios[0] - scale_ratios[1]) <= 1e-6,
                support_ratios[0] > 1. and
                abs(support_ratios[0] - support_ratios[1]) <= 1e-6))
    return tuple(audits)


def audit_snapshots(snapshots, wave_sizes, all_sites_exact):
    grammar = compile_frontier_state_grammar(snapshots, maximum_nodes=5)
    triples = _three_wave_audits(grammar)
    grouped = tuple(sum(wave_sizes[index:index + 4])
                    for index in range(0, len(wave_sizes), 4)
                    if len(wave_sizes[index:index + 4]) == 4)
    histogram = tuple(sorted(Counter(
        state.support_size for state in grammar.recurring_state_types
    ).items()))
    return FrontierStatePromotionBenchmark(
        len(snapshots), grammar.atom_count, tuple(wave_sizes), all_sites_exact,
        True, False, grammar.candidate_subgraphs,
        grammar.normalized_state_types, len(grammar.recurring_state_types),
        histogram, sum(len(state.occurrences)
                       for state in grammar.recurring_state_types),
        grammar.proper_pose_occurrences, grammar.repeated_covered_atoms,
        grammar.repeated_covered_atoms / grammar.atom_count,
        len(grammar.residual_sites), grammar.complete_cover, triples,
        sum(item.equal_expanding_scale for item in triples),
        sum(item.equal_expanding_scale and item.finite_proper_pose
            for item in triples),
        sum(item.equal_expanding_support for item in triples),
        len(grammar.stationary_witnesses), False, False, grouped, False,
        grammar.exponential_gate_passed,
        ("The structural compiler replaces count-only wave bundles with a "
         "complete cover of recurring proper-similarity frontier states and "
         "explicit residual sites."),
        ("One two-site state repeats the same expanding scale over three "
         "waves, but it has a continuous rotational stabilizer and its unique "
         "support shrinks instead of amplifying. No finite oriented candidate "
         "has both repeated expanding scale and repeated expanding "
         "support. The next promotion must learn transitions between state "
         "types rather than copy a constant-size terminal fragment."),
        grammar.grammar_digest)


def evaluate(waves=16):
    if waves < 3:
        raise ValueError("the promotion benchmark needs at least three waves")
    source = frontier(regenerative_wave_count=waves)
    snapshots = tuple(FrontierWaveSnapshot(
        trace.wave, trace.positions, trace.species, False)
        for trace in source.regenerative_growth_traces)
    sizes = tuple(item.plateau_sites
                  for item in source.regenerative_growth_waves)
    exact = all(item.false_sites == 0
                for item in source.regenerative_growth_waves)
    return audit_snapshots(snapshots, sizes, exact)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--waves", type=int, default=16)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.waves)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
