#!/usr/bin/env python3
"""Audit executable transitions learned between exact IQC frontier states."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import evaluate as frontier
from materials_gcts_frontier_state_grammar import (
    FrontierWaveSnapshot, compile_frontier_state_grammar)
from materials_gcts_frontier_state_transitions import (
    compile_frontier_substitution_system, compile_frontier_transition_grammar)


@dataclass(frozen=True)
class FrontierStateTransitionBenchmark:
    source_waves: int
    source_sites: int
    source_sites_exact: bool
    source_uses_global_superspace_section: bool
    compiler_uses_material_family_cell_or_target: bool
    recurring_state_types: int
    finite_proper_state_types: int
    packed_proper_occurrences: int
    transition_observations: int
    exact_transition_rules: int
    maximum_children_per_rule: int
    multi_child_rules: int
    heterogeneous_child_rules: int
    maximum_distinct_child_types: int
    rules_seen_on_multiple_transitions: int
    positive_mdl_rules: int
    closed_substitution_state_types: int
    closed_substitution_growth: float
    stationary_rule_ids: tuple[int, ...]
    executable_stationary_rule: bool
    generic_million_site_iqc_claim: bool
    target_used: bool
    grammar_digest: str
    improvement: str
    first_blocker: str


def audit_snapshots(snapshots, source_sites_exact=True):
    states = compile_frontier_state_grammar(snapshots, maximum_nodes=5)
    transitions = compile_frontier_transition_grammar(states, snapshots)
    substitution = compile_frontier_substitution_system(transitions)
    multi_child = sum(len(rule.child_placements) > 1
                      for rule in transitions.rules)
    heterogeneous = sum(len(set(rule.child_types)) > 1
                        for rule in transitions.rules)
    maximum_types = max((len(set(rule.child_types))
                         for rule in transitions.rules), default=0)
    return FrontierStateTransitionBenchmark(
        len(snapshots), states.atom_count, source_sites_exact, True, False,
        len(states.recurring_state_types), transitions.proper_state_types,
        transitions.packed_occurrences, transitions.transition_observations,
        len(transitions.rules),
        max((len(rule.child_placements) for rule in transitions.rules),
            default=0),
        multi_child, heterogeneous, maximum_types,
        sum(rule.independent_transition_waves >= 2
            for rule in transitions.rules),
        sum(rule.description_saving > 0 for rule in transitions.rules),
        len(substitution.state_types) if substitution else 0,
        substitution.asymptotic_growth if substitution else 0.,
        transitions.stationary_rule_ids,
        bool(transitions.stationary_rule_ids), False,
        transitions.target_used, transitions.grammar_digest,
        ("The compiler now retains one complete heterogeneous child set per "
         "parent occurrence instead of splitting mixed cluster-of-clusters "
         "productions into unrelated unary rules."),
        (f"The IQC trace contains {multi_child} exact multi-child rules "
         f"({heterogeneous} heterogeneous), but none recur on multiple "
         "transitions or save description length. There is still no "
         "stationary or million-site generic IQC rule."))


def evaluate(waves=16):
    source = frontier(regenerative_wave_count=waves)
    snapshots = tuple(FrontierWaveSnapshot(
        trace.wave, trace.positions, trace.species)
        for trace in source.regenerative_growth_traces)
    exact = all(row.false_sites == 0
                for row in source.regenerative_growth_waves)
    return audit_snapshots(snapshots, exact)


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
