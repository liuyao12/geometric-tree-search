#!/usr/bin/env python3
"""Sealed blind molecular-port continuation gate for ice Ih.

The oracle is used only to prepare a disjoint observed seed and, after every
trace is immutable, to open the outer scoring shell.  The learner/executors
receive no target coordinates, ice label, cell, formula, ring size, or expected
frontier size.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_ice_cover import ice_ih
from materials_gcts_molecular_gap_clusters import unwrapped_cluster_sites
from materials_gcts_molecular_port_growth import (
    execute_molecular_anchor_growth,
    execute_molecular_port_growth,
    fit_molecular_port_grammar,
    recognize_seed_molecules,
    score_sites,
)

Vector = tuple[float, float, float]
REPEATS = (8, 8, 5)
TRAIN_FRACTION = (.22, .22, .50)
EVAL_FRACTION = (.75, .75, .50)
TRAIN_RADIUS = 8.0
SEED_RADIUS = 4.0
TARGET_RADIUS = 8.0


@dataclass(frozen=True)
class BlindIceGrowthResult:
    training_atoms: int
    training_molecules: int
    frozen_ports: int
    seed_atoms: int
    seed_molecules: int
    target_atoms: int
    target_outer_atoms: int
    train_target_raw_molecule_overlap: int
    center_separation: float
    required_separation: float
    target_open_count: int
    whole_molecule_waves: tuple[tuple[int, int], ...]
    whole_emitted_atoms: int
    whole_correct_atoms: int
    whole_wrong_atoms: int
    whole_precision: float
    whole_outer_recall: float
    whole_correct_oxygen: int
    whole_wrong_oxygen: int
    whole_oxygen_precision: float
    whole_oxygen_outer_recall: float
    factored_first_wave_anchors: int
    factored_first_wave_correct: int
    factored_first_wave_wrong: int
    factored_first_wave_precision: float
    factored_first_wave_outer_recall: float
    factored_two_wave_anchors: int
    factored_two_wave_correct: int
    factored_two_wave_wrong: int
    factored_two_wave_precision: float
    factored_two_wave_outer_recall: float
    unresolved_orientation_hypotheses: int
    traces_frozen_before_target: bool
    target_used_by_grammar_or_execution: bool
    exact_port_geometry_certificates: bool
    one_wave_anchor_gate_passed: bool
    sustained_blind_molecular_growth_passed: bool
    stationary_or_exponential_claim: bool
    trace_digest: str


def _center(cell: tuple[Vector, Vector, Vector], fraction: Vector) -> Vector:
    return tuple(sum(fraction[index] * cell[index][axis] for index in range(3))
                 for axis in range(3))  # type: ignore[return-value]


def _crop(fraction: Vector, radius: float) -> tuple[
        tuple[int, ...], tuple[str, ...], tuple[Vector, ...],
        tuple[tuple[str, Vector], ...], Vector]:
    configuration = ice_ih(REPEATS)
    oxygen_count = len(configuration.positions) // 3
    center = _center(configuration.cell, fraction)
    molecule_ids = []
    sites = []
    for oxygen in range(oxygen_count):
        if math.dist(configuration.positions[oxygen], center) > radius:
            continue
        molecule_ids.append(oxygen)
        members = (oxygen, oxygen_count + 2 * oxygen,
                   oxygen_count + 2 * oxygen + 1)
        sites.extend(unwrapped_cluster_sites(
            configuration.species, configuration.positions, members,
            cell=configuration.cell))
    return (tuple(molecule_ids), tuple(species for species, _ in sites),
            tuple(point for _, point in sites), tuple(sites), center)


def evaluate() -> BlindIceGrowthResult:
    train_ids, train_species, train_positions, _, train_center = _crop(
        TRAIN_FRACTION, TRAIN_RADIUS)
    seed_ids, seed_species, seed_positions, _, eval_center = _crop(
        EVAL_FRACTION, SEED_RADIUS)
    grammar = fit_molecular_port_grammar(
        train_species, train_positions, pose_tolerance=.04,
        minimum_port_observations=2)
    _, seed_occurrences, seed_sites = recognize_seed_molecules(
        grammar, seed_species, seed_positions)

    whole = execute_molecular_port_growth(
        grammar, seed_occurrences, seed_sites,
        boundary_center=eval_center, boundary_radius=TARGET_RADIUS,
        maximum_waves=6, maximum_accepted_per_wave=256,
        minimum_witnesses=1)
    factored_one = execute_molecular_anchor_growth(
        grammar, seed_occurrences, boundary_center=eval_center,
        boundary_radius=TARGET_RADIUS, maximum_waves=1,
        maximum_hypotheses_per_anchor=8)
    factored_two = execute_molecular_anchor_growth(
        grammar, seed_occurrences, boundary_center=eval_center,
        boundary_radius=TARGET_RADIUS, maximum_waves=2,
        maximum_hypotheses_per_anchor=8)
    frozen_payload = {
        "whole": [wave.candidate_digest for wave in whole.waves],
        "one": [wave.candidate_digest for wave in factored_one.waves],
        "two": [wave.candidate_digest for wave in factored_two.waves],
        "whole_sites": sorted((species, *(round(value / .04) for value in point))
                              for species, point in whole.emitted_sites),
        "one_sites": sorted((species, *(round(value / .04) for value in point))
                            for species, point in factored_one.emitted_anchors),
        "two_sites": sorted((species, *(round(value / .04) for value in point))
                            for species, point in factored_two.emitted_anchors),
    }
    trace_digest = hashlib.sha256(json.dumps(
        frozen_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    target_open_count = 0

    def open_target():
        nonlocal target_open_count
        if target_open_count:
            raise AssertionError("sealed target may be opened exactly once")
        target_open_count += 1
        return _crop(EVAL_FRACTION, TARGET_RADIUS)

    target_ids, _, _, target_sites, opened_center = open_target()
    assert opened_center == eval_center
    whole_correct, whole_wrong, _ = score_sites(whole.emitted_sites, target_sites)
    target_oxygen = tuple(site for site in target_sites if site[0] == "O")
    predicted_oxygen = tuple(site for site in whole.emitted_sites if site[0] == "O")
    oxygen_correct, oxygen_wrong, _ = score_sites(predicted_oxygen, target_oxygen)
    one_correct, one_wrong, _ = score_sites(
        factored_one.emitted_anchors, target_oxygen)
    two_correct, two_wrong, _ = score_sites(
        factored_two.emitted_anchors, target_oxygen)
    target_outer_atoms = len(target_sites) - len(seed_sites)
    target_outer_oxygen = len(target_oxygen) - len(seed_occurrences)
    one_gate = (one_wrong == 0 and one_correct > 0
                and not whole.target_used and not factored_one.target_used)
    sustained = (two_wrong == 0 and len(factored_two.waves) >= 2
                 and all(wave.accepted_anchors > 0 for wave in factored_two.waves))
    return BlindIceGrowthResult(
        training_atoms=len(train_species), training_molecules=len(train_ids),
        frozen_ports=len(grammar.ports), seed_atoms=len(seed_sites),
        seed_molecules=len(seed_occurrences), target_atoms=len(target_sites),
        target_outer_atoms=target_outer_atoms,
        train_target_raw_molecule_overlap=len(set(train_ids) & set(target_ids)),
        center_separation=math.dist(train_center, eval_center),
        required_separation=TRAIN_RADIUS + TARGET_RADIUS,
        target_open_count=target_open_count,
        whole_molecule_waves=tuple((wave.candidates, wave.accepted)
                                   for wave in whole.waves),
        whole_emitted_atoms=len(whole.emitted_sites),
        whole_correct_atoms=whole_correct, whole_wrong_atoms=whole_wrong,
        whole_precision=whole_correct / max(1, whole_correct + whole_wrong),
        whole_outer_recall=whole_correct / target_outer_atoms,
        whole_correct_oxygen=oxygen_correct, whole_wrong_oxygen=oxygen_wrong,
        whole_oxygen_precision=oxygen_correct / max(1, oxygen_correct + oxygen_wrong),
        whole_oxygen_outer_recall=oxygen_correct / target_outer_oxygen,
        factored_first_wave_anchors=len(factored_one.emitted_anchors),
        factored_first_wave_correct=one_correct,
        factored_first_wave_wrong=one_wrong,
        factored_first_wave_precision=one_correct / max(1, one_correct + one_wrong),
        factored_first_wave_outer_recall=one_correct / target_outer_oxygen,
        factored_two_wave_anchors=len(factored_two.emitted_anchors),
        factored_two_wave_correct=two_correct,
        factored_two_wave_wrong=two_wrong,
        factored_two_wave_precision=two_correct / max(1, two_correct + two_wrong),
        factored_two_wave_outer_recall=two_correct / target_outer_oxygen,
        unresolved_orientation_hypotheses=factored_two.unresolved_new_molecules,
        traces_frozen_before_target=True,
        target_used_by_grammar_or_execution=(
            grammar.target_used or whole.target_used or factored_one.target_used
            or factored_two.target_used),
        exact_port_geometry_certificates=(
            whole.exact_geometry_certificates
            and factored_one.exact_port_geometry_certificates
            and factored_two.exact_port_geometry_certificates),
        one_wave_anchor_gate_passed=one_gate,
        sustained_blind_molecular_growth_passed=sustained,
        stationary_or_exponential_claim=False,
        trace_digest=trace_digest,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
