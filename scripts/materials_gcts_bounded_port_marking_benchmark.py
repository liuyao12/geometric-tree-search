#!/usr/bin/env python3
"""Causal ablation of a bounded local marking on identical port actions."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_bounded_port_marking import (
    build_frozen_target_decisions, build_port_decisions,
    evaluate_ranking_work, fit_bounded_port_marking,
    shuffle_training_contexts)
from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_periodic_growth import replicate


@dataclass(frozen=True)
class BoundedMarkingCase:
    system: str
    training_atoms: int
    target_atoms: int
    raw_port_classes: int
    abstract_action_states: int
    training_examples: int
    target_examples: int
    raw_training_contexts: int
    exact_marking_states: int
    backoff_states: int
    minimum_state_support: int
    exact_context_coverage: float
    backoff_context_coverage: float
    marked_mean_checks: float
    unmarked_mean_checks: float
    shuffled_mean_checks: float
    shuffled_best_mean_checks: float
    shuffled_runs: int
    empirical_shuffle_p_value: float
    marked_top_one: float
    unmarked_top_one: float
    shuffled_top_one: float
    gain_over_unmarked: float
    gain_over_shuffled: float
    identical_candidate_actions: bool
    marking_state_selection_train_only: bool
    material_labels_global_frame_target_tuning_unused: bool


def _case(training_configuration: AtomicConfiguration,
          target_configuration: AtomicConfiguration,
          shuffled_runs: int) -> BoundedMarkingCase:
    program = compile_irregular_port_program(
        training_configuration.species, training_configuration.positions)
    training = build_port_decisions(program)
    marking = fit_bounded_port_marking(training)
    frozen = enumerate_frozen_port_occurrences(
        program, target_configuration.species, target_configuration.positions,
        select_greedy_cover=True)
    target = build_frozen_target_decisions(program, frozen)
    marked_work = evaluate_ranking_work(marking, target, arm="marked")
    unmarked_work = evaluate_ranking_work(marking, target, arm="unmarked")
    shuffled_works = tuple(evaluate_ranking_work(
        fit_bounded_port_marking(shuffle_training_contexts(
            training, seed=1729 + run)), target, arm="marked")
                           for run in range(shuffled_runs))
    shuffled_checks = tuple(item.mean_checks for item in shuffled_works)
    identical = len({marked_work.candidate_digest,
                     unmarked_work.candidate_digest,
                     *(item.candidate_digest for item in shuffled_works)}) == 1
    static_actions = {feature[0] for decision in training
                      for feature in decision.candidate_features}
    return BoundedMarkingCase(
        training_configuration.name, len(training_configuration.positions),
        len(target_configuration.positions), len(program.atlas.ports),
        len(static_actions), len(training), len(target),
        marking.raw_contexts, len(marking.exact_counts),
        len(marking.backoff_counts), marking.minimum_state_support,
        marked_work.exact_context_coverage,
        marked_work.backoff_context_coverage, marked_work.mean_checks,
        unmarked_work.mean_checks, median(shuffled_checks),
        min(shuffled_checks), shuffled_runs,
        (1 + sum(value <= marked_work.mean_checks
                 for value in shuffled_checks)) / (shuffled_runs + 1),
        marked_work.top_one_accuracy, unmarked_work.top_one_accuracy,
        median(item.top_one_accuracy for item in shuffled_works),
        unmarked_work.mean_checks / marked_work.mean_checks,
        median(shuffled_checks) / marked_work.mean_checks,
        identical, True, True)


def evaluate(shuffled_runs: int = 31) -> tuple[BoundedMarkingCase, ...]:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    nacl = AtomicConfiguration(nacl.name, nacl.positions, nacl.species)
    iqc, _ = oracle_patch(3, 9.0)
    iqc_target, _ = oracle_patch(4, 15.0)
    cdyb = build_cdyb_split()
    return tuple(_case(training, target, shuffled_runs)
                 for training, target in (
                     (nacl, replicate(next(item for item in benchmark_systems()
                                           if item.name == "NaCl-rocksalt"))),
                     (iqc, iqc_target),
                     (cdyb.training, cdyb.validation)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps([asdict(item) for item in result], indent=2,
                     sort_keys=True) if arguments.json else result)


if __name__ == "__main__":
    main()
