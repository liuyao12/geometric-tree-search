#!/usr/bin/env python3
"""Use an Ih-fitted molecular port grammar for sealed cubic-ice growth."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Callable

from materials_gcts_ice_cover import IceConfiguration, ice_ic, ice_ih
from materials_gcts_molecular_gap_clusters import unwrapped_cluster_sites
from materials_gcts_molecular_port_growth import (
    execute_molecular_anchor_growth,
    execute_molecular_port_growth,
    fit_molecular_port_grammar,
    recognize_seed_molecules,
    score_sites,
)

Vector = tuple[float, float, float]


@dataclass(frozen=True)
class CrossPolytypeBlindGrowthResult:
    trained_polytype: str
    evaluated_polytype: str
    training_atoms: int
    frozen_ports: int
    seed_molecules: int
    target_molecules: int
    whole_emitted_atoms: int
    whole_correct_atoms: int
    whole_wrong_atoms: int
    whole_oxygen_precision: float
    whole_oxygen_outer_recall: float
    factored_first_wave_anchors: int
    factored_first_wave_correct: int
    factored_first_wave_wrong: int
    factored_first_wave_precision: float
    factored_two_wave_anchors: int
    factored_two_wave_correct: int
    factored_two_wave_wrong: int
    target_open_count: int
    target_used_before_scoring: bool
    first_wave_cross_polytype_gate_passed: bool
    sustained_cross_polytype_gate_passed: bool
    trace_digest: str


def _crop(factory: Callable[[], IceConfiguration], fraction: Vector,
          radius: float):
    configuration = factory()
    oxygen_count = len(configuration.positions) // 3
    center = tuple(sum(fraction[index] * configuration.cell[index][axis]
                       for index in range(3)) for axis in range(3))
    sites = []
    molecule_ids = []
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


def evaluate() -> CrossPolytypeBlindGrowthResult:
    train = _crop(lambda: ice_ih((8, 8, 5)), (.22, .22, .50), 8.0)
    seed = _crop(lambda: ice_ic((6, 6, 6)), (.75, .75, .50), 4.0)
    grammar = fit_molecular_port_grammar(
        train[1], train[2], pose_tolerance=.04,
        minimum_port_observations=2)
    _, seed_occurrences, seed_sites = recognize_seed_molecules(
        grammar, seed[1], seed[2])
    whole = execute_molecular_port_growth(
        grammar, seed_occurrences, seed_sites,
        boundary_center=seed[4], boundary_radius=8.0, maximum_waves=6)
    first = execute_molecular_anchor_growth(
        grammar, seed_occurrences, boundary_center=seed[4],
        boundary_radius=8.0, maximum_waves=1,
        maximum_hypotheses_per_anchor=8)
    second = execute_molecular_anchor_growth(
        grammar, seed_occurrences, boundary_center=seed[4],
        boundary_radius=8.0, maximum_waves=2,
        maximum_hypotheses_per_anchor=8)
    frozen = {
        "whole": [wave.candidate_digest for wave in whole.waves],
        "first": [wave.candidate_digest for wave in first.waves],
        "second": [wave.candidate_digest for wave in second.waves],
    }
    trace_digest = hashlib.sha256(json.dumps(
        frozen, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    target_open_count = 0

    def open_target():
        nonlocal target_open_count
        if target_open_count:
            raise AssertionError("target is single-use")
        target_open_count += 1
        return _crop(lambda: ice_ic((6, 6, 6)), (.75, .75, .50), 8.0)

    target = open_target()
    correct, wrong, _ = score_sites(whole.emitted_sites, target[3])
    predicted_oxygen = tuple(site for site in whole.emitted_sites if site[0] == "O")
    target_oxygen = tuple(site for site in target[3] if site[0] == "O")
    oxygen_correct, oxygen_wrong, _ = score_sites(predicted_oxygen, target_oxygen)
    first_correct, first_wrong, _ = score_sites(first.emitted_anchors, target_oxygen)
    second_correct, second_wrong, _ = score_sites(second.emitted_anchors, target_oxygen)
    outer_oxygen = len(target_oxygen) - len(seed_occurrences)
    return CrossPolytypeBlindGrowthResult(
        trained_polytype="ice-Ih", evaluated_polytype="ice-Ic",
        training_atoms=len(train[1]), frozen_ports=len(grammar.ports),
        seed_molecules=len(seed_occurrences), target_molecules=len(target[0]),
        whole_emitted_atoms=len(whole.emitted_sites), whole_correct_atoms=correct,
        whole_wrong_atoms=wrong,
        whole_oxygen_precision=oxygen_correct / max(1, oxygen_correct + oxygen_wrong),
        whole_oxygen_outer_recall=oxygen_correct / outer_oxygen,
        factored_first_wave_anchors=len(first.emitted_anchors),
        factored_first_wave_correct=first_correct,
        factored_first_wave_wrong=first_wrong,
        factored_first_wave_precision=first_correct / max(1, first_correct + first_wrong),
        factored_two_wave_anchors=len(second.emitted_anchors),
        factored_two_wave_correct=second_correct,
        factored_two_wave_wrong=second_wrong,
        target_open_count=target_open_count,
        target_used_before_scoring=(grammar.target_used or whole.target_used
                                    or first.target_used or second.target_used),
        first_wave_cross_polytype_gate_passed=(first_correct > 0 and first_wrong == 0),
        sustained_cross_polytype_gate_passed=(second_correct > 0 and second_wrong == 0),
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
