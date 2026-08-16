#!/usr/bin/env python3
"""Current best crystal + IQC executors against the autonomous-growth gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from types import SimpleNamespace

from materials_gcts_autonomous_growth_contract import (
    AutonomousGrowthContractAudit, ColoredGrowthScore,
    FrozenAutonomousTrace, audit_contract, audit_growth_case,
    cloud_digest, execute_then_open_target, freeze_trace)
from materials_gcts_frozen_frontier_replay import _site_key
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_iqc_reclustered_transfer_audit import (
    PATCH_CENTERS, TRAIN_PATCH_IDS, _pack)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_periodic_growth import replicate
from materials_gcts_recurrent_macro_execution_benchmark import (
    _fit_selected, _seed_occurrences)
from materials_gcts_recurrent_macro_executor import (
    ExecutionBoundary, execute_recurrent_macro_program,
    score_recurrent_macro_execution)
from materials_gcts_recursive_program import (
    discover_recursive_program, explicit_apply, symbolic_count)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop
from materials_pointset_benchmarks import amorphous_hard_core_point_set


def _configuration_sites(configuration):
    return tuple(zip(configuration.species, configuration.positions))


def _score_sites(trace, target):
    tolerance = .03
    proposed = {_site_key(site, tolerance) for site in trace.proposed_sites}
    seed = {_site_key(site, tolerance) for site in trace.seed_sites}
    target_sites = {_site_key(site, tolerance)
                    for site in _configuration_sites(target)}
    correct = proposed & target_sites
    novel_target = target_sites - seed
    return ColoredGrowthScore(
        len(proposed), len(correct), len(novel_target),
        len(correct) / max(1, len(proposed)),
        len(correct) / max(1, len(novel_target)))


def _nacl_case():
    seed = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    train = AtomicConfiguration(
        seed.name, seed.positions, seed.species)

    def execute(training, initial):
        program = discover_recursive_program(training)
        levels = tuple(explicit_apply(initial, program, action)
                       for action in (1, 2, 3))
        initial_keys = set(_configuration_sites(initial))
        proposed = tuple(site for site in _configuration_sites(levels[-1])
                         if site not in initial_keys)
        counts = (len(initial.positions),) + tuple(
            len(item.positions) for item in levels)
        emitted = tuple(right - left for left, right in zip(
            counts, counts[1:]))
        return FrozenAutonomousTrace(
            training.name, "specialized_positions_only_grid",
            program.family, cloud_digest(training.species,
                                         training.positions),
            cloud_digest(initial.species, initial.positions), "", (),
            (1, 1, 1), emitted, True, True, 3, False, True, 0, 3, 0,
            _configuration_sites(initial), proposed,
            False, None, None, None, None,
            tuple(symbolic_count(initial, program, action)
                  for action in range(8)), False, False, False)

    def target_factory():
        first = replicate(seed)
        second = replicate(first)
        return replicate(second)

    trace, score, post = execute_then_open_target(
        train, seed, executor=execute, target_factory=target_factory,
        scorer=_score_sites)
    return audit_growth_case(
        trace, score, role="crystal",
        target_constructed_after_trace_frozen=post)


def _iqc_case():
    # Mechanically reproduce the strictly disjoint R11 arm.  The executor
    # closure receives only train+seed artifacts.  `_crop(...score)` is called
    # by target_factory only after execute_then_open_target freezes the trace.
    oracle, _ = oracle_patch_fast(12, 55.)
    train_clouds = []
    raw_domains = []
    for patch_id, center in enumerate(PATCH_CENTERS):
        cloud, raw_ids = _crop(
            oracle, center, 11., f"autonomous-raw-train-{patch_id}")
        train_clouds.append(SimpleNamespace(
            sites=tuple(zip(cloud.species, cloud.positions))))
        raw_domains.append(frozenset(raw_ids))
    train_species, train_positions, train_patch = _pack(
        train_clouds, TRAIN_PATCH_IDS)
    atomic, _quotient, _selection, selected, promoted = _fit_selected(
        train_species, train_positions, train_patch, 3)
    center = (40., 0., 0.)
    seed_cloud, seed_ids = _crop(
        oracle, center, 7., "autonomous-iqc-seed")
    seed_occurrences = _seed_occurrences(
        atomic, selected, promoted, seed_cloud.species,
        seed_cloud.positions)
    train_raw_ids = set().union(*(raw_domains[index]
                                  for index in TRAIN_PATCH_IDS))

    def execute(_training, _seed):
        execution = execute_recurrent_macro_program(
            promoted, seed_occurrences,
            explicit_seed_sites=tuple(zip(seed_cloud.species,
                                          seed_cloud.positions)),
            boundary=ExecutionBoundary(center, 11.), maximum_waves=3,
            maximum_accepted_per_wave=40)
        seed_keys = {_site_key(site, .03) for site in execution.seed_sites}
        proposed = tuple(site for site in execution.sites
                         if _site_key(site, .03) not in seed_keys)
        return FrozenAutonomousTrace(
            "ideal-IQC-disjoint-r11",
            "generic_frozen_recurrent_macro_frontier",
            "recurring_port_graph_macro",
            cloud_digest(train_species, train_positions),
            cloud_digest(seed_cloud.species, seed_cloud.positions), "",
            tuple(item.candidate_digest for item in execution.waves),
            tuple(item.accepted_placements for item in execution.waves),
            tuple(item.emitted_atoms for item in execution.waves),
            execution.self_fed, execution.exact_certificates,
            execution.longest_parent_child_depth,
            execution.reachable_fixed_point,
            execution.stopped_by_wave_limit,
            execution.deferred_by_wave_cap, len(execution.accepted),
            len(execution.accepted), tuple(execution.seed_sites), proposed,
            False, None, None, None, None, (), True,
            execution.target_used_for_proposals_or_ranking, False)

    def target_factory():
        return _crop(oracle, center, 11., "autonomous-iqc-score")

    def scorer(trace, target):
        cloud, target_ids = target
        if (train_raw_ids.intersection(target_ids) or
                train_raw_ids.intersection(seed_ids)):
            raise AssertionError("IQC autonomous fixture is not raw-ID disjoint")
        execution_score = score_recurrent_macro_execution(
            SimpleNamespace(
                seed_sites=trace.seed_sites, sites=trace.seed_sites +
                trace.proposed_sites,
                target_used_for_proposals_or_ranking=
                trace.target_used_during_compile_or_execution),
            cloud.species, cloud.positions)
        return ColoredGrowthScore(
            execution_score.proposed_novel_atoms,
            execution_score.correct_novel_atoms,
            execution_score.target_atoms_outside_seed,
            execution_score.precision, execution_score.recall_outside_seed)

    trace, score, post = execute_then_open_target(
        (train_species, train_positions),
        (seed_cloud.species, seed_cloud.positions), executor=execute,
        target_factory=target_factory, scorer=scorer)
    return audit_growth_case(
        trace, score, role="quasicrystal",
        target_constructed_after_trace_frozen=post)


def evaluate() -> AutonomousGrowthContractAudit:
    cases = _nacl_case(), _iqc_case()
    amorphous = amorphous_hard_core_point_set(atom_count=216, seed=91)
    amorphous_configuration = AtomicConfiguration(
        amorphous.name, amorphous.positions, amorphous.species)
    amorphous_program = compile_irregular_port_program(
        amorphous_configuration.species, amorphous_configuration.positions)
    amorphous_macros = mine_port_graph_macros(
        amorphous_program, maximum_nodes=5,
        include_boundary_relations=True)
    amorphous_rejected = not amorphous_macros.macro_types
    return audit_contract(
        cases, amorphous_rejected=amorphous_rejected,
        nonqualifying_evidence_notes=(
            "NaCl exact autonomous output uses the specialized positions-only "
            "grid backend, not the generic recurrent port-macro production.",
            "The promoted-macro marking audit labels 718 train-frontier "
            "candidates, including 25 invalid actions, but all 62 evaluation "
            "commit contexts are unseen. Marked, unmarked, and 31 shuffled "
            "arms tie, so the matched marking gate remains red.",
            "The sealed IQC R11 executor certifies causal depth two and then "
            "reaches a finite fixed point. Changing the batch cap changes "
            "the displayed wave count but not its 148-atom final union, so "
            "wave count is not used as an autonomous-growth gate.",
        ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
