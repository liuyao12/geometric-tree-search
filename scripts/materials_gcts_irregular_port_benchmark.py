#!/usr/bin/env python3
"""Cross-family finite-port benchmark over learned irregular supports."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program


@dataclass(frozen=True)
class IrregularPortCase:
    system: str
    atoms: int
    complete_cover: bool
    repeated_support_types: int
    oriented_prototypes: int
    fitted_occurrences: int
    pose_fit_failures: int
    witnessed_overlap_relations: int
    finite_port_classes: int
    symmetry_orbit_collapses: int
    mean_atoms_shared_per_port: float
    improper_pose_rejections: int
    conflicting_relation_rejections: int


@dataclass(frozen=True)
class IrregularPortBenchmark:
    cases: tuple[IrregularPortCase, ...]
    all_complete: bool
    all_have_finite_ports: bool
    all_poses_proper: bool
    labels_cells_potentials_unused: bool


def _case(configuration: AtomicConfiguration) -> IrregularPortCase:
    program = compile_irregular_port_program(
        configuration.species, configuration.positions)
    atlas = program.atlas
    return IrregularPortCase(
        configuration.name, len(configuration.positions),
        program.cover.complete, program.cover.repeated_type_count,
        len(program.prototypes), len(program.occurrences),
        program.pose_fit_failures, atlas.witnessed_relations,
        len(atlas.ports), atlas.symmetry_orbit_collapses,
        (sum(len(port.overlap) for port in atlas.ports) / len(atlas.ports)
         if atlas.ports else 0.0), atlas.rejected_improper_occurrences,
        atlas.rejected_conflicting_relations)


def evaluate() -> IrregularPortBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    nacl = AtomicConfiguration(nacl.name, nacl.positions, nacl.species)
    iqc, _ = oracle_patch(3, 9.0)
    cdyb = build_cdyb_split().training
    cases = tuple(_case(item) for item in (nacl, iqc, cdyb))
    return IrregularPortBenchmark(
        cases, all(case.complete_cover for case in cases),
        all(case.finite_port_classes > 0 for case in cases),
        all(case.improper_pose_rejections == 0 for case in cases), True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
