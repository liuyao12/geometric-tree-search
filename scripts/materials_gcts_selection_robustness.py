#!/usr/bin/env python3
"""Robustness gate for family-blind recursive-program selection and growth."""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_2d_generic_atlas import layered_hexagonal_configuration
from materials_gcts_2d_robustness import corrupt_seed, _registered_score
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import AtomicConfiguration, benchmark_systems, perturb
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_periodic_growth import replicate
from materials_gcts_recursive_program import (
    discover_recursive_program_candidates, explicit_apply,
    select_recursive_program_candidate)
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class RobustSelectionCase:
    system: str
    corruption: str
    observed_atoms: int
    selected_program: str
    seed_replay_exact: bool
    grown_atoms: int
    clean_precision: float
    clean_recall: float
    chemical_accuracy: float
    registered_rms_error: float


@dataclass(frozen=True)
class SelectionRobustnessBenchmark:
    retained_cases: Tuple[RobustSelectionCase, ...]
    expected_programs: Tuple[str, ...]
    all_programs_retained: bool
    all_clean_precision_above_99_percent: bool
    all_clean_recall_above_99_percent: bool
    iqc_vacancy_proposals: int
    iqc_vacancy_rejection_seconds: float
    bounded_bad_hypothesis_rejection: bool
    defect_crystal_selected_program: str
    defect_crystal_seed_replay_exact: bool
    amorphous_trials: int
    amorphous_false_positives: int
    benchmark_passed: bool


def _score_case(observed: AtomicConfiguration, clean_target: AtomicConfiguration,
                corruption: str) -> RobustSelectionCase:
    candidates = discover_recursive_program_candidates(observed)
    selected = select_recursive_program_candidate(candidates)
    program = selected.program
    grown = explicit_apply(observed, program, 1)
    precision, recall, chemistry, rms = _registered_score(
        grown, clean_target, tolerance=.16)
    return RobustSelectionCase(
        observed.name, corruption, len(observed.positions), program.family,
        selected.seed_replay_exact, len(grown.positions), precision, recall,
        chemistry, rms)


def _remove_fraction(configuration: AtomicConfiguration, fraction: float,
                     seed: int) -> AtomicConfiguration:
    generator = random.Random(seed)
    keep = tuple(index for index in range(len(configuration.positions))
                 if generator.random() >= fraction)
    return AtomicConfiguration(
        configuration.name + "-vacancies",
        tuple(configuration.positions[index] for index in keep),
        tuple(configuration.species[index] for index in keep))


def evaluate() -> SelectionRobustnessBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    iqc, _ = oracle_patch(3, 9.0)
    fibonacci = make_input(9)
    basis = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    angles = (0.0, math.pi / 6)
    planar = layered_hexagonal_configuration(
        "robust-30deg-hBN", 18.0, basis, angles, global_rotation=True)
    observed = (
        perturb(nacl, .005, 123),
        perturb(iqc, .005, 123),
        perturb(fibonacci, .005, 123),
        corrupt_seed(planar, .006, .035, 703),
    )
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    targets = (
        replicate(nacl), oracle_patch(4, 9.0 * phi)[0], make_input(15),
        layered_hexagonal_configuration(
            "robust-30deg-hBN-target", 36.0, basis, angles,
            global_rotation=True),
    )
    corruptions = ("0.005 A Gaussian", "0.005 A Gaussian",
                   "0.005 A Gaussian", "0.006 A Gaussian + 3.5% vacancies")
    cases = tuple(_score_case(item, target, corruption)
                  for item, target, corruption in zip(
                      observed, targets, corruptions))
    expected = ("translation_quotient", "internal_section_inflation",
                "substitution_product", "planar_pose_address")

    vacancy_iqc = _remove_fraction(perturb(iqc, .005, 123), .01, 9)
    started = time.perf_counter()
    vacancy_candidates = discover_recursive_program_candidates(vacancy_iqc)
    rejection_seconds = time.perf_counter() - started

    defect_species = list(nacl.species)
    defect_species[len(defect_species) // 2] = "K"
    defect = AtomicConfiguration(
        "NaCl-single-substitution", nacl.positions, tuple(defect_species))
    defect_candidates = discover_recursive_program_candidates(defect)
    defect_selected = min(defect_candidates,
                          key=lambda item: item.selection_score)

    false_positives = 0
    trials = 2
    for seed in range(trials):
        sample = amorphous_hard_core_point_set(507, seed=91 + seed)
        cloud = AtomicConfiguration(sample.name, sample.positions,
                                    sample.species)
        false_positives += bool(discover_recursive_program_candidates(cloud))

    retained = tuple(case.selected_program for case in cases) == expected
    precision = all(case.clean_precision >= .99 for case in cases)
    recall = all(case.clean_recall >= .99 for case in cases)
    bounded = not vacancy_candidates and rejection_seconds < 10.0
    defect_ok = (defect_selected.program.family == "translation_quotient" and
                 not defect_selected.seed_replay_exact)
    passed = (retained and precision and recall and bounded and defect_ok and
              false_positives == 0)
    return SelectionRobustnessBenchmark(
        cases, expected, retained, precision, recall,
        len(vacancy_candidates), rejection_seconds, bounded,
        defect_selected.program.family, defect_selected.seed_replay_exact,
        trials, false_positives, passed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
