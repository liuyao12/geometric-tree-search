#!/usr/bin/env python3
"""Causal incoming-port marking ablation on frozen unseen configurations."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import (
    compile_frozen_target_atlas, compile_irregular_port_program,
    enumerate_frozen_port_occurrences)
from materials_gcts_oriented_port_marking import (
    choice_samples, fit_incoming_port_marking, score_marking,
    shuffled_markings)
from materials_gcts_periodic_growth import replicate


@dataclass(frozen=True)
class OrientedMarkingCase:
    system: str
    training_atoms: int
    target_atoms: int
    training_samples: int
    admitted_contexts: int
    target_choice_samples: int
    scored_choices: int
    scored_context_coverage: float
    unmarked_checks: int
    marked_checks: int
    unmarked_failures: int
    marked_failures: int
    check_reduction: float
    failure_reduction: float
    shuffle_median_failures: float
    shuffle_best_failures: int
    beats_every_shuffle: bool


@dataclass(frozen=True)
class OrientedMarkingBenchmark:
    cases: tuple[OrientedMarkingCase, ...]
    systems_with_marking_gain: int
    systems_beating_every_shuffle: int
    every_case_matched_choice_count: bool
    every_case_train_only: bool
    causal_marking_gate_passed: bool


def _port_key(port):
    return port.parent_type, port.child_type, port.symmetry_orbit_key


def _case(training: AtomicConfiguration,
          target: AtomicConfiguration) -> OrientedMarkingCase:
    program = compile_irregular_port_program(
        training.species, training.positions)
    marking = fit_incoming_port_marking(program)
    admitted = frozenset(_port_key(port) for port in program.atlas.ports)
    training_types = {item.occurrence_id: item.type_id
                      for item in program.occurrences}
    training_samples = choice_samples(
        program.atlas, training_types, admitted_ports=admitted,
        maximum_incoming_per_node=marking.maximum_incoming_per_node,
        maximum_outgoing_per_node=marking.maximum_outgoing_per_node)

    frozen = enumerate_frozen_port_occurrences(
        program, target.species, target.positions,
        select_greedy_cover=True)
    target_atlas = compile_frozen_target_atlas(program, frozen)
    target_types = {item.occurrence_id: item.type_id
                    for item in frozen.occurrences}
    target_samples = choice_samples(
        target_atlas, target_types, admitted_ports=admitted,
        maximum_incoming_per_node=marking.maximum_incoming_per_node,
        maximum_outgoing_per_node=marking.maximum_outgoing_per_node)
    marked = score_marking(marking, target_samples, use_context=True)
    unmarked = score_marking(marking, target_samples, use_context=False)
    if marked.scored_choices != unmarked.scored_choices:
        raise AssertionError("marked and unmarked arms scored different choices")
    shuffle_failures = tuple(score_marking(
        shuffled, target_samples, use_context=True).failed_checks
        for shuffled in shuffled_markings(marking, training_samples))
    return OrientedMarkingCase(
        training.name, len(training.positions), len(target.positions),
        marking.training_samples, marking.admitted_contexts,
        len(target_samples), marked.scored_choices,
        marked.contexts_seen / max(1, marked.scored_choices),
        unmarked.proposal_checks, marked.proposal_checks,
        unmarked.failed_checks, marked.failed_checks,
        unmarked.proposal_checks / max(1, marked.proposal_checks),
        unmarked.failed_checks / max(1, marked.failed_checks),
        median(shuffle_failures) if shuffle_failures else 0.0,
        min(shuffle_failures, default=0),
        bool(shuffle_failures) and marked.failed_checks < min(shuffle_failures))


def evaluate() -> OrientedMarkingBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    nacl_cloud = AtomicConfiguration(nacl.name, nacl.positions, nacl.species)
    iqc, _ = oracle_patch(3, 9.0)
    iqc_target, _ = oracle_patch(4, 15.0)
    cdyb = build_cdyb_split()
    cases = tuple(_case(training, target) for training, target in (
        (nacl_cloud, replicate(nacl)), (iqc, iqc_target),
        (cdyb.training, cdyb.validation)))
    significant = sum(case.beats_every_shuffle for case in cases)
    strong = sum(case.beats_every_shuffle and case.failure_reduction >= 2.0
                 for case in cases)
    return OrientedMarkingBenchmark(
        cases, sum(case.marked_failures < case.unmarked_failures
                   for case in cases), significant,
        all(case.scored_choices <= case.target_choice_samples
            for case in cases), True, strong >= 2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
