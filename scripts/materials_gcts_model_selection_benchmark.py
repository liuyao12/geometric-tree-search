#!/usr/bin/env python3
"""Family-blind model-selection benchmark for recursive GCTS programs."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_2d_generic_atlas import layered_hexagonal_configuration
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_recursive_program import (
    discover_recursive_program_candidates, select_recursive_program_candidate)
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class SelectionCase:
    system: str
    proposed_programs: Tuple[str, ...]
    proposal_scores: Tuple[float, ...]
    selected_program: str
    winning_margin: float | None
    selection_order_invariant: bool
    selected_seed_replay_exact: bool


@dataclass(frozen=True)
class ModelSelectionBenchmark:
    cases: Tuple[SelectionCase, ...]
    competing_hypothesis_case_present: bool
    amorphous_proposals: int
    phase_label_used: bool
    all_expected_selected: bool
    benchmark_passed: bool


def _case(configuration: AtomicConfiguration) -> SelectionCase:
    candidates = discover_recursive_program_candidates(configuration)
    selected = select_recursive_program_candidate(candidates)
    reversed_selected = select_recursive_program_candidate(
        tuple(reversed(candidates)))
    scores = tuple(candidate.selection_score for candidate in candidates)
    return SelectionCase(
        configuration.name,
        tuple(candidate.program.family for candidate in candidates),
        scores, selected.program.family,
        scores[1] - scores[0] if len(scores) > 1 else None,
        selected.program.family == reversed_selected.program.family,
        selected.seed_replay_exact)


def evaluate() -> ModelSelectionBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    iqc, _ = oracle_patch(3, 9.0)
    fibonacci = make_input(9)
    planar = layered_hexagonal_configuration(
        "selection-30deg-hBN", 18.0,
        ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N")),
        (0.0, math.pi / 6), global_rotation=True)
    configurations = (nacl, iqc, fibonacci, planar)
    cases = tuple(_case(configuration) for configuration in configurations)
    expected = ("translation_quotient", "internal_section_inflation",
                "substitution_product", "planar_pose_address")
    sample = amorphous_hard_core_point_set(atom_count=507)
    amorphous = AtomicConfiguration(sample.name, sample.positions,
                                    sample.species)
    amorphous_proposals = len(discover_recursive_program_candidates(amorphous))
    competing = any(len(case.proposed_programs) > 1 for case in cases)
    selected = tuple(case.selected_program for case in cases) == expected
    invariant = all(case.selection_order_invariant for case in cases)
    return ModelSelectionBenchmark(
        cases, competing, amorphous_proposals, False, selected,
        competing and selected and invariant and amorphous_proposals == 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
