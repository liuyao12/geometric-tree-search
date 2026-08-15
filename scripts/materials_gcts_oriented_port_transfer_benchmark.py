#!/usr/bin/env python3
"""Frozen cross-family transfer audit for irregular oriented ports."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import (
    compile_frozen_target_atlas, compile_irregular_port_program,
    enumerate_frozen_port_occurrences)
from materials_gcts_periodic_growth import replicate


@dataclass(frozen=True)
class OrientedPortTransferCase:
    system: str
    training_atoms: int
    target_atoms: int
    train_port_classes: int
    sampled_target_occurrences: int
    target_pose_failures: int
    target_port_classes: int
    transferred_port_classes: int
    target_overlap_relations: int
    transferred_overlap_relations: int
    port_class_recall: float
    weighted_relation_recall: float
    family_label_used: bool
    target_used_for_fit: bool


@dataclass(frozen=True)
class OrientedPortTransferBenchmark:
    cases: tuple[OrientedPortTransferCase, ...]
    every_family_has_transferred_ports: bool
    all_training_artifacts_frozen: bool


def _key(port):
    return port.parent_type, port.child_type, port.symmetry_orbit_key


def _case(training: AtomicConfiguration,
          target: AtomicConfiguration) -> OrientedPortTransferCase:
    program = compile_irregular_port_program(
        training.species, training.positions)
    frozen = enumerate_frozen_port_occurrences(
        program, target.species, target.positions,
        select_greedy_cover=True)
    target_atlas = compile_frozen_target_atlas(program, frozen)
    train_keys = {_key(port) for port in program.atlas.ports}
    transferred = tuple(port for port in target_atlas.ports
                        if _key(port) in train_keys)
    return OrientedPortTransferCase(
        training.name, len(training.positions), len(target.positions),
        len(program.atlas.ports), len(frozen.occurrences),
        frozen.pose_fit_failures, len(target_atlas.ports), len(transferred),
        target_atlas.witnessed_relations,
        sum(port.observations for port in transferred),
        len(transferred) / max(1, len(target_atlas.ports)),
        sum(port.observations for port in transferred) /
        max(1, target_atlas.witnessed_relations), False, False)


def evaluate() -> OrientedPortTransferBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    nacl_cloud = AtomicConfiguration(nacl.name, nacl.positions, nacl.species)
    iqc, _ = oracle_patch(3, 9.0)
    iqc_target, _ = oracle_patch(4, 15.0)
    cdyb = build_cdyb_split()
    cases = tuple(_case(training, target) for training, target in (
        (nacl_cloud, replicate(nacl)), (iqc, iqc_target),
        (cdyb.training, cdyb.validation)))
    return OrientedPortTransferBenchmark(
        cases, all(case.transferred_port_classes > 0 for case in cases),
        all(not case.family_label_used and not case.target_used_for_fit
            for case in cases))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
